from collections import Counter
from datetime import datetime, timedelta, timezone

import os
import shutil
from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import FileResponse,  JSONResponse
from middleware.authentication import  get_current_user
from utils.preprocess import perform_removal, read_abstract_from_docx, docx_to_pdf, getAbstractPagePDF,get_customDict, read_abstract_from_pdf
from model.advisor import Advisor
from model.user import User
from model.thesis import Term, ThesisCheckResponse, ThesisDocument, ThesisDocumentFormat as Thesis, ThesisFile
from pydantic import ValidationError
from config.db_connect import get_db, session

from pythainlp.tokenize import word_tokenize
from sqlalchemy.exc import IntegrityError
import io

from utils.create_watermark import  WaterMark


thesis_router = APIRouter()





@thesis_router.get('/description/{doc_id}', tags=['User in System'], response_model=Thesis)
async def read_thesis(doc_id: int, db: session = Depends(get_db)):

    # join
    thesis_info = db.query(ThesisDocument, ThesisFile, Advisor, User) \
        .join(ThesisFile, ThesisDocument.doc_id == ThesisFile.doc_id) \
        .join(Advisor, ThesisDocument.advisor_id == Advisor.advisor_id) \
        .join(User, ThesisDocument.user_id == User.user_id) \
        .filter(ThesisDocument.doc_id == doc_id,) \
        .all()
    if not thesis_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Thesis not found")

    thesis_doc, thesis_file, advisor, user = thesis_info[0]
    thesis_description = Thesis(
        doc_id=thesis_doc.doc_id,
        title_th=thesis_doc.title_th,
        title_en=thesis_doc.title_en,
        author_name=f"{user.firstname} {user.lastname}",
        advisor_name=advisor.advisor_name,
        year=thesis_doc.year,
        abstract=thesis_doc.abstract,
    )
    return thesis_description


