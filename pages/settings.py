import streamlit as st
import os
import time
from modules.data_processor import load_company_profile, save_company_profile, get_master_password, save_master_password, save_data
from utils.constants import BIOMETRIC_FILE

def show_settings():
    st.title("⚙️ Settings")
    t0, t1, t2 = st.tabs(["🏢 Company Profile", "🔐 Security", "🗑 Reset Data"])
    
    with t0:
        st.markdown("### Register Your Company")
        st.info("This information appears on audit reports")
        company = load_company_profile()
        col_a, col_b = st.columns(2)
        with col_a:
            cn = st.text_input("Company Name *", value=company.get('company_name', ''))
            ct = st.text_input("TIN Number *", value=company.get('tin', ''))
            industries = ["Retail", "Wholesale", "Luxury Goods", "Manufacturing", 
                         "Services", "Restaurant", "Construction", "Technology", "General"]
            current_industry = company.get('industry', 'General')
            bt = st.selectbox("Industry", industries, index=industries.index(current_industry) if current_industry in industries else 8)
        with col_b:
            currency = st.selectbox("Default Currency", ["USD", "ETB", "EUR"],
                                   index=["USD", "ETB", "EUR"].index(company.get('currency', 'USD')))
            tax_rate = st.number_input("Default Tax Rate (%)", 0.0, 50.0, 
                                      value=float(company.get('tax_rate', 15.0)), step=0.5)
        
        if st.button("💾 Save Company Profile", type="primary", use_container_width=True):
            profile = {
                "company_name": cn, "tin": ct, "business_type": bt,
                "registration_number": company.get('registration_number', ''),
                "address": company.get('address', ''),
                "phone": company.get('phone', ''),
                "email": company.get('email', ''),
                "industry": bt, "currency": currency, "tax_rate": tax_rate
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
        st.markdown("### Change Master Password")
        MASTER_PASSWORD = get_master_password()
        old = st.text_input("Current Password", type="password")
        new = st.text_input("New Password", type="password")
        confirm = st.text_input("Confirm New Password", type="password")
        if st.button("Update Password"):
            if old != MASTER_PASSWORD:
                st.error("Wrong current password")
            elif new != confirm:
                st.error("Passwords don't match")
            elif len(new) < 4:
                st.error("Password must be at least 4 characters")
            else:
                save_master_password(new)
                st.success("Password updated!")
        
        st.markdown("---")
        if os.path.exists(BIOMETRIC_FILE):
            st.success("✅ Face biometrics registered")
        else:
            st.warning("⚠️ No face biometrics registered")
    
    with t2:
        st.warning("⚠️ These actions cannot be undone!")
        if st.button("🗑 Reset All Scan Data", use_container_width=True):
            save_data({"total_audited": 0, "total_scanned": 0, "compliant_count": 0,
                       "flagged_count": 0, "total_saved": 0, "scan_history": [], "risk_scores": []})
            st.success("All scan data cleared!")
            st.rerun()
        if st.button("🔄 Reset Password to Default (admin123)", use_container_width=True):
            save_master_password("admin123")
            st.success("Password reset to: admin123")
