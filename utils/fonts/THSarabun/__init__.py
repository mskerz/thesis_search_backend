import os

# กำหนดเส้นทางของฟอนต์
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ชื่อฟอนต์
FONT_REGULAR = os.path.join(BASE_DIR, "THSarabunNew.ttf")
FONT_BOLD = os.path.join(BASE_DIR, "THSarabunNew_Bold.ttf")
FONT_ITALIC = os.path.join(BASE_DIR, "THSarabunNew_Italic.ttf")
FONT_BOLD_ITALIC = os.path.join(BASE_DIR, "THSarabunNew_BoldItalic.ttf")

def get_font(name: str):
    """
    ฟังก์ชันสำหรับส่งคืนเส้นทางฟอนต์ตามชื่อ
    :param name: ชื่อฟอนต์ เช่น 'regular', 'bold', 'italic', 'bold_italic'
    :return: เส้นทางของฟอนต์
    """
    if name == 'regular':
        return FONT_REGULAR
    elif name == 'bold':
        return FONT_BOLD
    elif name == 'italic':
        return FONT_ITALIC
    elif name == 'bold_italic':
        return FONT_BOLD_ITALIC
    else:
        raise ValueError("Font name must be one of: 'regular', 'bold', 'italic', 'bold_italic'")
