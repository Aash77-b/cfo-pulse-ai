# pages/policies.py

import streamlit as st
from modules.data_processor import load_expense_policies, save_expense_policies

def show_policies():
    st.title("📋 Expense Policies")
    p = load_expense_policies()
    
    col1, col2 = st.columns(2)
    with col1:
        p['max_meal_amount'] = st.number_input("Max Meal ($)", 0.0, 500.0, p.get('max_meal_amount', 50.0))
        p['max_entertainment'] = st.number_input("Max Entertainment ($)", 0.0, 1000.0, p.get('max_entertainment', 100.0))
    with col2:
        p['allow_weekend_transactions'] = st.checkbox("Allow Weekends", p.get('allow_weekend_transactions', False))
        bl = st.text_area("Blacklist Vendors", "\n".join(p.get('blacklist_vendors', [])))
        p['blacklist_vendors'] = [v.strip() for v in bl.split('\n') if v.strip()]
    
    p['enabled'] = st.checkbox("Enable Policies", p.get('enabled', True))
    
    if st.button("Save Policies", type="primary"):
        save_expense_policies(p)
        st.success("Saved!")
