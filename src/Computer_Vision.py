import cv2
import pytesseract
import re
import json
import numpy as np

class ReceiptProcessor:
    def __init__(self, tesseract_path=None):
        """
        Initialize the processor.
        Optionally set the path to the Tesseract executable.
        """
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

    # Phase 1: Image Preprocessing
    
    def preprocess_image(self, image_path):
        """
        Goal: Remove noise, boost contrast, and deskew for better OCR accuracy.
        """
        img = cv2.imread(image_path)

        # 1. Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. Denoising
        denoised = cv2.fastNlMeansDenoising(gray, h=10)

        # 3. Adaptive Thresholding
        binary_img = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

        # 4. Deskewing
        coords = cv2.findNonZero(binary_img)
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        (h, w) = binary_img.shape[:2]
        M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
        deskewed = cv2.warpAffine(binary_img, M, (w, h),
                                  flags=cv2.INTER_CUBIC,
                                  borderMode=cv2.BORDER_REPLICATE)

        return deskewed


    # Phase 2: OCR Extraction

    def extract_raw_text(self, processed_img):
        """
        Goal: Convert pixels into text using Tesseract OCR.
        """
        # Use PSM 6 (assumes a uniform block of text)
        raw_text = pytesseract.image_to_string(processed_img, config="--psm 6")
        return raw_text

   
    # Phase 3: Data Parsing
   
    def parse_data(self, raw_text):
        """
        Goal: Extract TIN, Date, and Total Amount using regex.
        """
        data = {
            "TIN_Number": None,
            "Date": None,
            "Total_Amount": None
        }

        # Ethiopian TIN (10 digits, sometimes prefixed with 'TIN')
        tin_pattern = r'(?:TIN[:\s]*)?(\d{10})'

        # Dates: DD/MM/YYYY, YYYY-MM-DD, or '20 Apr 2026'
        date_pattern = r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\b'

        # Total Amount: handles commas, spaces, decimals
        amount_pattern = r'(?:TOTAL|Total|AMT|Amount)[:\s]*([\d,]+(?:\.\d{2})?)'

        # Extract matches
        tin_match = re.search(tin_pattern, raw_text)
        date_match = re.search(date_pattern, raw_text)
        amount_match = re.search(amount_pattern, raw_text)

        if tin_match:
            data["TIN_Number"] = tin_match.group(1)
        if date_match:
            data["Date"] = date_match.group(1)
        if amount_match:
            data["Total_Amount"] = amount_match.group(1).replace(',', '')

        return data

    # Phase 4: Output Generation    
    def generate_output(self, data, output_path="output.json"):
        """
        Goal: Save extracted data in a structured JSON format.
        """
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=4)    
            
