import json
import os
import numpy as np
from datetime import datetime

# File paths relative to project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "cfo_pulse_data.json")
COMPANY_FILE = os.path.join(BASE_DIR, "company_profile.json")
POLICY_FILE = os.path.join(BASE_DIR, "expense_policies.json")
PASSWORD_FILE = os.path.join(BASE_DIR, "master_password.txt")

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
