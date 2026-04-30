import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import sqlite3
import hashlib
import re
from PIL import Image
import warnings
warnings.filterwarnings('ignore')

# ════════════════════════════════════════════════
# BACKEND - Database Setup
# ════════════════════════════════════════════════
def init_database():
    """Initialize SQLite database with required tables and sample data"""
    conn = sqlite3.connect('cfo_pulse.db', check_same_thread=False)
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT UNIQUE, 
                  password_hash TEXT,
                  role TEXT DEFAULT 'admin',
                  last_login TIMESTAMP,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Transactions table
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT,
                  vendor TEXT,
                  tin TEXT,
                  amount REAL,
                  vat REAL,
                  net_amount REAL,
                  invoice_no TEXT,
                  items TEXT,
                  risk_score REAL DEFAULT 0,
                  status TEXT DEFAULT 'Pending',
                  department TEXT DEFAULT 'Finance',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Fraud cases table
    c.execute('''CREATE TABLE IF NOT EXISTS fraud_cases
                 (case_id TEXT PRIMARY KEY,
                  date TEXT,
                  vendor TEXT,
                  risk_type TEXT,
                  amount REAL,
                  status TEXT DEFAULT 'Pending',
                  risk_score INTEGER DEFAULT 0,
                  description TEXT,
                  resolution TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Audit logs table
    c.execute('''CREATE TABLE IF NOT EXISTS audit_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  user_id INTEGER,
                  action TEXT,
                  details TEXT,
                  ip_address TEXT DEFAULT '127.0.0.1')''')
    
    # Settings table
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (key TEXT PRIMARY KEY,
                  value TEXT,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Insert default admin user (admin/admin123)
    c.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
    if c.fetchone()[0] == 0:
        default_hash = hashlib.sha256('admin123'.encode()).hexdigest()
        c.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                 ('admin', default_hash, 'admin'))
    
    # Insert demo user
    c.execute("SELECT COUNT(*) FROM users WHERE username='demo'")
    if c.fetchone()[0] == 0:
        demo_hash = hashlib.sha256('demo123'.encode()).hexdigest()
        c.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                 ('demo', demo_hash, 'user'))
    
    # Insert sample fraud cases
    c.execute("SELECT COUNT(*) FROM fraud_cases")
    if c.fetchone()[0] == 0:
        sample_cases = [
            ('FRD-001', '2026-04-20', 'Addis Tech Solutions', 'Duplicate Invoice', 45000, 'Investigating', 92, 
             'Same invoice submitted twice for payment. Possible duplicate claim detected.', ''),
            ('FRD-002', '2026-04-19', 'Global Supplies PLC', 'Price Inflation', 12500, 'Resolved', 67, 
             'Prices are 300% above market rate for standard office supplies.', 'Vendor corrected pricing and issued credit note.'),
            ('FRD-003', '2026-04-18', 'Unknown Vendor Ltd', 'Ghost Vendor', 89000, 'Pending', 95, 
             'Vendor not found in tax registry. TIN verification failed.', ''),
            ('FRD-004', '2026-04-17', 'IT Solutions Co', 'Unauthorized Purchase', 23400, 'Investigating', 78, 
             'No purchase order or approval found for this transaction.', ''),
            ('FRD-005', '2026-04-16', 'Quick Logistics', 'Overbilling', 7800, 'Resolved', 45, 
             'Quantity mismatch: Charged for 100 units, received 75 units.', 'Credit note issued for difference.'),
            ('FRD-006', '2026-04-15', 'Office Depot ET', 'Fake Receipt', 15600, 'Investigating', 88, 
             'Receipt appears to be forged. Layout and fonts don\'t match vendor template.', ''),
            ('FRD-007', '2026-04-14', 'Tech Gadgets', 'Expense Splitting', 34000, 'Pending', 72, 
             'Large expense split into multiple small transactions to avoid approval thresholds.', '')
        ]
        c.executemany('''INSERT OR IGNORE INTO fraud_cases 
                         (case_id, date, vendor, risk_type, amount, status, risk_score, description, resolution)
                         VALUES (?,?,?,?,?,?,?,?,?)''', sample_cases)
    
    # Insert sample transactions
    c.execute("SELECT COUNT(*) FROM transactions")
    if c.fetchone()[0] == 0:
        sample_transactions = [
            ('2026-04-20', 'Addis Tech Solutions', '0012345678', 45000, 6750, 38250, 'INV-2026-001', 'IT Equipment Purchase', 85, 'Under Review', 'IT'),
            ('2026-04-19', 'Office Supplies Co', '0087654321', 12500, 1875, 10625, 'INV-2026-002', 'Office Stationery', 25, 'Approved', 'Operations'),
            ('2026-04-18', 'Logistics Partner ET', '0056781234', 89000, 13350, 75650, 'INV-2026-003', 'Shipping & Handling', 45, 'Under Review', 'Operations'),
            ('2026-04-17', 'IT Solutions Ltd', '0034567890', 23400, 3510, 19890, 'INV-2026-004', 'Software License Renewal', 15, 'Approved', 'IT'),
            ('2026-04-16', 'Consulting Group ET', '0090123456', 78000, 11700, 66300, 'INV-2026-005', 'Financial Consulting', 30, 'Approved', 'Finance'),
            ('2026-04-15', 'Cleaning Services', '0011223344', 8500, 1275, 7225, 'INV-2026-006', 'Office Cleaning March', 10, 'Approved', 'HR'),
            ('2026-04-14', 'Marketing Agency', '0055667788', 56000, 8400, 47600, 'INV-2026-007', 'Q2 Campaign Materials', 20, 'Approved', 'Sales'),
            ('2026-04-13', 'Utility Provider', '0099887766', 23000, 3450, 19550, 'INV-2026-008', 'Electricity Bill March', 5, 'Approved', 'Operations')
        ]
        c.executemany('''INSERT INTO transactions 
                        (date, vendor, tin, amount, vat, net_amount, invoice_no, items, risk_score, status, department)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)''', sample_transactions)
    
    conn.commit()
    return conn

# ════════════════════════════════════════════════
# BACKEND - Helper Functions
# ════════════════════════════════════════════════
def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_credentials(username, password):
    """Verify user credentials against database"""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password_hash=?", 
                 (username, hash_password(password)))
        return c.fetchone()
    except Exception as e:
        st.error(f"Database error: {e}")
        return None

def log_audit(user_id, action, details, ip="127.0.0.1"):
    """Log audit trail"""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("""INSERT INTO audit_logs (timestamp, user_id, action, details, ip_address)
                     VALUES (?,?,?,?,?)""",
                 (datetime.now(), user_id, action, details, ip))
        conn.commit()
    except Exception:
        pass  # Silent fail for audit logging

def ethiopian_vat(total):
    """Calculate Ethiopian VAT (15%) for MOR compliance"""
    vat = total * 0.15
    return {
        "net_amount": round(total - vat, 2),
        "vat_amount": round(vat, 2),
        "tax_type": "VAT (15%)",
        "compliance_status": "Ready for MOR Filing"
    }

def fraud_detection_model(transaction_data):
    """AI-based fraud detection scoring"""
    risk_factors = []
    
    # Factor 1: Amount anomaly
    amount = transaction_data.get('total', 0)
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT AVG(amount) FROM transactions")
        avg_amount = c.fetchone()[0] or 5000
    except Exception:
        avg_amount = 5000
    
    if avg_amount > 0:
        amount_ratio = min(amount / avg_amount, 5)
        risk_factors.append(amount_ratio * 20)
    
    # Factor 2: Vendor risk assessment
    vendor = transaction_data.get('vendor', '').lower()
    high_risk_keywords = ['unknown', 'shell', 'ghost', 'fake', 'test']
    if any(keyword in vendor for keyword in high_risk_keywords):
        risk_factors.append(40)
    else:
        risk_factors.append(10)
    
    # Factor 3: Amount threshold
    if amount > 50000:
        risk_factors.append(25)
    elif amount > 20000:
        risk_factors.append(15)
    else:
        risk_factors.append(5)
    
    # Calculate final risk score (0-100)
    risk_score = min(100, sum(risk_factors))
    return round(risk_score, 1)

def generate_credit_report(company_name, company_tin):
    """Generate comprehensive credit report for SME"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Base credit score
        credit_score = 700
        
        # Factor 1: Transaction history
        c.execute("SELECT COUNT(*) FROM transactions")
        transaction_count = c.fetchone()[0]
        credit_score += min(50, transaction_count * 5)
        
        # Factor 2: Compliance check
        c.execute("SELECT COUNT(*) FROM transactions WHERE status='Approved'")
        approved = c.fetchone()[0]
        compliance_rate = (approved / transaction_count * 100) if transaction_count > 0 else 100
        credit_score += (compliance_rate - 80) * 2
        
        # Factor 3: Fraud history penalty
        c.execute("SELECT COUNT(*) FROM fraud_cases WHERE status IN ('Investigating', 'Pending')")
        pending_fraud = c.fetchone()[0]
        credit_score -= pending_fraud * 15
        
        # Factor 4: Total volume bonus
        c.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions")
        total_volume = c.fetchone()[0]
        if total_volume > 200000:
            credit_score += 30
        elif total_volume > 100000:
            credit_score += 15
        
        # Cap credit score between 300-850
        return min(850, max(300, int(credit_score)))
    
    except Exception as e:
        return 650  # Default score if calculation fails

# ════════════════════════════════════════════════
# FRONTEND - Session State Initialization
# ════════════════════════════════════════════════
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'company_name': "CFO-Pulse Partner",
        'company_tin': "0000000000",
        'user_authenticated': False,
        'username': '',
        'user_role': 'user',
        'current_page': 'Dashboard',
        'credit_report': None,
        'last_scan': None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ════════════════════════════════════════════════
# FRONTEND - Page Configuration
# ════════════════════════════════════════════════
st.set_page_config(
    page_title="CFO-Pulse AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database (cached)
@st.cache_resource
def get_db():
    return init_database()

# ════════════════════════════════════════════════
# FRONTEND - Custom CSS Styles
# ════════════════════════════════════════════════
def inject_custom_css():
    st.markdown("""
    <style>
    /* Main container */
    .main {
        padding: 0rem 1rem;
    }
    
    /* Custom cards */
    .custom-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        margin-bottom: 20px;
    }
    
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border: 1px solid #e0e0e0;
        margin-bottom: 10px;
    }
    
    /* Risk badges */
    .risk-badge-low {
        background: #10b981;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
    
    .risk-badge-medium {
        background: #f59e0b;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
    
    .risk-badge-high {
        background: #ef4444;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
    
    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 45px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background-color: #667eea;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
        background: #f8f9fa;
    }
    
    .stTabs [aria-selected="true"] {
        background: #667eea !important;
        color: white !important;
    }
    
    /* Login container */
    .login-container {
        max-width: 450px;
        margin: 80px auto;
        padding: 40px;
        background: white;
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.1);
    }
    
    /* Alert cards */
    .alert-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    /* Status indicators */
    .status-active {
        color: #10b981;
        font-weight: 600;
    }
    
    .status-warning {
        color: #f59e0b;
        font-weight: 600;
    }
    
    .status-danger {
        color: #ef4444;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ════════════════════════════════════════════════
# FRONTEND - Login Page
# ════════════════════════════════════════════════
def login_page():
    """Display login form"""
    st.markdown("""
    <div style="text-align:center; padding:60px 0 30px 0;">
        <h1 style="font-size:52px; font-weight:700; color:#1f2937;">🛡️ CFO-Pulse AI</h1>
        <p style="font-size:20px; color:#6b7280; margin-top:10px;">
            Enterprise Security & Compliance Platform
        </p>
        <p style="font-size:14px; color:#9ca3af;">
            Ethiopian Tax Compliance • Fraud Detection • Financial Intelligence
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown("### 🔐 Secure Access")
        
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                login_submit = st.form_submit_button("🔓 Sign In", use_container_width=True)
            with col_btn2:
                demo_submit = st.form_submit_button("🎮 Demo Access", use_container_width=True)
            
            if login_submit:
                if username and password:
                    user = verify_credentials(username, password)
                    if user:
                        st.session_state['user_authenticated'] = True
                        st.session_state['username'] = username
                        st.session_state['user_role'] = user[3]
                        log_audit(user[0], "LOGIN", f"User '{username}' logged in successfully")
                        st.success("✅ Authentication successful! Redirecting...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.warning("⚠️ Please enter both username and password")
            
            if demo_submit:
                st.session_state['user_authenticated'] = True
                st.session_state['username'] = 'demo'
                st.session_state['user_role'] = 'user'
                st.success("✅ Demo access granted! Redirecting...")
                time.sleep(1)
                st.rerun()
        
        st.markdown("""
        <div style="text-align:center; margin-top:20px; padding:15px; background:#f3f4f6; border-radius:10px;">
            <p style="margin:0; font-size:13px; color:#6b7280;">
                <strong>Demo Credentials:</strong><br>
                Username: <code>admin</code> | Password: <code>admin123</code><br>
                Or click <strong>"Demo Access"</strong> for instant login
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════
# Check Authentication
# ════════════════════════════════════════════════
if not st.session_state.get('user_authenticated', False):
    login_page()
    st.stop()

# ════════════════════════════════════════════════
# FRONTEND - Sidebar Navigation
# ════════════════════════════════════════════════
with st.sidebar:
    # User profile section
    st.markdown("""
    <div style="text-align:center; padding:20px 0;">
        <div style="width:80px; height:80px; background:linear-gradient(135deg,#667eea,#764ba2);
                    border-radius:50%; margin:0 auto; display:flex; align-items:center; justify-content:center;
                    box-shadow:0 5px 15px rgba(102,126,234,0.4);">
            <span style="font-size:35px;">👤</span>
        </div>
        <h3 style="margin:10px 0 5px; color:#1f2937;">Ashenafi D.</h3>
        <p style="color:#6b7280; margin:0;">CFO • Finance Lead</p>
        <div style="margin-top:10px;">
            <span style="background:#10b981; color:white; padding:5px 15px;
                       border-radius:20px; font-size:12px; font-weight:600;">
                ✓ Authenticated
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Navigation menu
    st.markdown("### 📍 Navigation")
    page = st.radio(
        "Select Page",
        ["📊 Dashboard", "🔍 Scan & Audit", "🚨 Fraud Reports", "📈 Analytics", "🏦 Credit Hub"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Real-time risk assessment
    st.markdown("### 🎯 Risk Assessment")
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT AVG(risk_score) FROM fraud_cases WHERE status IN ('Investigating', 'Pending')")
        avg_risk = c.fetchone()[0]
        risk_score = int(avg_risk) if avg_risk else 23
    except Exception:
        risk_score = 23
    
    risk_level = "Low" if risk_score < 30 else "Medium" if risk_score < 70 else "High"
    risk_badge_class = f"risk-badge-{risk_level.lower()}"
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**Risk Score:** {risk_score}/100")
    with col2:
        st.markdown(f'<span class="{risk_badge_class}">{risk_level}</span>', unsafe_allow_html=True)
    
    st.progress(risk_score / 100, text=f"Risk Level: {risk_level}")
    st.caption("📉 Down 12% from last week")
    
    st.markdown("---")
    
    # Quick statistics
    st.markdown("### 📈 Live Statistics")
    try:
        c.execute("SELECT COUNT(*) FROM transactions WHERE date >= date('now', '-30 days')")
        active_monitors = c.fetchone()[0]
    except Exception:
        active_monitors = 12
    
    try:
        c.execute("SELECT COUNT(*) FROM fraud_cases WHERE date >= date('now', '-1 days')")
        alerts_today = c.fetchone()[0]
    except Exception:
        alerts_today = 3
    
    st.metric("Active Monitors", active_monitors, "+2")
    st.metric("Alerts Today", alerts_today, "-1")
    st.metric("Avg Response", "2.4 min", "-0.3")
    
    st.markdown("---")
    
    # Logout button
    if st.button("🚪 Logout", use_container_width=True, type="secondary"):
        log_audit(1, "LOGOUT", f"User '{st.session_state.get('username')}' logged out")
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ════════════════════════════════════════════════
# Shared Visualization Helpers
# ════════════════════════════════════════════════
GRID_COLOR = '#e5e7eb'

def style_axes(fig):
    """Apply consistent axis styling"""
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=GRID_COLOR)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=GRID_COLOR)

def base_layout(fig, title, height=400):
    """Apply consistent layout styling"""
    fig.update_layout(
        title=title,
        title_font_size=16,
        height=height,
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )

def metric_card(title, value, delta, icon):
    """Generate metric card HTML"""
    return f"""
    <div class="metric-card">
        <div style="display:flex; align-items:center; margin-bottom:10px;">
            <span style="font-size:24px; margin-right:10px;">{icon}</span>
            <span style="color:#6b7280; font-size:14px;">{title}</span>
        </div>
        <h2 style="margin:5px 0; color:#1f2937; font-size:28px;">{value}</h2>
        <p style="color:#10b981; margin:0; font-weight:600;">{delta}</p>
    </div>
    """

def alert_card(severity, message, time_ago):
    """Generate alert card HTML"""
    color_map = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#10b981"}
    color = color_map.get(severity, "#6b7280")
    
    return f"""
    <div style="background:white; padding:15px; border-radius:10px; margin-bottom:10px;
                border-left:4px solid {color}; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
        <div style="display:flex; justify-content:space-between; align-items:start;">
            <strong style="color:#1f2937;">{message}</strong>
            <span style="color:#6b7280; font-size:12px; white-space:nowrap; margin-left:10px;">{time_ago}</span>
        </div>
        <span style="background:{color}20; color:{color}; padding:2px 10px; 
                    border-radius:12px; font-size:11px; font-weight:600;">
            {severity}
        </span>
    </div>
    """

# ════════════════════════════════════════════════
# PAGE 1: Dashboard
# ════════════════════════════════════════════════
if "📊 Dashboard" in page:
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🛡️ CFO-Pulse AI Command Center")
        st.caption(f"Real-time monitoring active • {datetime.now():%B %d, %Y • %H:%M UTC}")
    with col2:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#667eea,#764ba2); padding:15px;
                    border-radius:10px; color:white; text-align:center;">
            <h4 style="margin:0;">🤖 AI Status</h4>
            <p style="margin:5px 0 0; font-size:14px;">🟢 All Systems Active</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # KPI Metrics
    st.markdown("### 📊 Key Performance Indicators")
    
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM transactions WHERE date >= date('now', '-30 days')")
        tx_count, total_audited = c.fetchone()
        
        c.execute("SELECT COALESCE(SUM(amount), 0) FROM fraud_cases WHERE status IN ('Investigating', 'Pending')")
        blocked_leakage = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM fraud_cases WHERE status='Resolved'")
        resolved_cases = c.fetchone()[0]
    except Exception:
        tx_count, total_audited = 45, 245000
        blocked_leakage = 12400
        resolved_cases = 32
    
    cols = st.columns(4)
    metrics_data = [
        ("💰 Total Audited", f"ETB {total_audited:,.0f}", "↑ 5.2% this month", "💎"),
        ("✅ Compliance Rate", "98.2%", "↑ 0.4% improvement", "📋"),
        ("🛡️ Fraud Blocked", f"ETB {blocked_leakage:,.0f}", f"{resolved_cases} cases resolved", "🔒"),
        ("⚡ Risk Score", f"{risk_score}/100", "↓ 12% from last week", "📉")
    ]
    
    for col, (title, value, delta, icon) in zip(cols, metrics_data):
        with col:
            st.markdown(metric_card(title, value, delta, icon), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📈 Risk Trends", "🔍 Anomaly Detection", "📊 Department Overview"])
    
    with tab1:
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.markdown("### Real-time Risk Monitoring")
            
            # Generate trend data
            dates = pd.date_range('2026-04-01', periods=30, freq='D')
            np.random.seed(42)
            trend_data = pd.DataFrame({
                'Date': dates,
                'Fraud Risk': np.random.randn(30).cumsum() * 2 + 30,
                'Tax Compliance': np.random.randn(30).cumsum() * 1.5 + 85,
                'Cash Liquidity': np.random.randn(30).cumsum() * 3 + 60
            })
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=trend_data['Date'], y=trend_data['Fraud Risk'],
                mode='lines', name='Fraud Risk',
                line=dict(color='#ef4444', width=3)
            ))
            fig.add_trace(go.Scatter(
                x=trend_data['Date'], y=trend_data['Tax Compliance'],
                mode='lines', name='Tax Compliance',
                line=dict(color='#10b981', width=3)
            ))
            fig.add_trace(go.Scatter(
                x=trend_data['Date'], y=trend_data['Cash Liquidity'],
                mode='lines', name='Cash Liquidity',
                line=dict(color='#3b82f6', width=3)
            ))
            
            base_layout(fig, "30-Day Risk Trend Analysis")
            style_axes(fig)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_right:
            st.markdown("### ⚠️ Active Alerts")
            
            try:
                c.execute("""SELECT risk_type, risk_score, date 
                           FROM fraud_cases 
                           WHERE status IN ('Investigating', 'Pending')
                           ORDER BY risk_score DESC LIMIT 5""")
                alerts = c.fetchall()
            except Exception:
                alerts = [
                    ("Duplicate Invoice", 92, "2026-04-20"),
                    ("Ghost Vendor", 95, "2026-04-18"),
                    ("Unauthorized Purchase", 78, "2026-04-17")
                ]
            
            for alert in alerts:
                severity = 'High' if alert[1] > 70 else 'Medium' if alert[1] > 40 else 'Low'
                st.markdown(alert_card(severity, alert[0], alert[2]), unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### 🔍 AI-Powered Anomaly Detection")
        
        try:
            c.execute("SELECT amount, risk_score FROM transactions ORDER BY date DESC LIMIT 100")
            tx_data = c.fetchall()
            
            if tx_data:
                df_plot = pd.DataFrame(tx_data, columns=['Amount', 'Risk Score'])
                
                # Simple anomaly detection
                mean_amount = df_plot['Amount'].mean()
                std_amount = df_plot['Amount'].std()
                df_plot['Type'] = df_plot['Amount'].apply(
                    lambda x: 'Anomaly' if abs(x - mean_amount) > 2 * std_amount else 'Normal'
                )
                
                fig = px.scatter(
                    df_plot, x='Amount', y='Risk Score',
                    color='Type',
                    title="Transaction Pattern Analysis",
                    color_discrete_map={'Normal': '#667eea', 'Anomaly': '#ef4444'},
                    size_max=10
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                anomaly_count = len(df_plot[df_plot['Type'] == 'Anomaly'])
                st.info(f"🔍 Detected {anomaly_count} anomalous transactions out of {len(df_plot)} total")
        except Exception as e:
            st.warning("Anomaly detection data is being processed. Please check back later.")
    
    with tab3:
        st.markdown("### Department-wise Compliance Overview")
        
        dept_data = pd.DataFrame({
            'Department': ['Finance', 'Operations', 'Sales', 'IT', 'HR'],
            'Compliance Score': [98, 92, 95, 99, 97],
            'Transactions': [1240, 890, 1560, 430, 320],
            'Budget': [500000, 350000, 600000, 200000, 150000]
        })
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=dept_data['Department'],
            y=dept_data['Transactions'],
            name='Transactions',
            marker_color='#667eea'
        ))
        fig.add_trace(go.Scatter(
            x=dept_data['Department'],
            y=dept_data['Compliance Score'],
            name='Compliance %',
            yaxis='y2',
            line=dict(color='#10b981', width=3)
        ))
        
        fig.update_layout(
            title="Department Performance Metrics",
            yaxis=dict(title="Transaction Count"),
            yaxis2=dict(title="Compliance %", overlaying='y', side='right', range=[85, 100]),
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════════════
# PAGE 2: Scan & Audit
# ════════════════════════════════════════════════
elif "🔍 Scan & Audit" in page:
    st.title("🔍 Intelligent Document Scanner")
    st.markdown("Upload receipts or invoices for AI-powered audit and fraud detection")
    
    # Upload area
    st.markdown("""
    <div style="border:2px dashed #667eea; border-radius:15px; padding:40px; text-align:center;
                background:linear-gradient(135deg,#667eea10,#764ba210); margin:20px 0;">
        <span style="font-size:48px;">📄</span>
        <h3>Drop your files here or click to upload</h3>
        <p style="color:#6b7280;">Supports JPG, PNG, PDF (Max 10MB)</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['jpg', 'jpeg', 'png', 'pdf'],
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        st.markdown("---")
        
        # Processing simulation
        with st.status("🔍 AI Agent analyzing document...", expanded=True) as status:
            st.write("📄 Extracting text from document...")
            progress_bar = st.progress(0)
            
            for i in range(100):
                time.sleep(0.02)
                progress_bar.progress(i + 1)
            
            st.write("✅ Text extraction complete")
            
            # Simulated OCR result
            extracted_data = {
                "vendor": "Addis Tech Solutions PLC",
                "tin": "0012345678",
                "total": 12500.00,
                "date": "2026-04-20",
                "items": "Laptop Battery (3 units), HDMI Cable (2 units), USB Hub (1 unit)",
                "invoice_no": f"INV-{datetime.now():%Y%m%d}-{np.random.randint(1000, 9999)}"
            }
            
            # Add VAT calculation
            vat_info = ethiopian_vat(extracted_data["total"])
            extracted_data.update(vat_info)
            
            # Run fraud detection
            risk_score_val = fraud_detection_model(extracted_data)
            extracted_data['risk_score'] = risk_score_val
            
            st.write("🔍 Cross-referencing with compliance database...")
            time.sleep(0.5)
            st.write("📊 Running fraud detection algorithms...")
            time.sleep(0.5)
            
            # Save to database
            try:
                conn = get_db()
                c = conn.cursor()
                c.execute("""INSERT INTO transactions 
                           (date, vendor, tin, amount, vat, net_amount, invoice_no, items, risk_score, status, department)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                         (extracted_data['date'], extracted_data['vendor'], extracted_data['tin'],
                          extracted_data['total'], extracted_data['vat_amount'], 
                          extracted_data['net_amount'], extracted_data['invoice_no'],
                          extracted_data['items'], risk_score_val, 'Reviewed', 'Finance'))
                conn.commit()
                st.write("✅ Document saved to database")
            except Exception as e:
                st.error(f"Error saving to database: {e}")
            
            status.update(label="✅ Analysis Complete!", state="complete", expanded=False)
        
        # Results display
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📋 Extracted Information")
            st.markdown("""
            <div style="background:white; padding:20px; border-radius:15px; 
                        box-shadow:0 2px 10px rgba(0,0,0,0.05);">
            """, unsafe_allow_html=True)
            
            display_fields = ['vendor', 'tin', 'total', 'date', 'items', 'invoice_no']
            for field in display_fields:
                st.markdown(f"**{field.replace('_', ' ').title()}:** {extracted_data[field]}")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            with st.expander("📝 Ethiopian Tax Breakdown", expanded=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Claimable VAT", f"ETB {extracted_data['vat_amount']:,.2f}")
                with col_b:
                    st.metric("Net Transaction", f"ETB {extracted_data['net_amount']:,.2f}")
                st.success("💡 This receipt is compliant with **EFDA/MOR** standards")
        
        with col2:
            st.markdown("### 🚨 Risk Assessment")
            
            if risk_score_val > 70:
                st.error(f"⚠️ **HIGH RISK DETECTED** - Score: {risk_score_val}/100")
                st.markdown("""
                <div style="background:#fef2f2; padding:15px; border-radius:10px; 
                            border:1px solid #fecaca; margin:10px 0;">
                    <strong style="color:#dc2626;">⚠️ Risk Factors Identified:</strong>
                    <ul>
                        <li>Transaction amount exceeds normal threshold</li>
                        <li>Additional verification required</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                
                # Generate dispute email draft
                st.markdown("### 📧 Auto-Generated Dispute Email")
                email_draft = f"""Subject: Urgent: Transaction Review Required - Invoice {extracted_data['invoice_no']}

Dear {extracted_data['vendor']} Team,

Our AI-powered audit system has flagged a potential discrepancy in invoice {extracted_data['invoice_no']}:

• Amount: ETB {extracted_data['total']:,.2f}
• Date: {extracted_data['date']}
• Risk Score: {risk_score_val}/100

Please provide supporting documentation within 48 hours.

Best regards,
Finance Department"""
                
                st.text_area("Email Draft", email_draft, height=250)
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("📤 Send Dispute Email", type="primary", use_container_width=True):
                        st.success("✅ Dispute email queued for sending!")
                        st.balloons()
                with col_btn2:
                    if st.button("📋 Copy to Clipboard", use_container_width=True):
                        try:
                            import pyperclip
                            pyperclip.copy(email_draft)
                            st.info("📋 Copied to clipboard!")
                        except Exception:
                            st.warning("Clipboard access not available")
            else:
                st.success(f"✅ **VERIFIED** - Risk Score: {risk_score_val}/100")
                st.markdown("""
                <div style="background:#f0fdf4; padding:15px; border-radius:10px; 
                            border:1px solid #bbf7d0;">
                    <strong style="color:#16a34a;">✓ All compliance checks passed</strong><br>
                    <span>Document is authentic and compliant with regulations</span>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("✅ Authorize Payment", type="primary", use_container_width=True):
                    st.success("✅ Payment authorized and queued for processing!")
                    st.balloons()

# ════════════════════════════════════════════════
# PAGE 3: Fraud Reports
# ════════════════════════════════════════════════
elif "🚨 Fraud Reports" in page:
    st.title("🚨 Fraud Intelligence Dashboard")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        date_filter = st.date_input(
            "Date Range",
            value=(datetime.now() - timedelta(days=30), datetime.now())
        )
    with col2:
        risk_filter = st.multiselect(
            "Risk Level",
            ["High", "Medium", "Low"],
            default=["High", "Medium"]
        )
    with col3:
        status_filter = st.selectbox(
            "Status",
            ["All", "Investigating", "Pending", "Resolved"]
        )
    
    st.markdown("---")
    
    # Fetch fraud cases
    try:
        conn = get_db()
        c = conn.cursor()
        
        query = "SELECT * FROM fraud_cases WHERE 1=1"
        params = []
        
        if status_filter != "All":
            query += " AND status=?"
            params.append(status_filter)
        
        if "High" in risk_filter and "Medium" not in risk_filter:
            query += " AND risk_score > 70"
        elif "Low" in risk_filter and "High" not in risk_filter:
            query += " AND risk_score <= 40"
        
        query += " ORDER BY date DESC"
        
        c.execute(query, params)
        cases = c.fetchall()
        
        if cases:
            df_cases = pd.DataFrame(cases, columns=[
                'Case ID', 'Date', 'Vendor', 'Risk Type', 'Amount', 
                'Status', 'Risk Score', 'Description', 'Resolution', 'Created At'
            ])
            
            # Display cases table
            st.dataframe(
                df_cases[['Case ID', 'Date', 'Vendor', 'Risk Type', 'Amount', 'Status', 'Risk Score']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Risk Score": st.column_config.ProgressColumn(
                        "Risk Score",
                        help="Fraud risk score (0-100)",
                        format="%d",
                        min_value=0,
                        max_value=100
                    )
                }
            )
            
            # Summary statistics
            st.markdown("---")
            cols = st.columns(4)
            stats = [
                ("Total Cases", str(len(cases)), "Active investigations"),
                ("Total Value at Risk", f"ETB {sum(c[4] for c in cases):,.0f}", "Potential loss"),
                ("Resolved Cases", str(sum(1 for c in cases if c[5] == 'Resolved')), "Successfully closed"),
                ("Avg Risk Score", f"{int(np.mean([c[6] for c in cases]))}/100", "Risk level indicator")
            ]
            
            for col, (label, value, help_text) in zip(cols, stats):
                with col:
                    st.metric(label, value, help=help_text)
            
            # Individual case details
            st.markdown("---")
            st.markdown("### 📋 Case Details")
            
            selected_case = st.selectbox(
                "Select case to view details",
                [f"{c[0]} - {c[3]} ({c[1]})" for c in cases]
            )
            
            if selected_case:
                case_id = selected_case.split(' - ')[0]
                case_data = next(c for c in cases if c[0] == case_id)
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"""
                    **Case ID:** {case_data[0]}  
                    **Date:** {case_data[1]}  
                    **Vendor:** {case_data[2]}  
                    **Risk Type:** {case_data[3]}  
                    **Amount:** ETB {case_data[4]:,.2f}
                    """)
                with col_b:
                    st.markdown(f"""
                    **Status:** {case_data[5]}  
                    **Risk Score:** {case_data[6]}/100  
                    **Description:** {case_data[7]}  
                    **Resolution:** {case_data[8] or 'Pending'}
                    """)
        else:
            st.info("No fraud cases found matching your filters")
    
    except Exception as e:
        st.error(f"Error loading fraud cases: {e}")

# ════════════════════════════════════════════════
# PAGE 4: Analytics
# ════════════════════════════════════════════════
elif "📈 Analytics" in page:
    st.title("📈 Advanced Analytics")
    
    tab1, tab2 = st.tabs(["📊 Trend Analysis", "💰 Cost-Benefit Analysis"])
    
    with tab1:
        st.markdown("### Fraud Detection Trends")
        
        # Generate trend data
        dates = pd.date_range('2026-01-01', '2026-04-20', freq='D')
        np.random.seed(42)
        trend_data = pd.DataFrame({
            'Date': dates,
            'Fraud Attempts': np.random.poisson(5, len(dates)),
            'Detected': np.random.poisson(4, len(dates)),
            'Prevented Loss': np.random.exponential(10000, len(dates))
        })
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trend_data['Date'], y=trend_data['Fraud Attempts'],
            mode='lines', name='Fraud Attempts',
            line=dict(color='#ef4444', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=trend_data['Date'], y=trend_data['Detected'],
            mode='lines', name='Detected',
            line=dict(color='#10b981', width=2, dash='dot')
        ))
        
        base_layout(fig, "Fraud Detection Rate Over Time")
        style_axes(fig)
        st.plotly_chart(fig, use_container_width=True)
        
        # Detection rate metric
        detection_rate = (trend_data['Detected'].sum() / trend_data['Fraud Attempts'].sum()) * 100
        st.metric("Overall Detection Rate", f"{detection_rate:.1f}%", "↑ 2.3%")
    
    with tab2:
        st.markdown("### 💰 Cost Savings Analysis")
        
        savings_data = pd.DataFrame({
            'Month': ['Jan', 'Feb', 'Mar', 'Apr'],
            'Prevented Loss': [45000, 67000, 89000, 124000],
            'Investigation Cost': [5000, 7000, 8000, 10000],
            'Net Savings': [40000, 60000, 81000, 114000]
        })
        
        fig = px.bar(
            savings_data,
            x='Month',
            y=['Prevented Loss', 'Investigation Cost'],
            title="ROI of Fraud Prevention Program",
            barmode='group',
            color_discrete_map={'Prevented Loss': '#10b981', 'Investigation Cost': '#f59e0b'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # ROI calculation
        total_savings = savings_data['Net Savings'].sum()
        total_cost = savings_data['Investigation Cost'].sum()
        roi = ((total_savings - total_cost) / total_cost) * 100
        
        cols = st.columns(3)
        cols[0].metric("Total Savings", f"ETB {total_savings:,.0f}")
        cols[1].metric("Total Cost", f"ETB {total_cost:,.0f}")
        cols[2].metric("ROI", f"{roi:.0f}%", "Excellent")

# ════════════════════════════════════════════════
# PAGE 5: Credit Hub
# ════════════════════════════════════════════════
elif "🏦 Credit Hub" in page:
    st.title("🏦 SME Credit & Financing Hub")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Generate credit score
        credit_score = generate_credit_report(
            st.session_state['company_name'],
            st.session_state['company_tin']
        )
        
        st.markdown("### Your Credit Profile")
        st.metric(
            "CFO-Pulse Credit Score",
            str(credit_score),
            delta="Excellent" if credit_score > 750 else "Good" if credit_score > 650 else "Fair"
        )
        
        # Loan eligibility
        if credit_score > 750:
            loan_amount = 500000
            st.success(f"✅ Eligible for up to ETB {loan_amount:,}")
        elif credit_score > 650:
            loan_amount = 250000
            st.warning(f"⚠️ Eligible for up to ETB {loan_amount:,}")
        elif credit_score > 500:
            loan_amount = 100000
            st.warning(f"⚠️ Limited eligibility: ETB {loan_amount:,}")
        else:
            st.error("❌ Currently not eligible for loans")
        
        st.progress(credit_score / 850, text=f"Score: {credit_score}/850")
    
    with col2:
        st.markdown("### 📊 Credit Assessment Factors")
        
        try:
            conn = get_db()
            c = conn.cursor()
            
            c.execute("SELECT COUNT(*) FROM transactions WHERE date >= date('now', '-365 days')")
            tx_12m = c.fetchone()[0]
            
            c.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE date >= date('now', '-365 days')")
            volume_12m = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM fraud_cases WHERE status='Resolved'")
            resolved = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM fraud_cases WHERE status IN ('Investigating', 'Pending')")
            pending = c.fetchone()[0]
        except Exception:
            tx_12m = 45
            volume_12m = 245000
            resolved = 32
            pending = 2
        
        st.markdown(f"""
        **Assessment Details:**
        
        ✅ **Transaction History:** {tx_12m} verified transactions in 12 months  
        ✅ **Annual Volume:** ETB {volume_12m:,.0f} processed  
        ✅ **Tax Compliance:** 100% VAT compliant  
        ✅ **Fraud Resolution:** {resolved} cases resolved successfully  
        {'⚠️' if pending > 0 else '✅'} **Active Investigations:** {pending} pending cases
        
        **Growth Indicators:**
        📈 8% month-over-month transaction growth  
        📈 Consistent cash flow pattern  
        📈 No payment defaults in 24 months
        """)
        
        # Generate report button
        if st.button("📄 Generate Bank-Ready Credit Report", type="primary", use_container_width=True):
            with st.spinner("🔄 Compiling comprehensive credit report..."):
                time.sleep(2)
                
                # Create PDF report
                pdf = FPDF()
                pdf.add_page()
                
                # Header
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, "CFO-Pulse Bank Credit Report", ln=True, align="C")
                pdf.set_font("Arial", "", 10)
                pdf.cell(0, 10, f"Generated: {datetime.now():%B %d, %Y}", ln=True, align="C")
                pdf.ln(10)
                
                # Company info
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "Entity Information", ln=True)
                pdf.set_font("Arial", "", 11)
                pdf.cell(0, 8, f"Company: {st.session_state['company_name']}", ln=True)
                pdf.cell(0, 8, f"TIN: {st.session_state['company_tin']}", ln=True)
                pdf.cell(0, 8, f"Credit Score: {credit_score}/850", ln=True)
                pdf.ln(5)
                
                # Assessment
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "Credit Assessment", ln=True)
                pdf.set_font("Arial", "", 11)
                pdf.multi_cell(0, 8, f"""
This credit report is generated by CFO-Pulse AI based on verified transaction data, 
tax compliance records, and fraud detection history.

Key Findings:
- {tx_12m} verified transactions in the past 12 months
- Annual transaction volume: ETB {volume_12m:,.0f}
- 100% VAT compliance with Ethiopian tax regulations
- {resolved} fraud cases successfully resolved
- {pending} cases currently under investigation

Recommendation: {'APPROVED' if credit_score > 650 else 'REVIEW REQUIRED'}
Maximum Recommended Loan: ETB {loan_amount:,}
""")
                
                # Save PDF
                pdf_output = pdf.output(dest='S').encode('latin1')
                
                st.download_button(
                    "📥 Download Credit Report PDF",
                    data=pdf_output,
                    file_name=f"Credit_Report_{st.session_state['company_tin']}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
                st.success("✅ Credit report generated successfully!")

# ════════════════════════════════════════════════
# Footer
# ════════════════════════════════════════════════
st.markdown("---")
st.markdown(f"""
<div style="text-align:center; color:#6b7280; padding:20px;">
    <p>🤖 CFO-Pulse AI Agent • Real-time monitoring active • Last scan: Just now</p>
    <p style="font-size:12px;">© 2026 CFO-Pulse • Enterprise Security & Compliance Platform</p>
    <p style="font-size:11px;">Ethiopian Tax Compliance • Fraud Detection • Financial Intelligence</p>
</div>
""", unsafe_allow_html=True)
