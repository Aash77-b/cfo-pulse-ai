import streamlit as st
import os
from modules.data_processor import load_company_profile

# File paths - relative to project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "cfo_pulse_data.json")
BIOMETRIC_FILE = os.path.join(BASE_DIR, "biometric_data", "CFO_Ashenafi.jpg")
PASSWORD_FILE = os.path.join(BASE_DIR, "master_password.txt")
COMPANY_FILE = os.path.join(BASE_DIR, "company_profile.json")
POLICY_FILE = os.path.join(BASE_DIR, "expense_policies.json")

def init_session_state():
    """Initialize all session state variables"""
    company = load_company_profile()
    st.session_state.setdefault('company_name', company['company_name'])
    st.session_state.setdefault('company_tin', company['tin'])
    st.session_state.setdefault('company_currency', company.get('currency', 'USD'))
    st.session_state.setdefault('company_tax_rate', company.get('tax_rate', 15.0))
    st.session_state.setdefault('biometric_registered', os.path.exists(BIOMETRIC_FILE))
    st.session_state.setdefault('biometric_verified', False)
    st.session_state.setdefault('is_logged_in', False)
    st.session_state.setdefault('login_attempts', 0)
    st.session_state.setdefault('captured_face', None)
    st.session_state.setdefault('registration_step', 1)
    st.session_state.setdefault('show_login', True)
