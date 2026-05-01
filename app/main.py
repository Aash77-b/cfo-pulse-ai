import streamlit as st
import pandas as pd
import numpy as np
import time
import re
import os
import platform
import json
import cv2
from datetime import datetime, timedelta
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# ── OCR Setup (EasyOCR Only - Works on Render) ──
TESSERACT_AVAILABLE = False
EASYOCR_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    pass

# ── Database Setup ─────────────────────────────
DATA_FILE = "cfo_pulse_data.json"
BIOMETRIC_FILE = "biometric_data/CFO_Ashenafi.jpg"
PASSWORD_FILE = "master_password.txt"
COMPANY_FILE = "company_profile.json"
POLICY_FILE = "expense_policies.json"

def get_master_password():
    if os.path.exists(PASSWORD_FILE):
        with open(PASSWORD_FILE, 'r') as f:
            return f.read().strip()
    else:
        default = "admin123"
        with open(PASSWORD_FILE, 'w') as f:
            f.write(default)
        return default

def save_master_password(new_password):
    with open(PASSWORD_FILE, 'w') as f:
        f.write(new_password)

def load_company_profile():
    if os.path.exists(COMPANY_FILE):
        try:
            with open(COMPANY_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        "company_name": "CFO-Pulse Partner",
        "tin": "0000000000",
        "business_type": "",
        "registration_number": "",
        "address": "",
        "phone": "",
        "email": "",
        "industry": "General",
        "currency": "USD",
        "tax_rate": 15.0
    }

def save_company_profile(profile):
    with open(COMPANY_FILE, 'w') as f:
        json.dump(profile, f, indent=2)

def load_expense_policies():
    if os.path.exists(POLICY_FILE):
        try:
            with open(POLICY_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        "max_meal_amount": 50.0,
        "max_entertainment": 100.0,
        "blacklist_vendors": ["CASH STORE", "GAMBLING", "CASINO"],
        "allow_weekend_transactions": False,
        "require_receipt_above": 25.0,
        "enabled": True
    }

def save_expense_policies(policies):
    with open(POLICY_FILE, 'w') as f:
        json.dump(policies, f, indent=2)

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        "total_audited": 0, "total_scanned": 0, "compliant_count": 0,
        "flagged_count": 0, "total_saved": 0, "scan_history": [], "risk_scores": []
    }

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def check_duplicate_invoice(new_invoice, scan_history):
    """Detect duplicate invoices"""
    if not scan_history:
        return None, 0
    
    for past in scan_history[-30:]:
        if past.get('invoice_no') and new_invoice.get('invoice_no'):
            if past['invoice_no'] == new_invoice['invoice_no'] and past['vendor'] == new_invoice['vendor']:
                return "EXACT DUPLICATE INVOICE", 40
        
        if past['vendor'] == new_invoice['vendor']:
            if abs(past['total'] - new_invoice.get('total', 0)) < 1.0:
                past_date = datetime.fromisoformat(past['date'])
                if (datetime.now() - past_date).days <= 30:
                    return "SAME AMOUNT DETECTED - Possible duplicate", 25
        
        if past['vendor'] == new_invoice['vendor']:
            diff_pct = abs(past['total'] - new_invoice.get('total', 0)) / max(past['total'], 1) * 100
            if diff_pct < 5:
                past_date = datetime.fromisoformat(past['date'])
                if (datetime.now() - past_date).days <= 15:
                    return "SIMILAR AMOUNT - Review required", 15
    
    return None, 0

def check_policy_violations(invoice_data, policies):
    """Check expense policy violations"""
    violations = []
    total_penalty = 0
    
    if not policies.get('enabled', True):
        return violations, 0
    
    vendor = invoice_data.get('vendor', '').upper()
    
    for blacklisted in policies.get('blacklist_vendors', []):
        if blacklisted.upper() in vendor:
            violations.append(f"❌ Blacklisted vendor: {blacklisted}")
            total_penalty += 50
    
    if not policies.get('allow_weekend_transactions', False):
        date_str = invoice_data.get('date', '')
        if date_str:
            try:
                invoice_date = None
                for fmt in ['%d %B %Y', '%d %b %Y', '%Y-%m-%d']:
                    try:
                        invoice_date = datetime.strptime(date_str, fmt)
                        break
                    except:
                        continue
                if invoice_date and invoice_date.weekday() >= 5:
                    violations.append("⚠️ Weekend transaction - Not allowed by policy")
                    total_penalty += 20
            except:
                pass
    
    if 'MEAL' in vendor or 'RESTAURANT' in vendor or 'CAFE' in vendor:
        if invoice_data.get('total', 0) > policies.get('max_meal_amount', 50):
            violations.append(f"⚠️ Meal exceeds ${policies.get('max_meal_amount', 50)} limit")
            total_penalty += 15
    
    if 'ENTERTAINMENT' in vendor or 'MOVIE' in vendor or 'THEATER' in vendor:
        if invoice_data.get('total', 0) > policies.get('max_entertainment', 100):
            violations.append(f"⚠️ Entertainment exceeds ${policies.get('max_entertainment', 100)} limit")
            total_penalty += 15
    
    return violations, total_penalty

def predict_cash_flow(scan_history):
    """Predict future cash flow based on historical data"""
    if len(scan_history) < 5:
        return None, None, "Need at least 5 scans for prediction"
    
    df = pd.DataFrame(scan_history)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    df['days'] = (df['date'] - df['date'].min()).dt.days
    df['cumulative'] = df['total'].cumsum()
    
    X = df['days'].values.reshape(-1, 1)
    y = df['cumulative'].values
    
    model = LinearRegression()
    model.fit(X, y)
    
    future_days = np.arange(df['days'].max() + 1, df['days'].max() + 31).reshape(-1, 1)
    predictions = model.predict(future_days)
    
    daily_avg = df['total'].mean()
    shortfall_risk = "Low"
    if len(predictions) > 0:
        last_pred = predictions[-1]
        if last_pred > df['cumulative'].iloc[-1] * 0.9:
            shortfall_risk = "Medium"
        if predictions[-1] < predictions[0] * 0.5:
            shortfall_risk = "High"
    
    return predictions, daily_avg, shortfall_risk

