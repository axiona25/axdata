# 🎯 Prompt Master - Dataset On-Demand Portal

**Prompt unico da incollare in Cursor per sviluppo completo del progetto**

---

## 📋 PROMPT MASTER

```
SEI CURSOR (AI coding agent). Devi realizzare un portale web "Dataset On-Demand" con architettura a 3 ruoli: LLM (chat) → Backend (orchestratore + normalizzatori + billing) → API Collector (unico punto di accesso alle fonti pubbliche). Il backend NON deve mai chiamare direttamente le fonti esterne. Solo il Collector lo fa.

OBIETTIVO PRODOTTO

- Utente (ricercatore) crea account, apre chat, descrive dataset desiderato (settore, periodo, geografia, variabili, output).
- LLM interpreta la richiesta e genera un DatasetPlan v1.0 (JSON validabile).
- Backend valida il plan, crea una dataset_request, orchestration pipeline (collect → normalize → export → ready_for_payment).
- Pagamento online (Stripe come primary: Apple Pay/Google Pay/Visa/Mastercard; PayPal opzionale; Revolut via gateway o futura estensione).
- Solo dopo pagamento confermato da webhook idempotente: backend genera bundle finale scaricabile (CSV/JSON/Parquet + manifest + data_dictionary + provenance + README) e rilascia signed URL.
- Storico utente: elenco dataset, stati, download, fatture/ricevute.

STACK VINCOLANTE

- Backend: FastAPI + Pydantic v2 + SQLAlchemy 2 + Alembic + Redis + Celery (o Dramatiq) + S3-compatible storage (MinIO in dev).
- Frontend: React + Vite + TypeScript + Tailwind + shadcn/ui + TanStack Query + SSE/WebSocket.
- DB: PostgreSQL.
- Object storage: MinIO (dev) / S3/DO Spaces (prod).
- Pagamenti: Stripe Checkout + Webhooks idempotenti. PayPal opzionale.
- OpenAI: chat + tool calling. LLM NON accede ai dati esterni.

RESPONSABILITÀ (REGOLE D'ORO)

1) API COLLECTOR
   - Unico servizio che interroga fonti pubbliche.
   - Deve supportare connettori per settori multipli. MVP minimo: eurostat, worldbank, pubmed (poi clinicaltrials, who_gho, imf, oecd, un_data, istat, openml, cern_opendata, nasa_opendata, pangaea, ecc.).
   - Deve esporre un'API uniforme: `collect(connector, query_id, params)` → {records, metadata, provenance, retrieved_at}.
   - Retry, rate-limit, paginazione, caching, logging, audit.

2) LLM (CHAT)
   - Interpreta la richiesta dell'utente.
   - Produce SOLO DatasetPlan v1.0 (JSON valido) e invoca tools backend.
   - Non inventa fonti, non inventa dati, non costruisce URL tecnici se non richiesto dal connector.
   - Usa SOLO connettori "available_connectors" passati dal backend.

3) BACKEND
   - Auth utenti, chat sessions/messages, dataset_requests/steps, billing, invoices, storage signed URL.
   - Orchestration pipeline asincrona (queue workers).
   - Normalizzazione per dominio via Normalizers Python (BaseNormalizer + registry).
   - Produce dataset secondo standard internazionali (FAIR + manifest universale v1.0 + data dictionary v1.0; economics SDMX-like; biomedical record/study-based).
   - Mai chiamare fonti pubbliche direttamente.

4) PAGAMENTO E CONSEGNA
   - Dataset scaricabile SOLO quando `payment_status = paid`.
   - Webhook idempotenti (unique constraint su provider_ref, lock/transaction).
   - Generazione fattura/ricevuta PDF e archiviazione.

ARTEFATTI STANDARD (OBBLIGATORI IN OGNI DATASET)

- `manifest.json` (Manifest Universale v1.0, schema validabile)
- `data_dictionary.json` (Data Dictionary v1.0, schema validabile)
- `provenance.json` (fonti, query, timestamp, request_hash, licenze)
- `README.txt` (descrizione e citazione)
- Dati: CSV/JSON/Parquet (almeno uno, secondo outputs del plan)
- Bundle ZIP (default)

CONTRATTI (SCHEMI)

- DatasetPlan v1.0: plan_version, domain, sources[{connector, queries[{query_id, params, pagination?}]}], transformations?, outputs, documentation{include_manifest, include_data_dictionary...}.
- CollectorResponse v1.0: connector, query_id, retrieved_at, records[], metadata{row_count, bytes}, provenance{source_name, base_url, license?, request_hash, params_snapshot}.
- Manifest v1.0 + DataDictionary v1.0 come definito nei documenti.

REPOSITORY (MONOREPO)

portal/
  apps/
    backend/
    collector/
    frontend/
  packages/
    shared/
  docs/
  infra/
  docker-compose.yml

MILESTONE OPERATIVE (DEVONO ESSERE ESEGUITE IN ORDINE)

M0 Bootstrap
- docker-compose (postgres, redis, minio), backend/collector/frontend healthcheck

M1 Auth & Profile
- users + JWT + profile UI

M2 Chat + OpenAI planning
- chat sessions/messages, SSE streaming, tool create_dataset_plan, validazione JSON schema

M3 Dataset orchestration skeleton
- dataset_requests/steps, queue, progress events

M4 Collector connectors MVP
- eurostat + worldbank + pubmed con output standard + raw assets su storage

M5 Normalization + Export
- EconomicsNormalizer + BiomedicalNormalizer, export CSV/JSON/Parquet, manifest/dictionary/provenance

M6 Payments
- Stripe Checkout + webhook idempotenti, gating download

M7 Invoices/Receipts
- PDF, numerazione, UI elenco

M8 Lifecycle
- delete account (soft + purge), cancel subscription (se presente)

DONE CRITERIA

- Un utente crea account, chat → plan → pipeline produce dataset → ready_for_payment → paga → download bundle → vede fattura → storico completo → può cancellare account.

ISTRUZIONI DI IMPLEMENTAZIONE (IMPORTANTI)

- Usa API versioning: /api/v1/...
- Ogni endpoint verifica ownership (multi-tenant logico).
- Job lunghi sempre asincroni (Celery).
- Download solo signed URL (scadenza configurabile).
- Logging per step e trace_id.
- Scrivi `.env.example` per backend/collector/frontend.
- Scrivi almeno smoke test (pytest) su: plan validation, state machine, webhook idempotency.

INIZIA ORA:

1) Genera la struttura monorepo e docker-compose.
2) Crea backend FastAPI con auth e DB migrations.
3) Crea collector FastAPI con registry connectors (stub + 1 connettore reale).
4) Crea frontend React con pagine: auth, chat, datasets list/detail, billing, profile.
Procedi milestone per milestone, committando output coerenti.
```

