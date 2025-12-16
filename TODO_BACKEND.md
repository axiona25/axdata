# ✅ TODO List Backend — Dataset On-Demand Portal

## 📋 Stato Generale
- **Focus**: Sviluppo completo backend prima del frontend
- **Metodologia**: Milestone sequenziali con criteri di completamento
- **Stack**: FastAPI, PostgreSQL, Redis, Celery, MinIO/S3, OpenAI, Stripe

---

## 🚀 Milestone 0 — Bootstrap & Infrastruttura

### Struttura Repository
- [ ] Creare struttura monorepo:
  - [ ] `apps/backend/`
  - [ ] `apps/collector/`
  - [ ] `packages/shared/` (opzionale per schemi condivisi)
  - [ ] `infra/` (docker-compose, config)
  - [ ] `docs/`

### Docker Compose
- [ ] Creare `docker-compose.yml` con:
  - [ ] PostgreSQL (porta 5432) - compatibile DO Managed DB
  - [ ] Redis (porta 6379) - compatibile DO Managed Redis
  - [ ] MinIO (porta 9000, 9001) - S3-compatible per DO Spaces
- [ ] Configurare volumi persistenti
- [ ] Aggiungere healthcheck per ogni servizio
- [ ] Creare network isolato
- [ ] **IMPORTANTE**: Tutto configurabile via env vars (zero hardcoding)

### Backend FastAPI Base
- [ ] Inizializzare progetto FastAPI in `apps/backend/`
- [ ] Struttura cartelle:
  - [ ] `api/routers/`
  - [ ] `core/config.py` (Pydantic Settings per env vars)
  - [ ] `core/security.py`
  - [ ] `db/models/`
  - [ ] `db/session.py` (connection string da env)
  - [ ] `db/migrations/`
  - [ ] `services/`
  - [ ] `workers/`
- [ ] Endpoint `/health` e `/api/v1/health`
- [ ] Configurare logging base
- [ ] Creare `.env.example` con tutte le variabili (vedi STACK_DIGITALOCEAN.md)
- [ ] **Configurazione DigitalOcean-ready**: Tutto via env vars, supporto SSL/TLS

### Collector Service Base
- [ ] Inizializzare progetto Python in `apps/collector/`
- [ ] Struttura cartelle:
  - [ ] `connectors/`
  - [ ] `client/`
  - [ ] `schemas/`
  - [ ] `tasks/`
- [ ] Endpoint `/health`
- [ ] Creare `.env.example`

### Test Infrastruttura
- [ ] Verificare `docker compose up` avvia tutto
- [ ] Test connessione PostgreSQL
- [ ] Test connessione Redis
- [ ] Test connessione MinIO
- [ ] Healthcheck backend OK
- [ ] Healthcheck collector OK

**Criterio Done**: ✅ Tutti i servizi avviano correttamente e healthcheck passano

---

## 🔐 Milestone 1 — Autenticazione & Gestione Utenti

### Database Schema
- [ ] Creare modello `User` (SQLAlchemy):
  - [ ] id (UUID primary key)
  - [ ] email (unique, indexed)
  - [ ] hashed_password
  - [ ] is_active
  - [ ] is_verified (opzionale per email verification)
  - [ ] created_at, updated_at
  - [ ] deleted_at (soft delete)
- [ ] Creare modello `UserProfile`:
  - [ ] user_id (FK)
  - [ ] first_name, last_name
  - [ ] organization (opzionale)
  - [ ] preferences (JSON)
  - [ ] created_at, updated_at
- [ ] Creare migrazione Alembic iniziale
- [ ] Eseguire migrazione e verificare tabelle

### Security Core
- [ ] Implementare password hashing (argon2 o bcrypt)
- [ ] Funzione `verify_password()`
- [ ] Funzione `get_password_hash()`
- [ ] JWT token creation (`create_access_token()`)
- [ ] JWT token verification
- [ ] Refresh token creation
- [ ] Refresh token verification
- [ ] Dependency `get_current_user()`
- [ ] Dependency `get_current_active_user()`

### API Endpoints Auth
- [ ] `POST /api/v1/auth/register`:
  - [ ] Validazione email/password (Pydantic)
  - [ ] Hash password
  - [ ] Creazione user + profile
  - [ ] Return user (senza password)
- [ ] `POST /api/v1/auth/login`:
  - [ ] Verifica credenziali
  - [ ] Genera access + refresh token
  - [ ] Return tokens
