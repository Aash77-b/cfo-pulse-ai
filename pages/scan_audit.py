import streamlit as st
import time
from modules.data_processor import load_data, load_expense_policies, update_kpi_after_scan
from modules.fraud_detection import check_duplicate_invoice, check_policy_violations, calculate_risk_score
from utils.ocr_engine import process_invoice
from utils.helpers import TESSERACT_AVAILABLE, EASYOCR_AVAILABLE

def show_scan_audit():
    st.title("🔍 Document Scanner")
    st.markdown("Upload receipts or invoices for AI-powered audit")
    
    st.markdown("""
    <div style="border:2px dashed #667eea;border-radius:15px;padding:40px;text-align:center;
        background:linear-gradient(135deg,#667eea10,#764ba210)">
        <span style="font-size:48px">📤</span>
        <h3>Upload Document</h3>
        <p style="color:#6b7280">JPG, PNG, PDF (Max 10MB)</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded = st.file_uploader("", type=['jpg', 'jpeg', 'png', 'pdf'], label_visibility="collapsed")
    
    if uploaded:
        st.markdown("---")
        if TESSERACT_AVAILABLE or EASYOCR_AVAILABLE:
            with st.spinner("Processing document with AI..."):
                data = process_invoice(uploaded)
            
            if data is None:
                st.warning("OCR could not read this document. Using sample data.")
                data = {
                    "vendor": "SUPREME LUXURY PROVISIONS",
                    "total": 5393.88,
                    "subtotal": 4954.20,
                    "tax_amount": 439.68,
                    "currency": "USD",
                    "items": "Various luxury items",
                    "invoice_no": "INV-001"
                }
        else:
            st.warning("OCR engines not available. Using sample data.")
            data = {
                "vendor": "SUPREME LUXURY PROVISIONS",
                "total": 5393.88,
                "currency": "USD",
                "invoice_no": "INV-001"
            }
        
        scan_history = load_data().get('scan_history', [])
        duplicate_warning, duplicate_penalty = check_duplicate_invoice(data, scan_history)
        policies = load_expense_policies()
        policy_violations, policy_penalty = check_policy_violations(data, policies)
        fraud_score = calculate_risk_score(data, duplicate_penalty, policy_penalty)
        data['risk_score'] = fraud_score
        data['duplicate_warning'] = duplicate_warning
        data['policy_violations'] = policy_violations
        update_kpi_after_scan(data)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📋 Extracted Data")
            st.markdown(f"**Vendor:** {data.get('vendor', 'N/A')}")
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
                st.markdown(f"""
                <div class="alert-high">
                    <strong>⚠️ Immediate review required</strong><br>
                    Amount ({total:,.2f}) exceeds threshold ({threshold:,.2f})
                </div>
                """, unsafe_allow_html=True)
            elif fraud_score > 25:
                st.warning(f"⚠️ REVIEW NEEDED - Score: {fraud_score}/100")
            else:
                st.success(f"✅ VERIFIED - Score: {fraud_score}/100")
            st.caption("📊 Analytics updated with this scan")
