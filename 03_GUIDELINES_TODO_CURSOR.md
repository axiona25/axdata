# Linee guida di sviluppo + TODO list eseguibile (Cursor)

## 0) Regole di ingegneria (vincolanti)
- Monorepo con `apps/backend`, `apps/collector`, `apps/frontend`, `packages/shared`.
- Ogni API deve avere:
  - validation Pydantic
  - error model coerente
  - logging con trace_id
- I job lunghi devono passare in queue (mai bloccare la request).
- Tutti i download devono usare **signed URL** e controllo ownership.
- Webhook pagamenti: **idempotenti** (chiave idempotenza + unique constraint su provider_ref).
- Ogni dataset deve includere: `manifest.json` + `data_dictionary.json` + provenance.

---

## 1) Convenzioni di codice
### Backend (FastAPI)
- Struttura:
  - `api/routers/*`
  - `core/config.py` (env)
  - `core/security.py`
  - `db/models/*`, `db/session.py`, `db/migrations`
  - `services/*` (business logic)
  - `workers/*` (celery tasks)
- API versioning: `/api/v1/...`
- Test: pytest (smoke + unit su plan parsing e pipeline state machine)

### Collector
- Pattern plugin:
  - `connectors/base.py` (interface)
  - `connectors/registry.py`
  - `connectors/worldbank.py`, `eurostat.py`, `pubmed.py`
- Output standard:
  - `records: list[dict]`
  - `metadata: dict`
  - `provenance: {source, query, retrieved_at, license?, url?}`

### Frontend
- Routing:
  - `/auth/*`
  - `/app/chat`
  - `/app/datasets`
  - `/app/datasets/:id`
  - `/app/billing`
  - `/app/profile`
- State:
  - TanStack Query per API
  - SSE per progress pipeline + streaming chat

---

## 2) Variabili ambiente (template)
Creare `.env.example` per ogni app.

### backend
- DATABASE_URL=
- REDIS_URL=
- S3_ENDPOINT_URL=
- S3_ACCESS_KEY_ID=
- S3_SECRET_ACCESS_KEY=
- S3_BUCKET=
- JWT_SECRET=
- OPENAI_API_KEY=
- STRIPE_SECRET_KEY=
- STRIPE_WEBHOOK_SECRET=

### collector
- REDIS_URL=
- DATABASE_URL= (se scrive metadata direttamente) oppure usa backend API
- EXTERNAL_API_KEYS_* (quando necessario)

### frontend
- VITE_API_BASE_URL=

---

## 3) Modello stati dataset (state machine)
`dataset_requests.status`:
- `draft` → `running` → `ready_for_payment` → `paid` → `delivered`
- error: `failed`

`dataset_steps.status`:
- `queued` → `running` → `success` | `failed`

---

## 4) TODO list per milestone (con output verificabile)

### Milestone 0 — Bootstrap
- [ ] docker-compose: postgres, redis, minio
- [ ] backend FastAPI + /health
- [ ] collector + /health
- [ ] frontend Vite + routing base

**Criterio Done:** `docker compose up` avvia tutto e healthcheck ok.

### Milestone 1 — Auth & Profile
- [ ] users tables + alembic
- [ ] register/login/refresh/logout/me/update
- [ ] UI auth + profile

**Criterio Done:** utente si registra, effettua login, vede e modifica profilo.

### Milestone 2 — Chat + OpenAI (planning)
- [ ] chat_sessions/messages
- [ ] endpoint streaming chat (SSE)
- [ ] tool schema `create_dataset_plan` e validazione JSON
- [ ] UI chat streaming + persistenza

**Criterio Done:** conversazione salvata e DatasetPlan generato e validato.

### Milestone 3 — Dataset orchestration (skeleton)
- [ ] dataset_requests/steps schema
- [ ] enqueue jobs e progress events
- [ ] UI pagina dataset con stato/progress

**Criterio Done:** dataset_request creato da plan e mostra pipeline states.

### Milestone 4 — Collector connectors MVP
- [ ] connector registry
- [ ] worldbank + eurostat + pubmed
- [ ] raw assets su storage + metadata in DB
- [ ] retry + rate limit base

**Criterio Done:** step collect produce raw_assets e row_count.

### Milestone 5 — Normalization + Export
- [ ] normalizer economics (time series join)
- [ ] normalizer biomedical (record cleanup + dedup base)
- [ ] manifest + data_dictionary
- [ ] export CSV/JSON/Parquet + bundle

**Criterio Done:** bundle completo e scaricabile (in dev: signed URL).

### Milestone 6 — Payments
- [ ] Stripe Checkout dataset singolo
- [ ] webhook idempotente aggiorna `payments` e stato dataset
- [ ] UI checkout + blocco download se non paid

**Criterio Done:** pagamento test → dataset sbloccato e scaricabile.

### Milestone 7 — Invoices/Receipts
- [ ] generazione PDF
- [ ] numerazione documento
- [ ] UI elenco fatture/ricevute e download

**Criterio Done:** PDF generato e linkato al pagamento.

### Milestone 8 — Lifecycle
- [ ] delete account (soft) + purge job
- [ ] cancellation abbonamento (se presente) via provider portal link

**Criterio Done:** account eliminabile e dati non accessibili dopo delete.

---

## 5) Checklist sicurezza & qualità
- [ ] ownership check su ogni dataset/invoice/download
- [ ] rate limit su endpoints pubblici auth
- [ ] input validation su DatasetPlan (schema rigido)
- [ ] audit log su create_dataset, payment_confirm, download
- [ ] logs per step + trace_id su pipeline
