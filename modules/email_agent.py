# modules/email_agent.py
"""
AI Email Generation Agent
Generates professional business emails for finance, disputes, and alerts
"""

from datetime import datetime
from typing import Dict, List
from enum import Enum


class EmailType(Enum):
    """Email template types"""
    DISPUTE = "dispute"
    VENDOR_VERIFICATION = "vendor_verification"
    CEO_SUMMARY = "ceo_summary"
    CASH_WARNING = "cash_warning"
    COMPLIANCE_ALERT = "compliance_alert"
    TAX_DEADLINE = "tax_deadline"


class EmailAgent:
    """AI-powered email generation for finance operations"""
    
    def __init__(self, organization_name: str = "CFO Pulse AI"):
        self.organization_name = organization_name
        self.sender_title = "Finance Operations"
    
    def generate_dispute_email(self, invoice_details: Dict) -> str:
        """
        Generate professional dispute email for vendor.
        
        Args:
            invoice_details: Dictionary with:
                - invoice_number: Invoice ID
                - vendor_name: Vendor name
                - amount: Transaction amount
                - discrepancy: Nature of discrepancy
                - requested_action: What needs to be corrected
                
        Returns:
            Formatted email text
        """
        invoice_num = invoice_details.get("invoice_number", "N/A")
        vendor = invoice_details.get("vendor_name", "Vendor")
        amount = invoice_details.get("amount", "N/A")
        discrepancy = invoice_details.get("discrepancy", "pricing mismatch")
        action = invoice_details.get("requested_action", "clarification")
        
        email = f"""
Subject: Invoice {invoice_num} - Clarification Required

Dear {vendor},

We hope this email finds you well.

We are writing regarding invoice {invoice_num} dated {datetime.now().strftime("%Y-%m-%d")} with an amount of ETB {amount:,.2f}.

Upon our review, we have identified the following discrepancy:
• {discrepancy}

To ensure accurate record-keeping and timely payment processing, we kindly request that you provide {action}.

Please contact our accounts department at your earliest convenience to resolve this matter. We aim to process this invoice within the next 5 business days.

Thank you for your prompt attention to this matter.

Best regards,
{self.organization_name}
{self.sender_title}
Contact: finance@{self.organization_name.lower().replace(" ", "")}
        """.strip()
        
        return email
    
    def generate_vendor_verification_email(self, vendor_info: Dict) -> str:
        """
        Generate vendor verification request email.
        
        Args:
            vendor_info: Dictionary with:
                - vendor_name: Vendor name
                - tin: Tax identification number
                - registration_status: Status to verify
                - contact_person: Contact name
                
        Returns:
            Formatted email text
        """
        vendor = vendor_info.get("vendor_name", "Vendor")
        tin = vendor_info.get("tin", "Not Provided")
        status = vendor_info.get("registration_status", "verification")
        contact = vendor_info.get("contact_person", "Manager")
        
        email = f"""
Subject: Vendor Information Verification - {vendor}

Dear {contact},

Thank you for doing business with {self.organization_name}.

As part of our vendor management and compliance procedures, we are conducting routine verification of key vendor information. We have records showing:

Vendor Name: {vendor}
Tax Identification Number (TIN): {tin}

Please confirm the accuracy of the above information and provide the following if not already on file:
• Current valid business registration certificate
• Proof of tax compliance (MOR clearance)
• Current authorized bank account information

This information helps us maintain accurate records and ensure smooth transaction processing. Please reply within 5 business days.

If any information has changed, please provide updated documentation immediately.

Thank you for your cooperation.

Best regards,
{self.organization_name}
{self.sender_title}
        """.strip()
        
        return email
    
    def generate_ceo_weekly_summary(self, financial_data: Dict) -> str:
        """
        Generate executive weekly financial summary email.
        
        Args:
            financial_data: Dictionary with:
                - total_transactions: Number of transactions
                - total_amount: Total amount processed
                - total_tax: Total tax calculated
                - cash_balance: Current cash balance
                - critical_alerts: Count of critical alerts
                - compliance_violations: Count of violations
                
        Returns:
            Formatted email text
        """
        total_trans = financial_data.get("total_transactions", 0)
        total_amt = financial_data.get("total_amount", 0)
        total_tax = financial_data.get("total_tax", 0)
        cash_bal = financial_data.get("cash_balance", 0)
        critical = financial_data.get("critical_alerts", 0)
        violations = financial_data.get("compliance_violations", 0)
        
        # Risk assessment
        risk_status = "🟢 LOW" if critical == 0 else "🟠 MEDIUM" if critical <= 2 else "🔴 HIGH"
        
        email = f"""
Subject: Weekly Financial Summary - {datetime.now().strftime("%B %d, %Y")}

Dear CEO,

Please find below your weekly financial digest:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TRANSACTION SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Transactions Processed: {total_trans}
Total Amount: ETB {total_amt:,.2f}
Tax Calculated: ETB {total_tax:,.2f}
Current Cash Balance: ETB {cash_bal:,.2f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPLIANCE & RISK STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Overall Risk Level: {risk_status}
Critical Alerts: {critical}
Compliance Violations: {violations}

{"ACTION REQUIRED: Please review critical alerts immediately." if critical > 0 else "All systems operating normally."}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Review detailed compliance report in CFO Pulse dashboard
2. Approve pending vendor verifications
3. Confirm tax filing deadline (25th of next month)

For detailed analysis, please log into the CFO Pulse AI dashboard.

Best regards,
{self.organization_name}
Automated Financial Intelligence System
        """.strip()
        
        return email
    
    def generate_cash_warning_notice(self, cash_info: Dict) -> str:
        """
        Generate cash flow warning email.
        
        Args:
            cash_info: Dictionary with:
                - current_balance: Current cash balance
                - minimum_required: Minimum required balance
                - projected_deficit: Projected shortfall
                - days_until_critical: Days until critical threshold
                
        Returns:
            Formatted email text
        """
        current = cash_info.get("current_balance", 0)
        minimum = cash_info.get("minimum_required", 10000)
        deficit = cash_info.get("projected_deficit", 0)
        days = cash_info.get("days_until_critical", 7)
        
        urgency = "CRITICAL" if days <= 3 else "URGENT" if days <= 7 else "WARNING"
        
        email = f"""
Subject: ⚠️ {urgency}: Cash Flow Warning Notice

Dear Finance Team,

This is an automated alert regarding your cash position.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CASH POSITION ALERT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current Cash Balance: ETB {current:,.2f}
Minimum Required: ETB {minimum:,.2f}
Projected Deficit: ETB {deficit:,.2f}
Days Until Critical: {days}

⚠️ Your cash position is below optimal levels.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECOMMENDED ACTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Expedite outstanding receivables collections
2. Review payment schedule for non-critical obligations
3. Consider short-term financing options
4. Contact your bank regarding credit facilities
5. Prepare detailed cash flow projection

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ESCALATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This alert has been escalated to senior management.
Please contact the Finance Director immediately.

Automated Alert System
{self.organization_name}
        """.strip()
        
        return email
    
    def generate_compliance_alert_email(self, alert_details: Dict) -> str:
        """
        Generate compliance violation alert email.
        
        Args:
            alert_details: Dictionary with:
                - violation_type: Type of violation
                - severity: Severity level
                - affected_records: Number of affected records
                - description: Detailed description
                - remediation: Recommended remediation
                
        Returns:
            Formatted email text
        """
        violation = alert_details.get("violation_type", "Compliance Issue")
        severity = alert_details.get("severity", "HIGH").upper()
        affected = alert_details.get("affected_records", 1)
        description = alert_details.get("description", "Review required")
        remediation = alert_details.get("remediation", "Contact compliance team")
        
        icon = "🔴" if severity == "CRITICAL" else "🟠" if severity == "HIGH" else "🟡"
        
        email = f"""
Subject: {icon} Compliance Alert: {violation}

Dear Compliance Officer,

An automated compliance check has flagged the following issue:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VIOLATION DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Violation Type: {violation}
Severity Level: {severity}
Affected Records: {affected}
Timestamp: {datetime.now().isoformat()}

Description:
{description}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIRED ACTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Recommended Remediation:
{remediation}

Please review affected records in the CFO Pulse dashboard and take appropriate corrective action.

Timeline for Resolution: {"24 hours (Critical)" if severity == "CRITICAL" else "5 business days"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Please confirm receipt and action taken.

{self.organization_name}
Compliance Monitoring System
        """.strip()
        
        return email
    
    def generate_tax_deadline_reminder(self, deadline_info: Dict) -> str:
        """
        Generate tax filing deadline reminder email.
        
        Args:
            deadline_info: Dictionary with:
                - deadline_date: Date of deadline
                - days_remaining: Days until deadline
                - tax_type: Type of tax (VAT, ToT, etc.)
                - amount_due: Amount due
                - required_documents: List of documents needed
                
        Returns:
            Formatted email text
        """
        deadline = deadline_info.get("deadline_date", "N/A")
        days = deadline_info.get("days_remaining", 0)
        tax_type = deadline_info.get("tax_type", "Tax")
        amount = deadline_info.get("amount_due", 0)
        docs = deadline_info.get("required_documents", [])
        
        urgency = "CRITICAL" if days <= 3 else "URGENT" if days <= 7 else "REMINDER"
        
        email = f"""
Subject: {urgency}: {tax_type} Filing Deadline - {deadline}

Dear Finance Team,

This is a reminder of the upcoming tax filing deadline.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEADLINE INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tax Type: {tax_type}
Filing Deadline: {deadline}
Days Remaining: {days}
Amount Due: ETB {amount:,.2f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIRED DOCUMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{chr(10).join(f"☑ {doc}" for doc in docs) if docs else "☑ Complete transaction records"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Verify all required documents are prepared
2. Log into CFO Pulse for final tax summary report
3. Coordinate with tax advisor for final review
4. Submit to tax authority before deadline

Please confirm completion of tax filing requirements.

{self.organization_name}
        """.strip()
        
        return email
    
    def send_email(self, email_type: str, recipient: str, 
                  subject: str, content: str) -> Dict:
        """
        Mock email sending function (template-based, no API required).
        
        Args:
            email_type: Type of email being sent
            recipient: Email recipient
            subject: Email subject line
            content: Email content/body
            
        Returns:
            Dictionary with send status
        """
        return {
            "status": "queued",
            "timestamp": datetime.now().isoformat(),
            "email_type": email_type,
            "recipient": recipient,
            "subject": subject,
            "message": f"Email successfully queued for delivery to {recipient}",
            "note": "Email system is running in template mode. Integrate with actual SMTP or email API to send."
        }
