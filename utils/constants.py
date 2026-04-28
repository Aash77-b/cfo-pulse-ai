# utils/constants.py

import streamlit as st
import os
from modules.data_processor import load_company_profile

DATA_FILE = "cfo_pulse_data.json"
BIOMETRIC_FILE = "biometric_data/CFO_Ashenafi.jpg"
PASSWORD_FILE = "master_password.txt"
COMPANY_FILE = "company_profile.json"
POLICY_FILE = "expense_policies.json"

def init_session_state():
    company = load_company_profile()
    st.session_state.setdefault('company_name', company['company_name'])
    st.session_state.setdefault('company_tin', company['tin'])
    st.session_state.setdefault('company_currency', company.get('currency', 'USD'))
    st.session_state.setdefault('company_tax_rate', company.get('tax_rate', 15.0))
    st.session_state.setdefault('biometric_registered', os.path.exists(BIOMETRIC_FILE))
    st.session_state.setdefault('is_logged_in', False)
    st.session_state.setdefault('login_attempts', 0)
    st.session_state.setdefault('captured_face', None)
    st.session_state.setdefault('registration_step', 1)
