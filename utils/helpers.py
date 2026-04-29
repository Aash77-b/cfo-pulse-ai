import streamlit as st
import time
import cv2
import os
from modules.data_processor import get_master_password
from utils.constants import BIOMETRIC_FILE
from utils.biometric import capture_face_from_camera, detect_face, load_registered_face, verify_face_match, save_biometric_data

GRID_COLOR = '#e5e7eb'

# OCR status flags
TESSERACT_AVAILABLE = False
EASYOCR_AVAILABLE = False

def style_axes(fig):
    """Style chart axes with grid lines"""
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=GRID_COLOR)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=GRID_COLOR)

def base_layout(fig, title, height=400):
    """Set consistent chart layout"""
    fig.update_layout(
        title=title,
        height=height,
        hovermode='x unified',
        plot_bgcolor='white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )

def inject_styles():
    """Inject custom CSS styling for the entire app"""
    css = """
    <style>
    .main { padding: 0rem 1rem; }
    .metric-card { background:#fff; padding:20px; border-radius:12px;
                   box-shadow:0 2px 10px rgba(0,0,0,.05); border:1px solid #e0e0e0; }
    .risk-badge-low { background:#10b981; color:#fff; padding:5px 15px; border-radius:20px; font-weight:600; display:inline-block; }
    .risk-badge-medium { background:#f59e0b; color:#fff; padding:5px 15px; border-radius:20px; font-weight:600; display:inline-block; }
    .risk-badge-high { background:#ef4444; color:#fff; padding:5px 15px; border-radius:20px; font-weight:600; display:inline-block; }
    .stButton>button { width:100%; border-radius:8px; height:45px; font-weight:600; transition:all .3s; }
    .stButton>button:hover { transform:translateY(-2px); box-shadow:0 5px 15px rgba(0,0,0,.1); }
    .stProgress>div>div { background-color:#667eea; }
    .stTabs [data-baseweb="tab"] { border-radius:8px; padding:10px 20px; background:#f8f9fa; }
    .stTabs [aria-selected="true"] { background:#667eea!important; color:#fff!important; }
    .login-container { max-width:500px; margin:50px auto; padding:40px; background:#fff;
                       border-radius:20px; box-shadow:0 20px 60px rgba(0,0,0,.1); text-align:center; }
    .login-header { background:linear-gradient(135deg,#667eea,#764ba2); color:#fff; padding:30px;
                    border-radius:15px; margin-bottom:30px; }
    .camera-box { border:3px dashed #667eea; border-radius:20px; padding:30px; text-align:center; 
                  background:linear-gradient(135deg,#667eea10,#764ba210); margin:20px 0; }
    .success-box { border:2px solid #10b981; border-radius:15px; padding:20px; 
                   background:#f0fdf4; text-align:center; }
    .alert-high { border:2px solid #ef4444; background:#fef2f2; padding:20px; border-radius:15px; }
    .alert-medium { border:2px solid #f59e0b; background:#fffbeb; padding:20px; border-radius:15px; }
    .alert-low { border:2px solid #10b981; background:#f0fdf4; padding:20px; border-radius:15px; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def show_login_page():
    """Display the login screen with face or password authentication"""
    MASTER_PASSWORD = get_master_password()
    
    if st.session_state.get('login_attempts', 0) >= 5:
        st.markdown("""<div style="max-width:500px;margin:100px auto;padding:40px;text-align:center;
            border:2px solid #ef4444;border-radius:15px;background:#fef2f2">
            <h2>🔒 Account Locked</h2><p>Too many failed attempts. Please reset to try again.</p></div>""", unsafe_allow_html=True)
        if st.button("Reset & Try Again"):
            st.session_state['login_attempts'] = 0
            st.rerun()
        return
    
    st.markdown("""
    <div style="max-width:500px;margin:50px auto">
        <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;
                    padding:30px;border-radius:15px;text-align:center;margin-bottom:30px">
            <span style="font-size:64px">🛡️</span>
            <h1>CFO-Pulse AI</h1>
            <p>Enterprise Security Platform</p>
        </div>
    </div>""", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("### 🔐 Authentication Required")
        is_registered = os.path.exists(BIOMETRIC_FILE)
        
        if not is_registered:
            st.warning("No biometric data registered. Please complete face registration.")
            step = st.session_state.get('registration_step', 1)
            st.progress(step / 3)
            
            if step == 1:
                if st.button("📸 Start Face Registration", type="primary", use_container_width=True):
                    st.session_state['registration_step'] = 2
                    st.rerun()
            elif step == 2:
                if st.button("📸 Capture Face Now", type="primary", use_container_width=True):
                    with st.spinner("Accessing camera..."):
                        frame, error = capture_face_from_camera()
                    if error:
                        st.error(error)
                    elif frame is not None:
                        has_face, faces = detect_face(frame)
                        if has_face:
                            for (x, y, w, h) in faces:
                                cv2.rectangle(frame, (x, y), (x+w, y+h), (16, 185, 129), 3)
                            st.session_state['captured_face'] = frame
                            st.session_state['registration_step'] = 3
                            st.image(frame, channels="RGB")
                            st.success("Face captured successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("No face detected. Please try again.")
            elif step == 3:
                if st.session_state.get('captured_face') is not None:
                    st.image(st.session_state['captured_face'], channels="RGB", width=250)
                    if st.button("✅ Confirm Registration", type="primary", use_container_width=True):
                        save_biometric_data(st.session_state['captured_face'])
                        st.session_state['biometric_registered'] = True
                        st.session_state['registration_step'] = 1
                        st.success("✅ Registration complete! Please login.")
                        st.balloons()
                        time.sleep(2)
                        st.rerun()
        else:
            login_method = st.radio("Choose Login Method:", ["📸 Face Recognition", "🔑 Password"], horizontal=True)
            
            if "Face" in login_method:
                if st.button("📸 Scan Face to Login", type="primary", use_container_width=True):
                    with st.spinner("Scanning..."):
                        frame, error = capture_face_from_camera()
                    if error:
                        st.error(error)
                    elif frame is not None:
                        has_face, faces = detect_face(frame)
                        if not has_face:
                            st.error("No face detected")
                            st.session_state['login_attempts'] += 1
                        else:
                            registered = load_registered_face()
                            is_match, conf, msg = verify_face_match(frame, registered)
                            if is_match:
                                st.success(f"✅ {msg}")
                                st.session_state['is_logged_in'] = True
                                st.session_state['login_attempts'] = 0
                                st.balloons()
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")
                                st.session_state['login_attempts'] += 1
            else:
                pw = st.text_input("Master Password", type="password")
                if st.button("🔑 Login", use_container_width=True):
                    if pw == MASTER_PASSWORD:
                        st.session_state['is_logged_in'] = True
                        st.session_state['login_attempts'] = 0
                        st.rerun()
                    else:
                        st.error("Invalid password")
                        st.session_state['login_attempts'] += 1
    
    if st.session_state.get('login_attempts', 0) > 0:
        st.caption(f"Failed attempts: {st.session_state['login_attempts']}/5")
