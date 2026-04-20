import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg') # Set backend before importing pyplot
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta

# ==========================================
# 1. SAMPLE DATA GENERATION
# ==========================================

def generate_sample_data(n_rows=100):
    """
    Generates a synthetic financial dataset with intentional risks:
    - Anomalies (unusually high amounts)
    - Price Creeps (increasing unit prices for specific items)
    - Duplicates (same vendor, amount, and date)
    """
    np.random.seed(42)
    
    vendors = ["Global Corp", "Tech Solutions", "Office Depot", "Green Energy", "Blue Logistics"]
    items = ["Laptop", "Monitor", "Desk Chair", "Printer", "Cabling"]
    
    data = []
    base_date = datetime(2023, 1, 1)
    
    for i in range(n_rows):
        vendor = np.random.choice(vendors)
        item = np.random.choice(items)
        qty = np.random.randint(1, 10)
        
        # Base price logic
        base_unit_price = 100.0 if item == "Laptop" else 20.0
        
        # Inject Price Creep for 'Tech Solutions' + 'Laptop'
        if vendor == "Tech Solutions" and item == "Laptop":
            # Price increases slightly every time
            base_unit_price += (i * 0.5) 
            
        unit_price = base_unit_price + np.random.uniform(-2, 2)
        total_amount = qty * unit_price
        
        date = base_date + timedelta(days=i % 30)
        
        data.append({
            "transaction_id": f"TXN_{1000+i}",
            "vendor_name": vendor,
            "date": date,
            "item_name": item,
            "quantity": qty,
            "unit_price": round(unit_price, 2),
            "total_amount": round(total_amount, 2),
            "tin_number": f"TIN-{np.random.randint(100000, 999999)}"
        })
    
    df = pd.DataFrame(data)
    
    # Inject intentional Anomaly
    df.loc[0, "total_amount"] = 50000.0  # Massive outlier
    df.loc[0, "unit_price"] = 10000.0
    
    # Inject intentional Duplicate
    duplicate_row = df.iloc[10].copy()
    duplicate_row["transaction_id"] = "TXN_DUP_99"
    df = pd.concat([df, pd.DataFrame([duplicate_row])], ignore_index=True)
    
    return df

# ==========================================
# 2. CORE ML: ANOMALY DETECTION
# ==========================================

def detect_anomalies(df):
    """
    Uses Isolation Forest to detect outlier transactions based on numerical features.
    """
    print("Running Anomaly Detection...")
    features = ['total_amount', 'unit_price', 'quantity']
    
    # Scale features
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(df[features])
    
    # Initialize and fit Isolation Forest
    # contamination='auto' attempts to find the proportion of outliers
    model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    df['anomaly_score'] = model.fit_predict(scaled_data)
    
    # Conversion: Isolation Forest returns -1 for outliers and 1 for inliers
    # We'll keep it as 1 or -1 but clarify in comments
    df['is_anomaly'] = df['anomaly_score'].apply(lambda x: 1 if x == -1 else 0)
    
    return df

# ==========================================
# 3. FORENSIC LOGIC: PRICE CREEP DETECTION
# ==========================================

def detect_price_creep(df, threshold=0.10):
    """
    Identifies if a vendor is gradually increasing unit prices for the same item.
    """
    print("Running Price Creep Detection...")
    df = df.sort_values(['vendor_name', 'item_name', 'date'])
    
    # Group by vendor and item, then calculate percentage change in unit price
    df['price_pct_change'] = df.groupby(['vendor_name', 'item_name'])['unit_price'].pct_change()
    
    # Flag as price creep if latest change is > threshold
    df['price_creep_flag'] = df['price_pct_change'] > threshold
    
    # Additional logic: calculate rolling percentage increase to see trends
    df['cumulative_creep'] = df.groupby(['vendor_name', 'item_name'])['unit_price'].transform(
        lambda x: (x - x.min()) / x.min() if x.min() > 0 else 0
    )
    
    return df

