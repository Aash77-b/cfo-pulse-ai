import streamlit as st
from datetime import datetime

def show_settings():
    st.title("⚙️ System Configuration")
    
    tabs = st.tabs(["🔐 Security", "📊 Monitoring", "🔔 Alerts", "🤖 AI Models", "🏢 Company Profile"])
    
    with tabs[0]:
        st.markdown("### Security Settings")
        
        st.toggle("Enable Biometric Authentication", value=True)
        st.toggle("Two-Factor Authentication", value=True)
        st.toggle("Session Timeout (30 min)", value=True)
        
        st.markdown("### API Keys")
        st.text_input("OCR Service API Key", type="password", value="••••••••••••••••")
        st.text_input("Fraud Detection API Key", type="password", value="••••••••••••••••")
        
        if st.button("Save Security Settings"):
            st.success("Settings saved successfully!")
    
    with tabs[1]:
        st.markdown("### Monitoring Configuration")
        
        st.slider("Risk Threshold", 0, 100, 75)
        st.slider("Alert Sensitivity", 0, 100, 60)
        st.number_input("Transaction Review Threshold (ETB)", min_value=0, value=50000)
    
    with tabs[2]:
        st.markdown("### Alert Preferences")
        
        st.multiselect(
            "Alert Channels",
            ["Email", "SMS", "Slack", "Teams", "In-App"],
            default=["Email", "In-App"]
        )
        
        st.time_input("Daily Summary Report Time", value=datetime.strptime("09:00", "%H:%M").time())
        st.selectbox("Alert Frequency", ["Real-time", "Hourly Digest", "Daily Digest"])
    
    with tabs[3]:
        st.markdown("### AI Model Configuration")
        
        st.selectbox("OCR Engine", ["Tesseract", "AWS Textract", "Google Vision", "Azure OCR"])
        st.selectbox("Fraud Detection Model", ["Isolation Forest", "XGBoost", "Neural Network", "Ensemble"])
        st.slider("Model Confidence Threshold", 0.0, 1.0, 0.85)
    
    with tabs[4]:
        st.markdown("### 🏢 Company Onboarding")
        company_name = st.text_input("Entity Name", value=st.session_state.get('company_name', 'Your Company Name'))
        company_tin = st.text_input("TIN Number (12 digits)", value=st.session_state.get('company_tin', ''))
        
        # Update session state
        st.session_state['company_name'] = company_name
        st.session_state['company_tin'] = company_tin
        
        st.markdown("### 🔑 Security Protocol")
        reg_face = st.button("📸 Register CFO Biometrics")
        
        if reg_face:
            st.info("Camera initializing... Please look at the sensor.")
            # This is where Person 4's facial recognition registration code goes
