import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from modules.data_processor import calculate_current_kpis
from utils.helpers import style_axes

def show_analytics():
    st.title("📈 Advanced Analytics")
    st.caption("Real-time charts based on your scanned documents")
    
    kpis = calculate_current_kpis()
    scan_history = kpis.get('scan_history', [])
    
    if not scan_history:
        st.warning("📊 No scan data yet. Upload documents in **Scan & Audit** first.")
        return
    
    df = pd.DataFrame(scan_history)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    st.markdown("### 📊 Summary")
    total_scans = len(df)
    total_amount = df['total'].sum()
    avg_transaction = df['total'].mean()
    flagged = len(df[df['risk_score'] > 25])
    high_risk = len(df[df['risk_score'] > 60])
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Scans", total_scans)
    c2.metric("Total Audited", f"${total_amount:,.0f}")
    c3.metric("Avg Transaction", f"${avg_transaction:,.0f}")
    c4.metric("Flagged", f"{flagged} ({high_risk} high risk)")
    
    st.markdown("---")
    st.markdown("### 💰 Transaction History")
    
    df['day'] = df['date'].dt.date
    daily = df.groupby('day').agg(total_amount=('total', 'sum')).reset_index()
    
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(x=daily['day'], y=daily['total_amount'], name='Daily Total', 
                         marker=dict(color='#667eea'), text=[f"${v:,.0f}" for v in daily['total_amount']],
                         textposition='outside'))
    fig1.update_layout(title="Daily Transaction Volume", xaxis_title="Date", yaxis_title="Amount ($)",
                      height=400, plot_bgcolor='white', showlegend=False)
    style_axes(fig1)
    st.plotly_chart(fig1, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 🎯 Risk Score Per Scan")
    
    colors = ['#10b981' if s <= 25 else '#f59e0b' if s <= 60 else '#ef4444' for s in df['risk_score']]
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df['date'], y=df['risk_score'], mode='lines+markers',
                             name='Risk Score', line=dict(color='#6b7280', width=1),
                             marker=dict(size=10, color=colors, line=dict(color='white', width=2)),
                             text=df['vendor']))
    fig2.add_hline(y=25, line_dash="dash", line_color="#10b981")
    fig2.add_hline(y=60, line_dash="dash", line_color="#f59e0b")
    fig2.update_layout(title="Risk Score Per Transaction", xaxis_title="Date", 
                      yaxis_title="Risk Score (0-100)", height=400, plot_bgcolor='white', yaxis=dict(range=[0, 105]))
    style_axes(fig2)
    st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("---")
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("### 🍩 Risk Distribution")
        low = len(df[df['risk_score'] <= 25])
        medium = len(df[(df['risk_score'] > 25) & (df['risk_score'] <= 60)])
        high = len(df[df['risk_score'] > 60])
        fig3 = go.Figure(data=[go.Pie(labels=['Low Risk', 'Medium Risk', 'High Risk'],
                                     values=[low, medium, high], hole=0.4,
                                     marker=dict(colors=['#10b981', '#f59e0b', '#ef4444']),
                                     textinfo='label+percent+value')])
        fig3.update_layout(title="Scan Risk Levels", height=400)
        st.plotly_chart(fig3, use_container_width=True)
    
    with col_right:
        st.markdown("### 🏪 Top Vendors")
        vendor_counts = df['vendor'].value_counts().head(8)
        fig4 = go.Figure(data=[go.Pie(labels=vendor_counts.index, values=vendor_counts.values,
                                     hole=0.4, textinfo='label+value')])
        fig4.update_layout(title="Scans by Vendor", height=400)
        st.plotly_chart(fig4, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 📋 Recent Scans")
    recent = df.tail(10)[['date', 'vendor', 'total', 'currency', 'risk_score']].copy()
    recent = recent.sort_values('date', ascending=False)
    recent['date'] = recent['date'].dt.strftime('%Y-%m-%d %H:%M')
    recent.columns = ['Date', 'Vendor', 'Amount', 'Currency', 'Risk Score']
    recent['Amount'] = recent['Amount'].apply(lambda x: f"${x:,.2f}")
    st.dataframe(recent, hide_index=True, use_container_width=True)
