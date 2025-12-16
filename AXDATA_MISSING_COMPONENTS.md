# Componenti Mancanti - Sistema AXDATA

## ✅ Completato

1. **DS-SPEC v1** - Schema e modelli Pydantic ✅
2. **Source Selection Engine** - Filtro e ranking fonti ✅
3. **Template Decision Engine** - Auto-selezione 8 template ✅
4. **Source Manifests** - 26 manifest completi ✅
5. **Packaging** - Metadata, Schema, Compliance, README, Packager ✅
6. **Cross-validation** - Validazione tra fonti ✅
7. **Integrazione backend** - Endpoint `/from-ds-spec` ✅
8. **Test completi** - 49 test passati ✅

## ❌ Componenti Mancanti

### 1. Template Transformers (CRITICO)
**Cosa manca**: Logica per trasformare dati raw nei 8 template

**Dove**: `axdata/transformers/` (da creare)

**Cosa serve**:
- `tabular_transformer.py` - Flatten, join, 1 riga = 1 osservazione
- `time_series_transformer.py` - Identifica timestamp, ordina, gap handling
- `panel_transformer.py` - Entity tracking, costruzione entity_id + time
- `cross_sectional_transformer.py` - Filtro su 1 istante, collassa tempo
- `geospatial_transformer.py` - Arricchimento coordinate, CRS normalization
- `text_transformer.py` - Estrazione full-text, metadata enrichment
- `event_transformer.py` - Event detection, timestamp univoco
- `hybrid_transformer.py` - NER, linking ontologico, semantic tags

**Stato attuale**: Il template viene deciso, ma i dati non vengono trasformati nel formato del template.

---

### 2. Integrazione Reale con Collector (IMPORTANTE)
**Cosa manca**: `fetch_from_source` è ancora uno stub

**Dove**: `axdata/pipeline/run_pipeline.py:23`

**Cosa serve**:
- Chiamata reale al collector service (`/collect` endpoint)
- Oppure uso diretto dei connector dal registry
- Gestione errori e retry
- Parsing risposte collector

**Stato attuale**: Restituisce dati mock.

---

### 3. Worker Task per Pipeline AXDATA (IMPORTANTE)
**Cosa manca**: Task Celery che esegue la pipeline completa

**Dove**: `workers/tasks.py` (da aggiungere)

**Cosa serve**:
- `process_axdata_dataset_request(dataset_id)` task
- Esegue: collect → normalize → transform → package
- Aggiorna status dataset
- Gestisce errori

**Stato attuale**: L'endpoint crea il dataset ma non c'è un task che processa la pipeline.

---

### 4. Normalizzazione Template-Specific (MEDIO)
**Cosa manca**: Dopo la normalizzazione domain-specific, serve trasformazione template-specific

**Dove**: Dopo `normalizers/`, prima di `packaging/`

**Cosa serve**:
- Bridge tra normalizer (domain) e transformer (template)
- Applica trasformazioni template dopo normalizzazione
- Mantiene tracciabilità

**Stato attuale**: I normalizer esistono ma non sono integrati con i template transformers.

---

### 5. Quality Checks Avanzati (OPZIONALE)
**Cosa manca**: Quality checks dopo trasformazione

**Dove**: `axdata/quality/` (parzialmente fatto)

**Cosa serve**:
- Completeness check
- Consistency check
- Outlier detection
- Schema validation

**Stato attuale**: Solo cross-validation tra fonti.

---

### 6. Documentazione API (OPZIONALE)
**Cosa manca**: Documentazione OpenAPI migliorata per `/from-ds-spec`

**Dove**: `api/routers/datasets.py`

**Cosa serve**:
- Esempi di DS-SPEC
- Descrizioni dettagliate
- Error responses documentati

**Stato attuale**: Endpoint funziona ma documentazione base.

---

## Priorità di Implementazione

### 🔴 Alta Priorità (Blocca funzionalità)
1. **Template Transformers** - Senza questi i dati non vengono trasformati
2. **Integrazione Collector** - Senza questo non si raccolgono dati reali
3. **Worker Task** - Senza questo la pipeline non viene eseguita

### 🟡 Media Priorità (Migliora qualità)
4. **Normalizzazione Template-Specific** - Migliora qualità output
5. **Quality Checks** - Migliora affidabilità

### 🟢 Bassa Priorità (Nice to have)
6. **Documentazione API** - Migliora developer experience

---

## Note

- Il sistema è **architetturalmente completo** ✅
- I componenti core sono **testati** ✅
- Manca l'**implementazione della trasformazione dati** ❌
- Manca l'**integrazione operativa** con collector e workers ❌
