# utils/prompt_templates.py
"""
Prompt Templates for NLP and AI Tasks
Reusable templates for email generation, compliance analysis, and executive reporting
"""

class PromptTemplates:
    """Collection of reusable prompts for financial compliance and communication."""

    DISPUTE_PROMPT = """
Write a professional finance dispute email.
The email should clearly explain the discrepancy, reference the invoice number, and request corrective action.
Keep the tone calm, collaborative, and businesslike.
"""

    VENDOR_VERIFICATION_PROMPT = """
Write a vendor verification request email.
Include a request for current business registration, MOR clearance, and authorized bank account information.
Maintain a professional and respectful tone.
"""

    CEO_SUMMARY_PROMPT = """
Write a concise executive summary of weekly financial performance.
Highlight total transaction volume, tax obligations, compliance risk, and any critical alerts.
Use clear, executive-friendly language.
"""

    CASH_WARNING_PROMPT = """
Create a cash flow warning notice.
Detail current cash balance, projected deficit, and recommended next steps.
Keep the tone urgent but factual.
"""

    COMPLIANCE_VIOLATION_PROMPT = """
Summarize compliance violations from the following list:
{violations}
Provide an executive risk assessment and remediation priorities.
"""

    TAX_SUMMARY_PROMPT = """
Summarize tax obligations for Ethiopian VAT and ToT.
Include a recommendation for filing and compliance actions.
"""

    AUDIT_REPORT_PROMPT = """
Create an audit-ready report summary that documents key compliance findings, risk levels, and recommended remediation.
"""

    FINANCIAL_HEALTH_PROMPT = """
Provide a financial health assessment based on cash position, tax obligations, and compliance risk.
Generate clear action items and a concise status summary.
"""

    @staticmethod
    def get_dispute_prompt(invoice_number: str, vendor_name: str, amount: str, discrepancy: str, action: str) -> str:
        return PromptTemplates.DISPUTE_PROMPT + "\n\n" + (
            f"Invoice Number: {invoice_number}\n"
            f"Vendor: {vendor_name}\n"
            f"Amount: {amount}\n"
            f"Discrepancy: {discrepancy}\n"
            f"Requested Action: {action}\n"
        )

    @staticmethod
    def get_vendor_verification_prompt(vendor_name: str, tin: str, contact_person: str) -> str:
        return PromptTemplates.VENDOR_VERIFICATION_PROMPT + "\n\n" + (
            f"Vendor: {vendor_name}\n"
            f"TIN: {tin}\n"
            f"Contact: {contact_person}\n"
        )

    @staticmethod
    def get_ceo_summary_prompt(period: str, total_transactions: int, total_amount: float, critical_alerts: int, compliance_violations: int) -> str:
        return PromptTemplates.CEO_SUMMARY_PROMPT + "\n\n" + (
            f"Period: {period}\n"
            f"Total Transactions: {total_transactions}\n"
            f"Total Amount: {total_amount}\n"
            f"Critical Alerts: {critical_alerts}\n"
            f"Compliance Violations: {compliance_violations}\n"
        )

    @staticmethod
    def get_cash_warning_prompt(cash_balance: float, minimum_required: float, projected_deficit: float, days_until_critical: int) -> str:
        return PromptTemplates.CASH_WARNING_PROMPT + "\n\n" + (
            f"Cash Balance: {cash_balance}\n"
            f"Minimum Required: {minimum_required}\n"
            f"Projected Deficit: {projected_deficit}\n"
            f"Days Until Critical: {days_until_critical}\n"
        )

    @staticmethod
    def get_compliance_violation_prompt(violations: str) -> str:
        return PromptTemplates.COMPLIANCE_VIOLATION_PROMPT.format(violations=violations)

    @staticmethod
    def get_tax_summary_prompt() -> str:
        return PromptTemplates.TAX_SUMMARY_PROMPT

    @staticmethod
    def get_audit_report_prompt() -> str:
        return PromptTemplates.AUDIT_REPORT_PROMPT

    @staticmethod
    def get_financial_health_prompt() -> str:
        return PromptTemplates.FINANCIAL_HEALTH_PROMPT
