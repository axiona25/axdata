# 🌍 Implementazione Standard Globali per Dataset

## 📋 Riepilogo
Sistema completamente aggiornato per seguire gli standard globali accademici e rendere i dataset **FAIR-compliant** (Findable, Accessible, Interoperable, Reusable).

## ✅ Standard Implementati

### 1. **Economics** - SDMX (Statistical Data and Metadata eXchange)
**Standard #1 al mondo per dati economici e statistici**

- ✅ Usato da: World Bank, IMF, OECD, Eurostat, UN Data, Banche centrali
- ✅ Struttura SDMX:
  - **Dimensions**: time, geo, indicator
  - **Measures**: value (numeric)
  - **Attributes**: unit, frequency, source, notes
- ✅ Normalizzazione:
  - Date/time → SDMX temporal dimension
  - Geographic → ISO 3166
  - Indicator standardization
  - Time series join
- ✅ Validazione: Richiede measure (value) e temporal dimension

**File**: `apps/backend/normalizers/economics.py`

### 2. **Biomedical** - CDISC/HL7 FHIR/OMOP
**Standard per dati sanitari e studi clinici**

- ✅ **CDISC**: Clinical Data Interchange Standards Consortium (FDA/EMA)
- ✅ **HL7 FHIR**: Fast Healthcare Interoperability Resources
- ✅ **OMOP**: Observational Medical Outcomes Partnership
- ✅ Struttura:
  - Record-based (ogni riga = evento/studio/osservazione)
  - CDISC domains: STUDY, CM, COHORT, AE, VS
  - OMOP structure per studi osservazionali
- ✅ Privacy: **PII removal enforced** (solo dati aggregati/open)
- ✅ Deduplicazione critica

**File**: `apps/backend/normalizers/biomedical.py`

### 3. **Physics/Nature** - FAIR Data Principles / NetCDF
**Standard per dati ambientali e fisici**

- ✅ **FAIR Principles**: Findable, Accessible, Interoperable, Reusable
- ✅ **NetCDF/HDF5**: Per dati ambientali/climatologia
- ✅ **CERN Open Data Model**: Per esperimenti fisici
- ✅ Struttura:
  - Experiment/mission-based
  - Coordinate spaziali e temporali
  - Multi-file support (bundles)
- ✅ Metadata forti richiesti

**File**: `apps/backend/normalizers/physics.py`

### 4. **ML/Math** - OpenML / UCI ML Repository
**Standard per dataset machine learning**

- ✅ **OpenML Standard**: ML datasets, benchmarking
- ✅ **UCI ML Repository conventions**: Standard de facto accademico
- ✅ Struttura:
  - Features (variabili indipendenti)
  - Target (variabile dipendente/label)
  - Task: classification, regression, clustering
- ✅ Feature engineering support
- ✅ Train/test split (opzionale)

**File**: `apps/backend/normalizers/ml_math.py`

### 5. **Demography** - UN SDG / Eurostat
**Standard per statistiche demografiche e sociali**

- ✅ **UN SDG Metadata**: Sustainable Development Goals
- ✅ **Eurostat demographic model**
- ✅ **ISO 3166**: Countries
- ✅ **ISO 4217**: Currencies
- ✅ Struttura:
  - Dimensions: geo, year, indicator
  - Optional: age_group, sex
  - Multidimensional demographic data
- ✅ Validazione: Richiede geo, temporal, e measure

**File**: `apps/backend/normalizers/demography.py`

## 📦 Manifest FAIR-Compliant

Il manifest generato include sempre:

```json
{
  "title": "...",
  "dataset_id": "...",
  "domain": "...",
  "version": "1.0",
  "created_at": "...",
  
  "sources": [...],
  "transformations": [...],
  
  "row_count": 1234,
  "outputs": ["csv", "json", "parquet"],
  
  "methodology": "...",
  "license": "...",
  "citation": "...",
  "geographic_coverage": "...",
  "temporal_coverage": "...",
  
  "standards": {
    "fair_compliant": true,
    "domain_standard": "SDMX / CDISC / FAIR / OpenML / UN SDG"
  },
  
  "format_version": "2.0",
  "manifest_schema": "FAIR-Dataset-Manifest-v2.0"
}
```

