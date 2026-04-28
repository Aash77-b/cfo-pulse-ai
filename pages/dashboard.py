# pages/dashboard.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta
from modules.data_processor import calculate_current_kpis
from modules.fraud_detection import predict_cash_flow
from utils.helpers import base_layout, style_axes

def show_dashboard():
    st.title(f"🏢 {st.session_state['company_name']} Command Center")
    st.caption(f"Real-time monitoring - {datetime.now():%B %d, %Y %H:%M}")
    st.markdown("---")
    
    kpis = calculate_current_kpis()
    st.markdown(f"### Key Performance Indicators ({kpis['total_scanned']} scans)")
    cols = st.columns(4)
    for col, (title, val, delta) in zip(cols, [
        ("Total Audited", kpis['total_audited'], kpis['total_audited_delta']),
        ("Compliance", kpis['compliance_rate'], kpis['compliance_delta']),
        ("Saved", kpis['blocked_leakage'], kpis['blocked_delta']),
        ("Risk Score", kpis['risk_score'], kpis['risk_delta'])
    ]):
        with col:
            st.metric(title, val, delta)
    
    st.markdown("---")
    st.markdown("### 📈 AI-Powered Cash Flow Forecast")
    scan_history = kpis.get('scan_history', [])
    
    if len(scan_history) >= 5:
        predictions, daily_avg, shortfall_risk = predict_cash_flow(scan_history)
        if predictions is not None:
            col1, col2, col3 = st.columns(3)
            col1.metric("Daily Average Spend", f"${daily_avg:.2f}")
            col2.metric("30-Day Forecast", f"${predictions[-1]:,.0f}")
            col3.metric("Shortfall Risk", shortfall_risk)
            
            df_hist = pd.DataFrame(scan_history)
            df_hist['date'] = pd.to_datetime(df_hist['date'])
            df_hist = df_hist.sort_values('date')
            df_hist['cumulative'] = df_hist['total'].cumsum()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_hist['date'], y=df_hist['cumulative'], mode='lines+markers', name='Historical'))
            future_dates = [df_hist['date'].max() + timedelta(days=i+1) for i in range(30)]
            fig.add_trace(go.Scatter(x=future_dates, y=predictions, mode='lines', name='Forecast', line=dict(dash='dash')))
            base_layout(fig, "Cumulative Cash Flow Forecast (30 Days)", 400)
            style_axes(fig)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"📊 Need {5 - len(scan_history)} more scans for AI forecasting")