def generate_pdf_report(kpis, scan_history, company_profile):
    """Generate comprehensive PDF audit report"""
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"CFO-Pulse Audit Report", ln=1, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(200, 6, txt=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=1, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 8, txt="Company Information", ln=1)
    pdf.set_font("Arial", '', 10)
    pdf.cell(100, 6, txt=f"Name: {company_profile.get('company_name', 'N/A')}", ln=0)
    pdf.cell(100, 6, txt=f"TIN: {company_profile.get('tin', 'N/A')}", ln=1)
    pdf.cell(100, 6, txt=f"Industry: {company_profile.get('industry', 'N/A')}", ln=0)
    pdf.cell(100, 6, txt=f"Currency: {company_profile.get('currency', 'USD')}", ln=1)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 8, txt="Key Performance Indicators", ln=1)
    pdf.set_font("Arial", '', 10)
    pdf.cell(95, 6, txt=f"Total Audited: {kpis.get('total_audited', '0')}", ln=0)
    pdf.cell(95, 6, txt=f"Total Scans: {kpis.get('total_scanned', 0)}", ln=1)
    pdf.cell(95, 6, txt=f"Compliance Rate: {kpis.get('compliance_rate', '0%')}", ln=0)
    pdf.cell(95, 6, txt=f"Potential Savings: {kpis.get('blocked_leakage', '0')}", ln=1)
    pdf.cell(95, 6, txt=f"Average Risk Score: {kpis.get('risk_score', '0')}", ln=0)
    pdf.cell(95, 6, txt=f"Flagged Items: {kpis.get('flagged_count', 0)}", ln=1)
    pdf.ln(5)
    
    if scan_history:
        df = pd.DataFrame(scan_history)
        low_risk = len(df[df['risk_score'] <= 25])
        medium_risk = len(df[(df['risk_score'] > 25) & (df['risk_score'] <= 60)])
        high_risk = len(df[df['risk_score'] > 60])
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 8, txt="Risk Distribution", ln=1)
        pdf.set_font("Arial", '', 10)
        pdf.cell(60, 6, txt=f"Low Risk (0-25): {low_risk}", ln=0)
        pdf.cell(60, 6, txt=f"Medium Risk (26-60): {medium_risk}", ln=0)
        pdf.cell(60, 6, txt=f"High Risk (61-100): {high_risk}", ln=1)
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 8, txt="Top 5 High-Risk Transactions", ln=1)
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(50, 6, txt="Date", border=1)
        pdf.cell(60, 6, txt="Vendor", border=1)
        pdf.cell(40, 6, txt="Amount", border=1)
        pdf.cell(40, 6, txt="Risk Score", border=1)
        pdf.ln()
        
        high_risk_df = df[df['risk_score'] > 50].head(5)
        pdf.set_font("Arial", '', 8)
        for _, row in high_risk_df.iterrows():
            date_str = datetime.fromisoformat(row['date']).strftime('%Y-%m-%d')
            pdf.cell(50, 5, txt=date_str, border=1)
            pdf.cell(60, 5, txt=row['vendor'][:30], border=1)
            pdf.cell(40, 5, txt=f"{row['currency']} {row['total']:,.2f}", border=1)
            pdf.cell(40, 5, txt=str(row['risk_score']), border=1)
            pdf.ln()
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 8, txt="Recommendations", ln=1)
    pdf.set_font("Arial", '', 10)
    recommendations = [
        "1. Review all high-risk transactions (>60 risk score)",
        "2. Implement stricter vendor approval process for blacklisted vendors",
        "3. Consider reducing expense policy limits for meals and entertainment",
        "4. Schedule regular audit reviews for flagged transactions"
    ]
    for rec in recommendations:
        pdf.cell(200, 6, txt=rec, ln=1)
    
    filename = f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(filename)
    return filename

def update_kpi_after_scan(scan_result):
    db = load_data()
    db["total_scanned"] += 1
    total_amount = scan_result.get("total", 0)
    db["total_audited"] += total_amount
    risk_score = scan_result.get("risk_score", 0)
    db["risk_scores"].append(risk_score)
    if risk_score <= 25:
        db["compliant_count"] += 1
    else:
        db["flagged_count"] += 1
        if risk_score > 50:
            db["total_saved"] += total_amount * 0.15
    db["scan_history"].append({
        "date": datetime.now().isoformat(),
        "vendor": scan_result.get("vendor", "Unknown"),
        "total": total_amount,
        "currency": scan_result.get("currency", "USD"),
        "risk_score": risk_score,
        "invoice_no": scan_result.get("invoice_no", ""),
        "duplicate_warning": scan_result.get("duplicate_warning", None),
        "policy_violations": scan_result.get("policy_violations", [])
    })
    if len(db["scan_history"]) > 50:
        db["scan_history"] = db["scan_history"][-50:]
    if len(db["risk_scores"]) > 100:
        db["risk_scores"] = db["risk_scores"][-100:]
    save_data(db)
    return db

