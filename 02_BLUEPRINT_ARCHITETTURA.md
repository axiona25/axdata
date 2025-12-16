# Blueprint Architetturale & Applicativo — Dataset On-Demand Portal

## 1) Architettura logica (componenti)
1. **Frontend (React + TS)**: auth, dashboard, chat, progress pipeline, storico, billing.
2. **Backend (Python FastAPI)**: API gateway, orchestrazione dataset, OpenAI integration, pagamenti, fatture, ACL.
3. **Collector service (Python)**: connettori verso fonti esterne, rate-limit, retry, output standard.
4. **PostgreSQL**: metadata + pipeline steps + billing + audit.
5. **Object Storage** (MinIO dev / S3 compatibile prod): raw assets, bundle dataset, PDF fatture.
6. **Queue/Workers** (Redis + Celery/Dramatiq/RQ): job lunghi.

---

## 2) Stack tecnologico (vincolante) — DigitalOcean Ready
### Backend
- FastAPI, Pydantic v2
- SQLAlchemy 2 + Alembic
- Redis + Celery (o Dramatiq) con workers separati
- Auth JWT + refresh, password hashing (argon2/bcrypt)
- OpenAI API: chat + tool calling (DatasetPlan)
- Storage: **boto3** (S3-compatible) - MinIO (dev) / DigitalOcean Spaces (prod)
- **Tutto configurabile via env vars per plug-and-play dev→prod**

### Frontend
- React + Vite + TypeScript
- shadcn/ui + Tailwind
- TanStack Query
- Routing (React Router)

### Pagamenti
- Stripe Checkout + Webhooks (idempotenti)
- PayPal opzionale (integrazione separata)

---

## 3) Moduli applicativi (backend)
- `auth`: register/login/refresh/logout/reset/me
- `users`: profile update, preferences, delete
- `chat`: sessions + messages + streaming
- `datasets`: create request from plan, pipeline orchestration, status/progress, downloads
- `collector_proxy`: API interne verso collector, mapping errori e audit
- `billing`: checkout, webhook, invoices/receipts
- `storage`: signed urls, bundle management
- `audit`: audit log e trace ids

---

## 4) API Collector (moduli)
- `connectors/`: registry + adapters (worldbank, eurostat, pubmed, ...)
- `client/`: httpx + tenacity retry + rate limiting
- `schemas/`: output standard records + metadata + provenance
- `tasks/`: esecuzione steps (collect) + persist raw assets

---

## 5) Schema DB (alto livello)
Tabelle minime:
- `users`, `user_profiles`
- `chat_sessions`, `chat_messages`
- `connectors`
- `dataset_requests` (status: draft/running/ready_for_payment/paid/failed)
- `dataset_steps` (collect/normalize/export)
- `raw_assets`
- `final_datasets`
- `payments`
- `invoices`
- `audit_logs`

---

## 6) Contratto OpenAI → sistema: DatasetPlan JSON
L'assistente deve produrre un oggetto strutturato:
- domain (economics/biomedical/physics/math/demography)
- sources[]: connector + queries
- transformations[]: normalize/join/dedup/missing
- outputs[]: csv/json/parquet
- documentation: manifest + dictionary

Esempio:
```json
{
  "domain": "economics",
  "title": "Inflation and GDP EU 2000-2024",
  "sources": [{"connector":"eurostat","queries":[{"dataset_code":"prc_hicp_midx","filters":{"geo":["IT","FR"],"time":["2000","2024"]}}]}],
  "transformations": [{"type":"normalize_dates"},{"type":"join","on":["geo","time"]}],
  "outputs": ["csv","parquet","json"],
  "documentation": {"include_manifest": true, "include_data_dictionary": true}
}
```

---

## 7) Struttura repository (monorepo consigliato)
```
portal/
  apps/
    backend/
    collector/
    frontend/
  packages/
    shared/
  infra/
  docs/
  docker-compose.yml
```

---

## 8) Flussi end-to-end
### Flusso A: Dataset via chat
1) Chat → DatasetPlan
2) Salvataggio dataset_request + steps
3) Queue jobs: collect → normalize → export
4) Stato `ready_for_payment`
5) Checkout → webhook → `paid`
6) Bundle finale + invoice PDF
7) Download da storico

### Flusso B: Account deletion
- Soft delete + revoke sessions + cancel subs (se presenti) + purge schedulato

---

## 9) Prompt operativo (da incollare in Cursor dopo questa doc)
**Obiettivo:** costruire un portale web “Dataset On-Demand” con backend FastAPI + PostgreSQL + Redis/Celery + object storage, frontend React TS, collector service separato e chat OpenAI per generare DatasetPlan e orchestrare pipeline (collect→normalize→export→pay→deliver). Implementare MVP con 3 connector (WorldBank, Eurostat, PubMed), export CSV/JSON/Parquet, pagamenti Stripe Checkout e storico dataset/fatture per utente.
