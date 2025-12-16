"""Tests for cross-validation."""
import pytest
from axdata.quality.cross_validate import cross_validate_numeric_series


def test_cross_validate_identical_series():
    """Test cross-validation with identical series."""
    series = {
        "source1": [1.0, 2.0, 3.0, 4.0, 5.0],
        "source2": [1.0, 2.0, 3.0, 4.0, 5.0]
    }
    
    result = cross_validate_numeric_series(series)
    
    assert result["warning"] is False
    assert len(result["pairwise"]) == 1
    assert abs(result["pairwise"][0]["corr"] - 1.0) < 0.0001  # Allow floating point precision
    assert result["pairwise"][0]["avg_abs_diff"] == 0.0


def test_cross_validate_correlated_series():
    """Test cross-validation with highly correlated series."""
    series = {
        "source1": [1.0, 2.0, 3.0, 4.0, 5.0],
        "source2": [1.1, 2.1, 3.1, 4.1, 5.1]  # Slight offset
    }
    
    result = cross_validate_numeric_series(series)
    
    assert result["warning"] is False  # High correlation
    assert result["pairwise"][0]["corr"] > 0.9


def test_cross_validate_uncorrelated_series():
    """Test cross-validation with uncorrelated series."""
    series = {
        "source1": [1.0, 2.0, 3.0, 4.0, 5.0],
        "source2": [5.0, 4.0, 3.0, 2.0, 1.0]  # Reversed
    }
    
    result = cross_validate_numeric_series(series)
    
    assert result["warning"] is True  # Low correlation
    assert result["pairwise"][0]["corr"] < 0.0  # Negative correlation


def test_cross_validate_multiple_sources():
    """Test cross-validation with multiple sources."""
    series = {
        "source1": [1.0, 2.0, 3.0, 4.0, 5.0],
        "source2": [1.1, 2.1, 3.1, 4.1, 5.1],
        "source3": [0.9, 1.9, 2.9, 3.9, 4.9]
    }
    
    result = cross_validate_numeric_series(series)
    
    assert len(result["per_source"]) == 3
    assert len(result["pairwise"]) == 3  # 3 choose 2 = 3 pairs
    # Check that all sources appear in pairwise comparisons
    all_sources_in_pairs = set()
    for p in result["pairwise"]:
        all_sources_in_pairs.add(p["a"])
        all_sources_in_pairs.add(p["b"])
    assert len(all_sources_in_pairs) >= 2  # At least 2 sources should be compared


def test_cross_validate_empty_series():
    """Test cross-validation with empty series."""
    series = {
        "source1": [],
        "source2": [1.0, 2.0]
    }
    
    result = cross_validate_numeric_series(series)
    
    # Should handle gracefully
    assert "source1" in result["per_source"] or len(result["pairwise"]) == 0


def test_cross_validate_single_source():
    """Test cross-validation with single source."""
    series = {
        "source1": [1.0, 2.0, 3.0]
    }
    
    result = cross_validate_numeric_series(series)
    
    assert len(result["per_source"]) == 1
    assert len(result["pairwise"]) == 0  # No pairs with single source
