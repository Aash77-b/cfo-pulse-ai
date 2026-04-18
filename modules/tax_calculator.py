# modules/tax_calculator.py
def calculate_ethiopian_tax(total_amount):
    # Standard 15% VAT calculation
    vat_amount = total_amount * 0.15
    net_amount = total_amount - vat_amount
    return {
        "net_amount": net_amount,
        "vat_amount": vat_amount,
        "tax_type": "VAT (15%)",
        "compliance_status": "Ready for MOR Filing"
    }
