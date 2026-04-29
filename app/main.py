import streamlit as st
import sys
import os
from datetime import datetime

# Fix imports - add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now imports work
from modules.data_processor import load_company_profile, calculate_current_kpis
from modules.fraud_detection import predict_cash_flow
from pages.dashboard import show_dashboard
from pages.scan_audit import show_scan_audit
from pages.fraud_reports import show_fraud_reports
from pages.settings import show_settings
from pages.analytics import show_analytics
from pages.policies import show_policies
from utils.helpers import show_login_page, inject_styles
from utils.constants import init_session_state

# Page config must be first Streamlit command
st.set_page_config(page_title="CFO-Pulse AI", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

# Load CSS
inject_styles()

# Initialize session state
init_session_state()

# Check login
if not st.session_state.get('is_logged_in', False):
    show_login_page()
    st.stop()

# Sidebar Navigation
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center;padding:10px 0">
        <div style="width:80px;height:80px;background:linear-gradient(135deg,#667eea,#764ba2);
                    border-radius:50%;margin:0 auto;display:flex;align-items:center;justify-content:center">
            <span style="font-size:32px">🏢</span>
        </div>
        <h4 style="margin:8px 0 2px">{st.session_state.get('company_name', 'CFO-Pulse')}</h4>
        <p style="color:#6b7280;font-size:12px;margin:0">TIN: {st.session_state.get('company_tin', 'N/A')}</p>
        <p style="color:#10b981;font-size:11px;margin:5px 0">✓ Biometric Verified</p>
    </div>
    """, unsafe_allow_html=True)
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
    avg_risk_str = kpis['risk_score'].split('/')[0] if kpis.get('risk_score') else "0"
    try:
        avg_risk = int(float(avg_risk_str)) if avg_risk_str else 23
    except:
        avg_risk = 23
    st.markdown(f"**Risk Level:** {avg_risk}/100")
    st.progress(avg_risk / 100 if avg_risk > 0 else 0.23)
    st.markdown("---")

# Page Router
if page == "Dashboard":
    show_dashboard()
elif page == "Scan & Audit":
    show_scan_audit()
elif page == "Fraud Reports":
    show_fraud_reports()
elif page == "Policies":
    show_policies()
elif page == "Settings":
    show_settings()
elif page == "Analytics":
    show_analytics()

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align:center;color:#6b7280;padding:20px">
    <p><strong>{st.session_state.get('company_name', 'CFO-Pulse')}</strong> - AI-Powered Audit Platform</p>
    <p style="font-size:12px">© 2026 CFO-Pulse AI | Secure Biometric Access | Real-time Fraud Detection</p>
</div>
""", unsafe_allow_html=True)
