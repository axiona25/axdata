# AXDATA Dataset Standardization System

Sistema completo per la creazione di dataset standardizzati secondo 8 template universali, conforme agli standard FAIR e DCAT.

## Architettura

### Componenti principali

1. **DS-SPEC v1** (`axdata/spec/`)
   - Specifica dataset standardizzata
   - Modelli Pydantic per validazione
   - Schema JSON per documentazione

2. **Source Selection Engine** (`axdata/engine/source_selection.py`)
   - Selezione automatica delle fonti basata su DS-SPEC
   - Filtro per settore, geografia, licenza
   - Ranking per autorità e affidabilità

3. **Template Decision Engine** (`axdata/engine/template_decider.py`)
   - Selezione automatica del template (1 di 8)
   - Basato su dimensioni temporali, geografiche, entità

4. **Pipeline Orchestrator** (`axdata/pipeline/run_pipeline.py`)
   - Flusso unico per tutti i template
   - Integrazione con collector service
   - Gestione raw data

5. **Packaging** (`axdata/packaging/`)
   - Metadata builder (DCAT/FAIR)
   - Schema generator
   - Compliance builder
   - README builder
   - Packager completo (ZIP)

6. **Cross-validation** (`axdata/quality/cross_validate.py`)
   - Validazione tra fonti multiple
   - Correlazione e outlier detection

## 8 Template Supportati

1. **Tabular** - Dataset tabellare standard
2. **Time Series** - Dati temporali
3. **Cross-Sectional** - Snapshot temporale
4. **Panel/Longitudinal** - Stessi soggetti nel tempo
5. **Geospatial** - Dati con coordinate
6. **Text/Document** - Dataset testuali
7. **Event-Based** - Eventi discreti
8. **Hybrid/Knowledge-Enriched** - Dato + semantica LLM

## Utilizzo

### Creare dataset da DS-SPEC

```python
from axdata.spec.ds_spec import DatasetSpec
from axdata.pipeline.run_pipeline import run

# Crea DS-SPEC
ds_spec = DatasetSpec(
    request={
        "query_text": "Incidenza diabete in Europa 2015-2024",
        "language": "it"
    },
    sector="health",
    dimensions={
        "time": {"enabled": True, "start": "2015", "end": "2024"},
        "geo": {"enabled": True, "scope": "EU"},
        "entity": {"kind": "country"}
    },
    variables=[{"name": "diabetes_incidence", "type": "numeric"}]
)

# Esegui pipeline
result = run(ds_spec)
```

### Via API

```bash
POST /api/v1/datasets/from-ds-spec
{
  "ds_spec": {
    "version": "1.0",
    "request": {
      "query_text": "Incidenza diabete in Europa",
      "language": "it"
    },
    "sector": "health",
    "dimensions": {...},
    "variables": [...]
  }
}
```

## Source Manifests

I manifest delle fonti sono in `axdata/sources/manifests/`.

Ogni manifest definisce:
- Settori coperti
- Tipi di dato supportati
- Copertura geografica e temporale
- Licenza
- Autorità e affidabilità

## Output Standard

Ogni dataset generato contiene:

```
dataset_package/
  data/
    dataset.csv (o parquet/json/geojson)
  schema.json
  metadata.json (DCAT/FAIR)
  provenance.json
  compliance.json
  README.md
  quality.json (opzionale)
```

## Integrazione con Backend

Il servizio `services/axdata_service.py` integra la pipeline AXDATA con:
- Sistema di autenticazione
- Package management
- Storage service
- Audit logs

## Note

- La pipeline usa un flusso unico fino al 70%, poi si ramifica in 8 template
- Le fonti vengono selezionate automaticamente, non dall'utente
- Il template viene proposto automaticamente, con possibilità di override
- Tutti i dataset sono conformi FAIR e DCAT