---

## 📚 Documenti di Riferimento

- [README.md](./README.md) - Documentazione completa del progetto
- [CollectorResponse Schema](./apps/collector/schemas/collector_response.json) - Schema JSON per risposte collector
- [CollectorRequest Schema](./apps/collector/schemas/collector_request.json) - Schema JSON per richieste collector
- [Manifest Schema](./apps/backend/schemas/manifest_schema.json) - Schema Manifest Universale v1.0
- [Standards Implementation](./STANDARDS_IMPLEMENTATION.md) - Standard globali implementati

---

## ✅ Stato Implementazione

### Backend ✅ COMPLETO
- ✅ Auth & Users
- ✅ Chat + OpenAI Integration
- ✅ Dataset Orchestration
- ✅ Normalizers (Economics, Biomedical, Physics, Math, Demography)
- ✅ Export & Bundle Generation
- ✅ Payments (Stripe)
- ✅ Invoices/Receipts
- ✅ Audit Logs
- ✅ Manifest Universale v1.0
- ✅ Data Dictionary v1.0
- ✅ Provenance tracking

### Collector ✅ MVP COMPLETO
- ✅ Registry-based connectors
- ✅ Eurostat connector
- ✅ World Bank connector
- ✅ PubMed connector
- ✅ Standard response format
- ✅ Retry & rate limiting
- ✅ Storage integration

### Frontend ⏳ PENDING
- ⏳ React + Vite setup
- ⏳ Auth UI
- ⏳ Chat interface
- ⏳ Dataset list/detail
- ⏳ Billing UI
- ⏳ Profile management

---

**Il backend è completo e testato. Pronto per integrazione frontend.**

