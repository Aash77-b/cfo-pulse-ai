import streamlit as st
import time
from modules.data_processor import load_expense_policies, save_expense_policies

def show_policies():
    st.title("📋 Expense Policy Engine")
    st.markdown("Configure company spending rules - AI will automatically flag violations")
    
    policies = load_expense_policies()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💰 Spending Limits")
        policies['max_meal_amount'] = st.number_input("Max Meal Amount ($)", 0.0, 500.0, 
                                                      value=float(policies.get('max_meal_amount', 50.0)), step=5.0)
        policies['max_entertainment'] = st.number_input("Max Entertainment Amount ($)", 0.0, 1000.0, 
                                                        value=float(policies.get('max_entertainment', 100.0)), step=10.0)
        policies['require_receipt_above'] = st.number_input("Require Receipt Above ($)", 0.0, 500.0, 
                                                            value=float(policies.get('require_receipt_above', 25.0)), step=5.0)
    
    with col2:
        st.markdown("### 🚫 Restrictions")
        policies['allow_weekend_transactions'] = st.checkbox("Allow Weekend Transactions", 
                                                             value=policies.get('allow_weekend_transactions', False))
        blacklist_text = "\n".join(policies.get('blacklist_vendors', []))
        new_blacklist = st.text_area("Blacklisted Vendors (one per line)", blacklist_text, height=100)
        policies['blacklist_vendors'] = [v.strip() for v in new_blacklist.split('\n') if v.strip()]
    
    policies['enabled'] = st.checkbox("Enable Policy Enforcement", value=policies.get('enabled', True))
    
    if st.button("💾 Save Policies", type="primary", use_container_width=True):
        save_expense_policies(policies)
        st.success("✅ Expense policies saved!")
        st.balloons()
        time.sleep(1)
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 Active Policy Summary")
    if policies['enabled']:
        st.success("✅ Policy enforcement is ACTIVE")
        st.markdown(f"- Meals over **${policies['max_meal_amount']}** will be flagged")
        st.markdown(f"- Entertainment over **${policies['max_entertainment']}** will be flagged")
        st.markdown(f"- {'❌ Not allowed' if not policies['allow_weekend_transactions'] else '✅ Allowed'} - Weekend transactions")
        st.markdown(f"- Blacklisted vendors: **{', '.join(policies['blacklist_vendors']) if policies['blacklist_vendors'] else 'None'}'**")
    else:
        st.warning("⚠️ Policy enforcement is DISABLED")
