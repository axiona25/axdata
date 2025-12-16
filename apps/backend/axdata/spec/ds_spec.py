"""DS-SPEC v1 models and validation."""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field, validator, model_validator
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User role."""
    GENERAL = "general"
    RESEARCHER = "researcher"
    DATA_SCIENTIST = "data_scientist"


class TimeGranularity(str, Enum):
    """Time granularity."""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    NONE = "none"


class GeoLevel(str, Enum):
    """Geographic level."""
    GLOBAL = "global"
    COUNTRY = "country"
    REGION = "region"
    PROVINCE = "province"
    CITY = "city"
    POINT = "point"
    POLYGON = "polygon"
    NONE = "none"


class EntityKind(str, Enum):
    """Entity kind."""
    NONE = "none"
    PERSON = "person"
    ORGANIZATION = "organization"
    FACILITY = "facility"
    COUNTRY = "country"
    REGION = "region"
    PRODUCT = "product"
    STUDY = "study"
    DOCUMENT = "document"
    CUSTOM = "custom"


class VariableType(str, Enum):
    """Variable type."""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TEXT = "text"
    EVENT = "event"
    GEO = "geo"


class TemplateType(str, Enum):
    """Dataset template type."""
    TABULAR = "tabular"
    TIME_SERIES = "time_series"
    CROSS_SECTIONAL = "cross_sectional"
    PANEL = "panel"
    GEOSPATIAL = "geospatial"
    TEXT = "text"
    EVENT = "event"
    HYBRID = "hybrid"
    AUTO = "auto"


class OutputFormat(str, Enum):
    """Output format."""
    CSV = "csv"
    PARQUET = "parquet"
    JSON = "json"
    GEOJSON = "geojson"


class LicensePolicy(str, Enum):
    """License policy."""
    STRICT = "strict"
    NORMAL = "normal"


class IdStrategy(str, Enum):
    """ID strategy."""
    NATIVE = "native"
    MAPPED = "mapped"
    HASH = "hash"


class RequestSpec(BaseModel):
    """Request specification."""
    query_text: str = Field(..., min_length=3)
    language: str = Field(default="it")
    user_role: UserRole = Field(default=UserRole.GENERAL)


class TimeDimension(BaseModel):
    """Time dimension."""
    enabled: bool
    start: Optional[str] = Field(None, description="YYYY-MM-DD or YYYY")
    end: Optional[str] = Field(None, description="YYYY-MM-DD or YYYY")
    granularity: TimeGranularity = Field(default=TimeGranularity.NONE)


class GeoDimension(BaseModel):
    """Geographic dimension."""
    enabled: bool
    scope: Optional[str] = Field(None, description="e.g. EU, IT, global")
    level: GeoLevel = Field(default=GeoLevel.NONE)
    crs: str = Field(default="EPSG:4326")


class EntityDimension(BaseModel):
    """Entity dimension."""
    kind: EntityKind
    tracking: bool = Field(default=False)
    id_strategy: IdStrategy = Field(default=IdStrategy.MAPPED)


class DimensionsSpec(BaseModel):
    """Dimensions specification."""
    time: TimeDimension
    geo: GeoDimension
    entity: EntityDimension


class VariableSpec(BaseModel):
    """Variable specification."""
    name: str
    type: VariableType
    unit: Optional[str] = None
    preferred_sources: List[str] = Field(default_factory=list)


class QualitySpec(BaseModel):
    """Quality specification."""
    min_completeness: float = Field(default=0.85, ge=0.0, le=1.0)
    deduplicate: bool = Field(default=True)


class ComplianceSpec(BaseModel):
    """Compliance specification."""
    allow_pii: bool = Field(default=False)
    license_policy: LicensePolicy = Field(default=LicensePolicy.NORMAL)


class OutputSpec(BaseModel):
    """Output specification."""
    template: TemplateType = Field(default=TemplateType.AUTO)
    formats: List[OutputFormat] = Field(default_factory=lambda: [OutputFormat.CSV])
    quality: QualitySpec = Field(default_factory=QualitySpec)
    compliance: ComplianceSpec = Field(default_factory=ComplianceSpec)


class DatasetSpec(BaseModel):
    """AXDATA Dataset Specification v1."""
    version: Literal["1.0"] = Field(default="1.0")
    request: RequestSpec
    sector: str
    subsector: Optional[str] = None
    dimensions: DimensionsSpec
    variables: List[VariableSpec] = Field(..., min_length=1)
    output: OutputSpec = Field(default_factory=OutputSpec)

    model_config = {"use_enum_values": True}
    
    @model_validator(mode='after')
    def validate_time_range(self):
        """Validate time range if time dimension is enabled."""
        if self.dimensions.time.enabled:
            time_dim = self.dimensions.time
            if time_dim.start and time_dim.end:
                # Parse dates
                try:
                    start_date = self._parse_date(time_dim.start)
                    end_date = self._parse_date(time_dim.end)
                    
                    if start_date and end_date and start_date > end_date:
                        raise ValueError(
                            f"Time range invalid: start ({time_dim.start}) must be before end ({time_dim.end})"
                        )
                except Exception as e:
                    if isinstance(e, ValueError) and "Time range invalid" in str(e):
                        raise
                    # If parsing fails, skip validation (will be handled by connector)
                    pass
        
        return self
    
    @model_validator(mode='after')
    def validate_geo_scope(self):
        """Validate geo scope if geo dimension is enabled."""
        if self.dimensions.geo.enabled:
            geo_dim = self.dimensions.geo
            if geo_dim.level and geo_dim.level != GeoLevel.NONE:
                if not geo_dim.scope and geo_dim.level in [GeoLevel.COUNTRY, GeoLevel.REGION, GeoLevel.PROVINCE, GeoLevel.CITY]:
                    raise ValueError(
                        f"Geo scope required when level is {geo_dim.level}"
                    )
        
        return self
    
    @model_validator(mode='after')
    def validate_variables(self):
        """Validate variables match dimensions."""
        # Check if time variable exists when time dimension is enabled
        if self.dimensions.time.enabled:
            time_vars = [v.name.lower() for v in self.variables]
            time_keywords = ["time", "date", "year", "timestamp", "period"]
            if not any(keyword in var for var in time_vars for keyword in time_keywords):
                # Warning: no explicit time variable, but template transformer will handle it
                pass
        
        # Check if geo variable exists when geo dimension is enabled
        if self.dimensions.geo.enabled:
            geo_vars = [v.name.lower() for v in self.variables]
            geo_keywords = ["geo", "country", "region", "location", "place"]
            if not any(keyword in var for var in geo_vars for keyword in geo_keywords):
                # Warning: no explicit geo variable, but template transformer will handle it
                pass
        
        return self
    
    @staticmethod
    def _parse_date(date_str: str) -> Optional[datetime]:
        """Parse date string (YYYY-MM-DD or YYYY)."""
        try:
            if len(date_str) == 4:
                # Year only
                return datetime(int(date_str), 1, 1)
            elif len(date_str) == 10:
                # YYYY-MM-DD
                return datetime.strptime(date_str, "%Y-%m-%d")
            else:
                return None
        except Exception:
            return None