- [ ] `POST /api/v1/auth/refresh`:
  - [ ] Verifica refresh token
  - [ ] Genera nuovo access token
- [ ] `POST /api/v1/auth/logout`:
  - [ ] Revoca token (blacklist in Redis opzionale)
- [ ] `GET /api/v1/auth/me`:
  - [ ] Return user + profile (autenticato)
- [ ] `PUT /api/v1/users/me`:
  - [ ] Update profile
  - [ ] Validazione input

### Error Handling
- [ ] Modello error response standardizzato
- [ ] Exception handler per 401, 403, 404, 422, 500
- [ ] Logging errori con trace_id

### Test Auth
- [ ] Test registrazione
- [ ] Test login
- [ ] Test refresh token
- [ ] Test endpoint protetti
- [ ] Test update profile

**Criterio Done**: ✅ Utente può registrarsi, login, refresh, vedere/modificare profilo

---

## 💬 Milestone 2 — Chat & OpenAI Integration

### Database Schema
- [ ] Creare modello `ChatSession`:
  - [ ] id (UUID)
  - [ ] user_id (FK)
  - [ ] title (generato da primo messaggio)
  - [ ] created_at, updated_at
- [ ] Creare modello `ChatMessage`:
  - [ ] id (UUID)
  - [ ] session_id (FK)
  - [ ] role (user/assistant/system)
  - [ ] content (text)
  - [ ] metadata (JSON, per tool calls)
  - [ ] created_at
- [ ] Creare migrazione
- [ ] Eseguire migrazione

### OpenAI Integration
- [ ] Configurare client OpenAI
- [ ] Funzione `chat_completion()` con streaming
- [ ] Gestione tool calling
- [ ] Schema tool `create_dataset_plan`:
  - [ ] name: "create_dataset_plan"
  - [ ] description
  - [ ] parameters (JSON schema DatasetPlan)

### DatasetPlan Schema (Pydantic)
- [ ] Modello `DatasetPlan`:
  - [ ] domain (enum: economics/biomedical/physics/math/demography)
  - [ ] title (str)
  - [ ] sources (list[SourcePlan])
  - [ ] transformations (list[TransformationPlan])
  - [ ] outputs (list[str]: csv/json/parquet)
  - [ ] documentation (dict: manifest, dictionary)
- [ ] Modello `SourcePlan`:
  - [ ] connector (str)
  - [ ] queries (list[dict])
- [ ] Modello `TransformationPlan`
- [ ] Validazione schema rigido

### API Endpoints Chat
- [ ] `POST /api/v1/chat/sessions`:
  - [ ] Crea nuova sessione
  - [ ] Return session_id
- [ ] `GET /api/v1/chat/sessions`:
  - [ ] Lista sessioni utente (paginata)
- [ ] `GET /api/v1/chat/sessions/{session_id}`:
  - [ ] Dettaglio sessione + messaggi
- [ ] `POST /api/v1/chat/sessions/{session_id}/messages`:
  - [ ] Salva messaggio utente
  - [ ] Chiama OpenAI con streaming (SSE)
  - [ ] Salva messaggi assistant
  - [ ] Estrae DatasetPlan se presente
  - [ ] Return streaming response
- [ ] `GET /api/v1/chat/sessions/{session_id}/messages`:
  - [ ] Lista messaggi sessione

### Streaming (SSE)
- [ ] Implementare Server-Sent Events
- [ ] Stream token OpenAI
- [ ] Gestione errori in streaming
- [ ] Chiusura connessione corretta

### Logging
- [ ] Trace ID su ogni richiesta chat
- [ ] Log DatasetPlan generati
- [ ] Log errori OpenAI

### Test Chat
- [ ] Test creazione sessione
- [ ] Test invio messaggio
- [ ] Test streaming response
- [ ] Test DatasetPlan extraction
- [ ] Test validazione DatasetPlan

**Criterio Done**: ✅ Chat funziona, DatasetPlan generato e validato

---

## 📊 Milestone 3 — Dataset Orchestration (Skeleton)

### Database Schema
- [ ] Creare modello `DatasetRequest`:
  - [ ] id (UUID)
  - [ ] user_id (FK)
  - [ ] chat_session_id (FK, opzionale)
  - [ ] title
  - [ ] domain
  - [ ] plan_json (JSON, DatasetPlan serializzato)
  - [ ] status (enum: draft/running/ready_for_payment/paid/delivered/failed)
  - [ ] error_message (opzionale)
  - [ ] created_at, updated_at
