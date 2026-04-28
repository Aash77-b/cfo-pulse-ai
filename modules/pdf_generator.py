# modules/pdf_generator.py

from fpdf import FPDF
from datetime import datetime
import pandas as pd

def generate_pdf_report(kpis, scan_history, company_profile):
    """Generate comprehensive PDF audit report"""
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="CFO-Pulse Audit Report", ln=1, align='C')
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
        "2. Implement stricter vendor approval process",
        "3. Schedule regular audit reviews for flagged transactions"
    ]
    for rec in recommendations:
        pdf.cell(200, 6, txt=rec, ln=1)
    
    filename = f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(filename)
    return filename
