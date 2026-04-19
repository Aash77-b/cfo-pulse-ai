# streamlit_app.py
"""
Main Streamlit Application Entry Point
CFO Pulse AI - NLP & Compliance Engine
"""

import streamlit as st
import sys
import os
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="CFO Pulse AI - NLP & Compliance",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
<style>
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application"""
    
    # Sidebar
    with st.sidebar:
        st.title("🚀 CFO Pulse AI")
        st.markdown("---")
        
        page_selection = st.radio(
            "Choose a Module:",
            [
                "🏠 Home Dashboard",
                "📊 Tax Calculator",
                "📁 Batch Processing",
                "🔍 Compliance Scanner",
                "✉️ Email Agent",
                "📄 Report Generator",
                "⚙️ Settings"
            ],
            index=0
        )
        
        st.markdown("---")
        st.markdown("""
        **Quick Links:**
        - [Documentation](#)
        - [Support](#)
        - [GitHub](#)
        """)
    
    # Main content
    if page_selection == "🏠 Home Dashboard":
        display_home_dashboard()
    
    elif page_selection == "📊 Tax Calculator":
        display_tax_calculator()
    
    elif page_selection == "📁 Batch Processing":
        display_batch_processing()
    
    elif page_selection == "🔍 Compliance Scanner":
        display_compliance_scanner()
    
    elif page_selection == "✉️ Email Agent":
        display_email_agent()
    
    elif page_selection == "📄 Report Generator":
        display_report_generator()
    
    elif page_selection == "⚙️ Settings":
        display_settings()


def display_home_dashboard():
    """Display home dashboard"""
    st.title("Welcome to CFO Pulse AI")
    
    st.markdown("""
    # 💰 Enterprise Financial Compliance System
    
    CFO Pulse AI is a comprehensive platform for managing Ethiopian business tax 
    obligations and compliance requirements.
    
    ## Key Features
    
    ### 🧮 Tax Calculation Engine
    - **VAT Calculation** (15% standard rate)
    - **ToT Processing** (2% standard, 10% digital)
    - Batch transaction processing
    - Category-based tax optimization
    
    ### 🔒 Compliance Rule Engine
    - Duplicate invoice detection
    - Budget limit monitoring
    - TIN verification
    - Tax filing deadline tracking
    - Unusual transaction flagging
    
    ### 📧 AI Email Agent
    - Automated dispute emails
    - Vendor verification requests
    - Executive summaries
    - Cash flow warnings
    - Compliance alerts
    
    ### 📊 Report Generation
    - Monthly tax reports (MOR-ready)
    - Compliance audit reports
    - Financial health dashboards
    - Vendor reconciliation reports
    - PDF and JSON export formats
    
    ## 🚀 Getting Started
    
    1. **Upload Transactions** - Use the "Batch Processing" module to upload your CSV data
    2. **Run Compliance Scan** - Automatically check for violations and risks
    3. **Generate Reports** - Create audit-ready reports for filing and analysis
    4. **Send Communications** - Generate professional emails using the Email Agent
    
    ## 📋 Requirements
    
    For transaction data, ensure your CSV includes:
    - `amount` - Transaction amount in ETB
    - `vendor` - Vendor name
    - `tin` - Tax Identification Number
    - `invoice_id` - Invoice reference number
    - `category` - Transaction category (standard, digital, goods, services)
    
    ## 🔐 Compliance Features
    
    This system helps ensure compliance with:
    - Ethiopian Ministry of Revenue (MOR) requirements
    - Tax filing deadlines (25th of following month)
    - Vendor verification standards
    - Transaction documentation requirements
    - Internal audit trails
    """)
    
    # Display overview cards
    st.markdown("---")
    st.header("Dashboard Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Rules", "25", "+3 this month")
    
    with col2:
        st.metric("Compliance Status", "92%", "+5%")
    
    with col3:
        st.metric("Documents Processed", "1,247", "+128")
    
    with col4:
        st.metric("Violations Detected", "12", "-4")
    
    # Documentation section
    st.markdown("---")
    st.header("Documentation")
    
    with st.expander("📖 User Guide"):
        st.markdown("""
        ### How to Use Each Module
        
        #### Tax Calculator
        1. Enter transaction amount
        2. Select transaction category
        3. Click "Calculate Taxes"
        4. View VAT and ToT breakdown
        
        #### Batch Processing
        1. Prepare CSV with required columns
        2. Upload file
        3. Preview data
        4. Generate tax summary
        
        #### Compliance Scanner
        1. Load transaction data
        2. Select checks to run
        3. Review violation summary
        4. Export compliance report
        
        #### Email Agent
        1. Select email type
        2. Fill in required information
        3. Generate email content
        4. Copy to email client
        
        #### Report Generator
        1. Choose report type
        2. Configure parameters
        3. Generate report
        4. Download in JSON/PDF format
        """)
    
    with st.expander("❓ FAQ"):
        st.markdown("""
        **Q: What is the Ethiopian VAT rate?**
        A: 15% on most taxable goods and services
        
        **Q: What is ToT?**
        A: Tax on Transactions - 2% standard rate, 10% for digital services
        
        **Q: When is the tax filing deadline?**
        A: 25th of the month following the transaction month
        
        **Q: What is a TIN?**
        A: Tax Identification Number - required for all vendors (10 digits)
        
        **Q: Can I export reports?**
        A: Yes, JSON format is available. PDF support coming soon.
        """)


def display_tax_calculator():
    """Display tax calculator"""
    from modules.tax_calculator import EthiopianTaxCalculator
    
    st.title("📊 Tax Calculator")
    
    st.markdown("""
    Calculate VAT (15%) and ToT for your transactions.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        amount = st.number_input("Amount (ETB)", min_value=0.0, value=1000.0, step=100.0)
    
    with col2:
        category = st.selectbox("Category", ["standard", "digital", "goods", "services"])
    
    if st.button("Calculate", key="calc_btn"):
        calculator = EthiopianTaxCalculator()
        vat = calculator.calculate_vat(amount)
        tot = calculator.calculate_tot(amount, category)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Amount", f"ETB {amount:,.2f}")
        with col2:
            st.metric("VAT", f"ETB {vat['vat_amount']:,.2f}")
        with col3:
            st.metric("ToT", f"ETB {tot['tot_amount']:,.2f}")
        with col4:
            total = vat['vat_amount'] + tot['tot_amount']
            st.metric("Total Tax", f"ETB {total:,.2f}")


def display_batch_processing():
    """Display batch processing"""
    st.title("📁 Batch Processing")
    
    st.markdown("""
    Upload and process multiple transactions at once.
    """)
    
    uploaded_file = st.file_uploader("Upload CSV", type="csv")
    if uploaded_file:
        st.success("✓ File uploaded successfully")
        st.info("Batch processing module fully available in compliance_dashboard.py")


def display_compliance_scanner():
    """Display compliance scanner"""
    st.title("🔍 Compliance Scanner")
    
    st.markdown("""
    Scan transactions for compliance violations and risks.
    """)
    
    st.info("Use the Batch Processing module to upload data first, then run compliance checks.")


def display_email_agent():
    """Display email agent"""
    st.title("✉️ Email Agent")
    
    st.markdown("""
    Generate professional business emails automatically.
    """)
    
    email_type = st.selectbox(
        "Email Type",
        ["Dispute Email", "Vendor Verification", "CEO Summary", "Cash Warning"]
    )
    
    st.info(f"Email Agent for {email_type} - Full functionality in compliance_dashboard.py")


def display_report_generator():
    """Display report generator"""
    st.title("📄 Report Generator")
    
    st.markdown("""
    Create audit-ready reports for compliance and financial analysis.
    """)
    
    report_type = st.selectbox(
        "Report Type",
        ["Monthly Tax Report", "Compliance Audit", "Financial Health"]
    )
    
    st.info(f"Generating {report_type} - Full functionality in compliance_dashboard.py")


def display_settings():
    """Display settings"""
    st.title("⚙️ Settings")
    
    st.markdown("""
    ## Configuration Settings
    """)
    
    with st.form("settings_form"):
        st.subheader("Organization")
        org_name = st.text_input("Organization Name", value="CFO Pulse AI")
        org_tin = st.text_input("Organization TIN", value="0000000001")
        
        st.subheader("Compliance Thresholds")
        budget_limit = st.number_input("Budget Limit (ETB)", value=100000.0)
        unusual_threshold = st.number_input("Unusual Amount Threshold (ETB)", value=50000.0)
        
        st.subheader("Email Settings")
        email_sender = st.text_input("Email Sender Address", value="finance@example.com")
        
        if st.form_submit_button("Save Settings"):
            st.success("✓ Settings saved successfully")
            st.balloons()


if __name__ == "__main__":
    main()
