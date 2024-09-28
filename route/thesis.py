from collections import Counter
from datetime import datetime, timedelta, timezone

import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from middleware.authentication import verify_password, create_access_token, hash_password, get_current_user, JWT_EXPIRATION_MINUTES
from utils.preprocess import perform_removal, read_abstract_from_docx, extract_text_from_page, docx_to_pdf, PDF_DIR, DOCX_DIR
from model.advisor import Advisor
from model.user import User
from model.thesis import Term, ThesisResponse, ThesisCheckResponse, ThesisDocument, ThesisDocumentFormat as Thesis, ThesisFile
from pydantic import ValidationError
from config.db_connect import get_db, session, SessionLocal
from docx import Document
from docx2pdf import convert
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from urllib.parse import quote
from pythainlp.tokenize import word_tokenize
from sqlalchemy.exc import IntegrityError
import io


thesis_router = APIRouter()


@thesis_router.get('/thesis-description/{doc_id}', tags=['User in System'], response_model=Thesis)
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
async def download_file(doc_id: int, current_user: User = Depends(get_current_user), db: session = Depends(get_db)):
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

    # ตรวจสอบว่าไฟล์ .pdf มีอยู่แล้วหรือไม่
    if not os.path.exists(pdf_file_path):
        # แปลงไฟล์ .docx เป็น .pdf
        docx_file_path = thesis_file.file_path
        convert(docx_file_path, pdf_file_path)

    # ตรวจสอบว่าไฟล์ .pdf มีอยู่จริงหรือไม่
    if not os.path.exists(pdf_file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PDF file not found")

    # เปิดไฟล์ .pdf เป็นโหมดอ่านแบบ binary
    with open(pdf_file_path, "rb") as pdf_file:
        # ส่งกลับไฟล์ .pdf ให้ผู้ใช้ดาวน์โหลดโดยใช้ StreamingResponse
        return StreamingResponse(io.BytesIO(pdf_file.read()), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={quote(thesis_file.file_name.replace('.docx', '.pdf'))}"})


@thesis_router.get("/check-thesis")
async def check_thesis(
    current_user: User = Depends(get_current_user),
    db: session = Depends(get_db)
):
    thesis = db.query(ThesisDocument).filter(
        ThesisDocument.user_id == current_user.user_id).first()
    if current_user.access_role != 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    if thesis:
        return ThesisCheckResponse(
            has_thesis=True,
            thesis=ThesisResponse(
                doc_id=thesis.doc_id,
                title_th=thesis.title_th,
                title_en=thesis.title_en,
                advisor_id=thesis.advisor_id,
                year=thesis.year
            )
        )
    return ThesisCheckResponse(has_thesis=False)


@thesis_router.post('/student/import-thesis', tags=['Student Role Access'])
async def import_thesis(
    title_th: str = Form(...),
    title_en: str = Form(...),
    advisor_id: int = Form(...),
    year: int = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: session = Depends(get_db)
):

    if current_user.access_role != 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        # บันทึกไฟล์

    file_location = os.path.join(os.getcwd(), "upload", "docx", file.filename)
    pdf_location = os.path.join(
        os.getcwd(), "upload", "pdf", file.filename.replace(".docx", ".pdf"))
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
    # content = await file.read()

    with open(file_location, "rb") as file_object:
        content = file_object.read()

    try:

        abstract = read_abstract_from_docx(content)

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
        # แปลง DOCX เป็น PDF
        docx_to_pdf(file_location, pdf_location)
        # อัพเดตข้อมูลไฟล์ในฐานข้อมูล
        thesis_file = ThesisFile(
            doc_id=import_thesis.doc_id,
            file_name=file.filename,
            file_path=file_location
        )
        db.add(thesis_file)
        db.commit()

        return {"message": "Thesis imported successfully"}

    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": str(e)})


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

    documents = db.query(ThesisDocument).order_by(
        ThesisDocument.created_at.desc()).all()
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


@thesis_router.get('/file-preview/{file_name}', tags=['Admin Management'])
async def file_preview(file_name: str, current_user: User = Depends(get_current_user), db: session = Depends(get_db)):
    """
    Preview file content for the given file name.

    Args:
        file_name (str): The name of the file to be previewed.
        current_user (User): The current authenticated user. Automatically provided by the dependency.
        db (Session): The database session. Automatically provided by the dependency.

    Returns:
        FileResponse: The response containing the file to be previewed.

    Raises:
        HTTPException: If the file is not found in the database or on the disk.
    """
    path = os.path.join(os.getcwd(), "upload", "pdf", file_name)
    if current_user.access_role != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

     # Check if file exists in the database
    thesis_file = db.query(ThesisFile).filter(
        ThesisFile.file_name == file_name).first()
    if not thesis_file:
        raise HTTPException(status_code=404, detail="File not found")

    # Construct the file path
    file_path = thesis_file.file_path

    # Check if file exists on disk
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    # Return file as response
    return FileResponse(path=file_path, filename=file_name, media_type='application/pdf')


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
                            file_document.filename.replace(".docx", ".pdf"))

    # Extract text from the specified page
    docx_text = extract_text_from_page(pdf_path, page_number=4)  # หน้าบทคัดย่อ

    # Tokenize the content and remove stop words
    word_seg = word_tokenize(docx_text, keep_whitespace=False, engine='newmm')
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
        db.commit()
    elif status == 2:  # Delete document
        # delete ThesisDocument where doc_id == doc_id
        thailand_timezone = timezone(timedelta(hours=7))
        thesis_document.deleted_at = datetime.now(thailand_timezone)
        db.commit() 
 
        # Delete the file from the system
        if os.path.exists(file_path):
            os.remove(file_path)

        if os.path.exists(pdf_path):
            os.remove(pdf_path)

        return {"message": "Document deleted successfully."}
        # Clean up temporary files

    return {"message": "Recheck operation completed successfully.", "status": 200}


@thesis_router.post('/word_abstract', tags=['Admin Management'])
async def extract_abstract(file: UploadFile = File(...)):
    if not file.filename.endswith('.docx'):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Please upload a .docx file.")

    try:
        # Define paths for the temporary files
        docx_path = os.path.join(DOCX_DIR, "temp_docx_file.docx")
        pdf_path = os.path.join(PDF_DIR, "temp_pdf_file.pdf")

        # Save the uploaded file to the temporary directory
        with open(docx_path, "wb") as buffer:
            buffer.write(await file.read())

        # Convert DOCX to PDF
        docx_to_pdf(docx_path, pdf_path)

        # Extract text from the specified page
        extracted_text = extract_text_from_page(pdf_path, page_number=4)

        # Process the text
        word_seg = word_tokenize(
            extracted_text, keep_whitespace=False, engine='newmm')
        word_seg = list(map(perform_removal, word_seg))
        filtered_words = list(filter(lambda word: word != '', word_seg))

        # Calculate term frequency
        term_frequency = {}
        for word in filtered_words:
            term_frequency[word] = term_frequency.get(word, 0) + 1

        # Clean up temporary files
        os.remove(docx_path)
        os.remove(pdf_path)

        return {
            "text": " ".join(filtered_words),
            "term": term_frequency
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
