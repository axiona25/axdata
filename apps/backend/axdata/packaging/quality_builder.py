"""Quality report builder - completeness, consistency, outliers."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None


def now_iso() -> str:
    """Get current UTC time as ISO string."""
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def calculate_completeness(records: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate completeness for each column.
    
    Args:
        records: List of records
    
    Returns:
        Dictionary mapping column names to completeness (0.0-1.0)
    """
    if not records:
        return {}
    
    if not PANDAS_AVAILABLE:
        # Manual calculation
        if not records:
            return {}
        
        total_rows = len(records)
        completeness = {}
        
        # Get all column names
        all_columns = set()
        for record in records:
            all_columns.update(record.keys())
        
        for col in all_columns:
            non_null_count = sum(1 for r in records if r.get(col) is not None and r.get(col) != "")
            completeness[col] = non_null_count / total_rows if total_rows > 0 else 0.0
        
        return completeness
    
    df = pd.DataFrame(records)
    completeness = {}
    
    for col in df.columns:
        non_null = df[col].notna().sum()
        total = len(df)
        completeness[col] = non_null / total if total > 0 else 0.0
    
    return completeness


def detect_outliers(records: List[Dict[str, Any]], numeric_columns: Optional[List[str]] = None) -> Dict[str, List[Any]]:
    """
    Detect outliers in numeric columns.
    
    Args:
        records: List of records
        numeric_columns: Optional list of numeric column names
    
    Returns:
        Dictionary mapping column names to list of outlier values
    """
    if not records or not PANDAS_AVAILABLE:
        return {}
    
    df = pd.DataFrame(records)
    
    if numeric_columns is None:
        # Auto-detect numeric columns
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
    
    outliers = {}
    
    for col in numeric_columns:
        if col not in df.columns:
            continue
        
        # Use IQR method
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        col_outliers = df[
            (df[col] < lower_bound) | (df[col] > upper_bound)
        ][col].tolist()
        
        if col_outliers:
            outliers[col] = col_outliers[:10]  # Limit to 10 outliers
    
    return outliers


