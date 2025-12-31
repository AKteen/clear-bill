import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from sqlalchemy.orm import Session
from models import AuditPolicy
from schemas import AuditResult

def create_default_audit_policies(db: Session):
    """Create default audit policies for invoice validation"""
    
    default_policies = [
        {
            "rule_name": "Invoice Number Required",
            "rule_type": "required_field",
            "field_name": "invoice_number",
            "condition": "exists",
            "expected_value": None
        },
        {
            "rule_name": "Amount Required",
            "rule_type": "required_field", 
            "field_name": "amount",
            "condition": "exists",
            "expected_value": None
        },
        {
            "rule_name": "Date Required",
            "rule_type": "required_field",
            "field_name": "date",
            "condition": "exists", 
            "expected_value": None
        },
        {
            "rule_name": "Vendor Name Required",
            "rule_type": "required_field",
            "field_name": "vendor_name",
            "condition": "exists",
            "expected_value": None
        },
        {
            "rule_name": "Maximum Amount Limit",
            "rule_type": "amount_limit",
            "field_name": "amount",
            "condition": "max_value",
            "expected_value": "10000"
        },
        {
            "rule_name": "Minimum Amount Limit", 
            "rule_type": "amount_limit",
            "field_name": "amount",
            "condition": "min_value",
            "expected_value": "1"
        },
        {
            "rule_name": "Invoice Number Format",
            "rule_type": "format_check",
            "field_name": "invoice_number",
            "condition": "format_match",
            "expected_value": "^[A-Z0-9-]+$"
        },
        {
            "rule_name": "Date Range Check",
            "rule_type": "date_range",
            "field_name": "date", 
            "condition": "within_days",
            "expected_value": "365",
            "severity": "medium"
        },
        {
            "rule_name": "Alcohol Content Warning",
            "rule_type": "content_warning",
            "field_name": "content",
            "condition": "contains_keywords",
            "expected_value": "alcohol,beer,wine,liquor,vodka,whiskey,rum,gin,champagne,cocktail,bar,pub,brewery,distillery",
            "severity": "warning"
        },
        {
            "rule_name": "Entertainment Content Warning",
            "rule_type": "content_warning",
            "field_name": "content",
            "condition": "contains_keywords",
            "expected_value": "party,entertainment,club,nightclub,casino,gambling,strip club,adult entertainment,massage,spa",
            "severity": "warning"
        },
        {
            "rule_name": "High-Risk Vendor Warning",
            "rule_type": "content_warning",
            "field_name": "content",
            "condition": "contains_keywords",
            "expected_value": "cash only,no receipt,under table,off books,personal expense,gift,donation",
            "severity": "high"
        },
        {
            "rule_name": "Luxury Items Warning",
            "rule_type": "content_warning",
            "field_name": "content",
            "condition": "contains_keywords",
            "expected_value": "jewelry,luxury,designer,rolex,gucci,louis vuitton,expensive watch,diamond,gold",
            "severity": "warning"
        }
    ]
    
    # Add severity field to existing policies
    for policy_data in default_policies:
        if 'severity' not in policy_data:
            policy_data['severity'] = 'medium'
    
    # Check if policies already exist
    existing_count = db.query(AuditPolicy).count()
    if existing_count == 0:
        for policy_data in default_policies:
            policy = AuditPolicy(**policy_data)
            db.add(policy)
        db.commit()
        print(f"Created {len(default_policies)} default audit policies")

