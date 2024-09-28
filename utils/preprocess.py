


import io,os
import string
from docx import Document
from fastapi import HTTPException
from pythainlp.corpus import thai_stopwords
from pythainlp.corpus.common import thai_words
from pythainlp.util import Trie
from docx2pdf import convert
import fitz  # PyMuPDF
stop_words = thai_stopwords()
# Define directories for temporary storage


def identity_func(text):
    return text

def perform_removal(word):
    word = word.strip()
    word = word.lower()
    word = word.translate(str.maketrans('', '', string.punctuation))
    unwanted_words = ['ก', 'ข']  # หน้า ก ข 

    if word in stop_words or (word.isdigit() or word in unwanted_words and word not in ["2566", "2565"]):
        return ""  # ลบ stopword และตัวเลขที่ไม่ต้องการ
    else:
        return word

def read_abstract_from_docx(doc) -> str:
    """
    Extracts text from a DOCX file content.

    Args:
        content (bytes): Content of the DOCX file.

    Returns:
        str: Extracted text from the DOCX file.
    """
    # Load the DOCX content
    docx_content = Document(io.BytesIO(doc))
    
    # Extract text from paragraphs
    extracted_text = ""
    start_reading = False
    for paragraph in docx_content.paragraphs:
        if "บทคัดย่อ" in paragraph.text:
            start_reading = True
            continue
        if start_reading:
            extracted_text += paragraph.text.strip() + "\n"
            if "ข" in paragraph.text:
                break

    return extracted_text.strip()



def docx_to_pdf(docx_path, pdf_path):
    convert(docx_path, pdf_path)

def extract_text_from_page(pdf_path, page_number):
    document = fitz.open(pdf_path)
    if page_number < 0 or page_number >= len(document):
        document.close()
        raise HTTPException(status_code=400, detail="Page number out of range.")
    page = document.load_page(page_number)
    text = page.get_text()
    document.close()
    # ตรวจสอบและลบอักขระ "ก" ที่อยู่ด้านหน้าของข้อความ
    if text.startswith("ก"):
        text = text[1:]
    
    return text


def getAbstractPagePDF(pdf_path):
    """
    Args:
        pdf_path (str): The path to the PDF file.

    Returns:
        str: The text from the abstract page if found, otherwise an empty string.
    """
    document = fitz.open(pdf_path)

    # ตรวจสอบว่ามีหน้าในเอกสารหรือไม่
    if len(document) == 0:
        document.close()
        raise ValueError("No pages in PDF document.")
    
    # ตรวจสอบจำนวนหน้าในเอกสาร
    num_pages = len(document)
    
    # ค้นหาหน้าบทคัดย่อ
    for page_number in range(num_pages):
        page = document.load_page(page_number)
        text = page.get_text()
        
        # ตรวจสอบว่ามีคำว่า "บทคัดย่อ" อยู่ในข้อความหรือไม่
        if "บทคัดย่อ" in text:
            # ตรวจสอบและลบอักขระ "ก" ที่อยู่ด้านหน้าของข้อความ
            if text.startswith("ก"):
                text = text[1:]
                
            document.close()
            return text  # คืนค่าข้อความที่พบในหน้าบทคัดย่อ
    
    document.close()
    return ""  # หากไม่พบหน้าบทคัดย่อ

def get_customDict():
    # สร้าง Trie จาก custom dictionary
    words = []
    custom_dict_path = os.path.join(os.getcwd(),'utils','custom_dicts.txt')
    with open(custom_dict_path, 'r', encoding='utf-8') as f:
        for line in f:
            word = line.strip()
            if word:  # ตรวจสอบว่าคำไม่ว่าง
                words.append(word)
    
    # สร้าง Trie ด้วยคำที่อ่านได้
    thaiWord = set(thai_words())
    words = set(words)
    combined_words = thaiWord.union(words)
    
    return Trie(combined_words)





