import cv2
import numpy as np
import os
from utils.constants import BIOMETRIC_FILE

def capture_face_from_camera():
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return None, "Cannot access camera."
        for _ in range(15):
            cap.read()
        ret, frame = cap.read()
        cap.release()
        if not ret or frame is None:
            return None, "Failed to capture."
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), None
    except Exception as e:
        return None, f"Camera error: {str(e)}"

def detect_face(image):
    try:
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        return len(faces) > 0, faces
    except:
        return False, []

def save_biometric_data(image, user_id="CFO_Ashenafi"):
    save_dir = os.path.dirname(BIOMETRIC_FILE)
    os.makedirs(save_dir, exist_ok=True)
    filepath = BIOMETRIC_FILE
    cv2.imwrite(filepath, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    return filepath

def load_registered_face():
    if os.path.exists(BIOMETRIC_FILE):
        return cv2.cvtColor(cv2.imread(BIOMETRIC_FILE), cv2.COLOR_BGR2RGB)
    return None

def verify_face_match(captured_image, registered_image):
    if captured_image is None or registered_image is None:
        return False, 0.0, "Missing image data"
    try:
        target_size = (200, 200)
        img1 = cv2.resize(captured_image, target_size)
        img2 = cv2.resize(registered_image, target_size)
        gray1 = cv2.cvtColor(img1, cv2.COLOR_RGB2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_RGB2GRAY)
        hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])
        cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
        cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)
        similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        combined_score = similarity * 0.8 + (1 - np.mean(cv2.absdiff(gray1, gray2))/255) * 0.2
        if combined_score > 0.4:
            return True, combined_score, "Face matched"
        return False, combined_score, "Face does not match"
    except Exception as e:
        return False, 0.0, f"Error: {str(e)}"