@thesis_router.get('/download-file/{doc_id}', tags=['User in System'])
async def download_file(doc_id: int, background_tasks: BackgroundTasks,current_user: User = Depends(get_current_user), db: session = Depends(get_db)):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized!")

    # เรียกฟังก์ชันหาข้อมูลไฟล์จากฐานข้อมูลโดยใช้ doc_id
    thesis_file = db.query(ThesisFile).filter(
        ThesisFile.doc_id == doc_id).first()
    if not thesis_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Thesis file not found")

    # สร้างเส้นทางไฟล์ .pdf ที่จะใช้ในการบันทึกไฟล์ .pdf และในการส่งกลับให้ผู้ใช้
    pdf_file_path = os.path.join(
        os.getcwd(), "upload", "pdf", thesis_file.file_name.replace('.docx', '.pdf'))

    # ตรวจสอบว่าไฟล์ .pdf มีอยู่จริงหรือไม่
    if not os.path.exists(pdf_file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF file not found")
    
    # สร้าง watermark ใน PDF
    output_watermark_path = pdf_file_path.replace('.pdf', '_watermarked.pdf')
    wm = WaterMark(pathPDF=pdf_file_path)
    wm.addWaterMark("ภาควิชาวิทยาการคอมพิวเตอร์และสารสนเทศ มก.ฉกส.", output_watermark_path)

    # ตรวจสอบว่าไฟล์ watermark ถูกสร้างหรือไม่
    if not os.path.exists(output_watermark_path):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating watermark")
    # ส่งไฟล์ PDF ที่มี watermark กลับไปยังผู้ใช้ พร้อมลบไฟล์ชั่วคราวหลังจากการส่ง
    response = FileResponse(output_watermark_path, media_type='application/pdf', filename=os.path.basename(output_watermark_path))

    # ลบไฟล์หลังจากการส่ง
    # ลบไฟล์หลังจากการส่งด้วย BackgroundTasks
    background_tasks.add_task(os.remove, output_watermark_path)
    return response
     

 

@thesis_router.get("/check-thesis")
async def check_thesis(
    current_user: User = Depends(get_current_user),
    db: session = Depends(get_db)
):
    if current_user.access_role != 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")   
    thesis = db.query(ThesisDocument).filter(
        ThesisDocument.deleted_at == None,
        ThesisDocument.user_id == current_user.user_id).order_by(ThesisDocument.created_at.desc()).first()
    
        # หากไม่พบ thesis ให้คืนค่า has_thesis เป็น False
    if not thesis:
        return ThesisCheckResponse(
            has_thesis=False,
        )
    
    
 
    thesis_file = db.query(ThesisFile).filter(ThesisFile.doc_id == thesis.doc_id).first()
    advisor = db.query(Advisor).filter(Advisor.advisor_id == thesis.advisor_id).first()
    hasDelete = False

    pdfpath = os.path.join(os.getcwd(), "upload", "pdf",thesis_file.file_name.replace(".docx", ".pdf"))
    
    # ตรวจสอบว่าไฟล์ถูกปฏิเสธหรือไม่
    hasDelete = not os.path.exists(pdfpath) and thesis.recheck_status == 2
 
    return ThesisCheckResponse(
            has_thesis=True,
            has_deleted=hasDelete,
            thesis=Thesis(
                doc_id=thesis.doc_id,
                title_th=thesis.title_th,
                title_en=thesis.title_en,
                author_name=f"{current_user.firstname} {current_user.lastname}",
                advisor_name=advisor.advisor_name,
                recheck_status= thesis.recheck_status,
                year=thesis.year,
                abstract=thesis.abstract
            )
        )


@thesis_router.post('/user/import-thesis', tags=['Student Role Access'])
async def import_thesis(
    title_th: str = Form(...),
    title_en: str = Form(...),
    advisor_id: int = Form(...),
    year: int = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: session = Depends(get_db)
):
    
    """
    Import a thesis document, either in .docx or .pdf format, and save it to the database.

    Args:
        title_th (str): The title of the thesis in Thai.
        title_en (str): The title of the thesis in English.
        advisor_id (int): The ID of the thesis advisor.
        year (int): The year the thesis was written.
        file (UploadFile): The uploaded thesis file, either .docx or .pdf format.
        current_user (User): The current user uploading the thesis (must have student role access).
        db (session): The database session used to interact with the database.

    Description:
        This function handles the import of a thesis document. If the uploaded file is in .docx format, 
        it will be saved, the abstract will be extracted, and the file will be converted to PDF.
        If the file is in .pdf format, the PDF will be saved, and the abstract will be extracted directly from the PDF.
        The function then saves the thesis information and the file details to the database.

    Returns:
        dict: A message indicating whether the thesis was imported successfully or an error message if it fails.
    """
    if current_user.access_role != 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        # บันทึกไฟล์

    upload_folder = os.path.join(os.getcwd(),"upload");
    pdf_location = ''
    file_location = ''  # Ensure both variables are initialized
    if file.filename.endswith('.docx'):
        pdf_location = os.path.join(upload_folder, "pdf",file.filename.replace(".docx", ".pdf"))
        file_location = os.path.join(upload_folder, file.filename)
        # บันทึก DOCX
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
        # อ่านข้อมูลจากไฟล์ DOCX
        with open(file_location, "rb") as file_object:
            content = file_object.read()

        try:
            # อ่าน abstract จาก DOCX
            abstract = read_abstract_from_docx(content)

            # แปลง DOCX เป็น PDF
            docx_to_pdf(file_location, pdf_location)

        except Exception as e:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": str(e)})


    elif file.filename.endswith('.pdf'):
        ""
        pdf_folder = os.path.join(upload_folder, "pdf")
        pdf_location = os.path.join(pdf_folder, file.filename)

         # บันทึกไฟล์ PDF
        with open(pdf_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
        try:
            # อ่าน abstract จาก PDF
            abstract = read_abstract_from_pdf(pdf_location)

        except Exception as e:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": str(e)})
    
    
    # สร้างข้อมูลวิทยานิพนธ์
    import_thesis = ThesisDocument(
        title_th=title_th,
        title_en=title_en,
        user_id=current_user.user_id,
        advisor_id=advisor_id,
        year=year,
        abstract=abstract
    )
    db.add(import_thesis)
    db.commit()
    db.refresh(import_thesis)

    # อัพเดตข้อมูลไฟล์ในฐานข้อมูล
    thesis_file = ThesisFile(
        doc_id=import_thesis.doc_id,
        file_name=file.filename,
        file_path=pdf_location
    )
    db.add(thesis_file)
    db.commit()

    return {"message": "Thesis imported successfully","status": 200}


# Docx Recheck
    # recheck upload data list
@thesis_router.get('/record/thesess-upload', response_model=List[dict], tags=['Admin Management'])
async def show_recheck_list(current_user: User = Depends(get_current_user), db: session = Depends(get_db)):
    """
    Get the list of documents uploaded by students.

    Args:
        current_user (User): The current authenticated user. Automatically provided by the dependency.
        db (Session): The database session. Automatically provided by the dependency.

    Returns:
        List[dict]: The list of uploaded documents with the specified format.
    """
    if current_user.access_role != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    documents = db.query(ThesisDocument).filter(ThesisDocument.deleted_at == None).order_by(
        ThesisDocument.updated_at.desc()).all()
    results = []
    if not documents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No documents found")

    for idx, document in enumerate(documents, start=1):
        user = db.query(User).filter(User.user_id == document.user_id).first()
        advisor = db.query(Advisor).filter(
            Advisor.advisor_id == document.advisor_id).first()
        file = db.query(ThesisFile).filter(
            ThesisFile.doc_id == document.doc_id).first()

        if not user or not advisor or not file:
            continue 

        results.append({
            "idx": idx,
            "doc_id": document.doc_id,
            "title_th": document.title_th,
            "author_name": f"{user.firstname} {user.lastname}",
            "advisor_name": f"{advisor.advisor_name}",
            "recheck_status": document.recheck_status,
            "file_name": file.file_name.replace(".docx",".pdf")
        })

    return results

    # docx preview request show file




@thesis_router.put('/recheck-thesis/{doc_id}/', tags=['Admin Management'])
async def recheck(doc_id: int, status: int = Query(None), current_user: User = Depends(get_current_user), db: session = Depends(get_db)):
    """
    arg: doc_id, recheck_status

    """
    if current_user.access_role != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    file_document = db.query(ThesisFile).filter(
        ThesisFile.doc_id == doc_id).first()
    # Read the thesis file content
    file_path = os.path.join(os.getcwd(), "upload",
                             "docx", file_document.file_name)
    pdf_path = os.path.join(os.getcwd(), "upload", "pdf",
                            file_document.file_name.replace(".docx", ".pdf"))

    # Extract text from the specified page
    docx_text =getAbstractPagePDF(pdf_path=pdf_path)  # หน้าบทคัดย่อ

    custom_dicts = get_customDict()
    # Tokenize the content and remove stop words
    word_seg = word_tokenize(docx_text,custom_dict=custom_dicts, keep_whitespace=False, engine='newmm')
    word_seg = list(map(perform_removal, word_seg))
    filtered_words = list(filter(lambda word: word != '', word_seg))
    # Calculate term frequency manually
    term_frequency = {}
    for word in filtered_words:
        term_frequency[word] = term_frequency.get(word, 0) + 1
    # Convert term frequency to JSON format
    thesis_document = db.query(ThesisDocument).filter(
        ThesisDocument.doc_id == doc_id).first()
    if status == 1:  # Add index
        for term, frequency in term_frequency.items():
            try:
                new_term = Term(term=term, frequency=frequency, doc_id=doc_id)
                db.add(new_term)
            except IntegrityError:
                # Handle case where term already exists (assuming term is unique)
                pass
        thesis_document.recheck_status = status
        thesis_document.updated_at = datetime.now()
        db.commit()
    elif status == 2:  # Delete document
        
        thesis_document.recheck_status = status
        db.commit() 
 
        # Delete the file from the system
        if os.path.exists(file_path):
            os.remove(file_path)

        if os.path.exists(pdf_path):
            os.remove(pdf_path)

        return {"message": "Document deleted successfully."}
        # Clean up temporary files

    return {"message": "Recheck operation completed successfully.", "status": 200}


 
"""
test login 

admin
{
  "email": "wichasin.s@gmail.com",
  "password": "12345678"
}

nisit 1
{
  "email": "teststudent1234@gmail.com",
  "password": "1234567"
}
nisit 2 
{
  "email": "xyz1234@gmail.com",
  "password": "00000"
}

nisit 3
{
  "email": "kashatorn@gmail.com",
  "password": "xyz12345"
}

test import 
{
  "title_th": "ระบบขายเสื้อผ้ามือสอง",
  "title_en": "Used clothing sales system Web Application",
  "advisor_id": 1,
  "year": 2566
}
"""

 