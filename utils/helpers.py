# utils/helpers.py

import streamlit as st
import time
import cv2
import os
from modules.data_processor import get_master_password
from utils.biometric import capture_face_from_camera, detect_face, load_registered_face, verify_face_match, save_biometric_data
from utils.constants import BIOMETRIC_FILE

GRID_COLOR = '#e5e7eb'

def style_axes(fig):
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=GRID_COLOR)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=GRID_COLOR)

def base_layout(fig, title, height=400):
    fig.update_layout(title=title, height=height, hovermode='x unified', plot_bgcolor='white')

def show_login_page():
    MASTER_PASSWORD = get_master_password()
    
    if st.session_state.get('login_attempts', 0) >= 5:
        st.markdown("<h3>🔒 Account Locked</h3>", unsafe_allow_html=True)
        if st.button("Reset"):
            st.session_state['login_attempts'] = 0
            st.rerun()
        return
    
    st.markdown("<div style='text-align:center'><h1>🛡️ CFO-Pulse AI</h1></div>", unsafe_allow_html=True)
    
    if not os.path.exists(BIOMETRIC_FILE):
        step = st.session_state.get('registration_step', 1)
        if step == 1 and st.button("Start Registration"):
            st.session_state['registration_step'] = 2
            st.rerun()
        elif step == 2 and st.button("Capture Face"):
            frame, err = capture_face_from_camera()
            if frame and detect_face(frame):
                st.session_state['captured_face'] = frame
                st.session_state['registration_step'] = 3
                st.rerun()
        elif step == 3 and st.button("Confirm"):
            save_biometric_data(st.session_state['captured_face'])
            st.session_state['biometric_registered'] = True
            st.success("Registered! Login below")
            st.rerun()
    else:
        if st.button("Face Login"):
            frame, err = capture_face_from_camera()
            if frame:
                reg = load_registered_face()
                match, _, _ = verify_face_match(frame, reg)
                if match:
                    st.session_state['is_logged_in'] = True
                    st.rerun()
                else:
                    st.session_state['login_attempts'] += 1
