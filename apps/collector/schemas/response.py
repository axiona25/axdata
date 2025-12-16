"""CollectorResponse v1.0 Pydantic schema."""
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Any, Optional
from datetime import datetime


class LicenseInfo(BaseModel):
    """License information."""
    name: Optional[str] = Field(None, max_length=200)
    url: Optional[HttpUrl] = None
    notes: Optional[str] = Field(None, max_length=2000)


class Provenance(BaseModel):
    """Provenance information."""
    source_name: str = Field(..., min_length=1, max_length=200)
    base_url: HttpUrl
    endpoint: Optional[str] = Field(None, max_length=500)
    params_snapshot: Optional[Dict[str, Any]] = None
    request_hash: Optional[str] = Field(None, pattern="^[a-f0-9]{64}$")
    license: Optional[LicenseInfo] = None
    pagination: Optional[Dict[str, Any]] = None
    rate_limit_info: Optional[Dict[str, Any]] = None


class Metadata(BaseModel):
    """Collection metadata."""
    row_count: int = Field(..., ge=0)
    bytes: Optional[int] = Field(None, ge=0)
    columns: Optional[List[str]] = None
    source_specific: Optional[Dict[str, Any]] = None


class CollectorError(BaseModel):
    """Non-fatal error or warning."""
    message: str = Field(..., min_length=1)
    code: Optional[str] = None
    severity: Optional[str] = Field(None, pattern="^(warning|error|info)$")


class CollectorResponse(BaseModel):
    """
    Standard response format from API Collector to Backend.
    
    All connectors MUST return this format.
    """
    connector: str = Field(..., min_length=1, max_length=50)
    query_id: str = Field(..., min_length=1, max_length=100)
    retrieved_at: datetime
    records: List[Dict[str, Any]] = Field(..., min_items=0)
    metadata: Metadata
    provenance: Provenance
    storage_path: Optional[str] = Field(None, max_length=1000)
    errors: Optional[List[CollectorError]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "connector": "eurostat",
                "query_id": "q1",
                "retrieved_at": "2025-12-14T10:21:30Z",
                "records": [
                    {"geo": "IT", "time": "2022", "value": 1.5}
                ],
                "metadata": {
                    "row_count": 1,
                    "bytes": 100,
                    "columns": ["geo", "time", "value"]
                },
                "provenance": {
                    "source_name": "Eurostat API",
                    "base_url": "https://ec.europa.eu/eurostat",
                    "endpoint": "/api/dissemination/statistics/1.0/data/prc_hicp_midx",
                    "params_snapshot": {"geo": ["IT"], "time": ["2022"]},
                    "request_hash": "a8c...ff2",
                    "license": {
                        "name": "Eurostat reuse policy",
                        "url": "https://ec.europa.eu/eurostat"
                    }
                }
            }
        }

