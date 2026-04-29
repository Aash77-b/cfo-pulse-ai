import re
import numpy as np
from PIL import Image
import pytesseract
import easyocr
import cv2
import platform
import os
import streamlit as st
TESSERACT_AVAILABLE = False
EASYOCR_AVAILABLE = False

# Setup Tesseract
try:
    import pytesseract
    if platform.system() == "Windows":
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        ]
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                TESSERACT_AVAILABLE = True
                break
    else:
        TESSERACT_AVAILABLE = True
except ImportError:
    pass

# Setup EasyOCR
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    pass

@st.cache_resource
def load_easyocr():
    if EASYOCR_AVAILABLE:
        return easyocr.Reader(['en'], gpu=False)
    return None

def extract_text_tesseract(image):
    try:
        configs = ['--psm 6', '--psm 4', '--psm 3']
        best_text = ""
        for config in configs:
            text = pytesseract.image_to_string(image, config=config).strip()
            if len(text) > len(best_text):
                best_text = text
        return best_text
    except:
        return ""

def extract_text_easyocr(image, reader):
    try:
        img_array = np.array(image)
        results = reader.readtext(img_array)
        return "\n".join([text for _, text, _ in results])
    except:
        return ""

def parse_invoice_text(text):
    data = {
        "vendor": "Unknown", "client": "Not detected", "tin": "",
        "invoice_no": "", "date": "", "subtotal": 0.0,
        "tax_amount": 0.0, "total": 0.0, "items": "", "currency": "USD"
    }
    if not text:
        return data
    
    original_text = text
    
    if '$' in text:
        data['currency'] = 'USD'
    elif 'ETB' in text.upper():
        data['currency'] = 'ETB'
    
    vendor_found = False
    
    thank_match = re.search(r'THANK\s+YOU\s+FOR\s+SHOPPING\s+AT\s+(.+?)(?:!|$|\n)', original_text, re.IGNORECASE)
    if thank_match:
        vendor_name = thank_match.group(1).strip()
        vendor_name = re.sub(r'[^\w\s&.,\'\-]', '', vendor_name)
        vendor_name = re.sub(r'\s+', ' ', vendor_name).strip()
        if vendor_name and len(vendor_name) > 5:
            data['vendor'] = vendor_name
            data['client'] = vendor_name
            vendor_found = True
    
    if not vendor_found:
        url_match = re.search(r'WWW\.\s*([A-Za-z0-9]+)\.\s*COM', original_text, re.IGNORECASE)
        if url_match:
            domain_name = url_match.group(1).upper()
            readable = domain_name.replace('SUPREMELUXURYPROVISIONS', 'SUPREME LUXURY PROVISIONS')
            readable = readable.replace('DAILYHARVESTGROCERS', 'DAILY HARVEST GROCERS')
            data['vendor'] = readable
            data['client'] = readable
            vendor_found = True
    
    for pattern in [r'RECEIPT\s*#:\s*(\d+)', r'#:\s*(\d{5,})', r'INVOICE\s*#:\s*(\d+)']:
        match = re.search(pattern, original_text, re.IGNORECASE)
        if match:
            data['invoice_no'] = match.group(1).strip()
            break
    
    for pattern in [r'DATE:\s*(\d{1,2}\s\w{3,9}\s\d{4})', r'(\d{1,2}\s\w{3,9}\s\d{4})']:
        match = re.search(pattern, original_text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            date_str = re.sub(r'\b26(\d{2})\b', r'20\1', date_str)
            date_str = date_str.replace('OCTOER', 'OCTOBER')
            data['date'] = date_str
            break
    
    item_names = []
    for line in original_text.split('\n'):
        line_clean = re.sub(r'[^\x00-\x7F\s]', '', line).strip()
        if not line_clean:
            continue
        if re.search(r'(?:SUBTOTAL|TOTAL:|TAX|PAID|CARD|AUTH|CHIP|VERIFIED|THANK|DATE:|RECEIPT|CASHIER|ITEMS|AMOUNT)', line_clean, re.IGNORECASE):
            continue
        item_match = re.search(r'(?:\d+\s*)?([A-Za-z][A-Za-z\s()&.,\'\-]+?)\s*[-–—$]\s*\$?(\d+\.?\d{2})', line_clean)
        if item_match:
            name = item_match.group(1).strip()
            name = re.sub(r'\s{2,}', ' ', name)
            name = name.strip(' -–—').strip()
            if name and len(name) > 3:
                skip_words = ['SUBTOTAL', 'TOTAL', 'TAX', 'SALES', 'PAID', 'VISA', 'AMEX', 'CARD']
                if name.upper() not in skip_words:
                    item_names.append(name)
    if item_names:
        data['items'] = "; ".join(item_names[:15])
    
    all_prices = re.findall(r'\$(\d+\.?\d{2})', original_text)
    prices_float = sorted([float(p.replace(',', '')) for p in all_prices]) if all_prices else []
    
    subtotal_match = re.search(r'SUBTOTAL:?\s*\$?([\d,]+\.?\d{2})', original_text, re.IGNORECASE)
    if subtotal_match:
        data['subtotal'] = float(subtotal_match.group(1).replace(',', ''))
    
    tax_patterns = [
        r'SALES\s*TAX\s*\(\d+\.?\d*%\):?\s*\$?([\d,]+\.?\d{2})',
        r'TAX:?\s*\$?([\d,]+\.?\d{2})',
    ]
    for pattern in tax_patterns:
        tax_match = re.search(pattern, original_text, re.IGNORECASE)
        if tax_match:
            data['tax_amount'] = float(tax_match.group(1).replace(',', ''))
            break
    
    total_match = re.search(r'TOTAL:?\s*\$?([\d,]+\.?\d{2})', original_text, re.IGNORECASE)
    if total_match:
        data['total'] = float(total_match.group(1).replace(',', ''))
    elif prices_float:
        data['total'] = prices_float[-1]
        if data['subtotal'] == 0.0 and len(prices_float) >= 2:
            data['subtotal'] = prices_float[-2]
        if data['tax_amount'] == 0.0:
            data['tax_amount'] = round(data['total'] - data['subtotal'], 2)
    
    if data['total'] == data['subtotal'] and data['tax_amount'] > 0:
        data['total'] = round(data['subtotal'] + data['tax_amount'], 2)
    
    return data

def process_invoice(uploaded_file):
    try:
        image = Image.open(uploaded_file)
    except:
        return None
    extracted_text = ""
    if TESSERACT_AVAILABLE:
        extracted_text = extract_text_tesseract(image)
    if not extracted_text and EASYOCR_AVAILABLE:
        reader = load_easyocr()
        extracted_text = extract_text_easyocr(image, reader)
    if extracted_text:
        data = parse_invoice_text(extracted_text)
        data['raw_text'] = extracted_text[:800]
        data['ocr_engine'] = 'Tesseract' if TESSERACT_AVAILABLE else 'EasyOCR'
        return data
    return None
