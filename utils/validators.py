# utils/validators.py
"""
Data Validators for Financial Transactions
Validates TIN, amounts, tax types, and other financial data
"""

import re
from typing import Tuple, Dict, List


class FinancialValidator:
    """Validation functions for financial data"""
    
    # Ethiopian TIN format: 10 digits (e.g., 0000000001)
    TIN_PATTERN = r'^\d{10}$'
    
    # Supported tax types
    SUPPORTED_TAX_TYPES = ["vat", "tot", "income_tax", "custom_duty"]
    
    # Supported transaction categories
    SUPPORTED_CATEGORIES = ["standard", "digital", "goods", "services", "import", "export"]
    
    @staticmethod
    def is_valid_tin(tin: str) -> Tuple[bool, str]:
        """
        Validate Ethiopian Tax Identification Number (TIN).
        
        Ethiopian TIN format: 10 digits
        Example: 0000000001
        
        Args:
            tin: TIN string to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        if not tin:
            return False, "TIN cannot be empty"
        
        tin_str = str(tin).strip()
        
        if not re.match(FinancialValidator.TIN_PATTERN, tin_str):
            return False, f"TIN must be 10 digits. Got: {tin_str}"
        
        # Additional check: TIN should not be all zeros
        if tin_str == "0000000000":
            return False, "TIN cannot be all zeros"
        
        return True, "Valid TIN format"
    
    @staticmethod
    def is_positive_amount(amount: float, allow_zero: bool = False) -> Tuple[bool, str]:
        """
        Validate transaction amount.
        
        Args:
            amount: Amount to validate
            allow_zero: Whether zero is allowed
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            amount_float = float(amount)
        except (ValueError, TypeError):
            return False, f"Amount must be a number. Got: {amount}"
        
        if allow_zero:
            if amount_float < 0:
                return False, f"Amount cannot be negative. Got: {amount_float}"
            return True, "Valid amount"
        else:
            if amount_float <= 0:
                return False, f"Amount must be positive. Got: {amount_float}"
            return True, "Valid amount"
    
    @staticmethod
    def is_supported_tax_type(tax_type: str) -> Tuple[bool, str]:
        """
        Validate tax type.
        
        Args:
            tax_type: Tax type string to validate
            
        Returns:
            Tuple of (is_valid, message) with supported types
        """
        if not tax_type:
            return False, "Tax type cannot be empty"
        
        tax_type_lower = str(tax_type).lower().strip()
        
        if tax_type_lower not in FinancialValidator.SUPPORTED_TAX_TYPES:
            return False, f"Unsupported tax type: {tax_type}. Supported: {', '.join(FinancialValidator.SUPPORTED_TAX_TYPES)}"
        
        return True, f"Valid tax type: {tax_type_lower}"
    
    @staticmethod
    def is_valid_transaction_category(category: str) -> Tuple[bool, str]:
        """
        Validate transaction category.
        
        Args:
            category: Category string to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        if not category:
            return False, "Category cannot be empty"
        
        category_lower = str(category).lower().strip()
        
        if category_lower not in FinancialValidator.SUPPORTED_CATEGORIES:
            return False, f"Unsupported category: {category}. Supported: {', '.join(FinancialValidator.SUPPORTED_CATEGORIES)}"
        
        return True, f"Valid category: {category_lower}"
    
    @staticmethod
    def is_valid_email(email: str) -> Tuple[bool, str]:
        """
        Validate email address format.
        
        Args:
            email: Email string to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        if not email:
            return False, "Email cannot be empty"
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, str(email).strip()):
            return False, f"Invalid email format: {email}"
        
        return True, "Valid email format"
    
    @staticmethod
    def is_valid_invoice_number(invoice_num: str) -> Tuple[bool, str]:
        """
        Validate invoice number format.
        
        Args:
            invoice_num: Invoice number to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        if not invoice_num:
            return False, "Invoice number cannot be empty"
        
        invoice_str = str(invoice_num).strip()
        
        # Invoice should be alphanumeric and 3-20 characters
        if not (3 <= len(invoice_str) <= 20 and re.match(r'^[a-zA-Z0-9-_]+$', invoice_str)):
            return False, f"Invalid invoice format: {invoice_num}. Should be 3-20 alphanumeric characters."
        
        return True, "Valid invoice number format"
    
    @staticmethod
    def is_valid_vat_rate(rate: float) -> Tuple[bool, str]:
        """
        Validate VAT rate (should be approximately 15% for Ethiopia).
        
        Args:
            rate: VAT rate as decimal (e.g., 0.15 for 15%)
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            rate_float = float(rate)
        except (ValueError, TypeError):
            return False, f"VAT rate must be a number. Got: {rate}"
        
        # Ethiopian VAT is 15% (0.15)
        if not (0.14 <= rate_float <= 0.16):
            return False, f"VAT rate should be ~15% (0.15) for Ethiopia. Got: {rate_float}"
        
        return True, f"Valid VAT rate: {rate_float}"
    
    @staticmethod
    def is_valid_tot_rate(rate: float, category: str = "standard") -> Tuple[bool, str]:
        """
        Validate ToT (Tax on Transactions) rate.
        
        Args:
            rate: ToT rate as decimal
            category: Transaction category ('standard' or 'digital')
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            rate_float = float(rate)
        except (ValueError, TypeError):
            return False, f"ToT rate must be a number. Got: {rate}"
        
        category_lower = str(category).lower().strip()
        
        if category_lower == "digital":
            # Digital services: 10%
            if not (0.09 <= rate_float <= 0.11):
                return False, f"Digital ToT rate should be ~10% (0.10). Got: {rate_float}"
        else:
            # Standard: 2%
            if not (0.01 <= rate_float <= 0.03):
                return False, f"Standard ToT rate should be ~2% (0.02). Got: {rate_float}"
        
        return True, f"Valid ToT rate: {rate_float}"
    
    @staticmethod
    def validate_transaction(transaction: Dict) -> Dict:
        """
        Comprehensive transaction validation.
        
        Args:
            transaction: Dictionary with transaction fields
            
        Returns:
            Dictionary with validation results
        """
        results = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Validate amount
        is_valid, msg = FinancialValidator.is_positive_amount(
            transaction.get("amount")
        )
        if not is_valid:
            results["is_valid"] = False
            results["errors"].append(f"Amount: {msg}")
        
        # Validate TIN if present
        if "tin" in transaction and transaction["tin"]:
            is_valid, msg = FinancialValidator.is_valid_tin(
                transaction.get("tin")
            )
            if not is_valid:
                results["warnings"].append(f"TIN: {msg}")
        else:
            results["warnings"].append("TIN: Missing for transaction")
        
        # Validate invoice number if present
        if "invoice_id" in transaction and transaction["invoice_id"]:
            is_valid, msg = FinancialValidator.is_valid_invoice_number(
                transaction.get("invoice_id")
            )
            if not is_valid:
                results["errors"].append(f"Invoice: {msg}")
        
        # Validate category if present
        if "category" in transaction and transaction["category"]:
            is_valid, msg = FinancialValidator.is_valid_transaction_category(
                transaction.get("category")
            )
            if not is_valid:
                results["warnings"].append(f"Category: {msg}")
        
        return results
    
    @staticmethod
    def validate_batch_transactions(transactions: List[Dict]) -> Dict:
        """
        Validate multiple transactions.
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            Dictionary with batch validation results
        """
        results = {
            "total_transactions": len(transactions),
            "valid_count": 0,
            "invalid_count": 0,
            "warning_count": 0,
            "details": []
        }
        
        for idx, transaction in enumerate(transactions):
            validation = FinancialValidator.validate_transaction(transaction)
            
            if validation["is_valid"] and not validation["warnings"]:
                results["valid_count"] += 1
            elif validation["is_valid"] and validation["warnings"]:
                results["warning_count"] += 1
            else:
                results["invalid_count"] += 1
            
            if not validation["is_valid"] or validation["warnings"]:
                results["details"].append({
                    "transaction_index": idx,
                    "transaction": transaction,
                    "validation": validation
                })
        
        return results
    
    @staticmethod
    def get_validation_summary(batch_results: Dict) -> str:
        """
        Generate human-readable validation summary.
        
        Args:
            batch_results: Results from validate_batch_transactions
            
        Returns:
            Formatted summary string
        """
        summary = []
        summary.append("=" * 60)
        summary.append("TRANSACTION VALIDATION SUMMARY")
        summary.append("=" * 60)
        summary.append(f"Total Transactions: {batch_results['total_transactions']}")
        summary.append(f"✓ Valid: {batch_results['valid_count']}")
        summary.append(f"⚠ Warnings: {batch_results['warning_count']}")
        summary.append(f"✗ Invalid: {batch_results['invalid_count']}")
        summary.append("=" * 60)
        
        if batch_results['details']:
            summary.append("\nDETAILS:")
            for detail in batch_results['details']:
                summary.append(f"\nTransaction #{detail['transaction_index']}:")
                if detail['validation']['errors']:
                    summary.append("  Errors:")
                    for err in detail['validation']['errors']:
                        summary.append(f"    - {err}")
                if detail['validation']['warnings']:
                    summary.append("  Warnings:")
                    for warn in detail['validation']['warnings']:
                        summary.append(f"    - {warn}")
        
        return "\n".join(summary)
