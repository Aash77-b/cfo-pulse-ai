import streamlit as st
import pandas as pd
from modules.data_processor import calculate_current_kpis, load_company_profile
from modules.pdf_generator import generate_pdf_report

def show_fraud_reports():
    st.title("🚨 Fraud Reports")
    kpis = calculate_current_kpis()
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("📄 Export PDF Report", type="primary", use_container_width=True):
            if kpis['total_scanned'] == 0:
                st.error("No transactions found! Upload receipts first.")
            else:
                with st.spinner("Generating PDF..."):
                    company_profile = load_company_profile()
                    filename = generate_pdf_report(kpis, kpis['scan_history'], company_profile)
                    with open(filename, "rb") as f:
                        st.download_button("📥 Download Report", f, file_name=filename, mime="application/pdf")
    
    if kpis['scan_history']:
        df = pd.DataFrame(kpis['scan_history'])
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d %H:%M')
        st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.info("No scans yet. Upload in Scan & Audit.")
    
    st.markdown("---")
    for col, (l, v, d) in zip(st.columns(4), [
        ("Scans", str(kpis['total_scanned']), f"{kpis['flagged_count']} flagged"),
        ("Audited", kpis['total_audited'], ""),
        ("Saved", kpis['blocked_leakage'], ""),
        ("Avg Risk", kpis['risk_score'], "")
    ]):
        with col:
            st.metric(l, v, d)
