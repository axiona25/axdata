"""Compliance builder - license and PII guard (aligned with ChatGPT UI spec)."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime
from axdata.spec.ds_spec import DatasetSpec


def now_iso() -> str:
    """Get current UTC time as ISO string."""
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def detect_pii_fields(records: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Detect potential PII fields in records.
    
    Args:
        records: Optional list of records to analyze
    
    Returns:
        PII detection report
    """
    if not records:
        return {
            "personal_data_detected": False,
            "pii_risk": "None",
            "gdpr_impact": "Not applicable",
            "fields_checked": []
        }
    
    # Common PII field patterns
    pii_patterns = [
        "email", "phone", "ssn", "passport", "credit_card", "iban",
        "name", "address", "postal", "city", "birth", "age"
    ]
    
    # Check first record for field names
    if records:
        sample_record = records[0]
        field_names = list(sample_record.keys())
        
        potential_pii_fields = []
        for field in field_names:
            field_lower = field.lower()
            if any(pattern in field_lower for pattern in pii_patterns):
                potential_pii_fields.append(field)
        
        has_pii = len(potential_pii_fields) > 0
        
        return {
            "personal_data_detected": has_pii,
            "pii_risk": "High" if has_pii else "None",
            "gdpr_impact": "Applicable - review required" if has_pii else "Not applicable",
            "fields_checked": field_names[:10],  # Limit to first 10
            "potential_pii_fields": potential_pii_fields
        }
    
    return {
        "personal_data_detected": False,
        "pii_risk": "None",
        "gdpr_impact": "Not applicable",
        "fields_checked": []
    }


def determine_jurisdiction(sources_used: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Determine jurisdiction and relevant regulations.
    
    Args:
        sources_used: List of source manifests
    
    Returns:
        Jurisdiction information
    """
    # Check sources for EU-based publishers
    eu_publishers = ["European Commission", "Eurostat", "ECB", "ESA", "Copernicus"]
    us_publishers = ["CDC", "NASA", "NOAA"]
    
    jurisdictions = set()
    regulations = set()
    
    for source in sources_used:
        authority = source.get("authority", {})
        publisher = authority.get("publisher", "")
        
        if any(eu in publisher for eu in eu_publishers):
            jurisdictions.add("EU")
            regulations.add("GDPR")
            regulations.add("Open Data Directive")
        elif any(us in publisher for us in us_publishers):
            jurisdictions.add("US")
            regulations.add("FOIA")
    
    if not jurisdictions:
        jurisdictions.add("Global")
    
    return {
        "jurisdictions": list(jurisdictions),
        "relevant_regulations": list(regulations),
        "primary_jurisdiction": list(jurisdictions)[0] if jurisdictions else "Global"
    }


def build_compliance(
    ds_spec: Dict[str, Any] | DatasetSpec,
    sources_used: List[Dict[str, Any]],
    pii_detected: bool = False,
    records: Optional[List[Dict[str, Any]]] = None,
    notes: str = ""
) -> Dict[str, Any]:
    """
    Build comprehensive compliance information (aligned with ChatGPT UI spec).
    
    Includes:
    - Usage Rights
    - Licenses Overview
    - PII & Sensitive Data Check
    - Jurisdiction & Regulations
    - Compliance Notes
    
    Args:
        ds_spec: Dataset specification
        sources_used: List of source manifests used
        pii_detected: Whether PII was detected
        records: Optional records for PII detection
        notes: Additional notes
    
    Returns:
        Comprehensive compliance dictionary
    """
    # Convert to dict if needed
    if isinstance(ds_spec, DatasetSpec):
        spec_dict = ds_spec.model_dump()
    else:
        spec_dict = ds_spec
    
    policy = spec_dict.get("output", {}).get("compliance", {}).get("license_policy", "normal")
    allow_pii = spec_dict.get("output", {}).get("compliance", {}).get("allow_pii", False)
    
    # Build licenses overview
    licenses = []
    all_commercial_allowed = True
    all_academic_allowed = True
    attribution_required = False
    
    for s in sources_used:
        lic = s.get("license", {})
        if lic:
            commercial = lic.get("commercial_use", False)
            attribution = lic.get("attribution_required", True)
            
            if not commercial:
                all_commercial_allowed = False
            if attribution:
                attribution_required = True
            
            licenses.append({
                "source_id": s.get("source_id"),
                "source_name": s.get("name", s.get("source_id")),
                "license_name": lic.get("name", "Unknown"),
                "license_url": lic.get("url", ""),
                "commercial_use": commercial,
                "academic_use": True,  # Assume academic use is always allowed
                "attribution_required": attribution
            })
    
    # Determine usage rights
    usage_rights = {
        "commercial_use": "Allowed" if all_commercial_allowed else "Restricted",
        "academic_use": "Allowed" if all_academic_allowed else "Restricted",
        "attribution_required": "Yes" if attribution_required else "No",
        "status": "green" if all_commercial_allowed and all_academic_allowed else "yellow"
    }
    
    # Enhanced PII detection
    pii_report = detect_pii_fields(records)
    if pii_detected:
        pii_report["personal_data_detected"] = True
        pii_report["pii_risk"] = "High"
        pii_report["gdpr_impact"] = "Applicable - review required"
    
    # Determine jurisdiction
    jurisdiction_info = determine_jurisdiction(sources_used)
    
    # Build compliance notes
    if not notes:
        notes_parts = []
        
        if all_commercial_allowed:
            notes_parts.append("Dataset complies with all source licenses.")
        else:
            notes_parts.append("Some source licenses restrict commercial use - review individual licenses.")
        
        if not pii_report["personal_data_detected"]:
            notes_parts.append("Dataset does not contain personal or sensitive data.")
        else:
            notes_parts.append("PII detected - GDPR compliance review recommended.")
        
        if jurisdiction_info["jurisdictions"]:
            notes_parts.append(f"Relevant regulations: {', '.join(jurisdiction_info['relevant_regulations'])}.")
        
        notes = " ".join(notes_parts)
    
    return {
        "generated_at": now_iso(),
        "usage_rights": usage_rights,
        "license_policy": policy,
        "licenses": licenses,
        "pii": {
            "allow_pii": allow_pii,
            "pii_detected": pii_detected or pii_report["personal_data_detected"],
            "personal_data_detected": pii_report["personal_data_detected"],
            "pii_risk": pii_report["pii_risk"],
            "gdpr_impact": pii_report["gdpr_impact"],
            "action": "blocked" if ((pii_detected or pii_report["personal_data_detected"]) and not allow_pii) else "allowed",
            "fields_checked": pii_report.get("fields_checked", []),
            "potential_pii_fields": pii_report.get("potential_pii_fields", [])
        },
        "jurisdiction": jurisdiction_info,
        "notes": notes
    }
