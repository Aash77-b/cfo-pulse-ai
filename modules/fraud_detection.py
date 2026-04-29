import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.linear_model import LinearRegression

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
        
        if past['vendor'] == new_invoice['vendor'] and past['total'] > 0:
            diff_pct = abs(past['total'] - new_invoice.get('total', 0)) / past['total'] * 100
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
    
    try:
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
            if predictions[-1] > df['cumulative'].iloc[-1] * 0.9:
                shortfall_risk = "Medium"
            if predictions[-1] < predictions[0] * 0.5:
                shortfall_risk = "High"
        
        return predictions, daily_avg, shortfall_risk
    except Exception as e:
        return None, None, f"Prediction error"

def calculate_risk_score(data, duplicate_penalty=0, policy_penalty=0):
    from modules.data_processor import load_company_profile
    
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
        score += int((total / threshold) * 10) if threshold > 0 else 0
    
    vendor = str(data.get('vendor', ''))
    if vendor in ['Unknown', '=', ''] or len(vendor) <= 3:
        score += 20
    if data.get('tax_amount', 0) == 0 and total > 50:
        score += 15
    if not data.get('items'):
        score += 10
    if total > threshold * 2:
        score += 15
    
    score += duplicate_penalty + policy_penalty
    return min(100, score)