## 📊 Data Dictionary Completo

Il data dictionary include:

- **Column name, type, description**
- **Unit of measurement**
- **Domain-specific metadata**:
  - Economics: SDMX dimensions (geographic, temporal, measure)
  - Biomedical: CDISC domains
  - ML: Feature/target roles, task type
- **Statistics** per colonne numeriche
- **Validation rules**

## 🔗 Provenance Completo

Il provenance include:

- **Source information**: Connector, queries, row count
- **Transformations**: Tipo, parametri, timestamp
- **Lineage**: Raw data → Normalization → Export
- **Metadata**: Storage paths, collection timestamps

## 📁 Bundle Structure

Ogni dataset bundle include:

1. **Data files**:
   - `{dataset_id}.csv`
   - `{dataset_id}.json`
   - `{dataset_id}.parquet`

2. **Documentation** (FAIR-compliant):
   - `manifest.json` - Metadata completo
   - `data_dictionary.json` - Definizioni colonne
   - `provenance.json` - Lineage completo
   - `README.md` - Documentazione scientifica (per physics/math)

## 🎯 FAIR Compliance

Tutti i dataset sono **FAIR-compliant**:

- ✅ **Findable**: Rich metadata, persistent identifiers (dataset_id)
- ✅ **Accessible**: Standard protocols, authentication
- ✅ **Interoperable**: Standard formats (CSV, JSON, Parquet), vocabularies
- ✅ **Reusable**: Clear licenses, detailed provenance, methodology

## 🚀 Come Usare

### Nel DatasetPlan

```python
plan = DatasetPlan(
    domain=Domain.ECONOMICS,  # o BIOMEDICAL, PHYSICS, MATH, DEMOGRAPHY
    title="GDP Growth by Country",
    sources=[...],
    transformations=[...],
    methodology="Data collected from World Bank API and normalized to SDMX structure",
    license="CC BY 4.0",
    citation="World Bank. GDP Growth Dataset. 2024.",
    geographic_coverage="Global",
    temporal_coverage="2000-2023",
    indicators_metadata={
        "gdp_growth": {
            "description": "Annual GDP growth rate",
            "unit": "%",
            "notes": "Year-over-year percentage change"
        }
    }
)
```

### Normalizer Automatico

Il sistema seleziona automaticamente il normalizer corretto in base al `domain`:

```python
normalizer = get_normalizer("economics")  # → SDMX normalizer
normalizer = get_normalizer("biomedical")  # → CDISC/OMOP normalizer
normalizer = get_normalizer("physics")     # → FAIR normalizer
normalizer = get_normalizer("math")        # → OpenML normalizer
normalizer = get_normalizer("demography")  # → UN SDG normalizer
```

## 📚 Riferimenti Standard

- **SDMX**: https://sdmx.org/
- **CDISC**: https://www.cdisc.org/
- **HL7 FHIR**: https://www.hl7.org/fhir/
- **OMOP**: https://www.ohdsi.org/
- **FAIR**: https://www.go-fair.org/
- **OpenML**: https://www.openml.org/
- **UN SDG**: https://unstats.un.org/sdgs/

## ✅ Benefici

Implementando questi standard, il portale è:

1. ✅ **Vendibile**: Standard riconosciuti a livello mondiale
2. ✅ **Accademicamente legittimo**: Conforme agli standard accademici
3. ✅ **Superiore a tool ETL generici**: Domain-specific, FAIR-compliant
4. ✅ **Interoperabile**: Dati utilizzabili in tool standard
5. ✅ **Citabile**: Metadata completo per pubblicazioni

**Il sistema è ora accademicamente accettato e interoperabile!** 🎓🌍