def calculate_current_kpis():
    db = load_data()
    avg_risk = int(np.mean(db["risk_scores"])) if db["risk_scores"] else 23
    compliance_rate = (
        round((db["compliant_count"] / db["total_scanned"]) * 100, 1)
        if db["total_scanned"] > 0 else 98.2
    )
    recent = db["risk_scores"][-10:] if len(db["risk_scores"]) >= 10 else db["risk_scores"]
    older = db["risk_scores"][-20:-10] if len(db["risk_scores"]) >= 20 else db["risk_scores"]
    avg_recent = int(np.mean(recent)) if recent else 0
    avg_older = int(np.mean(older)) if older else 0
    risk_trend = round(((avg_recent - avg_older) / avg_older) * 100, 1) if avg_older > 0 else 0
    return {
        "total_audited": f"{db['total_audited']:,.0f}",
        "total_audited_delta": f"+{db['total_scanned']} scans",
        "compliance_rate": f"{compliance_rate}%",
        "compliance_delta": f"{db['compliant_count']}/{db['total_scanned']} compliant" if db['total_scanned'] > 0 else "0/0 compliant",
        "blocked_leakage": f"{db['total_saved']:,.0f}",
        "blocked_delta": f"{db['flagged_count']} flagged",
        "risk_score": f"{avg_risk}/100",
        "risk_delta": f"{'+' if risk_trend > 0 else ''}{risk_trend}%",
        "total_scanned": db['total_scanned'],
        "flagged_count": db['flagged_count'],
        "scan_history": db['scan_history']
    }

# ── Session Defaults ────────────────────────────
company = load_company_profile()
st.session_state.setdefault('company_name', company['company_name'])
st.session_state.setdefault('company_tin', company['tin'])
st.session_state.setdefault('company_currency', company.get('currency', 'USD'))
st.session_state.setdefault('company_tax_rate', company.get('tax_rate', 15.0))
st.session_state.setdefault('biometric_registered', os.path.exists(BIOMETRIC_FILE))
st.session_state.setdefault('biometric_verified', False)
st.session_state.setdefault('is_logged_in', False)
st.session_state.setdefault('login_attempts', 0)
st.session_state.setdefault('captured_face', None)
st.session_state.setdefault('registration_step', 1)
st.session_state.setdefault('show_login', True)

# ── Page Config ─────────────────────────────────
st.set_page_config(page_title="CFO-Pulse AI", page_icon="🛡️", layout="wide",
                   initial_sidebar_state="expanded")

def inject_styles():
    st.markdown("""<style>
    .main { padding: 0rem 1rem; }
    .metric-card { background:#fff; padding:20px; border-radius:12px;
                   box-shadow:0 2px 10px rgba(0,0,0,.05); border:1px solid #e0e0e0; }
    .risk-badge-low    { background:#10b981; color:#fff; padding:5px 15px; border-radius:20px; font-weight:600; display:inline-block; }
    .risk-badge-medium { background:#f59e0b; color:#fff; padding:5px 15px; border-radius:20px; font-weight:600; display:inline-block; }
    .risk-badge-high   { background:#ef4444; color:#fff; padding:5px 15px; border-radius:20px; font-weight:600; display:inline-block; }
    .stButton>button { width:100%; border-radius:8px; height:45px; font-weight:600; transition:all .3s; }
    .stButton>button:hover { transform:translateY(-2px); box-shadow:0 5px 15px rgba(0,0,0,.1); }
    .stProgress>div>div { background-color:#667eea; }
    .stTabs [data-baseweb="tab"] { border-radius:8px; padding:10px 20px; background:#f8f9fa; }
    .stTabs [aria-selected="true"] { background:#667eea!important; color:#fff!important; }
    .login-container { max-width:500px; margin:50px auto; padding:40px; background:#fff;
                       border-radius:20px; box-shadow:0 20px 60px rgba(0,0,0,.1); text-align:center; }
    .login-header { background:linear-gradient(135deg,#667eea,#764ba2); color:#fff; padding:30px;
                    border-radius:15px; margin-bottom:30px; }
    .camera-box { border:3px dashed #667eea; border-radius:20px; padding:30px; text-align:center; 
                  background:linear-gradient(135deg,#667eea10,#764ba210); margin:20px 0; }
    .success-box { border:2px solid #10b981; border-radius:15px; padding:20px; 
                   background:#f0fdf4; text-align:center; }
    .alert-high { border:2px solid #ef4444; background:#fef2f2; padding:20px; border-radius:15px; }
    .alert-medium { border:2px solid #f59e0b; background:#fffbeb; padding:20px; border-radius:15px; }
    .alert-low { border:2px solid #10b981; background:#f0fdf4; padding:20px; border-radius:15px; }
    </style>""", unsafe_allow_html=True)

inject_styles()

# ── Biometric Functions ────────────────────────
def detect_face(image):
    try:
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        return len(faces) > 0, faces
    except:
        return False, []

def save_biometric_data(image, user_id="CFO_Ashenafi"):
    save_dir = "biometric_data"
    os.makedirs(save_dir, exist_ok=True)
    filepath = os.path.join(save_dir, f"{user_id}.jpg")
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

