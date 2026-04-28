# pages/fraud_reports.py

import streamlit as st
import pandas as pd
from modules.data_processor import calculate_current_kpis, load_company_profile
from modules.pdf_generator import generate_pdf_report

def show_fraud_reports():
    st.title("🚨 Fraud Reports")
    kpis = calculate_current_kpis()
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("📄 Export PDF Report", type="primary"):
            with st.spinner("Generating PDF..."):
                filename = generate_pdf_report(kpis, kpis['scan_history'], load_company_profile())
                with open(filename, "rb") as f:
                    st.download_button("📥 Download", f, file_name=filename)
    
    if kpis['scan_history']:
        df = pd.DataFrame(kpis['scan_history'])
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d %H:%M')
        st.dataframe(df, hide_index=True, use_container_width=True)
    
    for col, (l, v, d) in zip(st.columns(4), [
        ("Scans", str(kpis['total_scanned']), f"{kpis['flagged_count']} flagged"),
        ("Audited", kpis['total_audited'], ""),
        ("Saved", kpis['blocked_leakage'], ""),
        ("Avg Risk", kpis['risk_score'], "")
    ]):
        with col:
            st.metric(l, v, d)
