"""Tests for configuration."""
import pytest
from core.config import Settings


def test_settings_load():
    """Test that settings can be loaded."""
    settings = Settings()
    assert settings.environment is not None
    assert settings.database_url is not None
    assert settings.redis_url is not None


def test_cors_origins_parsing():
    """Test CORS origins parsing."""
    settings = Settings()
    origins = settings.cors_origins_list
    assert isinstance(origins, list)
    assert len(origins) > 0


def test_environment_properties():
    """Test environment properties."""
    settings = Settings()
    assert isinstance(settings.is_development, bool)
    assert isinstance(settings.is_production, bool)