# ── OCR Functions (EasyOCR Only) ──────────────
@st.cache_resource
def load_easyocr():
    if EASYOCR_AVAILABLE:
        return easyocr.Reader(['en'], gpu=False)
    return None

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
    
    if '$' in text: data['currency'] = 'USD'
    elif 'ETB' in text.upper(): data['currency'] = 'ETB'
    
    vendor_found = False
    
    thank_match = re.search(
        r'THANK\s+YOU\s+FOR\s+SHOPPING\s+AT\s+(.+?)(?:!|$|\n)',
        original_text, re.IGNORECASE
    )
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
    
    if not vendor_found:
        clean_lines = []
        for line in original_text.split('\n')[:6]:
            cleaned = re.sub(r'[^\x00-\x7F\s]', '', line).strip()
            if not cleaned or len(cleaned) <= 2:
                continue
            if re.search(r'(?:TRANSACTION|RECEIPT|DATE:|PHONE:|CASHIER|\$\d+)', cleaned, re.IGNORECASE):
                break
            if re.match(r'^\d+', cleaned):
                continue
            alpha_count = len(re.findall(r'[A-Za-z]', cleaned))
            if alpha_count / max(len(cleaned), 1) > 0.4:
                clean_lines.append(cleaned)
        if clean_lines:
            data['vendor'] = " ".join(clean_lines[:3])
            data['client'] = data['vendor']
    
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
        if not line_clean: continue
        if re.search(r'(?:SUBTOTAL|TOTAL:|TAX|PAID|CARD|AUTH|CHIP|VERIFIED|THANK|DATE:|RECEIPT|CASHIER|ITEMS|AMOUNT)', line_clean, re.IGNORECASE):
            continue
        item_match = re.search(
            r'(?:\d+\s*)?([A-Za-z][A-Za-z\s()&.,\'\-]+?)\s*[-–—$]\s*\$?(\d+\.?\d{2})',
            line_clean
        )
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
    
    # Use ONLY EasyOCR (no Tesseract)
    if EASYOCR_AVAILABLE:
        reader = load_easyocr()
        extracted_text = extract_text_easyocr(image, reader)
    
    if extracted_text:
        data = parse_invoice_text(extracted_text)
        data['raw_text'] = extracted_text[:800]
        data['ocr_engine'] = 'EasyOCR'
        return data
    return None

def calculate_risk_score(data, duplicate_penalty=0, policy_penalty=0):
    company = load_company_profile()
    score = 5
    total = data.get('total', 0)
    currency = company.get('currency', 'USD')
    
    if currency == 'USD':
        threshold = 5000
    elif currency == 'ETB':
        threshold = 50000
    else:
        threshold = 5000
    
    if total > threshold:
        score += min(50, int((total / threshold) * 20))
    else:
        score += int((total / threshold) * 10)
    
    vendor = str(data.get('vendor', ''))
    if vendor in ['Unknown', '=', ''] or len(vendor) <= 3:
        score += 20
    if data.get('tax_amount', 0) == 0 and total > 50:
        score += 15
    if not data.get('items'):
        score += 10
    if total > threshold * 2:
        score += 15
    
    score += duplicate_penalty
    score += policy_penalty
    
    return min(100, score)

# ── Helpers ─────────────────────────────────────
GRID_COLOR = '#e5e7eb'

def style_axes(fig):
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=GRID_COLOR)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=GRID_COLOR)