- [ ] Creare modello `DatasetStep`:
  - [ ] id (UUID)
  - [ ] dataset_request_id (FK)
  - [ ] step_type (enum: collect/normalize/export)
  - [ ] step_order (int)
  - [ ] status (enum: queued/running/success/failed)
  - [ ] input_data (JSON)
  - [ ] output_data (JSON)
  - [ ] error_message (opzionale)
  - [ ] started_at, completed_at
- [ ] Creare migrazione
- [ ] Eseguire migrazione

### State Machine
- [ ] Implementare logica transizioni stato:
  - [ ] draft → running (quando primo step parte)
  - [ ] running → ready_for_payment (quando export completo)
  - [ ] ready_for_payment → paid (quando pagamento confermato)
  - [ ] paid → delivered (quando download avvenuto, opzionale)
  - [ ] * → failed (su errore)
- [ ] Validazione transizioni
- [ ] Logging transizioni

### Queue Setup
- [ ] Configurare Celery (o Dramatiq/RQ)
- [ ] Creare app Celery
- [ ] Configurare broker (Redis)
- [ ] Configurare result backend
- [ ] Test connessione queue

### Job Workers
- [ ] Creare task `process_dataset_request()`:
  - [ ] Aggiorna stato a `running`
  - [ ] Crea steps da plan
  - [ ] Enqueue step `collect`
- [ ] Creare task `execute_collect_step()`:
  - [ ] Chiama collector service
  - [ ] Aggiorna stato step
  - [ ] Enqueue step `normalize` se success
- [ ] Creare task `execute_normalize_step()`:
  - [ ] Chiama normalizer
  - [ ] Aggiorna stato step
  - [ ] Enqueue step `export` se success
- [ ] Creare task `execute_export_step()`:
  - [ ] Genera export
  - [ ] Crea bundle
  - [ ] Aggiorna stato dataset a `ready_for_payment`

### Progress Tracking
- [ ] Eventi progress (via Redis pub/sub o DB polling)
- [ ] Endpoint `GET /api/v1/datasets/{id}/progress`:
  - [ ] Return stato corrente + progress steps

### API Endpoints Dataset
- [ ] `POST /api/v1/datasets`:
  - [ ] Crea dataset_request da DatasetPlan
  - [ ] Enqueue job
  - [ ] Return dataset_request
- [ ] `GET /api/v1/datasets`:
  - [ ] Lista dataset utente (paginata, filtrata)
- [ ] `GET /api/v1/datasets/{id}`:
  - [ ] Dettaglio dataset + steps
- [ ] `GET /api/v1/datasets/{id}/progress`:
  - [ ] Progress real-time

### Test Orchestration
- [ ] Test creazione dataset_request
- [ ] Test state machine
- [ ] Test job enqueue
- [ ] Test progress tracking

**Criterio Done**: ✅ Dataset request creato, job enqueued, progress tracciato

---

## 🔌 Milestone 4 — Collector Connectors MVP

### Connector Architecture
- [ ] Creare `connectors/base.py`:
  - [ ] Classe astratta `BaseConnector`
  - [ ] Metodi: `connect()`, `fetch()`, `validate_query()`
- [ ] Creare `connectors/registry.py`:
  - [ ] Registry pattern
  - [ ] Registrazione connettori
  - [ ] Get connector by name

### HTTP Client
- [ ] Configurare httpx client
- [ ] Implementare retry logic (tenacity):
  - [ ] Retry su 5xx, timeout
  - [ ] Exponential backoff
- [ ] Implementare rate limiting base
- [ ] Timeout configurabili

### WorldBank Connector
- [ ] Implementare `WorldBankConnector(BaseConnector)`
- [ ] API World Bank (World Bank Open Data API)
- [ ] Parsing response
- [ ] Output standard (records + metadata + provenance)
- [ ] Test con query esempio

### Eurostat Connector
- [ ] Implementare `EurostatConnector(BaseConnector)`
- [ ] API Eurostat
- [ ] Parsing response
- [ ] Output standard
- [ ] Test con query esempio

### PubMed Connector
- [ ] Implementare `PubMedConnector(BaseConnector)`
- [ ] API PubMed/NCBI
- [ ] Parsing response (XML/JSON)
- [ ] Output standard
- [ ] Test con query esempio

