"""Cross-validation between sources."""
from __future__ import annotations
from typing import Dict, Any, List
import math


def _mean(xs: List[float]) -> float:
    """Calculate mean."""
    return sum(xs) / len(xs) if xs else float("nan")


def _corr(x: List[float], y: List[float]) -> float:
    """
    Calculate Pearson correlation coefficient.
    
    Args:
        x: First series
        y: Second series
    
    Returns:
        Correlation coefficient (or NaN if invalid)
    """
    n = min(len(x), len(y))
    if n == 0:
        return float("nan")
    
    x, y = x[:n], y[:n]
    mx, my = _mean(x), _mean(y)
    
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    denx = math.sqrt(sum((a - mx) ** 2 for a in x))
    deny = math.sqrt(sum((b - my) ** 2 for b in y))
    
    if denx == 0 or deny == 0:
        return float("nan")
    
    return num / (denx * deny)


def cross_validate_numeric_series(series_by_source: Dict[str, List[float]]) -> Dict[str, Any]:
    """
    Cross-validate numeric time series from multiple sources.
    
    Args:
        series_by_source: Dictionary mapping source_id to list of values
    
    Returns:
        Validation report with statistics and pairwise comparisons
    """
    stats = {}
    for sid, vals in series_by_source.items():
        if not vals:
            continue
        stats[sid] = {
            "min": min(vals),
            "max": max(vals),
            "mean": _mean(vals),
            "count": len(vals)
        }
    
    # pairwise comparisons
    pairs = []
    sids = list(series_by_source.keys())
    for i in range(len(sids)):
        for j in range(i + 1, len(sids)):
            a, b = sids[i], sids[j]
            xa, xb = series_by_source[a], series_by_source[b]
            n = min(len(xa), len(xb))
            if n == 0:
                continue
            
            diffs = [abs(xa[k] - xb[k]) for k in range(n)]
            pairs.append({
                "a": a,
                "b": b,
                "avg_abs_diff": _mean(diffs),
                "corr": _corr(xa, xb),
                "n": n
            })
    
    # semplice "verdetto"
    warning = any(
        (p["corr"] == p["corr"] and p["corr"] < 0.8)  # corr not NaN and < 0.8
        for p in pairs
    )
    
    return {
        "per_source": stats,
        "pairwise": pairs,
        "warning": warning,
        "note": "warning=true se una correlazione tra fonti scende sotto 0.8 (euristica)."
    }
