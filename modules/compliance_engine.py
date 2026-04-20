# modules/compliance_engine.py
"""
Compliance Rule Engine
Enforces business rules and flags compliance risks
"""

import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from enum import Enum


class RiskLevel(Enum):
    """Risk level classifications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceEngine:
    """Business rule enforcement and compliance checking"""
    
    def __init__(self):
        self.violations = []
        self.risk_flags = []
        
        # Configuration thresholds
        self.budget_limit = 100000  # ETB
        self.unusual_amount_threshold = 50000  # ETB
        self.duplicate_invoice_window = 30  # days
        self.tax_deadline_days = 25  # days from month end
    
    def check_duplicate_invoice(self, df: pd.DataFrame, invoice_col: str = "invoice_id") -> Dict:
        """
        Check for duplicate invoice submissions.
        
        Args:
            df: DataFrame with transaction records
            invoice_col: Column name containing invoice IDs
            
        Returns:
            Dictionary with violation details and risk level
        """
        if invoice_col not in df.columns:
            return {
                "status": "skipped",
                "reason": f"Column '{invoice_col}' not found",
                "violations": [],
                "risk_level": RiskLevel.LOW.value
            }
        
        duplicates = df[df.duplicated(subset=[invoice_col], keep=False)]
        
        violations = []
        if not duplicates.empty:
            duplicate_ids = duplicates[invoice_col].unique()
            for inv_id in duplicate_ids:
                count = len(df[df[invoice_col] == inv_id])
                violations.append({
                    "invoice_id": inv_id,
                    "count": count,
                    "rule": "Duplicate Invoice",
                    "severity": "high"
                })
        
        risk_level = RiskLevel.HIGH if violations else RiskLevel.LOW
        
        return {
            "status": "completed",
            "violations": violations,
            "risk_level": risk_level.value,
            "count": len(violations)
        }
    
    def check_budget_limit(self, df: pd.DataFrame, amount_col: str = "amount", 
                          limit: float = None) -> Dict:
        """
        Check for transactions exceeding budget limits.
        
        Args:
            df: DataFrame with transaction records
            amount_col: Column name containing transaction amounts
            limit: Budget limit in ETB (uses default if None)
            
        Returns:
            Dictionary with violation details and risk level
        """
        if limit is None:
            limit = self.budget_limit
        
        if amount_col not in df.columns:
            return {
                "status": "skipped",
                "reason": f"Column '{amount_col}' not found",
                "violations": [],
                "risk_level": RiskLevel.LOW.value
            }
        
        excess_df = df[df[amount_col] > limit]
        
        violations = []
        if not excess_df.empty:
            for idx, row in excess_df.iterrows():
                excess = row[amount_col] - limit
                violations.append({
                    "index": idx,
                    "amount": row[amount_col],
                    "excess": excess,
                    "rule": "Budget Limit Exceeded",
                    "severity": "high"
                })
        
        risk_level = RiskLevel.HIGH if violations else RiskLevel.LOW
        
        return {
            "status": "completed",
            "limit": limit,
            "violations": violations,
            "risk_level": risk_level.value,
            "count": len(violations)
        }
    
    def check_missing_tin(self, df: pd.DataFrame, tin_col: str = "tin") -> Dict:
        """
        Check for missing TIN (Tax Identification Number).
        
        Args:
            df: DataFrame with transaction records
            tin_col: Column name containing TIN values
            
        Returns:
            Dictionary with violation details and risk level
        """
        if tin_col not in df.columns:
            return {
                "status": "skipped",
                "reason": f"Column '{tin_col}' not found",
                "violations": [],
                "risk_level": RiskLevel.LOW.value
            }
        
        missing_tin = df[df[tin_col].isna() | (df[tin_col] == "")]
        
        violations = []
        if not missing_tin.empty:
            for idx, row in missing_tin.iterrows():
                violations.append({
                    "index": idx,
                    "vendor": row.get("vendor", "Unknown"),
                    "rule": "Missing TIN",
                    "severity": "critical"
                })
        
        risk_level = RiskLevel.CRITICAL if violations else RiskLevel.LOW
        
        return {
            "status": "completed",
            "violations": violations,
            "risk_level": risk_level.value,
            "count": len(violations)
        }
    
    def check_unusual_amount(self, df: pd.DataFrame, amount_col: str = "amount",
                            threshold: float = None) -> Dict:
        """
        Flag unusual transaction amounts.
        
        Args:
            df: DataFrame with transaction records
            amount_col: Column name containing transaction amounts
            threshold: Threshold amount (uses default if None)
            
        Returns:
            Dictionary with flagged transactions and risk level
        """
        if threshold is None:
            threshold = self.unusual_amount_threshold
        
        if amount_col not in df.columns:
            return {
                "status": "skipped",
                "reason": f"Column '{amount_col}' not found",
                "violations": [],
                "risk_level": RiskLevel.LOW.value
            }
        
        unusual_df = df[df[amount_col] > threshold]
        
        violations = []
        if not unusual_df.empty:
            for idx, row in unusual_df.iterrows():
                violations.append({
                    "index": idx,
                    "amount": row[amount_col],
                    "rule": "Unusual Amount",
                    "severity": "medium"
                })
        
        risk_level = RiskLevel.MEDIUM if violations else RiskLevel.LOW
        
        return {
            "status": "completed",
            "threshold": threshold,
            "violations": violations,
            "risk_level": risk_level.value,
            "count": len(violations)
        }
    
    def check_late_tax_deadline(self, df: pd.DataFrame = None, 
                               date_col: str = "date") -> Dict:
        """
        Check if tax filing deadline is approaching or passed.
        
        Args:
            df: DataFrame (optional) with transaction dates
            date_col: Column name containing dates
            
        Returns:
            Dictionary with deadline status and risk level
        """
        today = datetime.now()
        
        # Calculate next deadline (25th of next month)
        if today.day > self.tax_deadline_days:
            # Deadline already passed this month
            next_deadline = (today.replace(day=1) + timedelta(days=32)).replace(day=self.tax_deadline_days)
        else:
            # Deadline still this month
            next_deadline = today.replace(day=self.tax_deadline_days)
        
        days_until_deadline = (next_deadline - today).days
        
        # Determine risk level based on proximity
        if days_until_deadline < 0:
            risk_level = RiskLevel.CRITICAL
            status = "OVERDUE"
        elif days_until_deadline <= 3:
            risk_level = RiskLevel.HIGH
            status = "URGENT"
        elif days_until_deadline <= 7:
            risk_level = RiskLevel.MEDIUM
            status = "WARNING"
        else:
            risk_level = RiskLevel.LOW
            status = "OK"
        
        return {
            "status": status,
            "today": today.strftime("%Y-%m-%d"),
            "next_deadline": next_deadline.strftime("%Y-%m-%d"),
            "days_until_deadline": days_until_deadline,
            "risk_level": risk_level.value
        }
    
    def run_full_compliance_scan(self, df: pd.DataFrame, 
                                config: Dict = None) -> Dict:
        """
        Run all compliance checks on dataset.
        
        Args:
            df: DataFrame with transaction data
            config: Configuration dictionary with column mappings
            
        Returns:
            Dictionary with comprehensive compliance report
        """
        if config is None:
            config = {
                "invoice_col": "invoice_id",
                "amount_col": "amount",
                "tin_col": "tin",
                "date_col": "date"
            }
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_records": len(df),
            "overall_risk": RiskLevel.LOW.value,
            "checks": {}
        }
        
        # Run all checks
        results["checks"]["duplicate_invoice"] = self.check_duplicate_invoice(
            df, config.get("invoice_col", "invoice_id")
        )
        
        results["checks"]["budget_limit"] = self.check_budget_limit(
            df, config.get("amount_col", "amount")
        )
        
        results["checks"]["missing_tin"] = self.check_missing_tin(
            df, config.get("tin_col", "tin")
        )
        
        results["checks"]["unusual_amount"] = self.check_unusual_amount(
            df, config.get("amount_col", "amount")
        )
        
        results["checks"]["tax_deadline"] = self.check_late_tax_deadline(
            df, config.get("date_col", "date")
        )
        
        # Calculate overall risk level
        risk_levels = [
            RiskLevel[check["risk_level"].upper()].value 
            for check in results["checks"].values()
            if "risk_level" in check
        ]
        
        if RiskLevel.CRITICAL.value in risk_levels:
            results["overall_risk"] = RiskLevel.CRITICAL.value
        elif RiskLevel.HIGH.value in risk_levels:
            results["overall_risk"] = RiskLevel.HIGH.value
        elif RiskLevel.MEDIUM.value in risk_levels:
            results["overall_risk"] = RiskLevel.MEDIUM.value
        else:
            results["overall_risk"] = RiskLevel.LOW.value
        
        return results
    
    def get_violation_summary(self, scan_results: Dict) -> Dict:
        """
        Extract summary of violations from scan results.
        
        Args:
            scan_results: Results from run_full_compliance_scan
            
        Returns:
            Dictionary with violation counts and details
        """
        summary = {
            "total_violations": 0,
            "by_severity": {
                "critical": 0,
                "high": 0,
                "medium": 0
            },
            "by_rule": {}
        }
        
        for check_name, check_result in scan_results.get("checks", {}).items():
            if "violations" in check_result:
                for violation in check_result["violations"]:
                    summary["total_violations"] += 1
                    severity = violation.get("severity", "medium").lower()
                    if severity in summary["by_severity"]:
                        summary["by_severity"][severity] += 1
                    
                    rule = violation.get("rule", "Unknown")
                    if rule not in summary["by_rule"]:
                        summary["by_rule"][rule] = 0
                    summary["by_rule"][rule] += 1
        
        return summary
