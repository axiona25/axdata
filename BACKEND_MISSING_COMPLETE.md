# Cosa Manca Lato Backend - Analisi Completa

## 📊 Stato Attuale: 90% Completo

Il sistema AXDATA è **operativo e funzionante** per casi base. Tutti i componenti core sono implementati e testati.

---

## ❌ Componenti Mancanti (Priorità)

### 1. 🔴 Integrazione Normalizer → Transformer (CRITICO)

**Problema**: Due flussi separati non integrati

**Flusso Tradizionale** (DatasetPlan):
```
Collect → Normalize (domain) → Export
```

**Flusso AXDATA** (DS-SPEC):
```
Collect → Transform (template) → Package
```

**Cosa serve**: Unificare i flussi
```
Collect → Normalize (domain standard) → Transform (template) → Package
```

**Dove**: `axdata/pipeline/run_pipeline.py`

**Stato**: 
- ✅ Normalizers esistono (economics, biomedical, physics, math, demography)
- ✅ Transformers esistono (8 template)
- ❌ Non integrati nella pipeline AXDATA
- ❌ I normalizers applicano standard di dominio (SDMX, CDISC, FAIR) che vengono persi

**Impatto**: Senza questo, i dataset AXDATA non applicano standard di dominio (SDMX per economics, CDISC per biomedical, ecc.)

**Implementazione richiesta**:
```python
# In run_pipeline.py, dopo collect_raw():
1. Determinare domain da sector (mapping sector → domain)
2. Chiamare normalizer per domain
3. Passare dati normalizzati al transformer
4. Continuare con packaging
```

---

### 2. 🟡 Query Building Intelligente (IMPORTANTE)

**Problema**: Query building da DS-SPEC è semplificata

**Attuale** (`run_pipeline.py:47`):
```python
query = {
    "dataset_code": "default",  # Hardcoded!
    "filters": {}
}
```

**Cosa serve**:
- Estrazione intelligente di `dataset_code` dalle variabili DS-SPEC
- Mapping variabili → indicatori API specifici per connector
- Costruzione query specifiche per ogni connector (Eurostat, World Bank, ecc.)
- Fallback intelligenti se variabile non mappata

**Dove**: `axdata/pipeline/run_pipeline.py:45` (fetch_from_source)

**Stato**: Funziona ma query generiche, potrebbe non recuperare dati corretti

**Esempio mancante**:
```python
# DS-SPEC: variables = [{"name": "gdp_per_capita", "type": "numeric"}]
# Dovrebbe mappare a:
# - Eurostat: dataset_code = "nama_10_gdp" o "tec00001"
# - World Bank: indicator = "NY.GDP.PCAP.CD"
```

**Implementazione richiesta**:
- Creare `axdata/engine/query_builder.py`
- Mapping variabili → indicatori per ogni source
- Fallback intelligente

---

### 3. 🟡 Gestione Errori Robusta (IMPORTANTE)

**Problema**: Gestione errori base, nessun retry nella pipeline AXDATA

**Attuale**:
- `run_pipeline.py:70` usa `httpx.Client(timeout=300.0)` direttamente
- Nessun retry se collector service fallisce
- Nessun circuit breaker per fonti problematiche
- Nessun recovery parziale (se 1 fonte fallisce, tutto fallisce)

**Cosa serve**:
- Retry con exponential backoff (esiste nel collector client ma non usato)
- Circuit breaker per fonti problematiche
- Error recovery parziale (continua con altre fonti se 1 fallisce)
- Error reporting dettagliato

**Dove**: 
- `axdata/pipeline/run_pipeline.py` (fetch_from_source, collect_raw)
- Nota: `apps/collector/client/http_client.py` ha retry con tenacity, ma non è usato nella pipeline

**Stato**: Gestione base presente, ma non robusta per produzione

**Implementazione richiesta**:
```python
# Usare retry logic esistente dal collector client
from collector.client.http_client import make_request_with_retry

# Oppure implementare circuit breaker
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
def fetch_from_source(...):
    ...
```

---

### 4. 🟢 Caching Manifest (OPZIONALE)

**Problema**: Manifest vengono ricaricati ogni volta

**Attuale**: `axdata/sources/loader.py` carica manifest da disco ogni volta

**Cosa serve**:
- Cache in-memory dei manifest
- Invalidazione cache (se manifest modificati)
- Pre-loading all'avvio dell'applicazione

**Dove**: `axdata/sources/loader.py`

**Stato**: Funziona ma non ottimizzato (26 manifest ricaricati ogni request)

**Implementazione richiesta**:
```python
# Cache globale
_manifest_cache: Dict[str, List[Dict]] = {}
_manifest_cache_timestamp: Optional[datetime] = None

def load_manifests(manifest_dir: str | Path) -> List[Dict[str, Any]]:
    # Check cache first
    if _manifest_cache and _manifest_cache_timestamp:
        # Check if files modified
        ...
    # Load and cache
    ...
```

---

### 5. 🟢 Mapping Settore → Domain (OPZIONALE)

**Problema**: DS-SPEC usa "sector" ma normalizers usano "domain"

**Attuale**:
- DS-SPEC: `sector = "health"`
- Normalizer: `domain = "biomedical"`
- Mapping parziale in `axdata_service.py:160` (solo domain → sector, non reverse)