# ==========================================
# 4. FORENSIC LOGIC: DUPLICATE DETECTION
# ==========================================

def detect_duplicates(df):
    """
    Identifies duplicate transactions based on vendor, amount, and date.
    """
    print("Running Duplicate Detection...")
    # Consider duplicates if vendor, total_amount and date are identical
    duplicate_mask = df.duplicated(subset=['vendor_name', 'total_amount', 'date'], keep=False)
    df['duplicate_flag'] = duplicate_mask
    
    # Identify reference ID (the first occurrence)
    df['reference_transaction_id'] = None
    if df['duplicate_flag'].any():
        # This is a simplified way to find the 'first' instance as reference
        df.loc[df['duplicate_flag'], 'reference_transaction_id'] = df[df['duplicate_flag']].groupby(
            ['vendor_name', 'total_amount', 'date'])['transaction_id'].transform('first')
            
    return df

# ==========================================
# 5. RISK SCORING: FINANCIAL HEALTH SCORE
# ==========================================

def calculate_health_score(df):
    """
    Calculates a health score from 0-100 based on detected risks.
    """
    print("Calculating Financial Health Score...")
    
    # Base score per transaction
    # Note: In a real dashboard, you'd aggregate this per vendor or overall.
    # Here we calculate a 'Risk Score' per row and then an overall average.
    
    def row_score(row):
        score = 100
        if row['is_anomaly'] == 1:
            score -= 10
        if row['duplicate_flag']:
            score -= 15
        if row['price_creep_flag']:
            score -= 20
        return max(0, score)
    
    df['financial_health_score'] = df.apply(row_score, axis=1)
    
    return df

# ==========================================
# 6. VISUALIZATION
# ==========================================

def visualize_anomalies(df):
    """
    Plots the distribution of total amounts highlighting anomalies.
    """
    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")
    
    # Scatter plot: Date vs Total Amount
    sns.scatterplot(
        data=df, 
        x='date', 
        y='total_amount', 
        hue='is_anomaly', 
        palette={0: "blue", 1: "red"},
        style='is_anomaly',
        s=100
    )
    
    plt.title("Financial Transactions: Anomaly Detection View", fontsize=14)
    plt.xlabel("Date")
    plt.ylabel("Total Amount")
    plt.legend(title="Is Anomaly", labels=["Normal", "Anomaly"])
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save the plot
    plt.savefig("anomaly_distribution.png")
    print("\n[SUCCESS] Visualization saved as 'anomaly_distribution.png'")
    # Note: In a Streamlit app, you would use st.pyplot() instead.

# ==========================================
# MAIN EXECUTION BLOCK (FOR DEMO)
# ==========================================

if __name__ == "__main__":
    # 1. Generate Data
    raw_df = generate_sample_data(100)
    
    # 2. Sequential Processing
    processed_df = detect_anomalies(raw_df)
    processed_df = detect_price_creep(processed_df)
    processed_df = detect_duplicates(processed_df)
    processed_df = calculate_health_score(processed_df)
    
    # 3. Final Output Preview
    print("\n--- FINAL ENGINE OUTPUT (Sample Rows) ---")
    cols_to_show = [
        'transaction_id', 'vendor_name', 'item_name', 
        'total_amount', 'is_anomaly', 'price_creep_flag', 
        'duplicate_flag', 'financial_health_score'
    ]
    print(processed_df[cols_to_show].head(15))
    
    # Show the specific anomalies/duplicates injected
    print("\n--- DETECTED RISKS ---")
    risks = processed_df[(processed_df['is_anomaly'] == 1) | 
                         (processed_df['duplicate_flag'] == True) | 
                         (processed_df['price_creep_flag'] == True)]
    print(risks[cols_to_show])
    
    # 4. Global Health Summary
    avg_score = processed_df['financial_health_score'].mean()
    print(f"\n>>> OVERALL SYSTEM FINANCIAL HEALTH SCORE: {avg_score:.2f} / 100")
    
    # 5. Visualization
    visualize_anomalies(processed_df)
