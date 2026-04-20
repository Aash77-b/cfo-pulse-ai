# modules/tax_calculator.py
"""
Ethiopian Tax Calculation Engine
Handles VAT (15%), ToT (Tax on Transactions), and tax categorization
"""

import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime


class EthiopianTaxCalculator:
    """Core Ethiopian tax calculation engine"""
    
    # Tax rates for Ethiopia
    VAT_RATE = 0.15  # 15% VAT
    TOT_RATE_STANDARD = 0.02  # 2% ToT standard
    TOT_RATE_DIGITAL = 0.10  # 10% ToT for digital services
    
    def __init__(self):
        self.calculations = []
    
    def calculate_vat(self, amount: float, is_exempt: bool = False) -> Dict:
        """
        Calculate VAT (Value Added Tax) on amount.
        
        Args:
            amount: Transaction amount
            is_exempt: Whether the transaction is VAT exempt
            
        Returns:
            Dictionary with vat_amount, net_amount, rate
        """
        if is_exempt:
            vat_amount = 0.0
            rate = 0.0
        else:
            vat_amount = amount * self.VAT_RATE
            rate = self.VAT_RATE
        
        return {
            "gross_amount": amount,
            "vat_amount": round(vat_amount, 2),
            "net_amount": round(amount - vat_amount, 2),
            "rate": rate,
            "is_exempt": is_exempt,
            "tax_type": "VAT"
        }
    
    def calculate_tot(self, amount: float, category: str = "standard") -> Dict:
        """
        Calculate ToT (Tax on Transactions).
        
        Args:
            amount: Transaction amount
            category: 'standard' (2%) or 'digital' (10%)
            
        Returns:
            Dictionary with tot_amount and rate
        """
        if category.lower() == "digital":
            tot_rate = self.TOT_RATE_DIGITAL
        else:
            tot_rate = self.TOT_RATE_STANDARD
        
        tot_amount = amount * tot_rate
        
        return {
            "transaction_amount": amount,
            "tot_amount": round(tot_amount, 2),
            "rate": tot_rate,
            "category": category,
            "tax_type": "ToT"
        }
    
    def split_transaction(self, amount: float, tax_types: List[str] = None) -> Dict:
        """
        Split a transaction into multiple tax obligations.
        
        Args:
            amount: Total transaction amount
            tax_types: List of applicable tax types ['vat', 'tot']
            
        Returns:
            Dictionary with all tax calculations
        """
        if tax_types is None:
            tax_types = ["vat", "tot"]
        
        result = {
            "original_amount": amount,
            "taxes": {},
            "total_tax": 0.0,
            "amount_after_tax": amount
        }
        
        if "vat" in tax_types:
            vat_calc = self.calculate_vat(amount)
            result["taxes"]["vat"] = vat_calc
            result["total_tax"] += vat_calc["vat_amount"]
        
        if "tot" in tax_types:
            tot_calc = self.calculate_tot(amount, "standard")
            result["taxes"]["tot"] = tot_calc
            result["total_tax"] += tot_calc["tot_amount"]
        
        result["total_tax"] = round(result["total_tax"], 2)
        result["amount_after_tax"] = round(amount - result["total_tax"], 2)
        
        return result
    
    def generate_tax_summary(self, df: pd.DataFrame) -> Dict:
        """
        Generate tax summary from transaction dataframe.
        
        Expects columns: amount, category, is_vat_exempt
        
        Args:
            df: DataFrame with transactions
            
        Returns:
            Dictionary with aggregated tax summary
        """
        if df.empty:
            return {
                "total_transactions": 0,
                "total_amount": 0.0,
                "total_vat": 0.0,
                "total_tot": 0.0,
                "total_tax": 0.0,
                "average_transaction": 0.0
            }
        
        total_amount = df["amount"].sum()
        total_vat = 0.0
        total_tot = 0.0
        
        # Calculate VAT (excluding exempt transactions)
        taxable_df = df[df.get("is_vat_exempt", False) == False]
        if not taxable_df.empty:
            total_vat = (taxable_df["amount"].sum() * self.VAT_RATE)
        
        # Calculate ToT
        for idx, row in df.iterrows():
            category = row.get("category", "standard")
            amount = row["amount"]
            tot_calc = self.calculate_tot(amount, category)
            total_tot += tot_calc["tot_amount"]
        
        total_tax = round(total_vat + total_tot, 2)
        
        return {
            "total_transactions": len(df),
            "total_amount": round(total_amount, 2),
            "total_vat": round(total_vat, 2),
            "total_tot": round(total_tot, 2),
            "total_tax": total_tax,
            "average_transaction": round(total_amount / len(df), 2) if len(df) > 0 else 0.0,
            "vat_percentage": round((total_vat / total_amount * 100), 2) if total_amount > 0 else 0.0,
            "tot_percentage": round((total_tot / total_amount * 100), 2) if total_amount > 0 else 0.0
        }
    
    def get_tax_category_summary(self, df: pd.DataFrame) -> Dict:
        """
        Break down taxes by transaction category.
        
        Args:
            df: DataFrame with transactions
            
        Returns:
            Dictionary with per-category tax summaries
        """
        if df.empty:
            return {}
        
        categories = df.get("category", "other").unique()
        summary = {}
        
        for cat in categories:
            cat_df = df[df.get("category", "other") == cat]
            cat_amount = cat_df["amount"].sum()
            
            # Calculate taxes for this category
            cat_vat = (cat_amount * self.VAT_RATE) if not cat_df.get("is_vat_exempt", False).any() else 0.0
            cat_tot = cat_amount * (self.TOT_RATE_DIGITAL if cat == "digital" else self.TOT_RATE_STANDARD)
            
            summary[cat] = {
                "transaction_count": len(cat_df),
                "amount": round(cat_amount, 2),
                "vat": round(cat_vat, 2),
                "tot": round(cat_tot, 2),
                "total_tax": round(cat_vat + cat_tot, 2)
            }
        
        return summary


def calculate_ethiopian_tax(total_amount):
    """Legacy function for backward compatibility"""
    calculator = EthiopianTaxCalculator()
    vat_calc = calculator.calculate_vat(total_amount)
    
    return {
        "net_amount": vat_calc["net_amount"],
        "vat_amount": vat_calc["vat_amount"],
        "tax_type": "VAT (15%)",
        "compliance_status": "Ready for MOR Filing"
    }
