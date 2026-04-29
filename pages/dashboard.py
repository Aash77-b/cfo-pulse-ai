import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from modules.data_processor import calculate_current_kpis
from modules.fraud_detection import predict_cash_flow
from utils.helpers import base_layout, style_axes

def show_dashboard():
    st.title(f"🏢 {st.session_state.get('company_name', 'CFO-Pulse')} Command Center")
    st.caption(f"Real-time monitoring - {datetime.now().strftime('%B %d, %Y %H:%M')}")
    st.markdown("---")
    
    kpis = calculate_current_kpis()
    st.markdown(f"### Key Performance Indicators ({kpis['total_scanned']} scans)")
    cols = st.columns(4)
    metrics = [
        ("Total Audited", kpis['total_audited'], kpis['total_audited_delta']),
        ("Compliance", kpis['compliance_rate'], kpis['compliance_delta']),
        ("Potential Savings", kpis['blocked_leakage'], kpis['blocked_delta']),
        ("Risk Score", kpis['risk_score'], kpis['risk_delta'])
    ]
    for col, (title, val, delta) in zip(cols, metrics):
        with col:
            st.metric(title, val, delta)
    
    st.markdown("---")
    st.markdown("### 📈 AI-Powered Cash Flow Forecast")
    scan_history = kpis.get('scan_history', [])
    
    if len(scan_history) >= 5:
        predictions, daily_avg, shortfall_risk = predict_cash_flow(scan_history)
        if predictions is not None:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Daily Average Spend", f"${daily_avg:.2f}")
            with col2:
                st.metric("30-Day Forecast", f"${predictions[-1]:,.0f}")
            with col3:
                risk_color = "🟢" if shortfall_risk == "Low" else "🟡" if shortfall_risk == "Medium" else "🔴"
                st.metric("Shortfall Risk", f"{risk_color} {shortfall_risk}")
            
            df_hist = pd.DataFrame(scan_history)
            df_hist['date'] = pd.to_datetime(df_hist['date'])
            df_hist = df_hist.sort_values('date')
            df_hist['cumulative'] = df_hist['total'].cumsum()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_hist['date'], y=df_hist['cumulative'], 
                                    mode='lines+markers', name='Historical',
                                    line=dict(color='#667eea', width=2)))
            future_dates = [df_hist['date'].max() + timedelta(days=i+1) for i in range(30)]
            fig.add_trace(go.Scatter(x=future_dates, y=predictions, 
                                    mode='lines', name='Forecast',
                                    line=dict(color='#ef4444', width=2, dash='dash')))
            base_layout(fig, "Cumulative Cash Flow Forecast (30 Days)", 400)
            style_axes(fig)
            st.plotly_chart(fig, use_container_width=True)
    else:
        scans_needed = 5 - len(scan_history)
        st.info(f"📊 Need {scans_needed} more scan(s) to enable AI cash flow forecasting")
    
    st.markdown("---")
    
    if scan_history:
        high_risk_count = len([s for s in scan_history if s.get('risk_score', 0) > 60])
        flagged_count = kpis['flagged_count']
        saved_str = kpis['blocked_leakage'].replace(',', '')
        total_saved = float(saved_str) if saved_str else 0
        
        st.info(f"""💡 **AI Executive Summary:** Based on {kpis['total_scanned']} scanned documents, 
        your organization has {flagged_count} flagged transactions with {high_risk_count} high-risk items. 
        Potential savings of ${total_saved:,.0f} identified through fraud prevention. 
        {'⚠️ Review high-risk vendors immediately' if high_risk_count > 3 else '✅ Compliance rate is strong.'}""")