def check_consistency(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Check data consistency.
    
    Args:
        records: List of records
    
    Returns:
        Consistency report
    """
    if not records:
        return {
            "consistent": True,
            "warnings": []
        }
    
    warnings = []
    
    if not PANDAS_AVAILABLE:
        # Basic checks without pandas
        if len(records) == 0:
            warnings.append("Empty dataset")
        
        # Check for duplicate records
        seen = set()
        duplicates = 0
        for record in records:
            record_str = str(sorted(record.items()))
            if record_str in seen:
                duplicates += 1
            seen.add(record_str)
        
        if duplicates > 0:
            warnings.append(f"Found {duplicates} duplicate records")
        
        return {
            "consistent": len(warnings) == 0,
            "warnings": warnings
        }
    
    df = pd.DataFrame(records)
    
    # Check for duplicates
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        warnings.append(f"Found {duplicates} duplicate rows")
    
    # Check for inconsistent types in same column
    for col in df.columns:
        if df[col].dtype == 'object':
            # Check if column has mixed types
            types = df[col].apply(type).unique()
            if len(types) > 1:
                warnings.append(f"Column '{col}' has mixed types: {[str(t) for t in types]}")
    
    return {
        "consistent": len(warnings) == 0,
        "warnings": warnings,
        "duplicate_count": int(duplicates)
    }


def build_quality_report(
    records: List[Dict[str, Any]],
    ds_spec: Dict[str, Any],
    cross_validation_result: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Build comprehensive quality report.
    
    This aligns with the Quality tab in the UI.
    
    Args:
        records: Transformed records
        ds_spec: Dataset specification
        cross_validation_result: Optional cross-validation result from multiple sources
    
    Returns:
        Quality report dictionary
    """
    if not records:
        return {
            "generated_at": now_iso(),
            "completeness": {},
            "outliers": {},
            "consistency": {"consistent": True, "warnings": []},
            "cross_validation": None,
            "overall_score": 0.0,
            "status": "empty"
        }
    
    # Calculate completeness
    completeness = calculate_completeness(records)
    overall_completeness = sum(completeness.values()) / len(completeness) if completeness else 0.0
    
    # Detect outliers
    numeric_columns = [
        v["name"] for v in ds_spec.get("variables", [])
        if v.get("type") == "numeric"
    ]
    outliers = detect_outliers(records, numeric_columns)
    
    # Check consistency
    consistency = check_consistency(records)
    
    # Overall quality score (0.0-1.0)
    # Based on completeness, consistency, and outlier ratio
    outlier_penalty = min(len(outliers) / max(len(records), 1) * 0.1, 0.1)  # Max 10% penalty
    consistency_penalty = 0.1 if not consistency.get("consistent", True) else 0.0
    
    overall_score = max(0.0, min(1.0, overall_completeness - outlier_penalty - consistency_penalty))
    
    # Determine status
    if overall_score >= 0.9:
        status = "excellent"
    elif overall_score >= 0.75:
        status = "good"
    elif overall_score >= 0.5:
        status = "fair"
    else:
        status = "poor"
    
    # Build missing values analysis
    missing_by_variable = {}
    for var_name, comp in completeness.items():
        missing_pct = (1.0 - comp) * 100
        missing_by_variable[var_name] = {
            "completeness": round(comp, 3),
            "missing_percentage": round(missing_pct, 1),
            "missing_count": int((1.0 - comp) * len(records)),
            "warning": missing_pct > 5.0  # Warning if > 5% missing
        }
    
    # Build outliers summary
    outliers_summary = {
        "detected": len(outliers) > 0,
        "method": "IQR (Interquartile Range)",
        "total_outliers": sum(len(v) for v in outliers.values()),
        "affected_records": len(set(
            idx for col_outliers in outliers.values() for idx in range(len(col_outliers))
        )),
        "action": "flagged (not removed)",
        "per_column": outliers
    }
    
    # Build cross-source validation summary
    cross_source_summary = None
    if cross_validation_result:
        pairwise = cross_validation_result.get("pairwise", [])
        if pairwise:
            # Get best correlation
            best_corr = max(p.get("corr", 0) for p in pairwise)
            sources_involved = set()
            for p in pairwise:
                sources_involved.add(p.get("source_a", ""))
                sources_involved.add(p.get("source_b", ""))
            
            cross_source_summary = {
                "multi_source": True,
                "sources_count": len(sources_involved),
                "best_correlation": round(best_corr, 3),
                "status": "Consistent" if best_corr > 0.8 else "Inconsistent",
                "details": cross_validation_result
            }
        else:
            cross_source_summary = {
                "multi_source": False,
                "status": "Single source dataset"
            }
    else:
        cross_source_summary = {
            "multi_source": False,
            "status": "Single source dataset"
        }
    
    # Generate quality notes (human-readable explanation)
    quality_notes = []
    if overall_completeness < 0.9:
        quality_notes.append(f"Completeness is {overall_completeness*100:.1f}% - minor gaps may exist in early years due to delayed reporting.")
    
    if outliers_summary["detected"]:
        quality_notes.append(f"Outliers detected ({outliers_summary['total_outliers']} values) - flagged but not removed for transparency.")
    
    if not consistency.get("consistent", True):
        warnings = consistency.get("warnings", [])
        if warnings:
            quality_notes.append(f"Consistency warnings: {', '.join(warnings[:2])}.")
    
    if cross_source_summary.get("multi_source"):
        corr = cross_source_summary.get("best_correlation", 0)
        if corr > 0.8:
            quality_notes.append(f"Multi-source validation confirms data consistency (correlation: {corr:.2f}).")
        else:
            quality_notes.append(f"Multi-source validation shows some discrepancies (correlation: {corr:.2f}) - review recommended.")
    
    if not quality_notes:
        quality_notes.append("Dataset quality is high and suitable for research & commercial use.")
    
    # Determine quality status label
    if overall_score >= 0.9:
        status_label = "High"
        status_description = "Suitable for research & commercial use"
    elif overall_score >= 0.75:
        status_label = "Good"
        status_description = "Suitable for most use cases"
    elif overall_score >= 0.5:
        status_label = "Fair"
        status_description = "Review recommended before use"
    else:
        status_label = "Poor"
        status_description = "Not recommended for production use"
    
    return {
        "generated_at": now_iso(),
        "quality_score": {
            "overall_score": round(overall_score, 3),
            "percentage": round(overall_score * 100, 1),
            "status": status_label,
            "status_description": status_description
        },
        "completeness": {
            "records_expected": len(records),
            "records_available": len(records),
            "completeness_percentage": round(overall_completeness * 100, 1),
            "overall": overall_completeness,
            "per_column": completeness,
            "missing_data_count": sum(
                (1.0 - comp) * len(records)
                for comp in completeness.values()
            )
        },
        "missing_values_analysis": missing_by_variable,
        "outliers": outliers_summary,
        "consistency": consistency,
        "cross_source_validation": cross_source_summary,
        "quality_notes": " ".join(quality_notes),
        "record_count": len(records),
        "column_count": len(completeness)
    }
