```markdown
# CFO-Pulse AI

**An intelligent financial audit platform for Ethiopian SMEs seeking bank loans**

Built by a team of 5 for the 2026 Innovation Challenge. We're solving a real problem: small businesses in Ethiopia need verifiable financial records to access credit. Our platform helps them scan receipts, detect fraud, and generate bank-ready audit reports.

---

## What Our Platform Does

**For Business Owners:**
- Scan receipts using your phone camera or upload images
- Get instant fraud risk scores on every transaction
- Set spending policies for your team
- Download audit reports banks actually accept

**For Banks:**
- Verifiable transaction history
- Creditworthiness score (0-100)
- Risk assessment summary
- Tamper-proof PDF reports

---

## Why We Built This

Researchs show  who runs a small business got rejected for a loan, because their financial records are "disorganized." .People said 70% of SME applications get rejected for the same reason.

The problem isn't that these businesses are risky. The problem is they can't prove they're not.

We built CFO-Pulse AI to fix that.

---


## Tech Stack

| Tool | What it does | Who owns it |
|------|---------------|-------------|
| Python 3.11 | Core language | Everyone |
| Streamlit | Web framework | Meron |
| OpenCV | Face recognition | Selam |
| Tesseract / EasyOCR | Text extraction | Ashenafi |
| scikit-learn | Cash flow prediction | Dawit |
| FPDF | PDF reports | Yonas |
| Plotly | Charts | Dawit |

---


## Installation 

### 1. Clone the repo

```bash
git clone https://github.com/Aash77-b/cfo-pulse-ai.git
cd cfo-pulse-ai
```

### 2. Set up virtual environment

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```
```bash
for windows use this instead

.\venv\Scripts\activate
```
### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Tesseract OCR

**Windows:** Download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/releases)  
Install to `C:\Program Files\Tesseract-OCR\`

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

### 5. Run the app

```bash
streamlit run app.py
```

---

## First Time Login

1. **Register your face** - Webcam required. works best in good lighting.
2. **Set up company profile** - Add your business name and TIN.
3. **Configure policies** - Set spending limits.
4. **Start scanning** - Upload a receipt.

**Default password if face login fails:** `admin123`

---

## Demo Data

Want to see how it works without scanning real receipts? We included sample data.

1. Go to **Scan & Audit**
2. Upload any image (it will auto-fill with demo data if OCR fails)
3. See the risk score and policy checks in action


---

## What the Judges Should Look For

| Criteria | Where to see it |
|----------|-----------------|
| Innovation | AI cash flow prediction on Dashboard |
| Technical complexity | Face recognition + OCR + ML in one app |
| Real-world impact | Bank report generation in Fraud Reports |
| Team collaboration | Every module has clear ownership |
| Polish | Custom CSS, error handling, loading states |

---

## Known Issues (We're Honest)

- **OCR accuracy drops on blurry receipts.** 
- **Face recognition requires decent webcam.** we tested with 3 different cameras. Built-in laptop cameras work fine.
- **Cash flow prediction needs 5+ transactions.** The model needs data to learn.
- **PDF reports are basic.** we focused on content over design. Banks care about numbers, not fonts.

---

## What We'd Build Next (If We Had More Time)

| Feature | 
|---------|---------------|
| Ethiopian Birr tax calculator |
| Receipt image enhancement | 
| Two-factor authentication |
| Integration with Ethiopian banks' APIs |

---

## Competition Submission

**Category:** for Financial Inclusion  
**Target users:** Ethiopian SMEs with 1-50 employees  
**Problem solved:** Banks won't lend without verifiable records. We provide those records.


---


**Project Repository:** https://github.com/team-cfopulse/cfo-pulse-ai  

---

*Built with coffee, frustration, and determination. Ethiopia to the world.*
```