### Output Standard
- [ ] Schema `ConnectorOutput`:
  - [ ] records: list[dict]
  - [ ] metadata: dict (row_count, columns, etc.)
  - [ ] provenance: dict (source, query, retrieved_at, license, url)
- [ ] Validazione output

### Storage Raw Assets
- [ ] Creare modello `RawAsset`:
  - [ ] id (UUID)
  - [ ] dataset_step_id (FK)
  - [ ] connector_name
  - [ ] storage_path (S3 key)
  - [ ] metadata (JSON)
  - [ ] created_at
- [ ] Funzione salvataggio raw usando **boto3** (S3-compatible):
  - [ ] Configurazione da env vars (endpoint, keys, bucket)
  - [ ] Funziona con MinIO (dev) e DO Spaces (prod)
  - [ ] Zero hardcoding, tutto via env
- [ ] Funzione recupero raw
- [ ] Migrazione DB

### Collector Service API
- [ ] Endpoint `POST /collect`:
  - [ ] Input: connector_name, query, dataset_step_id
  - [ ] Esegue connector
  - [ ] Salva raw asset
  - [ ] Salva metadata in DB (via backend API o direttamente)
  - [ ] Return output standard

### Error Handling
- [ ] Gestione errori connector
- [ ] Logging errori con trace_id
- [ ] Audit log operazioni

### Test Connectors
- [ ] Test WorldBank connector
- [ ] Test Eurostat connector
- [ ] Test PubMed connector
- [ ] Test retry logic
- [ ] Test rate limiting
- [ ] Test storage raw assets

**Criterio Done**: ✅ 3 connettori funzionanti, dati raw salvati, metadata in DB

---

## 🔄 Milestone 5 — Normalization & Export

### Normalizer Architecture
- [ ] Creare `normalizers/base.py`:
  - [ ] Classe astratta `BaseNormalizer`
  - [ ] Metodi: `normalize()`, `validate()`
- [ ] Creare `normalizers/registry.py`:
  - [ ] Registry pattern
  - [ ] Get normalizer by domain

### Economics Normalizer
- [ ] Implementare `EconomicsNormalizer(BaseNormalizer)`
- [ ] Normalizzazione date/time
- [ ] Join time series
- [ ] Handling missing values
- [ ] Standardizzazione colonne

### Biomedical Normalizer
- [ ] Implementare `BiomedicalNormalizer(BaseNormalizer)`
- [ ] Cleanup record
- [ ] Deduplicazione base
- [ ] Normalizzazione campi
- [ ] Validazione dati

### Manifest Generator
- [ ] Funzione `generate_manifest()`:
  - [ ] Dataset metadata
  - [ ] Sources info
  - [ ] Transformations applied
  - [ ] Output formats
  - [ ] Created at, version
- [ ] Salvataggio `manifest.json`

### Data Dictionary Generator
- [ ] Funzione `generate_data_dictionary()`:
  - [ ] Colonne dataset
  - [ ] Tipi dati
  - [ ] Descrizioni (se disponibili)
  - [ ] Valori possibili (se enum)
- [ ] Salvataggio `data_dictionary.json`

### Export CSV
- [ ] Funzione `export_to_csv()`
- [ ] Encoding UTF-8
- [ ] Handling special characters
- [ ] Test export

### Export JSON
- [ ] Funzione `export_to_json()`
- [ ] Formattazione leggibile
- [ ] Handling nested data
- [ ] Test export

### Export Parquet
- [ ] Funzione `export_to_parquet()`
- [ ] Usare pyarrow o fastparquet
- [ ] Schema preservation
- [ ] Test export

### Bundle Creator
- [ ] Funzione `create_bundle()`:
  - [ ] Crea directory temporanea
  - [ ] Copia file export
  - [ ] Aggiunge manifest.json
  - [ ] Aggiunge data_dictionary.json
  - [ ] Aggiunge provenance.json
  - [ ] Crea ZIP o tar.gz
- [ ] Upload bundle a storage
- [ ] Cleanup file temporanei

### Storage Final Dataset
- [ ] Creare modello `FinalDataset`:
  - [ ] id (UUID)
  - [ ] dataset_request_id (FK)
  - [ ] storage_path (bundle)
  - [ ] formats (JSON: csv, json, parquet paths)
  - [ ] file_size
  - [ ] row_count
  - [ ] created_at