def validate_bill_format(groq_response: str) -> Tuple[bool, str]:
    """Validate if the document looks like a proper bill/invoice"""
    
    content = groq_response.lower()
    
    # Required bill indicators
    bill_keywords = ['invoice', 'bill', 'receipt', 'statement', 'charge']
    business_indicators = ['company', 'business', 'corp', 'inc', 'ltd', 'llc', 'store', 'shop']
    amount_indicators = ['total', 'amount', 'due', 'balance', '$', 'price', 'cost', 'subtotal']
    date_indicators = ['date', 'issued', 'billed']
    
    # Check for bill keywords
    has_bill_keyword = any(keyword in content for keyword in bill_keywords)
    if not has_bill_keyword:
        return False, "Document does not appear to be a bill or invoice"
    
    # Check for business/vendor information
    has_business_info = any(indicator in content for indicator in business_indicators)
    if not has_business_info:
        return False, "Document lacks proper business/vendor information"
    
    # Check for amount/pricing information
    has_amount_info = any(indicator in content for indicator in amount_indicators)
    if not has_amount_info:
        return False, "Document lacks pricing or amount information"
    
    # Check for date information
    has_date_info = any(indicator in content for indicator in date_indicators)
    if not has_date_info:
        return False, "Document lacks date information"
    
    # Check for structured format (line items, totals, etc.)
    structure_indicators = ['subtotal', 'tax', 'total', 'quantity', 'qty', 'item', 'description']
    structure_score = sum(1 for indicator in structure_indicators if indicator in content)
    
    if structure_score < 2:
        return False, "Document lacks proper bill structure (items, totals, etc.)"
    
    # Additional format checks
    if len(content.split()) < 20:
        return False, "Document content is too brief to be a proper bill"
    
    return True, "Document format validated as proper bill/invoice"
    """Extract structured data from Groq response"""
    
    # This is a simplified extraction - in production, you'd use more sophisticated NLP
    invoice_data = {}
    
    # Extract invoice number
    invoice_patterns = [
        r'invoice\s*(?:number|#|no\.?)\s*:?\s*([A-Z0-9-]+)',
        r'inv\s*(?:number|#|no\.?)\s*:?\s*([A-Z0-9-]+)',
        r'bill\s*(?:number|#|no\.?)\s*:?\s*([A-Z0-9-]+)'
    ]
    
    for pattern in invoice_patterns:
        match = re.search(pattern, groq_response, re.IGNORECASE)
        if match:
            invoice_data['invoice_number'] = match.group(1)
            break
    
    # Extract amount
    amount_patterns = [
        r'(?:total|amount|sum)\s*:?\s*\$?([0-9,]+\.?[0-9]*)',
        r'\$([0-9,]+\.?[0-9]*)',
        r'([0-9,]+\.?[0-9]*)\s*(?:dollars?|usd|\$)'
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, groq_response, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                invoice_data['amount'] = float(amount_str)
                break
            except ValueError:
                continue
    
    # Extract date
    date_patterns = [
        r'date\s*:?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
        r'([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
        r'([A-Za-z]+ [0-9]{1,2},? [0-9]{4})'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, groq_response, re.IGNORECASE)
        if match:
            invoice_data['date'] = match.group(1)
            break
    
    # Extract vendor name
    vendor_patterns = [
        r'(?:from|vendor|company|business)\s*:?\s*([A-Za-z\s&.,]+?)(?:\n|$|[0-9])',
        r'bill\s+from\s+([A-Za-z\s&.,]+?)(?:\n|$|[0-9])',
        r'invoice\s+from\s+([A-Za-z\s&.,]+?)(?:\n|$|[0-9])'
    ]
    
    for pattern in vendor_patterns:
        match = re.search(pattern, groq_response, re.IGNORECASE)
        if match:
            vendor_name = match.group(1).strip()
            if len(vendor_name) > 2:  # Basic validation
                invoice_data['vendor_name'] = vendor_name
                break
    
    return invoice_data

def validate_against_policies(invoice_data: Dict[str, Any], policies: List[AuditPolicy]) -> AuditResult:
    """Validate invoice data against audit policies"""
    
    violations = []
    total_rules = len([p for p in policies if p.is_active])
    
    for policy in policies:
        if not policy.is_active:
            continue
            
        violation = None
        field_value = invoice_data.get(policy.field_name)
        
        if policy.rule_type == "required_field":
            if policy.condition == "exists" and not field_value:
                violation = {
                    "rule_name": policy.rule_name,
                    "field_name": policy.field_name,
                    "violation_type": "missing_field",
                    "severity": getattr(policy, 'severity', 'medium'),
                    "message": f"{policy.field_name.replace('_', ' ').title()} is required but missing"
                }
        
        elif policy.rule_type == "amount_limit" and field_value:
            try:
                amount = float(field_value)
                limit = float(policy.expected_value)
                
                if policy.condition == "max_value" and amount > limit:
                    violation = {
                        "rule_name": policy.rule_name,
                        "field_name": policy.field_name,
                        "violation_type": "amount_exceeded",
                        "severity": getattr(policy, 'severity', 'medium'),
                        "message": f"Amount ${amount} exceeds maximum limit of ${limit}"
                    }
                elif policy.condition == "min_value" and amount < limit:
                    violation = {
                        "rule_name": policy.rule_name,
                        "field_name": policy.field_name,
                        "violation_type": "amount_below_minimum",
                        "severity": getattr(policy, 'severity', 'medium'),
                        "message": f"Amount ${amount} is below minimum limit of ${limit}"
                    }
            except (ValueError, TypeError):
                pass
        
        elif policy.rule_type == "content_warning":
            if policy.condition == "contains_keywords":
                keywords = [kw.strip().lower() for kw in policy.expected_value.split(',')]
                content_text = groq_response.lower()
                
                found_keywords = [kw for kw in keywords if kw in content_text]
                if found_keywords:
                    violation = {
                        "rule_name": policy.rule_name,
                        "field_name": policy.field_name,
                        "violation_type": "content_warning",
                        "severity": getattr(policy, 'severity', 'warning'),
                        "message": f"Content contains flagged items: {', '.join(found_keywords)}",
                        "flagged_items": found_keywords
                    }
        
        elif policy.rule_type == "format_check" and field_value:
            if policy.condition == "format_match":
                pattern = policy.expected_value
                if not re.match(pattern, str(field_value)):
                    violation = {
                        "rule_name": policy.rule_name,
                        "field_name": policy.field_name,
                        "violation_type": "format_mismatch",
                        "severity": getattr(policy, 'severity', 'medium'),
                        "message": f"{policy.field_name.replace('_', ' ').title()} format is invalid"
                    }
        
        elif policy.rule_type == "date_range" and field_value:
            if policy.condition == "within_days":
                try:
                    # Simple date parsing - in production, use more robust parsing
                    days_limit = int(policy.expected_value)
                    current_date = datetime.now()
                    cutoff_date = current_date - timedelta(days=days_limit)
                    
                    # This is simplified - you'd want better date parsing
                    if "old" in str(field_value).lower() or "expired" in str(field_value).lower():
                        violation = {
                            "rule_name": policy.rule_name,
                            "field_name": policy.field_name,
                            "violation_type": "date_out_of_range",
                            "severity": getattr(policy, 'severity', 'medium'),
                            "message": f"Invoice date appears to be outside acceptable range"
                        }
                except (ValueError, TypeError):
                    pass
        
        if violation:
            violations.append(violation)
    
    # Calculate compliance score and categorize violations
    warnings = [v for v in violations if v.get('severity') == 'warning']
    errors = [v for v in violations if v.get('severity') in ['medium', 'high']]
    
    compliance_score = max(0, (total_rules - len(errors)) / total_rules * 100) if total_rules > 0 else 100
    
    # Generate summary
    if len(violations) == 0:
        summary = "Invoice is fully compliant with all audit policies"
    else:
        warning_text = f", {len(warnings)} warnings" if warnings else ""
        summary = f"Invoice has {len(errors)} policy violations{warning_text} out of {total_rules} rules checked"
    
    return AuditResult(
        is_compliant=len(violations) == 0,
        total_violations=len(violations),
        violations=violations,
        compliance_score=round(compliance_score, 2),
        summary=summary
    )

def perform_audit(groq_response: str, db: Session) -> AuditResult:
    """Perform complete audit of invoice"""
    
    # Get active policies
    policies = db.query(AuditPolicy).filter(AuditPolicy.is_active == True).all()
    
    # Extract invoice data
    invoice_data = extract_invoice_data(groq_response)
    
    # Validate against policies
    audit_result = validate_against_policies(invoice_data, policies)
    
    return audit_result