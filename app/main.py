# app.py
import streamlit as st
from modules.tax_calculator import calculate_ethiopian_tax

# Page config must be first
st.set_page_config(
    page_title="CFO-Pulse AI", 
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
with open('assets/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Import pages
from pages.dashboard import show_dashboard
from pages.scan_audit import show_scan_audit
from pages.fraud_reports import show_fraud_reports
from pages.settings import show_settings
from pages.analytics import show_analytics

# Sidebar navigation
with st.sidebar:
    # [Your sidebar code here]
    page = st.radio("", ["📊 Dashboard", "🔍 Scan & Audit", "🚨 Fraud Reports", "⚙️ Settings", "📈 Analytics"])

# Page routing
if page == "📊 Dashboard":
    show_dashboard()
elif page == "🔍 Scan & Audit":
    show_scan_audit()
elif page == "🚨 Fraud Reports":
    show_fraud_reports()
elif page == "⚙️ Settings":
    show_settings()
elif page == "📈 Analytics":
    show_analytics()
