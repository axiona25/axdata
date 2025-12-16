"""Tests for collector configuration."""
import pytest
from core.config import Settings


def test_settings_load():
    """Test that settings can be loaded."""
    settings = Settings()
    assert settings.environment is not None
    assert settings.s3_bucket is not None


def test_environment_properties():
    """Test environment properties."""
    settings = Settings()
    assert isinstance(settings.is_development, bool)
    assert isinstance(settings.is_production, bool)

