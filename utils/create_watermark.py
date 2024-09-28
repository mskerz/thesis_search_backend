import fitz  # PyMuPDF
import os
from .fonts.THSarabun import get_font
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class WaterMark:
    def __init__(self, pathPDF):
        self.pathPDF = pathPDF
        self.pdf_document = fitz.open(self.pathPDF)

    def create_watermark_pdf(self, text1: str, temp_watermark_path: str):
        # สร้างไฟล์ PDF ชั่วคราวสำหรับ watermark
        c = canvas.Canvas(temp_watermark_path, pagesize=letter)
        width, height = letter  # ขนาดหน้าของ PDF
        
        # โหลดฟอนต์จากไฟล์
        font_path = get_font('bold')  # เปลี่ยนเป็น 'regular', 'bold', 'italic', 'bold_italic' ตามต้องการ
        pdfmetrics.registerFont(TTFont('THSarabunNew', font_path))

        # ตั้งค่าฟอนต์และขนาด
        c.setFont('THSarabunNew', 40)
        c.setFillColorRGB(0.8, 0.8, 0.8)  # สีเทาอ่อน

         # วางข้อความที่กลางหน้า
        text_width = c.stringWidth(text1, 'THSarabunNew', 40)
        x = (width - text_width) / 2
        y = height / 2

        # เริ่มต้นการวาดข้อความ
        c.saveState()  # เก็บสถานะปัจจุบัน
        c.translate(x + text_width / 2, y)  # ย้ายจุดศูนย์กลางไปที่ตำแหน่ง x,y
        c.rotate(45)  # หมุน 45 องศา
        c.drawString(-text_width / 2, 0, text1)  # วาดข้อความที่จุดใหม่
        c.restoreState()  # คืนสถานะกลับ


        c.save()  # บันทึกไฟล์ PDF ชั่วคราว

    def addWaterMark(self, text: str, output_path: str):
        # สร้างไฟล์ PDF ชั่วคราวสำหรับ watermark
        temp_watermark_path = "temp_watermark.pdf"
        self.create_watermark_pdf(text, temp_watermark_path)

        # วาง watermark ลงในแต่ละหน้าของ PDF
        for page_number in range(self.pdf_document.page_count):
            page = self.pdf_document[page_number]
            rect = page.rect
            
            # นำเข้า watermark
            with fitz.open(temp_watermark_path) as watermark_pdf:
                page.show_pdf_page(rect, watermark_pdf, 0)  # วางซ้อน watermark

        # บันทึกไฟล์ PDF ที่มี Watermark
        self.pdf_document.save(output_path)
        self.pdf_document.close()

        # ลบไฟล์ชั่วคราว
        os.remove(temp_watermark_path)

# ตัวอย่างการใช้งาน
# path = os.path.join(r"D:\รวมวิทยานิพนธ์2566_pdf", "วิศรุต_weaponsdex_วิศรุต_รวมเล่ม.pdf")
# wm = WaterMark(pathPDF=path)
# wm.addWaterMark("ภาควิชาวิทยาการคอมพิวเตอร์และสารสนเทศ", "output.pdf")
