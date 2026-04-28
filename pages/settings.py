# pages/settings.py

import streamlit as st
import os
from modules.data_processor import load_company_profile, save_company_profile, get_master_password, save_master_password, save_data
from utils.biometric import BIOMETRIC_FILE

def show_settings():
    st.title("⚙️ Settings")
    t0, t1, t2 = st.tabs(["🏢 Company Profile", "🔐 Security", "🗑 Reset"])
    
    with t0:
        st.markdown("### Register Your Company")
        company = load_company_profile()
        col_a, col_b = st.columns(2)
        with col_a:
            cn = st.text_input("Company Name", value=company.get('company_name', ''))
            ct = st.text_input("TIN Number", value=company.get('tin', ''))
        with col_b:
            currency = st.selectbox("Currency", ["USD", "ETB", "EUR"], index=["USD", "ETB", "EUR"].index(company.get('currency', 'USD')))
        
        if st.button("💾 Save Company Profile", type="primary"):
            profile = {**company, "company_name": cn, "tin": ct, "currency": currency}
            save_company_profile(profile)
            st.success("Saved!")
            st.rerun()
    
    with t1:
        MASTER_PASSWORD = get_master_password()
        old = st.text_input("Current Password", type="password")
        new = st.text_input("New Password", type="password")
        if st.button("Update Password"):
            if old == MASTER_PASSWORD and new:
                save_master_password(new)
                st.success("Password updated!")
    
    with t2:
        if st.button("🗑 Reset All Scans"):
            save_data({"total_audited": 0, "total_scanned": 0, "compliant_count": 0, "flagged_count": 0, "total_saved": 0, "scan_history": [], "risk_scores": []})
            st.success("Reset complete!")
            st.rerun()
