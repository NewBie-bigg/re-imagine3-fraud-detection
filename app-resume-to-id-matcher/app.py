from Resume_scanner import is_fake
from fastapi import FastAPI, UploadFile, File
import os
import shutil
app = FastAPI()

@app.post("/check_cv")
async def check_cv(cv_file: UploadFile = File(...), id_file: UploadFile = File(...)):
    # Perform your processing logic here with the file contents
    # Call your is_fake function with the file contents
    # Read the uploaded PDF file as bytes

    delete_files("cvs")
    delete_files("ids")
    # Save the CV file
    cv_type=cv_file.content_type
    cv_filename = os.path.join("cvs", cv_file.filename)

    if not(cv_file.filename.endswith(('pdf','docx'))):
        return {"result": "valid CV format are: pdf or docx"}
    
    with open(cv_filename, "wb+") as file_object:
        shutil.copyfileobj(cv_file.file, file_object)

    # Save the ID file
    id_type=id_file.content_type
    id_filename = os.path.join("ids", id_file.filename)
    
    if not(id_file.filename.endswith(('pdf')) or id_file.content_type.startswith('image')):
        return {"result": "valid Id format are: pdf or an image"}

    with open(id_filename, "wb+") as file_object:
        shutil.copyfileobj(id_file.file, file_object)

    result=is_fake(cv_filename,id_filename,cv_type,id_type)
    delete_files("cvs")
    delete_files("ids")
    # Return the result as a response
    # return "success"
    return result

def delete_files(folder_name):
    files = os.listdir(folder_name)
    for file in files:
        os.remove(os.path.join(folder_name, file))
