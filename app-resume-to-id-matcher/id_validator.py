from google.cloud import documentai
import vertexai
from vertexai.language_models import TextGenerationModel
import json
import logging as log
log.basicConfig(level=log.INFO)


# Authenticate using default credentials
client = documentai.DocumentProcessorServiceClient()



def extract_and_get_data(project_key, inpText):
    '''
    Description
    -----------
    The method uses vertex-ai 'text-bison' model to take a unstructured and un-clean
    text that is extracted from the OCR of a document file as input and analyse it, after that it extracts the type of the document
    if it finds that the document is an Id document, then it extracts the type of ID it is.
    else it tries to find other relevant information like Name, DOB etc.
    
    Author
    ------
    Anksuk Ray

    '''

    vertexai.init(project=project_key, location="us-central1")
    parameters = {
        "temperature": 0.8,
        "max_output_tokens": 1021,
        "top_p": 1,
        "top_k": 40
    }
    model = TextGenerationModel.from_pretrained("text-bison@001")
    response = model.predict(
        """Inout-1:
        An input will be provided and you have to extract relevant personal information from the data.
        The input will not be clean.
    Input 2:
        parameters to be extracted from the un-clean data which can then be used by python code. data output needs to be in json.

    The parent parameter of the output will be \"Id\" that is the type of the Id document (any of the following type) : Passport,Aadhar, Driving Licence, Permanent Account Number (PAN Card), Voter ID.
    The json output should be constant format and keys must be only those from input 2 and values must be a single string that is not a json.

    If Name has the surname twice , there are high chances that the Father's name is also captured as Name while summarizing. Please re-check and provide ONLY name in Name field.
    
    If Id itself cannot be derived, the document is not an Id document. Treat it as an extract from biodata or resume.
    In that case, 
                    extract the other fields mentioned in input2.
    IF A FIELD IS NOT FOUND, VALUE MUST BE \'None\'

    input: \'B\\nThis passport contains 36 pages.\\nRETURI REPUBLIC OF INDIA\\nan/Type\\nregte / Country Code grete/Passport No.\\nIND\\nS1234567\\nSurname\\nHOOD\\nf/Given Name(s)\\nROBIN\\nfein / Sex\\nDate of Birth\\nerrar/Nationality\\nINDIAN\\nM\\n12/02/1983\\nPlace of Birth\\nKOLKATA, WEST BENGAL\\nv/ Place of 
    input: Id,Number,Name,Gender,Birth Date
    output: {
    \"Id\": \"Passport\",
    \"Number\": \"S1234567\",
    \"Name\": \"ROBIN HOOD\",
    \"Gender\": \"Male\",
    \"Birth Date\": \"12/02/1983\"
    }


    input: \'Diana\\nHighlights\\nRichardson\\nWorks well under pressure\\nExceptional interpersonal skills\\nTrained in liquor, wine, and food service\\nMaster of sales techniques\\nHighly responsible and reliable\\nFood Ingredients expert\\nExperience\\nExperienced Server bringing\\nenthusiasm, dedication and\\nan exceptional work ethic.\\nTrained in customer service\\nwith knowledge of Italy\\ncuisine. High energy and\\noutgoing with a dedication to\\npositive guest relations. High\\nvolume dining customer\\nservice, and cash handling\\nbackground.\\nHead Waiter - 09/2017 to 05/2019\\nMomo Restaurant, New York\\nCoach new waiters and floor staff on guest\\nservice expectations, safety procedures,\\nproper food handling, and restaurant\\nprotocols.\\nMonitor dining room to guarantee optimal\\nguest experiences.\\nWork with individual servers to improve\\nperformance.\\nAnswer customer inquiries and resolve\\nissues immediately.\\n•\\n•\\nContact\\n+1 (970) 333-3833\\ndiana.richardson@mail.com\\nwww.linkedin.com/diana.richardson\\nWaitress - 09/2015 to 05/2017\\nSi Italian Restaurant, New York\\nAnswered questions about menu (elections\\nand made recommendations when\\nrequested).\\nAccurately recorded orders and partnered\\nwith team members to serve food and\\nbeverages.\\nEffectively communicated with kitchen staff\\nregarding customer allergies, dietary needs,\\nand other special requests.\\nConsistently adhered to quality expectations\\nand standards.\\nHobbies\\n•\\n• cooking\\nItalian culture\\n•\\nEducation\\nBachelor of Science: Cook - 2014\\nCookery School (High School), Dublin\\n\'
    input: Id,Number,Name,Gender,Birth Date
    output: {
    \"Id\": \"None\",
    \"Number\": \"None\",
    \"Name\": \"Diana Richardson\",
    \"Gender\": \"Female\",
    \"Birth Date\": \"None\"
    }
    """+"""
    input: """+inpText
    +""" 
    input: Id,Number,Name,Gender,Birth Date """,
        **parameters
    )

    return response.text

def process_document(file_path,content_type,isId:bool=True):
    '''
    Description
    -----------
    The function takes a file and it's content type as input and put's it into a Document-AI processor.
    The processsor identifies if the document is a valid ID or it's manipulated.
    It also extracts the text from the file.

    Author
    ------
    Ankshuk Ray
    '''
    log.info("processing and Verifying ... .. ")

    project_id = "gcds-oht33215u2-2023"
    location = "us"
    processor_id = "a2ede37268d33328"
    
    with open(file_path, "rb") as image:
        image_content = image.read()

    # Create the request
    name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"

    # Load Binary Data into Document AI RawDocument Object
    raw_document = documentai.RawDocument(content=image_content, mime_type=content_type)

    # Configure the process request
    request = documentai.ProcessRequest(
        name=name, raw_document=raw_document
    )

    response = client.process_document(request=request)
    analyzed_text=extract_and_get_data(project_id,response.document.text)
    analyzed_text=analyzed_text.replace("\n", "").replace("output:","").strip()
    # Convert the cleaned string to a dictionary
    analysed_data = json.loads(analyzed_text)
    if not isId:
        return analysed_data
    # Extract the desired information from the response
    # Example: Get the document text
    parameters = list(response.document.entities)
    passed_criterias=list(filter(lambda x:x.normalized_value.text=='PASS',parameters))
    failed_criterias=list(filter(lambda x:x.normalized_value.text!='PASS',parameters))

    log.info("processing and verification complete ... .. ")

    return ({x.type_:x.normalized_value.text for x in passed_criterias},{x.type_:x.normalized_value.text for x in failed_criterias},analysed_data)