- [ ] Migrazione DB
- [ ] Salvataggio bundle

### API Integration
- [ ] Aggiornare task `execute_normalize_step()`:
  - [ ] Chiama normalizer
  - [ ] Salva dati normalizzati
- [ ] Aggiornare task `execute_export_step()`:
  - [ ] Genera tutti gli export
  - [ ] Crea bundle
  - [ ] Salva FinalDataset

### Test Normalization & Export
- [ ] Test economics normalizer
- [ ] Test biomedical normalizer
- [ ] Test manifest generation
- [ ] Test data dictionary
- [ ] Test export CSV/JSON/Parquet
- [ ] Test bundle creation

**Criterio Done**: ✅ Bundle completo con manifest, dictionary, provenance, export multipli

---

## 💳 Milestone 6 — Pagamenti Stripe

### Database Schema
- [ ] Creare modello `Payment`:
  - [ ] id (UUID)
  - [ ] user_id (FK)
  - [ ] dataset_request_id (FK)
  - [ ] amount (Decimal)
  - [ ] currency (str, default "eur")
  - [ ] status (enum: pending/completed/failed/refunded)
  - [ ] provider (str: "stripe")
  - [ ] provider_ref (str, unique, Stripe payment intent ID)
  - [ ] provider_checkout_session_id (str)
  - [ ] idempotency_key (str, unique)
  - [ ] metadata (JSON)
  - [ ] created_at, updated_at
- [ ] Creare migrazione
- [ ] Eseguire migrazione

### Stripe Configuration
- [ ] Configurare Stripe client
- [ ] Variabili ambiente (secret key, webhook secret)
- [ ] Test mode setup

### Checkout Session
- [ ] Funzione `create_checkout_session()`:
  - [ ] Crea Stripe Checkout Session
  - [ ] Metadata: dataset_request_id, user_id
  - [ ] Success URL, Cancel URL
  - [ ] Return session URL
- [ ] Endpoint `POST /api/v1/billing/checkout`:
  - [ ] Input: dataset_request_id
  - [ ] Verifica ownership
  - [ ] Verifica stato ready_for_payment
  - [ ] Crea checkout session
  - [ ] Salva payment record (status: pending)
  - [ ] Return checkout URL

### Webhook Handler
- [ ] Endpoint `POST /api/v1/billing/webhooks/stripe`:
  - [ ] Verifica signature webhook
  - [ ] Parse evento Stripe
  - [ ] Gestione eventi:
    - [ ] `checkout.session.completed`
    - [ ] `payment_intent.succeeded`
    - [ ] `payment_intent.payment_failed`
- [ ] Idempotency:
  - [ ] Estrai idempotency_key da metadata
  - [ ] Verifica se già processato (DB lookup)
  - [ ] Se già processato, return early
  - [ ] Salva idempotency_key dopo processamento

### Payment Processing
- [ ] Funzione `process_payment_success()`:
  - [ ] Aggiorna payment status a `completed`
  - [ ] Aggiorna dataset_request status a `paid`
  - [ ] Audit log
- [ ] Funzione `process_payment_failure()`:
  - [ ] Aggiorna payment status a `failed`
  - [ ] Log errore

### Download Blocco
- [ ] Aggiornare endpoint download:
  - [ ] Verifica dataset status = `paid`
  - [ ] Se non paid, return 402 Payment Required

### API Endpoints
- [ ] `GET /api/v1/billing/payments`:
  - [ ] Lista pagamenti utente
- [ ] `GET /api/v1/billing/payments/{id}`:
  - [ ] Dettaglio pagamento

### Test Payments
- [ ] Test creazione checkout session
- [ ] Test webhook success
- [ ] Test webhook failure
- [ ] Test idempotency
- [ ] Test blocco download

**Criterio Done**: ✅ Pagamento test funziona, dataset sbloccato, download abilitato

---

## 🧾 Milestone 7 — Fatture & Ricevute

### Database Schema
- [ ] Creare modello `Invoice`:
  - [ ] id (UUID)
  - [ ] invoice_number (str, unique, sequenziale)
  - [ ] user_id (FK)
  - [ ] payment_id (FK)
  - [ ] dataset_request_id (FK)
  - [ ] amount (Decimal)
  - [ ] tax_amount (Decimal, opzionale)
  - [ ] total_amount (Decimal)
  - [ ] currency (str)
  - [ ] invoice_date (date)
  - [ ] due_date (date, opzionale)
  - [ ] status (enum: draft/issued/paid/cancelled)
  - [ ] storage_path (PDF in S3)
  - [ ] metadata (JSON)
  - [ ] created_at, updated_at