**Cosa serve**:
- Mapping automatico sector → domain (reverse)
- Tabella di conversione completa
- Fallback intelligente

**Dove**: `services/axdata_service.py` o nuovo `axdata/engine/sector_mapper.py`

**Stato**: Mapping manuale presente ma non completo (manca reverse)

**Implementazione richiesta**:
```python
SECTOR_TO_DOMAIN = {
    "health": "biomedical",
    "economy": "economics",
    "physics": "physics",
    "math": "math",
    "society": "demography",
    ...
}
```

---

### 6. 🟢 Documentazione API (OPZIONALE)

**Problema**: Documentazione OpenAPI base

**Cosa serve**:
- Esempi DS-SPEC completi negli endpoint
- Error responses documentati
- Schema examples
- Tutorial passo-passo

**Dove**: `api/routers/datasets.py`

**Stato**: Endpoint funziona, documentazione base

---

### 7. 🟢 Test di Integrazione End-to-End (OPZIONALE)

**Problema**: Test unitari esistono, ma mancano test di integrazione

**Cosa serve**:
- Test end-to-end: DS-SPEC → Pipeline → Package → ZIP
- Test con collector service reale (mock)
- Test con normalizer + transformer insieme

**Dove**: `tests/test_integration.py` (da creare)

**Stato**: Test unitari completi (54 test), mancano test integrazione

---

### 8. 🟢 Validazione Input Robusta (OPZIONALE)

**Problema**: Validazione base presente (Pydantic), ma potrebbe essere più robusta

**Cosa serve**:
- Validazione business logic (es: time range valido, geo scope valido)
- Validazione cross-field (es: se time enabled, start/end richiesti)
- Messaggi di errore più chiari

**Dove**: `axdata/spec/ds_spec.py` (validators Pydantic)

**Stato**: Validazione base presente, potrebbe essere migliorata

---

### 9. 🟢 Monitoring/Logging Avanzato (OPZIONALE)

**Problema**: Logging base presente

**Cosa serve**:
- Structured logging (JSON)
- Metrics (tempo pipeline, record count, error rate)
- Tracing (correlation IDs)
- Alerting su errori critici

**Dove**: Tutto il sistema

**Stato**: Logging base presente, non strutturato

---

## 🎯 Priorità di Implementazione

### 🔴 Critico (Blocca funzionalità avanzata)
1. **Integrazione Normalizer → Transformer** 
   - **Impatto**: Senza questo, dataset AXDATA non applicano standard di dominio
   - **Effort**: Medio (2-3 ore)
   - **Valore**: Alto (qualità dati)

### 🟡 Importante (Migliora qualità/affidabilità)
2. **Query Building Intelligente**
   - **Impatto**: Migliora accuratezza dati recuperati
   - **Effort**: Alto (4-6 ore)
   - **Valore**: Alto (accuratezza)

3. **Gestione Errori Robusta**
   - **Impatto**: Migliora affidabilità in produzione
   - **Effort**: Medio (2-3 ore)
   - **Valore**: Alto (affidabilità)

### 🟢 Opzionale (Nice to have)
4. **Caching Manifest** - Ottimizzazione performance
5. **Mapping Settore → Domain** - Comodità
6. **Documentazione API** - Developer experience
7. **Test Integrazione** - Qualità codice
8. **Validazione Input** - UX
9. **Monitoring/Logging** - Operazioni

---

## 📊 Riepilogo

| Componente | Priorità | Stato | Effort | Impatto |
|------------|----------|-------|--------|---------|
| Normalizer Integration | 🔴 Critico | ❌ Mancante | Medio | Alto |
| Query Building | 🟡 Importante | ⚠️ Base | Alto | Alto |
| Error Handling | 🟡 Importante | ⚠️ Base | Medio | Alto |
| Caching Manifest | 🟢 Opzionale | ⚠️ Non ottimizzato | Basso | Basso |
| Sector Mapping | 🟢 Opzionale | ⚠️ Parziale | Basso | Basso |
| API Docs | 🟢 Opzionale | ⚠️ Base | Basso | Basso |
| Test Integrazione | 🟢 Opzionale | ❌ Mancante | Medio | Medio |
| Validazione | 🟢 Opzionale | ⚠️ Base | Basso | Basso |
| Monitoring | 🟢 Opzionale | ⚠️ Base | Alto | Medio |

---

## 🚀 Raccomandazione

**Per produzione enterprise, implementare in ordine:**

1. ✅ **Integrazione Normalizer → Transformer** (CRITICO)
   - Permette applicazione standard di dominio
   - Migliora qualità dati
   - Effort ragionevole

2. ✅ **Query Building Intelligente** (IMPORTANTE)
   - Migliora accuratezza dati
   - Effort più alto ma valore alto

3. ✅ **Gestione Errori Robusta** (IMPORTANTE)
   - Migliora affidabilità
   - Effort ragionevole

**Il resto può essere fatto iterativamente dopo il lancio.**

---

## ✅ Conclusione

Il sistema è **90% completo e operativo** per casi base.

**Manca principalmente**:
- Integrazione normalizer (per standard di dominio)
- Query building intelligente (per accuratezza)
- Error handling robusto (per affidabilità)

**Tutto il resto è nice-to-have e può essere fatto iterativamente.**
