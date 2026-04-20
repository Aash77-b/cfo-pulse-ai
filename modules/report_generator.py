# modules/report_generator.py
"""
Report Generation Engine
Creates audit-ready PDF and JSON reports for compliance and financial reporting
"""

from typing import Dict, Optional
from datetime import datetime
from io import BytesIO
import json

import pandas as pd
from fpdf import FPDF


class ReportGenerator:
    """Generates comprehensive financial and compliance reports"""

    def __init__(self, organization_name: str = "CFO Pulse AI", organization_tin: str = "0000000001"):
        self.organization_name = organization_name
        self.organization_tin = organization_tin
        self.report_version = "1.0"

    def create_monthly_pdf(self, transactions_df: pd.DataFrame, tax_summary: Dict, month: int, year: int) -> bytes:
        """Create a monthly tax report PDF and return PDF bytes."""
        periods = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        period_name = periods[month] if 1 <= month <= 12 else f"Month {month}"
        report_title = f"Monthly Tax Report - {period_name} {year}"

        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, self.organization_name, ln=True, align="C")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, report_title, ln=True, align="C")
        pdf.ln(5)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Executive Summary", ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 6, f"Total Transactions: {tax_summary.get('total_transactions', 0)}")
        pdf.multi_cell(0, 6, f"Total Amount: ETB {tax_summary.get('total_amount', 0):,.2f}")
        pdf.multi_cell(0, 6, f"Total VAT: ETB {tax_summary.get('total_vat', 0):,.2f}")
        pdf.multi_cell(0, 6, f"Total ToT: ETB {tax_summary.get('total_tot', 0):,.2f}")
        pdf.multi_cell(0, 6, f"Total Tax Liability: ETB {tax_summary.get('total_tax', 0):,.2f}")
        pdf.ln(4)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Tax Breakdown", ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 6, f"VAT Rate: 15%", ln=True)
        pdf.cell(0, 6, f"ToT Rate: 2% standard / 10% digital", ln=True)
        pdf.cell(0, 6, f"VAT Amount: ETB {tax_summary.get('total_vat', 0):,.2f}", ln=True)
        pdf.cell(0, 6, f"ToT Amount: ETB {tax_summary.get('total_tot', 0):,.2f}", ln=True)
        pdf.ln(4)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Report Metadata", ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
        pdf.cell(0, 6, f"Organization TIN: {self.organization_tin}", ln=True)
        pdf.cell(0, 6, f"Report Version: {self.report_version}", ln=True)

        if transactions_df is not None and not transactions_df.empty:
            pdf.add_page()
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, "Sample Transaction Details", ln=True)
            pdf.set_font("Arial", "", 10)
            sample_df = transactions_df.head(10)
            for _, row in sample_df.iterrows():
                pdf.multi_cell(0, 5, f"Invoice: {row.get('invoice_id', '')} | Vendor: {row.get('vendor', '')} | Amount: ETB {row.get('amount', 0):,.2f} | Category: {row.get('category', '')}")

        output = pdf.output(dest="S").encode("latin-1")
        return output

    def create_compliance_pdf(self, scan_results: Dict, violation_summary: Dict) -> bytes:
        """Create a compliance audit PDF and return PDF bytes."""
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, self.organization_name, ln=True, align="C")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, "Compliance Audit Report", ln=True, align="C")
        pdf.ln(5)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Executive Summary", ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 6, f"Total Records Scanned: {scan_results.get('total_records', 0)}")
        pdf.multi_cell(0, 6, f"Overall Risk Level: {scan_results.get('overall_risk', 'low').upper()}")
        pdf.multi_cell(0, 6, f"Total Violations: {violation_summary.get('total_violations', 0)}")
        pdf.ln(4)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Violation Summary", ln=True)
        pdf.set_font("Arial", "", 11)
        for rule, count in violation_summary.get('by_rule', {}).items():
            pdf.cell(0, 6, f"{rule}: {count}", ln=True)
        pdf.ln(4)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Risk Breakdown", ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 6, f"Critical: {violation_summary.get('by_severity', {}).get('critical', 0)}", ln=True)
        pdf.cell(0, 6, f"High: {violation_summary.get('by_severity', {}).get('high', 0)}", ln=True)
        pdf.cell(0, 6, f"Medium: {violation_summary.get('by_severity', {}).get('medium', 0)}", ln=True)
        pdf.ln(4)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Recommendations", ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 6, "1. Review all critical violations immediately.")
        pdf.multi_cell(0, 6, "2. Document remediation actions.")
        pdf.multi_cell(0, 6, "3. Update controls based on audit findings.")

        output = pdf.output(dest="S").encode("latin-1")
        return output

    def create_financial_health_report(self, financial_data: Dict, cash_info: Optional[Dict] = None) -> Dict:
        """Create executive financial health report data."""
        if cash_info is None:
            cash_info = {}

        health_score = 100
        if financial_data.get("critical_alerts", 0) > 0:
            health_score -= 20
        if financial_data.get("compliance_violations", 0) > 0:
            health_score -= 15
        if cash_info.get("days_until_critical", 30) < 7:
            health_score -= 15

        health_status = "Excellent" if health_score >= 80 else "Good" if health_score >= 65 else "Fair" if health_score >= 45 else "Poor"

        report = {
            "document_type": "Financial Health Report",
            "organization": self.organization_name,
            "organization_tin": self.organization_tin,
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "report_version": self.report_version,
            "financial_health_score": {
                "score": health_score,
                "status": health_status,
                "max_score": 100
            },
            "transaction_metrics": {
                "total_transactions": financial_data.get("total_transactions", 0),
                "total_amount": financial_data.get("total_amount", 0),
                "total_tax": financial_data.get("total_tax", 0),
                "average_transaction": financial_data.get("average_transaction", 0)
            },
            "liquidity_position": {
                "cash_balance": cash_info.get("cash_balance", 0),
                "minimum_required": cash_info.get("minimum_required", 0),
                "cash_health": "Healthy" if cash_info.get("cash_balance", 0) > cash_info.get("minimum_required", 0) else "At Risk"
            },
            "risk_dashboard": {
                "critical_alerts": financial_data.get("critical_alerts", 0),
                "compliance_violations": financial_data.get("compliance_violations", 0),
                "overall_risk": "Low" if financial_data.get("critical_alerts", 0) == 0 else "Medium" if financial_data.get("critical_alerts", 0) <= 2 else "High"
            },
            "action_items": {
                "immediate": ["Address critical alerts" if financial_data.get("critical_alerts", 0) > 0 else "Continue standard monitoring"],
                "weekly": ["Review compliance violations" if financial_data.get("compliance_violations", 0) > 0 else "Verify cash flow projections"],
                "monthly": ["Tax compliance review", "Cash flow forecast update", "Budget variance analysis"]
            },
            "certification": "Generated by CFO Pulse AI Compliance Engine"
        }

        return report

    def create_financial_health_pdf(self, report_data: Dict) -> bytes:
        """Create a financial health report PDF and return PDF bytes."""
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, self.organization_name, ln=True, align="C")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, "Financial Health Report", ln=True, align="C")
        pdf.ln(5)

        health = report_data.get("financial_health_score", {})
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Health Score", ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 6, f"Score: {health.get('score', 0)}/100", ln=True)
        pdf.cell(0, 6, f"Status: {health.get('status', 'Unknown')}", ln=True)
        pdf.ln(4)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Transaction Metrics", ln=True)
        pdf.set_font("Arial", "", 11)
        metrics = report_data.get("transaction_metrics", {})
        pdf.multi_cell(0, 6, f"Total Transactions: {metrics.get('total_transactions', 0)}")
        pdf.multi_cell(0, 6, f"Total Amount: ETB {metrics.get('total_amount', 0):,.2f}")
        pdf.multi_cell(0, 6, f"Total Tax: ETB {metrics.get('total_tax', 0):,.2f}")
        pdf.ln(4)

        liquidity = report_data.get("liquidity_position", {})
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Liquidity Position", ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 6, f"Cash Balance: ETB {liquidity.get('cash_balance', 0):,.2f}")
        pdf.multi_cell(0, 6, f"Minimum Required: ETB {liquidity.get('minimum_required', 0):,.2f}")
        pdf.multi_cell(0, 6, f"Cash Health: {liquidity.get('cash_health', 'Unknown')}")
        pdf.ln(4)

        output = pdf.output(dest="S").encode("latin-1")
        return output

    def export_report_to_json(self, report: Dict, filename: Optional[str] = None) -> str:
        """Export report to JSON string or save to file."""
        json_str = json.dumps(report, indent=2, default=str)
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(json_str)
            return f"Report exported to {filename}"
        return json_str