- [ ] Creare migrazione
- [ ] Eseguire migrazione

### PDF Generation
- [ ] Scegliere libreria (reportlab o fpdf)
- [ ] Template fattura/ricevuta:
  - [ ] Header (logo, company info)
  - [ ] Invoice number, date
  - [ ] Customer info (da user profile)
  - [ ] Line items (dataset info)
  - [ ] Totals
  - [ ] Footer (terms, contact)
- [ ] Funzione `generate_invoice_pdf()`:
  - [ ] Crea PDF
  - [ ] Salva temporaneamente
  - [ ] Upload a storage
  - [ ] Cleanup

### Numerazione Documenti
- [ ] Funzione `generate_invoice_number()`:
  - [ ] Formato: INV-YYYY-NNNN
  - [ ] Sequenziale per anno
  - [ ] Thread-safe (lock DB)
- [ ] Test numerazione

### Invoice Creation
- [ ] Funzione `create_invoice()`:
  - [ ] Genera invoice number
  - [ ] Crea record Invoice
  - [ ] Genera PDF
  - [ ] Salva PDF path
  - [ ] Collega a payment
- [ ] Chiamare dopo payment success

### Storage PDF
- [ ] Upload PDF a MinIO/S3
- [ ] Path: `invoices/{invoice_number}.pdf`
- [ ] Signed URL per download

### API Endpoints
- [ ] `GET /api/v1/billing/invoices`:
  - [ ] Lista fatture utente (paginata)
- [ ] `GET /api/v1/billing/invoices/{id}`:
  - [ ] Dettaglio fattura
- [ ] `GET /api/v1/billing/invoices/{id}/download`:
  - [ ] Signed URL PDF
  - [ ] Ownership check

### Test Invoices
- [ ] Test generazione PDF
- [ ] Test numerazione
- [ ] Test creazione invoice
- [ ] Test download PDF

**Criterio Done**: ✅ PDF generato, numerato, salvato, scaricabile

---

## 📦 Milestone 8 — Storage & Download

### Signed URL Generation
- [ ] Funzione `generate_signed_url()` usando **boto3**:
  - [ ] `generate_presigned_url()` S3-compatible
  - [ ] Funziona con MinIO (dev) e DO Spaces (prod)
  - [ ] TTL configurabile via env (default 1 ora)
  - [ ] Metodo GET
  - [ ] Configurazione da env vars (zero hardcoding)
- [ ] Test signed URL

### Ownership Check
- [ ] Funzione `verify_dataset_ownership()`:
  - [ ] Verifica user_id su dataset_request
- [ ] Funzione `verify_invoice_ownership()`:
  - [ ] Verifica user_id su invoice
- [ ] Applicare a tutti gli endpoint download

### Download Dataset Bundle
- [ ] Endpoint `GET /api/v1/datasets/{id}/download`:
  - [ ] Ownership check
  - [ ] Verifica status = `paid`
  - [ ] Recupera FinalDataset
  - [ ] Genera signed URL bundle
  - [ ] Audit log download
  - [ ] Return signed URL

### Download Invoice PDF
- [ ] Endpoint `GET /api/v1/billing/invoices/{id}/download`:
  - [ ] Ownership check
  - [ ] Recupera Invoice
  - [ ] Genera signed URL PDF
  - [ ] Audit log
  - [ ] Return signed URL

### TTL Configuration
- [ ] Variabile ambiente `SIGNED_URL_TTL` (secondi)
- [ ] Default 3600 (1 ora)

### Audit Log Download
- [ ] Log ogni download:
  - [ ] user_id
  - [ ] resource_type (dataset/invoice)
  - [ ] resource_id
  - [ ] timestamp
  - [ ] IP address (opzionale)

### Test Download
- [ ] Test signed URL generation
- [ ] Test ownership check
- [ ] Test download dataset
- [ ] Test download invoice
- [ ] Test TTL expiration

**Criterio Done**: ✅ Download funzionanti con signed URL, ownership verificato

---

## 📚 Milestone 9 — Storico & Audit

