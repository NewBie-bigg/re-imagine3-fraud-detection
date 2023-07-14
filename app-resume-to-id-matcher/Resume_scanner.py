import cv2
import numpy as np
from docx import Document
import fitz
import face_recognition
from skimage.io import imread
from id_validator import process_document
from google.api_core.exceptions import InvalidArgument
from pdf2image import convert_from_path
import logging as log
import concurrent.futures as threadpools

log.basicConfig(level=log.INFO)
def extract_images_docx(cv_doc):
    log.info("extracting images from document - docx")
    doc = Document(cv_doc)
    iml=[]
    for rel in doc.part.rels.values():
        if "image" in rel.reltype:
            image_data = rel.target_part.blob
            nparr = np.frombuffer(image_data, np.uint8)
            img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            iml.append(img_np)
    return iml

# Function to extract images if the document is of PDF format

def extract_images_pdf(cv_doc):
    log.info("extracting images from document - pdf")
    iml=[]
    # Open the PDF file
    pdf = fitz.open(cv_doc, filetype="pdf")
    for page in pdf:
        pix = page.get_pixmap()
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.h, pix.w, pix.n)
        iml.append(img)
    return iml

def rotate_image(image, angle):
    # Get image dimensions
    height, width = image.shape[:2]

    # Calculate the rotation matrix
    rotation_matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)

    # Apply rotation to the image
    rotated_image = cv2.warpAffine(image, rotation_matrix, (width, height))

    return rotated_image

angles = [30, 60, 90, -30, -60, -90]

def rotate_and_getfaces(image,rotating=False):
    log.info("getting faces")
    faces = []
    # rgb_image = enhanceImage(image)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    rotates=[rgb_image]
    if rotating:
        rotates+=[rotate_image(rgb_image, angle) for angle in angles]
    with threadpools.ThreadPoolExecutor(max_workers=3,thread_name_prefix="worker_") as masterpool:
        futures=masterpool.map(get_face,rotates)
        raw_faces=[future for future in futures]
        faces = [item for sublist in raw_faces for item in sublist]
        masterpool.shutdown(wait=True)

    log.info("found %d faces for the document",len(faces))    
    return faces
def get_face(rt_img):
    l_faces=[]
    log.info("extracting a face...")
        # Detect faces in the image
    face_locations = face_recognition.face_locations(rt_img)
    log.info(" %d locations fetched" , len(face_locations))
    # Extract the face region
    for face_location in face_locations:
        # top, right, bottom, left = face_location
        # face_image = rt_img[top:bottom, left:right]
        face_encoding = face_recognition.face_encodings(
            rt_img, known_face_locations=[face_location], model='large')[0]
        log.info("encodings fetched ... ")
        l_faces.append(face_encoding)
    log.info("faces extracted... ...")
    return l_faces
    
# Function to extract human face Images from PDF or word document


def extract_human_faces(inp_doc, rotating=False):
    log.info("extracting human faces")
    image_list = []
    try:
        if inp_doc.endswith('.docx'):
            image_list=extract_images_docx(inp_doc)
        elif inp_doc.endswith('.pdf'):
            image_list=extract_images_pdf(inp_doc)
        else:
            image_list = [imread(inp_doc)]
        assert(len(image_list)>0)
    except:
        if inp_doc.endswith('.pdf'):
            scannedpdfImages=convert_from_path(inp_doc)
            image_list = [np.array(x) for x in scannedpdfImages]
        else:
            return []
    humanImages = []
    for image in image_list:
        humanImages += rotate_and_getfaces(image,rotating)
    log.info("extracting human faces complete with %d faces",len(humanImages))
    return humanImages

def is_fake(cv_path, id_path,cv_type,id_type):
    # Initializations
    (overallStat, matchtype) = ('FAIL', 'NO-Match')

    (passed_criterias, failed_criterias, analysed_data_id,
     analysed_data_cv) = (None, None, None, None)

    # extract face from CV
    face_from_cv = extract_human_faces(cv_path)
    faces_from_id = extract_human_faces(id_path, rotating=True)
    if (len(faces_from_id) < 1):
        return {
            'CV_MATCH': matchtype,
            'ID-Authentication':None,
            'Id-Summary': "PROVIDED WRONG ID DOCUMENT",
            'Over-All-Status': overallStat}
    if (len(face_from_cv) < 1):
        return {
            'CV_MATCH': matchtype+" PROVIDED CV without a picture ".capitalize(),
            'ID-Authentication':None,
            'Id-Summary': None,
            'Over-All-Status': overallStat}
    for face in face_from_cv:
        matchtype = "Full Match" if sum(face_recognition.compare_faces(
            faces_from_id, face)) != 0 else "No-Match"
        if matchtype != "Full Match":
            return {
            'CV_MATCH': matchtype + " - Faces Don't match ",
            'ID-Authentication':None,
            'Id-Summary': None,
            'Over-All-Status': overallStat}            
    # un-comment theese lines and comment the others to stop the description invocation    
    # return {
    #     'CV_MATCH': matchtype,
    #     'ID-Authentication':None,
    #     'Id-Summary': None,
    #     'Over-All-Status': overallStat}
        
    try:
        (passed_criterias, failed_criterias, analysed_data_id) = process_document(
            id_path, id_type)
    except InvalidArgument as e:
        return {'reason': e.reason, 'metadata': e.metadata,'Over-All-Status': overallStat}

    if (len(passed_criterias) < 3 or (not passed_criterias.__contains__('fraud_signals_is_identity_document'))):

        return {
            'CV_MATCH': matchtype,
            'ID-Authentication':
            {
                'Passed-Checks': passed_criterias,
                'Failed-Checks': failed_criterias
            },
            'Id-Summary': "PROVIDED WRONG ID DOCUMENT",
            'Over-All-Status': overallStat}
    #################
    try:
        analysed_data_cv = process_document(
            cv_path, cv_type, isId=False)
    except InvalidArgument as e:
        return {'reason': e.reason, 'metadata': e.metadata}
        #################
    matchParam = 0
    for key in set("Name,Gender,Birth Date".split(",")):
        matchParam += (1 if (analysed_data_id[key].upper() == analysed_data_cv[key].upper())
                       or (analysed_data_id[key].upper() == 'NONE') or (analysed_data_cv[key].upper() == 'NONE')
                       else 0)
    #################
    if (analysed_data_id['Name'].upper() != 'NONE' and analysed_data_cv['Name'].upper() != 'NONE' and matchParam == 3):
        matchtype = "Full-Match"
        overallStat = 'PASS'
    return ({
        'CV_MATCH': matchtype,
        'ID-Authentication':
        {
            'Passed-Checks': passed_criterias,
            'Failed-Checks': failed_criterias
        },
        'Id-Summary': analysed_data_id,
        'CV-Summary': analysed_data_cv,
        'Over-All-Status': overallStat})
