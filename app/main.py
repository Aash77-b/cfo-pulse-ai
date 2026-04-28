# app.py - Main Streamlit Application

import streamlit as st
from modules.data_processor import *
from modules.fraud_detection import *
from modules.pdf_generator import *
from pages.dashboard import show_dashboard
from pages.scan_audit import show_scan_audit
from pages.fraud_reports import show_fraud_reports
from pages.settings import show_settings
from pages.analytics import show_analytics
from pages.policies import show_policies
from utils.helpers import show_login_page, inject_styles

# Page Config
st.set_page_config(page_title="CFO-Pulse AI", page_icon="🛡️", layout="wide")

# Session State Init
from utils.constants import init_session_state
init_session_state()

# Login Gate
if not st.session_state.get('is_logged_in', False):
    show_login_page()
    st.stop()

# Sidebar Navigation
with st.sidebar:
    st.markdown(f"""... company info ...""")
    page = st.radio("Menu", ["Dashboard", "Scan & Audit", "Fraud Reports", "Policies", "Settings", "Analytics"])

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
st.markdown(f"... footer ...")