### Database Schema Audit
- [ ] Creare modello `AuditLog`:
  - [ ] id (UUID)
  - [ ] user_id (FK, opzionale)
  - [ ] action (str: create_dataset, payment, download, etc.)
  - [ ] resource_type (str)
  - [ ] resource_id (UUID)
  - [ ] trace_id (str)
  - [ ] metadata (JSON)
  - [ ] ip_address (str, opzionale)
  - [ ] created_at
- [ ] Creare migrazione
- [ ] Eseguire migrazione
- [ ] Indici su user_id, action, created_at

### Audit Logging Service
- [ ] Funzione `log_audit_event()`:
  - [ ] Crea record AuditLog
  - [ ] Async (non blocca request)
- [ ] Integrare in:
  - [ ] Creazione dataset
  - [ ] Pagamento
  - [ ] Download
  - [ ] Modifiche critiche

### Storico Dataset
- [ ] Endpoint `GET /api/v1/datasets`:
  - [ ] Filtri: status, domain, date range
  - [ ] Paginazione
  - [ ] Ordinamento
  - [ ] Return lista completa
- [ ] Endpoint `GET /api/v1/datasets/{id}/history`:
  - [ ] Storico modifiche dataset
  - [ ] Steps timeline

### Clone Dataset
- [ ] Endpoint `POST /api/v1/datasets/{id}/clone`:
  - [ ] Ownership check
  - [ ] Recupera plan originale
  - [ ] Crea nuovo dataset_request con stesso plan
  - [ ] Return nuovo dataset
- [ ] Test clone

### Trace ID
- [ ] Middleware per generare trace_id
- [ ] Aggiungere trace_id a tutti i log
- [ ] Includere trace_id in audit log

### Audit Log Endpoint (Admin)
- [ ] Endpoint `GET /api/v1/admin/audit-logs`:
  - [ ] Filtri avanzati
  - [ ] Paginazione
  - [ ] Solo admin (RBAC)

### Test Audit
- [ ] Test audit logging
- [ ] Test storico dataset
- [ ] Test clone dataset
- [ ] Test trace ID

**Criterio Done**: ✅ Storico completo, audit log funzionante, clone dataset ok

---

## 🗑️ Milestone 10 — Lifecycle & Account Deletion

### Soft Delete User
- [ ] Endpoint `DELETE /api/v1/users/me`:
  - [ ] Soft delete (set deleted_at)
  - [ ] Revoca tutti i token attivi
  - [ ] Disabilita account (is_active = false)
  - [ ] Audit log
- [ ] Middleware: escludere utenti deleted da query

### Revoca Sessioni
- [ ] Funzione `revoke_user_sessions()`:
  - [ ] Blacklist token in Redis (opzionale)
  - [ ] O semplicemente invalidare refresh token
- [ ] Chiamare durante delete

### Cancellazione Abbonamenti
- [ ] Se presenti subscription:
  - [ ] Recupera subscription Stripe
  - [ ] Cancella subscription
  - [ ] Log operazione
- [ ] Endpoint `GET /api/v1/billing/cancel-subscription`:
  - [ ] Link a Stripe customer portal (opzionale)

### Purge Job Schedulato
- [ ] Creare task `purge_deleted_users()`:
  - [ ] Trova utenti con deleted_at > 30 giorni (configurabile)
  - [ ] Elimina dati associati:
    - [ ] Chat sessions/messages
    - [ ] Dataset requests (soft delete)
    - [ ] Payments (anonymize)
    - [ ] Invoices (anonymize o delete)
    - [ ] Audit logs (anonymize user_id)
  - [ ] Elimina user definitivamente
- [ ] Schedulare con Celery Beat (giornaliero)

### Compliance GDPR
- [ ] Verificare eliminazione dati personali
- [ ] Anonimizzazione dove necessario
- [ ] Log operazioni purge

### Test Lifecycle
- [ ] Test soft delete
- [ ] Test revoca sessioni
- [ ] Test purge job
- [ ] Test compliance

**Criterio Done**: ✅ Account eliminabile, dati purgati dopo periodo, compliance ok

---

## 🔒 Milestone 11 — Sicurezza & Compliance

### Rate Limiting
- [ ] Implementare rate limiting (slowapi o similar):
  - [ ] Endpoint pubblici (register, login): 5/min per IP
  - [ ] Endpoint autenticati: 100/min per user
  - [ ] Endpoint chat: 20/min per user
- [ ] Configurazione Redis backend
- [ ] Error response 429

