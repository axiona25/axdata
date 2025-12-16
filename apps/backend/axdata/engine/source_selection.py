"""Source Selection Engine - filters and ranks sources based on DS-SPEC."""
from __future__ import annotations
from typing import Any, Dict, List
from axdata.spec.ds_spec import DatasetSpec


def _license_ok(ds_spec: Dict[str, Any], src: Dict[str, Any]) -> bool:
    """Check if source license is compatible with DS-SPEC policy."""
    policy = ds_spec.get("output", {}).get("compliance", {}).get("license_policy", "normal")
    # strict: accetta solo fonti con commercial_use true (utile se vendi dataset)
    if policy == "strict" and not src.get("license", {}).get("commercial_use", False):
        return False
    return True


def _geo_ok(ds_spec: Dict[str, Any], src: Dict[str, Any]) -> bool:
    """Check if source geographic coverage matches DS-SPEC."""
    geo = ds_spec.get("dimensions", {}).get("geo", {})
    if not geo.get("enabled", False):
        return True
    
    scope = (geo.get("scope") or "").lower()
    src_scope = (src.get("geo_coverage", {}).get("scope") or "").lower()
    
    # semplice: se scope richiesto è contenuto nello scope della fonte
    return (scope == "") or (scope in src_scope) or (src_scope == "global")


def _dtype_ok(template: str, src: Dict[str, Any]) -> bool:
    """Check if source supports the required data type."""
    src_types = set(src.get("data_types", []))
    # Tabular è sempre supportato come fallback
    if template == "tabular":
        return len(src_types) > 0
    return template in src_types


def _sector_ok(ds_spec: Dict[str, Any], src: Dict[str, Any]) -> bool:
    """Check if source covers the required sector."""
    sector = ds_spec.get("sector", "")
    src_sectors = set(src.get("sectors", []))
    return sector in src_sectors


def score_source(ds_spec: Dict[str, Any], src: Dict[str, Any]) -> float:
    """
    Score a source based on authority, reliability, and coverage match.
    
    Returns:
        Score (higher is better)
    """
    auth = src.get("authority", {}).get("level", 1)  # 1..5
    up = src.get("reliability", {}).get("uptime_score", 0.9)
    
    # preferisci fonti con geo scope più vicino (euristica)
    geo_req = (ds_spec.get("dimensions", {}).get("geo", {}).get("scope") or "").lower()
    geo_src = (src.get("geo_coverage", {}).get("scope") or "").lower()
    geo_bonus = 0.2 if geo_req and geo_req in geo_src else (0.1 if geo_src == "global" else 0.0)
    
    return (auth * 10.0) + (up * 5.0) + geo_bonus


def select_sources(
    ds_spec: Dict[str, Any] | DatasetSpec,
    template: str,
    manifests: List[Dict[str, Any]],
    top_n: int = 3
) -> List[Dict[str, Any]]:
    """
    Select and rank sources based on DS-SPEC and template.
    
    Args:
        ds_spec: Dataset specification
        template: Selected template
        manifests: List of source manifests
        top_n: Number of top sources to return
    
    Returns:
        List of selected sources (ranked)
    """
    # Convert to dict if needed
    if isinstance(ds_spec, DatasetSpec):
        spec_dict = ds_spec.model_dump()
    else:
        spec_dict = ds_spec
    
    candidates = []
    for src in manifests:
        if not _sector_ok(spec_dict, src):
            continue
        if not _dtype_ok(template, src):
            continue
        if not _geo_ok(spec_dict, src):
            continue
        if not _license_ok(spec_dict, src):
            continue
        candidates.append(src)
    
    ranked = sorted(candidates, key=lambda s: score_source(spec_dict, s), reverse=True)
    return ranked[:top_n]
