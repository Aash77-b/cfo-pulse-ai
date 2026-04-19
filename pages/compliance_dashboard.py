# pages/compliance_dashboard.py
"""
NLP & Compliance Dashboard
Main dashboard for tax calculations, compliance scanning, and report generation
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.tax_calculator import EthiopianTaxCalculator
from modules.compliance_engine import ComplianceEngine, RiskLevel
from modules.email_agent import EmailAgent
from modules.report_generator import ReportGenerator
from utils.validators import FinancialValidator
from utils.prompt_templates import PromptTemplates


def display_tax_summary_section():
    """Display tax calculation and summary section"""
    st.header("📊 Tax Calculation Engine")
    
    col1, col2 = st.columns(2)
    
    with col1:
        amount = st.number_input(
            "Enter Amount (ETB)",
            min_value=0.0,
            value=1000.0,
            step=100.0
        )
    
    with col2:
        category = st.selectbox(
            "Transaction Category",
            ["standard", "digital", "goods", "services"]
        )
    
    if st.button("Calculate Taxes", key="calc_tax"):
        calculator = EthiopianTaxCalculator()
        
        # Calculate VAT
        vat_calc = calculator.calculate_vat(amount)
        
        # Calculate ToT
        tot_calc = calculator.calculate_tot(amount, category)
        
        # Display results
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Gross Amount", f"ETB {amount:,.2f}")
        
        with col2:
            st.metric("VAT (15%)", f"ETB {vat_calc['vat_amount']:,.2f}")
        
        with col3:
            rate = tot_calc['rate'] * 100
            st.metric("ToT", f"ETB {tot_calc['tot_amount']:,.2f} ({rate}%)")
        
        with col4:
            total_tax = vat_calc['vat_amount'] + tot_calc['tot_amount']
            st.metric("Total Tax", f"ETB {total_tax:,.2f}")
        
        st.success(f"✓ Tax calculation complete for {category} transaction")


def display_csv_upload_section():
    """Display CSV upload and batch processing section"""
    st.header("📁 Batch Transaction Processing")
    
    uploaded_file = st.file_uploader(
        "Upload CSV with transactions",
        type="csv",
        help="CSV should have columns: amount, vendor, tin, invoice_id, category"
    )
    
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            st.success(f"✓ Loaded {len(df)} transactions")
            
            # Display preview
            st.subheader("Data Preview")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Tax summary
            if st.button("Generate Tax Summary", key="gen_summary"):
                calculator = EthiopianTaxCalculator()
                summary = calculator.generate_tax_summary(df)
                
                st.subheader("Tax Summary")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Transactions", summary["total_transactions"])
                
                with col2:
                    st.metric("Total Amount", f"ETB {summary['total_amount']:,.2f}")
                
                with col3:
                    st.metric("Total VAT", f"ETB {summary['total_vat']:,.2f}")
                
                with col4:
                    st.metric("Total ToT", f"ETB {summary['total_tot']:,.2f}")
                
                st.success(f"✓ Total Tax Due: ETB {summary['total_tax']:,.2f}")
            
            return df
        
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")
    
    return None


def display_compliance_scan_section(df=None):
    """Display compliance scanning section"""
    st.header("🔍 Compliance Scanner")
    
    if df is None or df.empty:
        st.info("Please upload transaction data first")
        return
    
    if st.button("Run Full Compliance Scan", key="run_scan"):
        engine = ComplianceEngine()
        
        # Prepare config
        config = {
            "invoice_col": "invoice_id" if "invoice_id" in df.columns else "id",
            "amount_col": "amount",
            "tin_col": "tin" if "tin" in df.columns else "vendor_tin",
            "date_col": "date" if "date" in df.columns else None
        }
        
        # Run scan
        scan_results = engine.run_full_compliance_scan(df, config)
        violation_summary = engine.get_violation_summary(scan_results)
        
        # Display overall status
        col1, col2, col3 = st.columns(3)
        
        with col1:
            overall_risk = scan_results["overall_risk"].upper()
            if overall_risk == "CRITICAL":
                st.metric("Risk Level", overall_risk, delta="🔴 Critical")
            elif overall_risk == "HIGH":
                st.metric("Risk Level", overall_risk, delta="🟠 High")
            elif overall_risk == "MEDIUM":
                st.metric("Risk Level", overall_risk, delta="🟡 Medium")
            else:
                st.metric("Risk Level", overall_risk, delta="🟢 Low")
        
        with col2:
            st.metric("Total Records", scan_results["total_records"])
        
        with col3:
            st.metric("Total Violations", violation_summary["total_violations"])
        
        # Display violations by severity
        st.subheader("Violations by Severity")
        sev_col1, sev_col2, sev_col3 = st.columns(3)
        
        with sev_col1:
            st.error(f"🔴 Critical: {violation_summary['by_severity'].get('critical', 0)}")
        
        with sev_col2:
            st.warning(f"🟠 High: {violation_summary['by_severity'].get('high', 0)}")
        
        with sev_col3:
            st.info(f"🟡 Medium: {violation_summary['by_severity'].get('medium', 0)}")
        
        # Display detailed checks
        st.subheader("Detailed Check Results")
        
        for check_name, check_result in scan_results["checks"].items():
            if check_result.get("count", 0) > 0:
                with st.expander(f"⚠️ {check_name.replace('_', ' ').title()} ({check_result.get('count', 0)} issues)"):
                    violations = check_result.get("violations", [])
                    if violations:
                        violations_df = pd.DataFrame(violations)
                        st.dataframe(violations_df, use_container_width=True)
                    else:
                        st.success("✓ No violations found")
            else:
                st.success(f"✓ {check_name.replace('_', ' ').title()}: No violations")


def display_email_generation_section(df=None):
    """Display email generation section"""
    st.header("✉️ Email Agent")
    
    email_type = st.selectbox(
        "Select Email Type",
        ["dispute_email", "vendor_verification", "ceo_weekly_summary", "cash_warning"]
    )
    
    agent = EmailAgent()
    
    if email_type == "dispute_email":
        st.subheader("Generate Dispute Email")
        
        col1, col2 = st.columns(2)
        with col1:
            invoice_num = st.text_input("Invoice Number", value="INV-2024-001")
            vendor = st.text_input("Vendor Name", value="Sample Vendor Ltd")
        
        with col2:
            amount = st.number_input("Amount (ETB)", value=5000.0)
        
        discrepancy = st.text_area("Discrepancy Description", 
                                  value="Amount mismatch between PO and invoice")
        
        if st.button("Generate Dispute Email"):
            email_content = agent.generate_dispute_email({
                "invoice_number": invoice_num,
                "vendor_name": vendor,
                "amount": amount,
                "discrepancy": discrepancy,
                "requested_action": "correction"
            })
            
            st.text_area("Generated Email", value=email_content, height=300)
            st.success("✓ Email generated successfully")
    
    elif email_type == "vendor_verification":
        st.subheader("Generate Vendor Verification Email")
        
        col1, col2 = st.columns(2)
        with col1:
            vendor = st.text_input("Vendor Name", value="Sample Vendor Ltd")
            tin = st.text_input("TIN", value="0000000001")
        
        with col2:
            contact = st.text_input("Contact Person", value="Manager")
        
        if st.button("Generate Verification Email"):
            email_content = agent.generate_vendor_verification_email({
                "vendor_name": vendor,
                "tin": tin,
                "contact_person": contact,
                "registration_status": "verification"
            })
            
            st.text_area("Generated Email", value=email_content, height=300)
            st.success("✓ Email generated successfully")
    
    elif email_type == "ceo_weekly_summary":
        st.subheader("Generate CEO Weekly Summary")
        
        col1, col2 = st.columns(2)
        with col1:
            total_trans = st.number_input("Total Transactions", value=45)
            total_amt = st.number_input("Total Amount (ETB)", value=250000.0)
        
        with col2:
            total_tax = st.number_input("Total Tax (ETB)", value=45000.0)
            critical_alerts = st.number_input("Critical Alerts", value=0)
        
        cash_balance = st.number_input("Cash Balance (ETB)", value=150000.0)
        violations = st.number_input("Compliance Violations", value=2)
        
        if st.button("Generate CEO Summary"):
            email_content = agent.generate_ceo_weekly_summary({
                "total_transactions": total_trans,
                "total_amount": total_amt,
                "total_tax": total_tax,
                "cash_balance": cash_balance,
                "critical_alerts": critical_alerts,
                "compliance_violations": violations
            })
            
            st.text_area("Generated Email", value=email_content, height=400)
            st.success("✓ Email generated successfully")
    
    elif email_type == "cash_warning":
        st.subheader("Generate Cash Warning Notice")
        
        col1, col2 = st.columns(2)
        with col1:
            current_balance = st.number_input("Current Cash Balance (ETB)", value=8000.0)
            minimum_required = st.number_input("Minimum Required (ETB)", value=20000.0)
        
        with col2:
            deficit = st.number_input("Projected Deficit (ETB)", value=12000.0)
            days = st.number_input("Days Until Critical", value=5)
        
        if st.button("Generate Cash Warning"):
            email_content = agent.generate_cash_warning_notice({
                "current_balance": current_balance,
                "minimum_required": minimum_required,
                "projected_deficit": deficit,
                "days_until_critical": days
            })
            
            st.text_area("Generated Email", value=email_content, height=400)
            st.success("✓ Email generated successfully")


def display_report_generation_section(df=None):
    """Display report generation section"""
    st.header("📄 Report Generator")
    
    report_type = st.selectbox(
        "Select Report Type",
        ["monthly_tax_report", "compliance_report", "financial_health_report"]
    )
    
    generator = ReportGenerator()
    
    if report_type == "monthly_tax_report":
        st.subheader("Monthly Tax Report")
        
        col1, col2 = st.columns(2)
        with col1:
            month = st.number_input("Month", min_value=1, max_value=12, value=1)
        
        with col2:
            year = st.number_input("Year", min_value=2020, max_value=2030, value=2024)
        
        if df is not None and not df.empty:
            calculator = EthiopianTaxCalculator()
            tax_summary = calculator.generate_tax_summary(df)
        else:
            tax_summary = {
                "total_transactions": 0,
                "total_amount": 0,
                "total_vat": 0,
                "total_tot": 0,
                "total_tax": 0
            }
        
        if st.button("Generate Monthly Tax Report"):
            report = generator.create_monthly_tax_report(df, tax_summary, month, year)
            
            # Display report
            st.success("✓ Report generated successfully")
            st.subheader("Report Content")
            
            report_text = generator.export_report_summary_text(report)
            st.text_area("Report Preview", value=report_text, height=400)
            
            # Export option
            json_export = generator.export_report_to_json(report)
            st.download_button(
                label="Download as JSON",
                data=json_export,
                file_name=f"tax_report_{year}_{month:02d}.json",
                mime="application/json"
            )
    
    elif report_type == "compliance_report":
        st.subheader("Compliance Audit Report")
        
        # Create sample compliance results
        sample_results = {
            "total_records": len(df) if df is not None else 0,
            "overall_risk": "low",
            "checks": {}
        }
        
        sample_violations = {
            "total_violations": 0,
            "by_severity": {"critical": 0, "high": 0, "medium": 0},
            "by_rule": {}
        }
        
        if st.button("Generate Compliance Report"):
            report = generator.create_compliance_report(sample_results, sample_violations)
            
            st.success("✓ Report generated successfully")
            st.subheader("Report Content")
            
            report_text = generator.export_report_summary_text(report)
            st.text_area("Report Preview", value=report_text, height=400)
            
            json_export = generator.export_report_to_json(report)
            st.download_button(
                label="Download as JSON",
                data=json_export,
                file_name=f"compliance_report_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
    
    elif report_type == "financial_health_report":
        st.subheader("Financial Health Report")
        
        col1, col2 = st.columns(2)
        with col1:
            total_trans = st.number_input("Total Transactions", value=45)
            total_amt = st.number_input("Total Amount (ETB)", value=250000.0)
        
        with col2:
            total_tax = st.number_input("Total Tax (ETB)", value=45000.0)
            cash_balance = st.number_input("Cash Balance (ETB)", value=150000.0)
        
        critical_alerts = st.number_input("Critical Alerts", value=0)
        violations = st.number_input("Compliance Violations", value=2)
        
        if st.button("Generate Financial Health Report"):
            report = generator.create_financial_health_report(
                {
                    "total_transactions": total_trans,
                    "total_amount": total_amt,
                    "total_tax": total_tax,
                    "critical_alerts": critical_alerts,
                    "compliance_violations": violations
                },
                {"cash_balance": cash_balance}
            )
            
            st.success("✓ Report generated successfully")
            st.subheader("Report Content")
            
            report_text = generator.export_report_summary_text(report)
            st.text_area("Report Preview", value=report_text, height=400)
            
            json_export = generator.export_report_to_json(report)
            st.download_button(
                label="Download as JSON",
                data=json_export,
                file_name=f"financial_health_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )


def main():
    """Main dashboard application"""
    st.set_page_config(
        page_title="CFO Pulse - NLP & Compliance Engine",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("🚀 CFO Pulse AI - NLP & Compliance Engine")
    st.markdown("""
    **Comprehensive Financial Compliance & Tax Management System**
    
    This dashboard provides tools for:
    - Ethiopian tax calculations (VAT & ToT)
    - Compliance rule enforcement
    - Automated email generation
    - Audit-ready report generation
    """)
    
    # Sidebar navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Select Module",
            ["Tax Calculator", "Batch Processing", "Compliance Scanner", 
             "Email Agent", "Report Generator"]
        )
    
    # Display content based on selection
    df = None
    
    if page == "Tax Calculator":
        display_tax_summary_section()
    
    elif page == "Batch Processing":
        df = display_csv_upload_section()
    
    elif page == "Compliance Scanner":
        st.info("Upload transaction data in the 'Batch Processing' section first")
        # Try to load from session state if available
        if "uploaded_df" in st.session_state:
            df = st.session_state.uploaded_df
        display_compliance_scan_section(df)
    
    elif page == "Email Agent":
        display_email_generation_section(df)
    
    elif page == "Report Generator":
        display_report_generation_section(df)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    **CFO Pulse AI** - Enterprise Financial Management System
    
    For support and documentation, visit: [GitHub Repository](https://github.com/Aash77-b/cfo-pulse-ai)
    """)


if __name__ == "__main__":
    main()