### Input Validation
- [ ] Validazione DatasetPlan schema rigido:
  - [ ] Pydantic model con validators
  - [ ] Reject plan non conformi
  - [ ] Log tentativi invalidi
- [ ] Sanitizzazione input utente
- [ ] Protezione SQL injection (SQLAlchemy già protegge)

### Ownership Check
- [ ] Verificare ownership su:
  - [ ] Dataset requests
  - [ ] Chat sessions
  - [ ] Payments
  - [ ] Invoices
  - [ ] Download
- [ ] Middleware o dependency comune

### CORS
- [ ] Configurare CORS:
  - [ ] Allowed origins (env)
  - [ ] Allowed methods
  - [ ] Allowed headers
  - [ ] Credentials

### Security Headers
- [ ] Middleware security headers:
  - [ ] X-Content-Type-Options: nosniff
  - [ ] X-Frame-Options: DENY
  - [ ] X-XSS-Protection: 1; mode=block
  - [ ] Strict-Transport-Security (se HTTPS)

### Logging Sicuro
- [ ] Rimuovere PII da log:
  - [ ] No password in log
  - [ ] No token in log
  - [ ] Anonimizzazione email se necessario
- [ ] Log level configurabile

### Backup Strategy
- [ ] Documentare backup:
  - [ ] PostgreSQL (giornaliero)
  - [ ] Object storage (replica)
  - [ ] Retention policy

### Test Security
- [ ] Test rate limiting
- [ ] Test input validation
- [ ] Test ownership check
- [ ] Test CORS
- [ ] Test security headers

**Criterio Done**: ✅ Sicurezza hardenata, compliance verificata

---

## 🧪 Milestone 12 — Testing & Documentazione

### Test Unitari
- [ ] Setup pytest
- [ ] Test auth functions
- [ ] Test security functions
- [ ] Test DatasetPlan validation
- [ ] Test normalizers
- [ ] Test export functions
- [ ] Coverage >80%

### Test Integrazione
- [ ] Test endpoint auth (register/login)
- [ ] Test endpoint chat
- [ ] Test pipeline end-to-end
- [ ] Test pagamenti (Stripe test mode)
- [ ] Test download

### Test Smoke Pipeline
- [ ] Test completo:
  - [ ] Chat → DatasetPlan
  - [ ] Creazione dataset
  - [ ] Collect → Normalize → Export
  - [ ] Bundle generato
- [ ] Verifica output

### Test State Machine
- [ ] Test tutte le transizioni stato
- [ ] Test transizioni invalide (reject)
- [ ] Test error handling

### Documentazione API
- [ ] OpenAPI/Swagger:
  - [ ] Tutti gli endpoint documentati
  - [ ] Schemi Pydantic
  - [ ] Esempi request/response
  - [ ] Error responses
- [ ] Accessibile su `/docs`

### README Tecnico
- [ ] Struttura progetto
- [ ] Setup sviluppo
- [ ] Variabili ambiente
- [ ] Comandi utili
- [ ] Architettura overview

### Setup Guide
- [ ] Guida passo-passo:
  - [ ] Prerequisiti
  - [ ] Clone repository
  - [ ] Setup Docker
  - [ ] Configurazione env
  - [ ] Migrazioni DB
  - [ ] Avvio servizi
  - [ ] Test iniziali

### Test Finali
- [ ] Eseguire tutti i test
- [ ] Verificare coverage
- [ ] Test manuale flow completo
- [ ] Verifica documentazione

**Criterio Done**: ✅ Test completi, documentazione aggiornata, ready for production

---

## 📝 Note Generali

### Convenzioni
- Tutti gli endpoint sotto `/api/v1/`
- Error response standardizzato
- Logging con trace_id
- Validazione Pydantic ovunque
- Migrazioni Alembic per ogni cambio schema

### Priorità MVP
Per MVP funzionante, completare almeno:
- ✅ Milestone 0-1: Infrastruttura + Auth
- ✅ Milestone 2-3: Chat + Orchestration
- ✅ Milestone 4-5: Collectors + Export
- ✅ Milestone 6: Payments
- ✅ Milestone 8: Download base

Milestone 7, 9-12 possono essere completate dopo per produzione.

### Prossimi Passi
1. Iniziare con Milestone 0 (Bootstrap)
2. Procedere sequenzialmente
3. Testare ogni milestone prima di procedere
4. Documentare decisioni architetturali

