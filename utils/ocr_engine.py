# utils/ocr_engine.py

import re
import numpy as np
from PIL import Image
import pytesseract
import easyocr
import cv2

TESSERACT_AVAILABLE = False
EASYOCR_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except:
    pass

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except:
    pass

def parse_invoice_text(text):
    data = {"vendor": "Unknown", "invoice_no": "", "date": "", "subtotal": 0.0, "tax_amount": 0.0, "total": 0.0, "items": "", "currency": "USD"}
    if not text:
        return data
    
    if '$' in text:
        data['currency'] = 'USD'
    
    thank_match = re.search(r'THANK\s+YOU\s+FOR\s+SHOPPING\s+AT\s+(.+?)(?:!|$|\n)', text, re.I)
    if thank_match:
        data['vendor'] = thank_match.group(1).strip()
    
    total_match = re.search(r'TOTAL:?\s*\$?([\d,]+\.?\d{2})', text, re.I)
    if total_match:
        data['total'] = float(total_match.group(1).replace(',', ''))
    
    return data

def process_invoice(uploaded_file):
    try:
        image = Image.open(uploaded_file)
    except:
        return None
    
    text = ""
    if TESSERACT_AVAILABLE:
        try:
            text = pytesseract.image_to_string(image)
        except:
            pass
    
    if text:
        return parse_invoice_text(text)
    return None
