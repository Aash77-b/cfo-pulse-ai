# pages/analytics.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from modules.data_processor import calculate_current_kpis
from utils.helpers import style_axes

def show_analytics():
    st.title("📈 Advanced Analytics")
    kpis = calculate_current_kpis()
    
    if not kpis['scan_history']:
        st.warning("No data yet. Upload documents first.")
        return
    
    df = pd.DataFrame(kpis['scan_history'])
    df['date'] = pd.to_datetime(df['date'])
    
    st.markdown("### 📊 Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Scans", len(df))
    c2.metric("Total Audited", f"${df['total'].sum():,.0f}")
    c3.metric("Avg Transaction", f"${df['total'].mean():,.0f}")
    c4.metric("Flagged", len(df[df['risk_score'] > 25]))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['date'], y=df['risk_score'], mode='lines+markers', name='Risk Score'))
    fig.add_hline(y=25, line_dash="dash", line_color="#10b981")
    fig.add_hline(y=60, line_dash="dash", line_color="#ef4444")
    style_axes(fig)
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(df[['date', 'vendor', 'total', 'risk_score']].tail(20), use_container_width=True)