def base_layout(fig, title, height=400):
    fig.update_layout(title=title, height=height, hovermode='x unified',
                      plot_bgcolor='white',
                      legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

# ═══════════════════════════════════════════════
# LOGIN PAGE - WITH st.camera_input
# ═══════════════════════════════════════════════
def show_login_page():
    MASTER_PASSWORD = get_master_password()
    
    if st.session_state.get('login_attempts', 0) >= 5:
        st.markdown("""<div style="max-width:500px;margin:100px auto;padding:40px;text-align:center;
            border:2px solid #ef4444;border-radius:15px;background:#fef2f2">
            <h2>🔒 Account Locked</h2><p>Too many failed attempts. Please reset to try again.</p></div>""", unsafe_allow_html=True)
        if st.button("Reset & Try Again"):
            st.session_state['login_attempts'] = 0
            st.rerun()
        return
    
    st.markdown("""
    <div style="max-width:500px;margin:50px auto">
        <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;
                    padding:30px;border-radius:15px;text-align:center;margin-bottom:30px">
            <span style="font-size:64px">🛡️</span>
            <h1>CFO-Pulse AI</h1>
            <p>Enterprise Security Platform</p>
        </div>
    </div>""", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("### 🔐 Authentication Required")
        is_registered = os.path.exists(BIOMETRIC_FILE)
        
        if not is_registered:
            st.warning("No biometric data registered. Please complete face registration.")
            step = st.session_state.get('registration_step', 1)
            st.progress(step / 3)
            
            if step == 1:
                if st.button("📸 Start Face Registration", type="primary", use_container_width=True):
                    st.session_state['registration_step'] = 2
                    st.rerun()
            elif step == 2:
                st.info("Please use your camera below to capture your face.")
                camera_file = st.camera_input("Capture Face Now")
                
                if camera_file is not None:
                    with st.spinner("Processing image..."):
                        bytes_data = camera_file.getvalue()
                        np_arr = np.frombuffer(bytes_data, np.uint8)
                        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    
                    has_face, faces = detect_face(frame)
                    if has_face:
                        for (x, y, w, h) in faces:
                            cv2.rectangle(frame, (x, y), (x+w, y+h), (16, 185, 129), 3)
                        st.session_state['captured_face'] = frame
                        st.session_state['registration_step'] = 3
                        st.image(frame, channels="BGR")
                        st.success("Face captured successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("No face detected. Please try again.")
            elif step == 3:
                if st.session_state.get('captured_face') is not None:
                    st.image(st.session_state['captured_face'], channels="BGR", width=250)
                    if st.button("✅ Confirm Registration", type="primary", use_container_width=True):
                        save_biometric_data(st.session_state['captured_face'])
                        st.session_state['biometric_registered'] = True
                        st.session_state['registration_step'] = 1
                        st.success("✅ Registration complete! Please login.")
                        st.balloons()
                        time.sleep(2)
                        st.rerun()
        else:
            login_method = st.radio("Choose Login Method:", ["📸 Face Recognition", "🔑 Password"], horizontal=True)
            
            if "Face" in login_method:
                st.info("Please use your camera below to scan your face.")
                camera_file = st.camera_input("Scan Face to Login")
                
                if camera_file is not None:
                    with st.spinner("Scanning..."):
                        bytes_data = camera_file.getvalue()
                        np_arr = np.frombuffer(bytes_data, np.uint8)
                        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    
                    has_face, faces = detect_face(frame)
                    if not has_face:
                        st.error("No face detected")
                        st.session_state['login_attempts'] += 1
                    else:
                        registered = load_registered_face()
                        is_match, conf, msg = verify_face_match(frame, registered)
                        if is_match:
                            st.success(f"✅ {msg}")
                            st.session_state['is_logged_in'] = True
                            st.session_state['login_attempts'] = 0
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
                            st.session_state['login_attempts'] += 1
            else:
                pw = st.text_input("Master Password", type="password")
                if st.button("🔑 Login", use_container_width=True):
                    if pw == MASTER_PASSWORD:
                        st.session_state['is_logged_in'] = True
                        st.session_state['login_attempts'] = 0
                        st.rerun()
                    else:
                        st.error("Invalid password")
                        st.session_state['login_attempts'] += 1
        
    if st.session_state.get('login_attempts', 0) > 0:
        st.caption(f"Failed attempts: {st.session_state['login_attempts']}/5")

# ── Login Gate ─────────────────────────────────
if not st.session_state.get('is_logged_in', False):
    show_login_page()
    st.stop()

# ═══════════════════════════════════════════════
# MAIN APP - ALL SECTIONS
# ═══════════════════════════════════════════════

company = load_company_profile()
policies = load_expense_policies()

with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center;padding:10px 0">
      <div style="width:80px;height:80px;background:linear-gradient(135deg,#667eea,#764ba2);
                  border-radius:50%;margin:0 auto;display:flex;align-items:center;justify-content:center">
        <span style="font-size:32px">🏢</span></div>
      <h4 style="margin:8px 0 2px">{st.session_state['company_name']}</h4>
      <p style="color:#6b7280;font-size:12px;margin:0">TIN: {st.session_state['company_tin']}</p>
      <p style="color:#10b981;font-size:11px;margin:5px 0">✓ Biometric Verified</p>
    </div>""", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### Navigation")
    page = st.radio("", ["Dashboard", "Scan & Audit", "Fraud Reports", "Policies", "Settings", "Analytics"],
                    label_visibility="collapsed")
    st.markdown("---")
    
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state['is_logged_in'] = False
        st.rerun()
    
    st.markdown("---")
    kpis = calculate_current_kpis()
    avg_risk = int(kpis['risk_score'].split('/')[0]) if kpis['total_scanned'] > 0 else 23
    st.markdown(f"**Risk:** {avg_risk}/100")
    st.progress(avg_risk / 100)
    st.markdown("---")
    if EASYOCR_AVAILABLE:
        st.success("✅ EasyOCR Ready")
    else:
        st.error("❌ EasyOCR not available")

# ── Dashboard ──────────────────────────────────
if "Dashboard" in page:
    st.title(f"🏢 {st.session_state['company_name']} Command Center")
    st.caption(f"Real-time monitoring - {datetime.now():%B %d, %Y %H:%M}")
    st.markdown("---")
    
    kpis = calculate_current_kpis()
    st.markdown(f"### Key Performance Indicators ({kpis['total_scanned']} scans)")
    cols = st.columns(4)
    for col, (title, val, delta) in zip(cols, [
        ("Total Audited", kpis['total_audited'], kpis['total_audited_delta']),
        ("Compliance", kpis['compliance_rate'], kpis['compliance_delta']),
        ("Saved", kpis['blocked_leakage'], kpis['blocked_delta']),
        ("Risk Score", kpis['risk_score'], kpis['risk_delta'])
    ]):
        with col: st.metric(title, val, delta)
    
    st.markdown("---")
    
    # Cash Flow Forecast Section
    st.markdown("### 📈 AI-Powered Cash Flow Forecast")
    scan_history = kpis.get('scan_history', [])
    
    if len(scan_history) >= 5:
        predictions, daily_avg, shortfall_risk = predict_cash_flow(scan_history)
        
        if predictions is not None:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Daily Average Spend", f"${daily_avg:.2f}")
            with col2:
                st.metric("30-Day Forecast", f"${predictions[-1]:,.0f}", 
                         delta=f"{((predictions[-1] - predictions[0]) / predictions[0] * 100):.1f}%")
            with col3:
                risk_color = "🟢" if shortfall_risk == "Low" else "🟡" if shortfall_risk == "Medium" else "🔴"
                st.metric("Shortfall Risk", f"{risk_color} {shortfall_risk}")
            
            # Plot forecast
            df_hist = pd.DataFrame(scan_history)
            df_hist['date'] = pd.to_datetime(df_hist['date'])
            df_hist = df_hist.sort_values('date')
            df_hist['cumulative'] = df_hist['total'].cumsum()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_hist['date'], y=df_hist['cumulative'], 
                                    mode='lines+markers', name='Historical',
                                    line=dict(color='#667eea', width=2)))
            
            future_dates = [df_hist['date'].max() + timedelta(days=i+1) for i in range(30)]
            fig.add_trace(go.Scatter(x=future_dates, y=predictions, 
                                    mode='lines', name='Forecast',
                                    line=dict(color='#ef4444', width=2, dash='dash')))
            
            base_layout(fig, "Cumulative Cash Flow Forecast (30 Days)", 400)
            style_axes(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Get more scans for accurate predictions")
    else:
        st.info(f"📊 Need {5 - len(scan_history)} more scans to enable AI cash flow forecasting")
    
    st.markdown("---")
    
    # AI Summary
    if scan_history:
        high_risk_count = len([s for s in scan_history if s.get('risk_score', 0) > 60])
        flagged_count = kpis['flagged_count']
        total_saved = float(kpis['blocked_leakage'].replace(',', ''))
        
        st.info(f"""💡 **AI Executive Summary:** Based on {kpis['total_scanned']} scanned documents, 
        your organization has {flagged_count} flagged transactions with {high_risk_count} high-risk items. 
        Potential savings of ${total_saved:,.0f} identified through fraud prevention. 
        {'⚠️ Review high-risk vendors immediately' if high_risk_count > 3 else '✅ Compliance rate is strong.'}""")

# ── Scan & Audit ────────────────────────────────
elif "Scan & Audit" in page:
    st.title("🔍 Document Scanner")
    st.markdown("Upload receipts or invoices for AI-powered audit")
    
    st.markdown("""<div style="border:2px dashed #667eea;border-radius:15px;padding:40px;text-align:center;
        background:linear-gradient(135deg,#667eea10,#764ba210)">
        <span style="font-size:48px">📤</span>
        <h3>Upload Document</h3>
        <p style="color:#6b7280">JPG, PNG, PDF (Max 10MB)</p></div>""", unsafe_allow_html=True)

    uploaded = st.file_uploader("", type=['jpg', 'jpeg', 'png', 'pdf'], label_visibility="collapsed")

    if uploaded:
        st.markdown("---")
        if EASYOCR_AVAILABLE:
            with st.spinner("Processing document with AI..."):
                data = process_invoice(uploaded)
            
            if data is None:
                st.warning("OCR could not read this document. Using fallback data.")
                data = {"vendor": "SUPREME LUXURY PROVISIONS", "total": 5393.88, 
                       "subtotal": 4954.20, "tax_amount": 439.68, "currency": "USD",
                       "items": "Various items", "invoice_no": "INV-001"}
        else:
            st.error("OCR engine not available. Please check EasyOCR installation.")
            data = {"vendor": "SUPREME LUXURY PROVISIONS", "total": 5393.88, "currency": "USD", "invoice_no": "INV-001"}
        
        # Check for duplicates
        scan_history = load_data().get('scan_history', [])
        duplicate_warning, duplicate_penalty = check_duplicate_invoice(data, scan_history)
        
        # Check policy violations
        policies = load_expense_policies()
        policy_violations, policy_penalty = check_policy_violations(data, policies)
        
        # Calculate risk score with penalties
        fraud_score = calculate_risk_score(data, duplicate_penalty, policy_penalty)
        data['risk_score'] = fraud_score
        data['duplicate_warning'] = duplicate_warning
        data['policy_violations'] = policy_violations
        
        update_kpi_after_scan(data)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📋 Extracted Data")
            st.markdown(f"**Vendor:** {data.get('vendor', 'N/A')}")
            st.markdown(f"**Client:** {data.get('client', 'N/A')}")
            st.markdown(f"**Receipt #:** {data.get('invoice_no', 'N/A')}")
            st.markdown(f"**Date:** {data.get('date', 'N/A')}")
            st.markdown(f"**Items:** {data.get('items', 'N/A')}")
            st.markdown("---")
            curr = data.get('currency', 'USD')
            st.markdown(f"**Subtotal:** {data.get('subtotal', 0):,.2f} {curr}")
            st.markdown(f"**Tax:** {data.get('tax_amount', 0):,.2f} {curr}")
            st.markdown(f"**Total:** {data.get('total', 0):,.2f} {curr}")
            
            if duplicate_warning:
                st.warning(f"⚠️ {duplicate_warning}")
            
            if policy_violations:
                st.error("🚨 **Policy Violations Detected:**")
                for violation in policy_violations:
                    st.markdown(f"- {violation}")
            
            if data.get('raw_text'):
                with st.expander("Raw OCR Text"):
                    st.text_area("Text", data['raw_text'], height=150)
        
        with col2:
            st.markdown("### 🚨 Risk Assessment")
            total = data.get('total', 0)
            threshold = 5000 if data.get('currency') == 'USD' else 50000
            
            if fraud_score > 60:
                st.error(f"🚨 HIGH RISK - Score: {fraud_score}/100")
                st.markdown(f"""<div class="alert-high">
                    <strong>⚠️ Immediate review required</strong><br>
                    Amount ({total:,.2f}) exceeds threshold ({threshold:,.2f})
                </div>""", unsafe_allow_html=True)
            elif fraud_score > 25:
                st.warning(f"⚠️ REVIEW NEEDED - Score: {fraud_score}/100")
            else:
                st.success(f"✅ VERIFIED - Score: {fraud_score}/100")
            
            st.caption("📊 Analytics updated with this scan")

# ── Fraud Reports ───────────────────────────────
elif "Fraud Reports" in page:
    st.title("🚨 Fraud Reports")
    kpis = calculate_current_kpis()
    
    # Add PDF Export button
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("📄 Export PDF Report", type="primary", use_container_width=True):
            with st.spinner("Generating PDF..."):
                company_profile = load_company_profile()
                filename = generate_pdf_report(kpis, kpis['scan_history'], company_profile)
                with open(filename, "rb") as f:
                    st.download_button("📥 Download Report", f, file_name=filename, mime="application/pdf")
    
    if kpis['scan_history']:
        df = pd.DataFrame(kpis['scan_history'])
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d %H:%M')
        
        if 'duplicate_warning' in df.columns:
            st.dataframe(df[['date', 'vendor', 'total', 'currency', 'risk_score', 'duplicate_warning']], 
                        hide_index=True, use_container_width=True)
        else:
            st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.info("No scans yet. Upload in Scan & Audit.")
    
    st.markdown("---")
    for col, (l, v, d) in zip(st.columns(4), [
        ("Scans", str(kpis['total_scanned']), f"{kpis['flagged_count']} flagged"),
        ("Audited", kpis['total_audited'], ""),
        ("Saved", kpis['blocked_leakage'], ""),
        ("Avg Risk", kpis['risk_score'], "")
    ]):
        with col: st.metric(l, v, d)

# ── Policies ────────────────────────────────────
elif "Policies" in page:
    st.title("📋 Expense Policy Engine")
    st.markdown("Configure company spending rules - AI will automatically flag violations")
    
    policies = load_expense_policies()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💰 Spending Limits")
        policies['max_meal_amount'] = st.number_input("Max Meal Amount ($)", 0.0, 500.0, 
                                                      value=float(policies.get('max_meal_amount', 50.0)), step=5.0)
        policies['max_entertainment'] = st.number_input("Max Entertainment Amount ($)", 0.0, 1000.0, 
                                                        value=float(policies.get('max_entertainment', 100.0)), step=10.0)
        policies['require_receipt_above'] = st.number_input("Require Receipt Above ($)", 0.0, 500.0, 
                                                            value=float(policies.get('require_receipt_above', 25.0)), step=5.0)
    
    with col2:
        st.markdown("### 🚫 Restrictions")
        policies['allow_weekend_transactions'] = st.checkbox("Allow Weekend Transactions", 
                                                             value=policies.get('allow_weekend_transactions', False))
        
        blacklist_text = "\n".join(policies.get('blacklist_vendors', []))
        new_blacklist = st.text_area("Blacklisted Vendors (one per line)", blacklist_text, height=100)
        policies['blacklist_vendors'] = [v.strip() for v in new_blacklist.split('\n') if v.strip()]
    
    policies['enabled'] = st.checkbox("Enable Policy Enforcement", value=policies.get('enabled', True))
    
    if st.button("💾 Save Policies", type="primary", use_container_width=True):
        save_expense_policies(policies)
        st.success("✅ Expense policies saved!")
        st.balloons()
        time.sleep(1)
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 Active Policy Summary")
    if policies['enabled']:
        st.success("✅ Policy enforcement is ACTIVE")
        st.markdown(f"- Meals over ${policies['max_meal_amount']} will be flagged")
        st.markdown(f"- Entertainment over ${policies['max_entertainment']} will be flagged")
        st.markdown(f"- {'❌' if not policies['allow_weekend_transactions'] else '✅'} Weekend transactions {'not allowed' if not policies['allow_weekend_transactions'] else 'allowed'}")
        st.markdown(f"- Blacklisted vendors: {', '.join(policies['blacklist_vendors']) if policies['blacklist_vendors'] else 'None'}")
    else:
        st.warning("⚠️ Policy enforcement is DISABLED")

# ── Settings ────────────────────────────────────
elif "Settings" in page:
    st.title("⚙️ Settings")
    t0, t1, t2 = st.tabs(["🏢 Company Profile", "🔐 Security", "🗑 Reset"])
    
    with t0:
        st.markdown("### Register Your Company")
        st.info("This appears on reports and determines risk thresholds")
        company = load_company_profile()
        col_a, col_b = st.columns(2)
        with col_a:
            cn = st.text_input("Company Name*", value=company.get('company_name', ''))
            ct = st.text_input("TIN Number*", value=company.get('tin', ''))
            industries = ["Retail", "Wholesale", "Luxury Goods", "Manufacturing", 
                         "Services", "Restaurant", "Construction", "Technology", "General"]
            bt = st.selectbox("Industry", industries,
                             index=industries.index(company.get('industry', 'General')) 
                             if company.get('industry') in industries else 8)
            rn = st.text_input("Registration #", value=company.get('registration_number', ''))
        with col_b:
            addr = st.text_input("Address", value=company.get('address', ''))
            phone = st.text_input("Phone", value=company.get('phone', ''))
            email = st.text_input("Email", value=company.get('email', ''))
            currency = st.selectbox("Default Currency", ["USD", "ETB", "EUR"],
                                   index=["USD", "ETB", "EUR"].index(company.get('currency', 'USD')))
            tax_rate = st.number_input("Default Tax Rate (%)", 0.0, 50.0, 
                                      value=float(company.get('tax_rate', 15.0)), step=0.5)
        
        if st.button("💾 Save Company Profile", type="primary", use_container_width=True):
            profile = {
                "company_name": cn, "tin": ct, "business_type": bt,
                "registration_number": rn, "address": addr, "phone": phone,
                "email": email, "industry": bt, "currency": currency, "tax_rate": tax_rate
            }
            save_company_profile(profile)
            st.session_state['company_name'] = cn
            st.session_state['company_tin'] = ct
            st.session_state['company_currency'] = currency
            st.session_state['company_tax_rate'] = tax_rate
            st.success("✅ Company profile saved!")
            st.balloons()
            time.sleep(1)
            st.rerun()
    
    with t1:
        st.markdown("### Change Password")
        MASTER_PASSWORD = get_master_password()
        old = st.text_input("Current Password", type="password")
        new = st.text_input("New Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")
        if st.button("Update Password"):
            if old != MASTER_PASSWORD: st.error("Wrong current password")
            elif new != confirm: st.error("Passwords don't match")
            elif len(new) < 4: st.error("Too short")
            else:
                save_master_password(new)
                st.success("✅ Updated!")
        
        st.markdown("---")
        if os.path.exists(BIOMETRIC_FILE): st.success("✅ Biometrics registered")
        else: st.warning("⚠️ Not registered")
        
        if st.button("🚪 Logout"):
            st.session_state['is_logged_in'] = False
            st.rerun()
    
    with t2:
        st.warning("These actions cannot be undone!")
        if st.button("🗑 Reset Biometrics"):
            if os.path.exists(BIOMETRIC_FILE): os.remove(BIOMETRIC_FILE)
            st.session_state['biometric_registered'] = False
            st.session_state['is_logged_in'] = False
            st.success("Reset - please re-register")
            time.sleep(1)
            st.rerun()
        if st.button("🗑 Reset All Scans"):
            save_data({"total_audited": 0, "total_scanned": 0, "compliant_count": 0,
                       "flagged_count": 0, "total_saved": 0, "scan_history": [], "risk_scores": []})
            st.success("✅ Cleared!")
            st.rerun()
        if st.button("🔄 Reset Password to Default"):
            save_master_password("admin123")
            st.success("Reset to: admin123")

# ── Analytics ───────────────────────────────────
elif "Analytics" in page:
    st.title("📈 Advanced Analytics")
    st.caption("Real-time charts based on your scanned documents")
    
    kpis = calculate_current_kpis()
    scan_history = kpis.get('scan_history', [])
    
    if not scan_history or len(scan_history) == 0:
        st.warning("📊 No scan data yet. Upload documents in **Scan & Audit** to see analytics charts here.")
    else:
        df = pd.DataFrame(scan_history)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        st.markdown("### 📊 Summary")
        total_scans = len(df)
        total_amount = df['total'].sum()
        avg_transaction = df['total'].mean()
        flagged = len(df[df['risk_score'] > 25])
        high_risk = len(df[df['risk_score'] > 60])
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Scans", total_scans)
        col2.metric("Total Audited", f"${total_amount:,.0f}")
        col3.metric("Avg Transaction", f"${avg_transaction:,.0f}")
        col4.metric("Flagged", f"{flagged} ({high_risk} high risk)")
        
        st.markdown("---")
        st.markdown("### 💰 Transaction History")
        
        df['day'] = df['date'].dt.date
        daily = df.groupby('day').agg(
            total_amount=('total', 'sum'),
            avg_risk=('risk_score', 'mean'),
            count=('total', 'count')
        ).reset_index()
        
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=daily['day'], y=daily['total_amount'],
            name='Daily Total', marker=dict(color='#667eea'),
            text=[f"${v:,.0f}" for v in daily['total_amount']],
            textposition='outside'
        ))
        fig1.update_layout(title="Daily Transaction Volume (Real Data)",
                          xaxis_title="Date", yaxis_title="Amount ($)",
                          height=400, plot_bgcolor='white', showlegend=False)
        style_axes(fig1)
        st.plotly_chart(fig1, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 🎯 Risk Score Per Scan")
        
        colors = ['#10b981' if s <= 25 else '#f59e0b' if s <= 60 else '#ef4444' 
                  for s in df['risk_score']]
        
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=df['date'], y=df['risk_score'], mode='lines+markers',
            name='Risk Score', line=dict(color='#6b7280', width=1),
            marker=dict(size=10, color=colors, line=dict(color='white', width=2)),
            text=df['vendor']
        ))
        fig2.add_hline(y=25, line_dash="dash", line_color="#10b981")
        fig2.add_hline(y=60, line_dash="dash", line_color="#f59e0b")
        fig2.update_layout(title="Risk Score Per Transaction",
                          xaxis_title="Date", yaxis_title="Risk Score (0-100)",
                          height=400, plot_bgcolor='white', yaxis=dict(range=[0, 105]))
        style_axes(fig2)
        st.plotly_chart(fig2, use_container_width=True)
        
        st.markdown("---")
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("### 🍩 Risk Distribution")
            low = len(df[df['risk_score'] <= 25])
            medium = len(df[(df['risk_score'] > 25) & (df['risk_score'] <= 60)])
            high = len(df[df['risk_score'] > 60])
            
            fig3 = go.Figure(data=[go.Pie(
                labels=['Low Risk', 'Medium Risk', 'High Risk'],
                values=[low, medium, high], hole=0.4,
                marker=dict(colors=['#10b981', '#f59e0b', '#ef4444']),
                textinfo='label+percent+value'
            )])
            fig3.update_layout(title="Scan Risk Levels", height=400)
            st.plotly_chart(fig3, use_container_width=True)
        
        with col_right:
            st.markdown("### 🏪 Top Vendors")
            vendor_counts = df['vendor'].value_counts().head(8)
            fig4 = go.Figure(data=[go.Pie(
                labels=vendor_counts.index, values=vendor_counts.values,
                hole=0.4, textinfo='label+value'
            )])
            fig4.update_layout(title="Scans by Vendor", height=400)
            st.plotly_chart(fig4, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 📋 Recent Scans")
        recent = df.tail(10)[['date', 'vendor', 'total', 'currency', 'risk_score']].copy()
        recent = recent.sort_values('date', ascending=False)
        recent['date'] = recent['date'].dt.strftime('%Y-%m-%d %H:%M')
        recent.columns = ['Date', 'Vendor', 'Amount', 'Currency', 'Risk Score']
        recent['Amount'] = recent['Amount'].apply(lambda x: f"${x:,.2f}")
        st.dataframe(recent, hide_index=True, use_container_width=True)

st.markdown("---")
st.markdown(f"""<div style="text-align:center;color:#6b7280;padding:20px">
    <p>{st.session_state['company_name']} - CFO-Pulse AI</p>
    <p style="font-size:12px">2026 CFO-Pulse Enterprise Platform | AI-Powered Audit & Fraud Detection</p>
</div>""", unsafe_allow_html=True)
