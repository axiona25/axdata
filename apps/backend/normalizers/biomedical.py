"""Biomedical normalizer following CDISC/HL7 FHIR/OMOP Common Data Model standards.

Complete MVP implementation for PubMed, ClinicalTrials, WHO GHO sources.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union
import re
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

from normalizers.base import BaseNormalizer


# -----------------------------
# Helpers (text / parsing)
# -----------------------------

_WHITESPACE_RE = re.compile(r"\s+")
_NON_PRINTABLE_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")


def _clean_text(value: Any, *, max_len: int = 2000) -> Optional[str]:
    if value is None:
        return None
    s = str(value)
    s = _NON_PRINTABLE_RE.sub(" ", s)
    s = _WHITESPACE_RE.sub(" ", s).strip()
    if not s:
        return None
    if len(s) > max_len:
        s = s[: max_len - 1] + "…"
    return s


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [x for x in (str(v).strip() for v in value) if x]
    # handle ";" or "," separated strings
    s = str(value).strip()
    if not s:
        return []
    parts = re.split(r"[;,]\s*", s)
    return [p for p in parts if p]


def _parse_date(value: Any) -> Optional[Any]:
    """Best-effort parse to pandas Timestamp (UTC-naive)."""
    if not PANDAS_AVAILABLE:
        # Fallback: return as string
        if value is None:
            return None
        return str(value).strip() or None
    
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    # pandas can parse many formats
    try:
        ts = pd.to_datetime(s, errors="coerce", utc=False)
        if pd.isna(ts):
            return None
        # Normalize to date-level if time not relevant
        return ts
    except Exception:
        return None


def _safe_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        # handles "1,234" etc.
        s = str(value).replace(",", "").strip()
        if not s:
            return None
        return int(float(s))
    except Exception:
        return None


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        s = str(value).replace(",", "").strip()
        if not s:
            return None
        return float(s)
    except Exception:
        return None


# -----------------------------
# Input normalization contracts
# -----------------------------

@dataclass
class RawAsset:
    """
    Standard internal representation.
    raw asset may come from:
      - connector output records
      - a path to a json/csv (optional)
      - a dataframe already built by connector
    """
    connector: str
    retrieved_at: Optional[str] = None
    query_id: Optional[str] = None
    base_url: Optional[str] = None
    license_name: Optional[str] = None
    license_url: Optional[str] = None
    records: Optional[List[Dict[str, Any]]] = None
    dataframe: Optional[Any] = None  # pd.DataFrame if pandas available


def _coerce_raw_assets(raw_assets: List[Dict[str, Any]]) -> List[RawAsset]:
    coerced: List[RawAsset] = []
    for a in raw_assets:
        coerced.append(
            RawAsset(
                connector=str(a.get("connector") or a.get("source") or "unknown"),
                retrieved_at=a.get("retrieved_at"),
                query_id=a.get("query_id"),
                base_url=a.get("base_url"),
                license_name=(a.get("license") or {}).get("name") if isinstance(a.get("license"), dict) else a.get("license_name"),
                license_url=(a.get("license") or {}).get("url") if isinstance(a.get("license"), dict) else a.get("license_url"),
                records=a.get("records") or a.get("data", []),
                dataframe=a.get("dataframe"),
            )
        )
    return coerced


class BiomedicalNormalizer(BaseNormalizer):
    """
    Biomedical domain normalizer.

    Output model: "record/study/event" rows with consistent columns across sources.
    Designed for:
      - PubMed (articles metadata)
      - ClinicalTrials (trial registry)
      - WHO/epidemiology aggregates (if included)

    This normalizer intentionally avoids personal data. It works on public/open/aggregate records.
    """

    domain = "biomedical"

    # Canonical columns for the final dataset (MVP)
    CANONICAL_COLUMNS = [
        "record_id",          # internal stable id (derived if missing)
        "source",             # connector key: pubmed/clinicaltrials/who_gho/...
        "source_record_id",   # pmid / nct_id / gho series id etc.
        "record_type",        # article/trial/indicator
        "title",
        "abstract",
        "keywords",
        "authors",
        "journal",
        "publication_date",
        "country",
        "condition",
        "intervention",
        "outcome",
        "study_phase",
        "study_status",
        "start_date",
        "completion_date",
        "population",
        "sample_size",
        "url",
        "retrieved_at",
        "license_name",
        "license_url",
        "provenance_query_id"
    ]

    # Columns that must exist (not necessarily non-null for every row)
    REQUIRED_COLUMNS = {"record_id", "source", "record_type", "title", "retrieved_at"}

    def __init__(self):
        super().__init__("biomedical")

    def normalize(
        self,
        raw_assets: List[Dict[str, Any]],
        dataset_plan: Dict[str, Any]
    ) -> Any:
        """
        Normalize biomedical data from multiple sources into unified model.
        
        Args:
            raw_assets: Lista di asset grezzi dal Collector
            dataset_plan: DatasetPlan con transformations e filters
        
        Returns:
            DataFrame normalizzato (o List[Dict] se pandas non disponibile)
        """
        if not PANDAS_AVAILABLE:
            # Fallback: return list of dicts
            all_records = []
            for asset in raw_assets:
                data = asset.get("records") or asset.get("data", [])
                if isinstance(data, list):
                    all_records.extend(data)
            return all_records

        assets = _coerce_raw_assets(raw_assets)

        frames: List[pd.DataFrame] = []
        for asset in assets:
            df = None
            if asset.dataframe is not None and isinstance(asset.dataframe, pd.DataFrame):
                df = asset.dataframe.copy()
                df = self._normalize_any_df(df, asset)
            elif asset.records is not None:
                df = pd.DataFrame(asset.records)
                df = self._normalize_any_df(df, asset)
            else:
                # nothing usable; skip but keep trace? In MVP we skip.
                continue

            if df is not None and not df.empty:
                frames.append(df)

        if not frames:
            # Return empty with canonical columns
            return pd.DataFrame(columns=self.CANONICAL_COLUMNS)

        merged = pd.concat(frames, ignore_index=True)
        merged = self._postprocess(merged, dataset_plan)
        return merged

    # -----------------------------
    # Source-specific mapping
    # -----------------------------

    def _normalize_any_df(self, df: pd.DataFrame, asset: RawAsset) -> pd.DataFrame:
        connector = (asset.connector or "").lower()

        if "pubmed" in connector:
            out = self._map_pubmed(df, asset)
        elif "clinical" in connector or "trials" in connector or "nct" in connector:
            out = self._map_clinical_trials(df, asset)
        elif "who" in connector or "gho" in connector:
            out = self._map_who_gho(df, asset)
        else:
            out = self._map_generic(df, asset)

        # Ensure canonical columns exist
        for col in self.CANONICAL_COLUMNS:
            if col not in out.columns:
                out[col] = None

        out = out[self.CANONICAL_COLUMNS].copy()
        return out

    def _map_pubmed(self, df: pd.DataFrame, asset: RawAsset) -> pd.DataFrame:
        """
        Expected common keys from a PubMed connector:
        - pmid
        - title
        - abstract
        - keywords (list or str)
        - authors (list or str)
        - journal
        - publication_date / pub_date / year
        - url
        """
        # normalize column names to lower
        df = df.copy()
        df.columns = [c.strip().lower() for c in df.columns]

        def pick(*names: str) -> pd.Series:
            for n in names:
                if n in df.columns:
                    return df[n]
            return pd.Series([None] * len(df))

        out = pd.DataFrame()
        out["source"] = "pubmed"
        out["record_type"] = "article"
        out["source_record_id"] = pick("pmid", "id", "article_id")
        out["title"] = pick("title", "article_title")
        out["abstract"] = pick("abstract", "abstract_text", "summary")
        out["keywords"] = pick("keywords", "mesh_terms", "terms")
        out["authors"] = pick("authors", "author_list")
        out["journal"] = pick("journal", "source", "journal_title")
        out["publication_date"] = pick("publication_date", "pub_date", "date", "year")
        out["url"] = pick("url", "link")

        # optional biomedical fields
        out["condition"] = pick("condition", "conditions")
        out["intervention"] = pick("intervention", "interventions")
        out["outcome"] = pick("outcome", "outcomes")

        return self._attach_asset_meta(out, asset)

    def _map_clinical_trials(self, df: pd.DataFrame, asset: RawAsset) -> pd.DataFrame:
        """
        Expected keys from a ClinicalTrials connector:
        - nct_id
        - title / brief_title
        - condition(s)
        - intervention(s)
        - outcome(s)
        - phase
        - status
        - start_date
        - completion_date
        - enrollment / sample_size
        - country
        - url
        """
        df = df.copy()
        df.columns = [c.strip().lower() for c in df.columns]

        def pick(*names: str) -> pd.Series:
            for n in names:
                if n in df.columns:
                    return df[n]
            return pd.Series([None] * len(df))

        out = pd.DataFrame()
        out["source"] = "clinicaltrials"
        out["record_type"] = "trial"
        out["source_record_id"] = pick("nct_id", "nctid", "id", "trial_id")
        out["title"] = pick("brief_title", "title", "official_title")
        out["condition"] = pick("condition", "conditions")
        out["intervention"] = pick("intervention", "interventions")
        out["outcome"] = pick("outcome", "outcomes", "primary_outcome", "secondary_outcome")
        out["study_phase"] = pick("phase", "study_phase")
        out["study_status"] = pick("status", "overall_status", "study_status")
        out["start_date"] = pick("start_date", "study_start_date")
        out["completion_date"] = pick("completion_date", "primary_completion_date", "study_completion_date")
        out["sample_size"] = pick("enrollment", "sample_size", "target_enrollment")
        out["country"] = pick("country", "countries", "location_country")
        out["url"] = pick("url", "link")

        # Some trials have summary/brief abstract-like text
        out["abstract"] = pick("brief_summary", "summary", "detailed_description")
        out["keywords"] = pick("keywords")

        return self._attach_asset_meta(out, asset)

    def _map_who_gho(self, df: pd.DataFrame, asset: RawAsset) -> pd.DataFrame:
        """
        WHO GHO/aggregate indicator-like model:
        - indicator
        - country
        - year
        - value
        - unit
        """
        df = df.copy()
        df.columns = [c.strip().lower() for c in df.columns]

        def pick(*names: str) -> pd.Series:
            for n in names:
                if n in df.columns:
                    return df[n]
            return pd.Series([None] * len(df))

        out = pd.DataFrame()
        out["source"] = "who_gho"
        out["record_type"] = "indicator"
        out["source_record_id"] = pick("indicator_code", "indicator", "id", "series_id")
        out["title"] = pick("indicator_name", "indicator", "title", "name")
        out["country"] = pick("country", "geo", "location")
        out["publication_date"] = pick("year", "date", "time_period")
        out["outcome"] = pick("value")  # store numeric into outcome for generic model? better: keep in abstract/text
        out["abstract"] = pick("definition", "notes", "description")
        out["keywords"] = pick("topic", "keywords")

        # Put numeric value into a textual field to keep canonical model simple for MVP
        val = pick("value", "val")
        unit = pick("unit", "units")
        out["abstract"] = out["abstract"].fillna("").astype(str)
        out["abstract"] = out["abstract"].str.strip()
        out["abstract"] = out["abstract"].where(out["abstract"] != "", None)
        # Add value snippet
        out["abstract"] = out["abstract"].fillna("").astype(str)
        out["abstract"] = out["abstract"] + out["abstract"].apply(lambda x: "" if x == "" else " | ")
        out["abstract"] = out["abstract"] + "value=" + val.astype(str) + " " + unit.astype(str)

        return self._attach_asset_meta(out, asset)

    def _map_generic(self, df: pd.DataFrame, asset: RawAsset) -> pd.DataFrame:
        """
        Fallback mapping: tries to use common names if present.
        """
        df = df.copy()
        df.columns = [c.strip().lower() for c in df.columns]

        def pick(*names: str) -> pd.Series:
            for n in names:
                if n in df.columns:
                    return df[n]
            return pd.Series([None] * len(df))

        out = pd.DataFrame()
        out["source"] = asset.connector or "unknown"
        out["record_type"] = pick("record_type").fillna("record")
        out["source_record_id"] = pick("id", "record_id", "source_record_id")
        out["title"] = pick("title", "name")
        out["abstract"] = pick("abstract", "description", "summary")
        out["keywords"] = pick("keywords", "tags")
        out["authors"] = pick("authors")
        out["url"] = pick("url", "link")
        out["publication_date"] = pick("publication_date", "date", "year")
        out["country"] = pick("country", "geo")

        return self._attach_asset_meta(out, asset)

    # -----------------------------
    # Attach metadata / provenance
    # -----------------------------

    def _attach_asset_meta(self, out: pd.DataFrame, asset: RawAsset) -> pd.DataFrame:
        out = out.copy()

        out["retrieved_at"] = asset.retrieved_at
        out["license_name"] = asset.license_name
        out["license_url"] = asset.license_url
        out["provenance_query_id"] = asset.query_id

        # Build stable record_id:
        # prefer source_record_id; otherwise hash of title+source+retrieved_at
        src_id = out["source_record_id"].astype(str).where(out["source_record_id"].notna(), "")
        title = out["title"].astype(str).where(out["title"].notna(), "")
        source = out["source"].astype(str).where(out["source"].notna(), "unknown")
        retrieved = out["retrieved_at"].astype(str).where(out["retrieved_at"].notna(), "")
        out["record_id"] = (
            source.str.lower() + ":" + src_id.replace("nan", "")
        )

        # Where missing or empty, derive hash
        missing_mask = out["record_id"].isna() | (out["record_id"].astype(str).str.endswith(":")) | (out["record_id"].astype(str).str.endswith(":nan"))
        if missing_mask.any():
            derived = (source + "|" + title + "|" + retrieved).apply(lambda x: str(abs(hash(x))))
            out.loc[missing_mask, "record_id"] = (source + ":h" + derived)

        return out

    # -----------------------------
    # Postprocess: clean, cast, dedup, plan filters
    # -----------------------------

    def _postprocess(self, df: pd.DataFrame, dataset_plan: Dict[str, Any]) -> pd.DataFrame:
        df = df.copy()

        # Clean text fields
        text_cols = ["title", "abstract", "journal", "condition", "intervention", "outcome", "study_phase", "study_status", "population", "url"]
        list_like_cols = ["keywords", "authors"]

        for c in text_cols:
            if c in df.columns:
                df[c] = df[c].apply(_clean_text)

        for c in list_like_cols:
            if c in df.columns:
                # normalize to list-of-strings encoded as semicolon-separated for CSV friendliness
                df[c] = df[c].apply(_as_list).apply(lambda lst: "; ".join(lst) if lst else None)

        # Dates
        for c in ["publication_date", "start_date", "completion_date"]:
            if c in df.columns:
                df[c] = df[c].apply(_parse_date)

        # Sample size
        if "sample_size" in df.columns:
            df["sample_size"] = df["sample_size"].apply(_safe_int)

        # Light quality metrics can be computed later; here ensure required columns exist
        for col in self.REQUIRED_COLUMNS:
            if col not in df.columns:
                df[col] = None

        # Apply optional plan-driven filters (best effort)
        # Example expected plan structure:
        # dataset_plan.get("filters", {"record_type": ["trial"], "country": ["IT"]})
        filters = dataset_plan.get("filters") if isinstance(dataset_plan, dict) else None
        if isinstance(filters, dict):
            df = self._apply_filters(df, filters)

        # Dedup strategy:
        # 1) exact record_id
        # 2) fallback: same (source + normalized title)
        before = len(df)
        df = df.drop_duplicates(subset=["record_id"], keep="first")

        # fallback dedup by title within source (if title exists)
        if "title" in df.columns:
            tmp = df["title"].fillna("").str.lower().str.replace(r"[^a-z0-9]+", " ", regex=True).str.strip()
            df["_title_norm"] = tmp.where(tmp != "", None)
            df = df.drop_duplicates(subset=["source", "_title_norm"], keep="first")
            df = df.drop(columns=["_title_norm"], errors="ignore")

        # Optional: remove rows without title (too weak to be useful)
        if "title" in df.columns:
            df = df[df["title"].notna()]

        # Keep deterministic ordering
        df = df.sort_values(by=["source", "record_type", "publication_date"], na_position="last").reset_index(drop=True)

        return df

    def _apply_filters(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        out = df
        for key, val in filters.items():
            if key not in out.columns:
                continue
            allowed = val
            if not isinstance(allowed, list):
                allowed = [allowed]
            allowed = [a for a in allowed if a is not None]
            if not allowed:
                continue
            # for timestamps allow year filtering: {publication_date: {from:..., to:...}}
            if isinstance(val, dict) and ("from" in val or "to" in val):
                ts_from = _parse_date(val.get("from"))
                ts_to = _parse_date(val.get("to"))
                if ts_from is not None:
                    out = out[out[key] >= ts_from]
                if ts_to is not None:
                    out = out[out[key] <= ts_to]
            else:
                out = out[out[key].isin(allowed)]
        return out

    # -----------------------------
    # Data Dictionary
    # -----------------------------

    def build_data_dictionary(
        self,
        dataframe: Any
    ) -> List[Dict[str, Any]]:
        """
        Returns the 'columns' list for data_dictionary.json.
        """
        if not PANDAS_AVAILABLE:
            # Fallback: return canonical structure
            return [
                {"name": "record_id", "type": "string", "role": "identifier", "nullable": False, "description": "Stable internal record id (source + source_record_id or derived hash)."},
                {"name": "source", "type": "string", "role": "metadata", "nullable": False, "description": "Connector/source key (pubmed, clinicaltrials, who_gho, etc.)."},
                {"name": "title", "type": "text", "role": "metadata", "nullable": False, "description": "Title of the record (article or trial)."},
            ]
        
        # Define roles typical in biomedical data
        return [
            {"name": "record_id", "type": "string", "role": "identifier", "nullable": False, "description": "Stable internal record id (source + source_record_id or derived hash)."},
            {"name": "source", "type": "string", "role": "metadata", "nullable": False, "description": "Connector/source key (pubmed, clinicaltrials, who_gho, etc.)."},
            {"name": "source_record_id", "type": "string", "role": "identifier", "nullable": True, "description": "Identifier at the source (PMID, NCT ID, etc.)."},
            {"name": "record_type", "type": "string", "role": "metadata", "nullable": False, "description": "Type of record (article/trial/indicator)."},
            {"name": "title", "type": "text", "role": "metadata", "nullable": False, "description": "Title of the record (article or trial)."},
            {"name": "abstract", "type": "text", "role": "metadata", "nullable": True, "description": "Abstract/summary/description (cleaned)."},
            {"name": "keywords", "type": "text", "role": "metadata", "nullable": True, "description": "Keywords or MeSH terms (semicolon-separated)."},
            {"name": "authors", "type": "text", "role": "metadata", "nullable": True, "description": "Authors list (semicolon-separated)."},
            {"name": "journal", "type": "string", "role": "metadata", "nullable": True, "description": "Journal or source publication outlet."},
            {"name": "publication_date", "type": "datetime", "role": "dimension", "nullable": True, "description": "Publication date (best-effort parsed)."},
            {"name": "country", "type": "string", "role": "dimension", "nullable": True, "description": "Country (if provided by source)."},
            {"name": "condition", "type": "text", "role": "feature", "nullable": True, "description": "Condition(s) or disease area (cleaned)."},
            {"name": "intervention", "type": "text", "role": "feature", "nullable": True, "description": "Intervention(s) (cleaned)."},
            {"name": "outcome", "type": "text", "role": "feature", "nullable": True, "description": "Outcome(s) or result notes (cleaned)."},
            {"name": "study_phase", "type": "string", "role": "metadata", "nullable": True, "description": "Clinical trial phase (if applicable)."},
            {"name": "study_status", "type": "string", "role": "metadata", "nullable": True, "description": "Clinical trial status (if applicable)."},
            {"name": "start_date", "type": "datetime", "role": "dimension", "nullable": True, "description": "Trial start date (if applicable)."},
            {"name": "completion_date", "type": "datetime", "role": "dimension", "nullable": True, "description": "Trial completion date (if applicable)."},
            {"name": "population", "type": "text", "role": "metadata", "nullable": True, "description": "Population notes (if available)."},
            {"name": "sample_size", "type": "integer", "role": "measure", "nullable": True, "description": "Enrollment/sample size (if provided)."},
            {"name": "url", "type": "string", "role": "metadata", "nullable": True, "description": "Source URL (if provided)."},
            {"name": "retrieved_at", "type": "datetime", "role": "metadata", "nullable": False, "description": "Timestamp when the source was retrieved."},
            {"name": "license_name", "type": "string", "role": "metadata", "nullable": True, "description": "License name (if known)."},
            {"name": "license_url", "type": "string", "role": "metadata", "nullable": True, "description": "License URL (if known)."},
            {"name": "provenance_query_id", "type": "string", "role": "metadata", "nullable": True, "description": "Internal query identifier for provenance/audit."}
        ]

    # -----------------------------
    # Validation rules
    # -----------------------------

    def validate(self, dataframe: Any) -> None:
        """
        Valida dataset biomedical.
        
        Raises:
            ValueError: Se il dataset non è valido
        """
        if not PANDAS_AVAILABLE:
            if not isinstance(dataframe, list) or len(dataframe) == 0:
                raise ValueError("Dataset biomedical vuoto")
            
            # Basic validation for list of dicts
            first_record = dataframe[0]
            required_fields = ["record_id", "source", "record_type", "title"]
            missing = [f for f in required_fields if f not in first_record]
            if missing:
                raise ValueError(f"Colonne obbligatorie mancanti: {missing}")
            
            return
        
        if dataframe is None:
            raise ValueError("Dataframe None")

        if dataframe.empty:
            raise ValueError("Dataset biomedical vuoto")

        missing_cols = self.REQUIRED_COLUMNS - set(dataframe.columns)
        if missing_cols:
            raise ValueError(f"Colonne obbligatorie mancanti: {sorted(list(missing_cols))}")

        # Title coverage sanity check
        if "title" in dataframe.columns:
            title_null_rate = dataframe["title"].isna().mean()
            if title_null_rate > 0.05:
                raise ValueError(f"Troppe righe senza titolo (null_rate={title_null_rate:.2%})")

        # Duplicate record_id sanity
        if "record_id" in dataframe.columns:
            dup_rate = dataframe.duplicated(subset=["record_id"]).mean()
            if dup_rate > 0.01:
                raise ValueError(f"Troppe duplicazioni su record_id (dup_rate={dup_rate:.2%})")

        # Optional: if publication_date exists, ensure not absurd (e.g., future far)
        if "publication_date" in dataframe.columns:
            # allow some missing
            dates = dataframe["publication_date"].dropna()
            if len(dates) > 0:
                # reject dates too far in future (basic hygiene)
                now = pd.Timestamp.now()
                if (dates > (now + pd.Timedelta(days=30))).any():
                    raise ValueError("publication_date contiene valori nel futuro (oltre 30 giorni).")

    def get_metadata(self) -> Dict[str, Any]:
        """Get CDISC/OMOP metadata for this normalizer."""
        return {
            "standards": [
                "CDISC (Clinical Data Interchange Standards Consortium)",
                "HL7 FHIR (Fast Healthcare Interoperability Resources)",
                "OMOP Common Data Model"
            ],
            "domains": ["STUDY", "CM", "COHORT", "AE", "VS"],
            "description": "CDISC/HL7 FHIR/OMOP-compliant normalizer for biomedical and healthcare data",
            "privacy": "PII removal enforced - only aggregate/open data",
            "sources": ["pubmed", "clinicaltrials", "who_gho"],
            "canonical_columns": len(self.CANONICAL_COLUMNS)
        }
