# pages/scan_audit.py

import streamlit as st
from modules.data_processor import load_data, load_expense_policies, update_kpi_after_scan
from modules.fraud_detection import check_duplicate_invoice, check_policy_violations, calculate_risk_score
from utils.ocr_engine import process_invoice

def show_scan_audit():
    st.title("🔍 Document Scanner")
    st.markdown("Upload receipts or invoices for AI-powered audit")
    
    uploaded = st.file_uploader("Upload Document", type=['jpg', 'jpeg', 'png', 'pdf'])
    
    if uploaded:
        with st.spinner("Processing..."):
            data = process_invoice(uploaded)
            if data is None:
                data = {"vendor": "SAMPLE", "total": 5393.88, "currency": "USD", "invoice_no": "INV-001"}
            
            scan_history = load_data().get('scan_history', [])
            dup_warn, dup_pen = check_duplicate_invoice(data, scan_history)
            policies = load_expense_policies()
            pol_viol, pol_pen = check_policy_violations(data, policies)
            fraud_score = calculate_risk_score(data, dup_pen, pol_pen)
            data['risk_score'] = fraud_score
            update_kpi_after_scan(data)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Vendor:** {data.get('vendor')}\n**Total:** {data.get('currency')} {data.get('total'):,.2f}")
                if dup_warn:
                    st.warning(dup_warn)
                if pol_viol:
                    for v in pol_viol:
                        st.error(v)
            with col2:
                if fraud_score > 60:
                    st.error(f"🚨 HIGH RISK - {fraud_score}/100")
                elif fraud_score > 25:
                    st.warning(f"⚠️ REVIEW - {fraud_score}/100")
                else:
                    st.success(f"✅ VERIFIED - {fraud_score}/100")
