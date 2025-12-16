# 🗺️ Roadmap Backend — Dataset On-Demand Portal

## 📋 Panoramica
Questa roadmap definisce lo sviluppo completo del backend prima di procedere con il frontend. Il lavoro è organizzato in milestone sequenziali con criteri di completamento verificabili.

---

## 🎯 Milestone 0 — Bootstrap & Infrastruttura
**Obiettivo**: Setup completo dell'ambiente di sviluppo e infrastruttura base.

### Componenti
- Docker Compose con servizi essenziali (PostgreSQL, Redis, MinIO)
- Backend FastAPI con struttura base e healthcheck
- Collector Service con struttura base e healthcheck
- Configurazione ambiente e variabili
- **Tutto configurabile via env vars per DigitalOcean (plug-and-play)**

### Stack DigitalOcean Ready
- **PostgreSQL**: Docker (dev) → DO Managed DB (prod) - connection string via env
- **Redis**: Docker (dev) → DO Managed Redis (prod) - connection string via env
- **Storage**: MinIO (dev) → DO Spaces (prod) - boto3 S3-compatible
- **OpenAI**: API esterna (stesso dev/prod)
- **Stripe**: Test keys (dev) → Live keys (prod) - stesso codice

### Criterio Done
✅ `docker compose up` avvia tutti i servizi  
✅ Healthcheck endpoint funzionanti per backend e collector  
✅ Connessioni DB, Redis e storage verificate

**Stima**: 1-2 giorni

---

## 🔐 Milestone 1 — Autenticazione & Gestione Utenti
**Obiettivo**: Sistema completo di autenticazione e gestione profili utente.

### Componenti
- Schema database: `users`, `user_profiles`
- Migrazioni Alembic
- Endpoint auth: register, login, refresh, logout, me, update profile
- JWT + refresh token
- Password hashing (argon2/bcrypt)
- Validazione Pydantic
- Error handling coerente

### Criterio Done
✅ Utente può registrarsi  
✅ Utente può effettuare login e ricevere JWT  
✅ Refresh token funziona  
✅ Endpoint `/me` restituisce dati utente  
✅ Profilo modificabile  
✅ Logout revoca token

**Stima**: 2-3 giorni

---

## 💬 Milestone 2 — Chat & OpenAI Integration
**Obiettivo**: Sistema di chat con integrazione OpenAI per generare DatasetPlan.

### Componenti
- Schema database: `chat_sessions`, `chat_messages`
- Endpoint chat con streaming (SSE)
- Integrazione OpenAI API
- Tool calling: `create_dataset_plan`
- Validazione DatasetPlan JSON (schema rigido)
- Persistenza conversazioni
- Logging con trace_id

### Criterio Done
✅ Creazione sessione chat  
✅ Messaggi salvati in DB  
✅ Streaming risposte OpenAI funzionante  
✅ Tool calling produce DatasetPlan valido  
✅ DatasetPlan validato secondo schema  
✅ Conversazioni recuperabili dallo storico

**Stima**: 3-4 giorni

---

## 📊 Milestone 3 — Dataset Orchestration (Skeleton)
**Obiettivo**: Struttura base per orchestrazione pipeline dataset.

### Componenti
- Schema database: `dataset_requests`, `dataset_steps`
- State machine: draft → running → ready_for_payment → paid → delivered
- Creazione dataset_request da DatasetPlan
- Queue setup (Redis + Celery)
- Job workers base
- Progress tracking e eventi
- Endpoint status/progress

### Criterio Done
✅ DatasetPlan convertito in dataset_request  
✅ Steps creati (collect, normalize, export)  
✅ Job enqueued correttamente  
✅ Stato dataset aggiornato  
✅ Progress events emessi  
✅ Endpoint restituisce stato corrente

**Stima**: 2-3 giorni

---

## 🔌 Milestone 4 — Collector Connectors MVP
**Obiettivo**: Connettori funzionanti per 3 fonti dati (WorldBank, Eurostat, PubMed).

### Componenti
- Connector registry pattern
- Base connector interface
- WorldBank connector
- Eurostat connector
- PubMed connector
- Retry logic (tenacity)
- Rate limiting base
- Raw assets storage (MinIO/S3)
- Metadata in DB (`raw_assets`)
- Error handling e audit

### Criterio Done
✅ Registry connettori funzionante  
✅ 3 connettori implementati e testati  
✅ Dati raw salvati in storage  
✅ Metadata salvati in DB  
✅ Retry su errori temporanei  
✅ Rate limiting applicato  
✅ Provenance tracciata

**Stima**: 4-5 giorni

---

## 🔄 Milestone 5 — Normalization & Export
**Obiettivo**: Normalizzazione dati e export in formati standard con documentazione.

### Componenti
- Normalizer plugin system
- Normalizer economics (time series join)
- Normalizer biomedical (cleanup + dedup)
- Manifest generator (`manifest.json`)
- Data dictionary generator (`data_dictionary.json`)
- Export CSV
- Export JSON
- Export Parquet
- Bundle creator (dataset + manifest + dictionary + provenance)
- Storage bundle finale

### Criterio Done
✅ Normalizzazione applicata per economics  
✅ Normalizzazione applicata per biomedical  
✅ Manifest generato correttamente  
✅ Data dictionary generato correttamente  
✅ Export CSV funzionante  
✅ Export JSON funzionante  
✅ Export Parquet funzionante  
✅ Bundle completo creato e salvato  
✅ Provenance inclusa

**Stima**: 4-5 giorni

---

## 💳 Milestone 6 — Pagamenti Stripe
**Obiettivo**: Integrazione completa Stripe Checkout con webhook idempotenti.

### Componenti
- Schema database: `payments`
- Stripe Checkout session creation
- Webhook endpoint (idempotente)
- Idempotency key handling
- Unique constraint su `provider_ref`
- Aggiornamento stato dataset (ready_for_payment → paid)
- Blocco download se non paid
- Audit log pagamenti

### Criterio Done
✅ Checkout session creata correttamente  
✅ Webhook riceve eventi Stripe  
✅ Idempotenza garantita (no duplicati)  
✅ Stato dataset aggiornato a `paid`  
✅ Download bloccato se non paid  
✅ Payment record salvato in DB  
✅ Audit log creato

**Stima**: 3-4 giorni

---

## 🧾 Milestone 7 — Fatture & Ricevute
**Obiettivo**: Generazione PDF fatture/ricevute e gestione documenti.

### Componenti
- Schema database: `invoices`
- Generazione PDF (reportlab/fpdf)
- Numerazione documenti
- Template fattura/ricevuta
- Storage PDF in object storage
- Endpoint lista fatture
- Signed URL per download PDF
- Collegamento payment → invoice

### Criterio Done
✅ PDF generato dopo pagamento  
✅ Numerazione sequenziale corretta  
✅ Template conforme  
✅ PDF salvato in storage  
✅ Endpoint restituisce lista fatture  
✅ Download PDF via signed URL funzionante  
✅ Invoice collegata a payment

**Stima**: 2-3 giorni

---

## 📦 Milestone 8 — Storage & Download
**Obiettivo**: Gestione completa download con signed URL e controllo ownership.

### Componenti
- Signed URL generation (MinIO/S3)
- Ownership check su ogni download
- Endpoint download dataset bundle
- Endpoint download invoice PDF
- TTL signed URL configurabile
- Audit log download

### Criterio Done
✅ Signed URL generato correttamente  
✅ Ownership verificato prima download  
✅ Download dataset bundle funzionante  
✅ Download invoice funzionante  
✅ URL scadono dopo TTL  
✅ Audit log registra download

**Stima**: 1-2 giorni

---

## 📚 Milestone 9 — Storico & Audit
**Obiettivo**: Sistema completo di storico utente e audit log.

### Componenti
- Schema database: `audit_logs`
- Endpoint storico dataset utente
- Filtri e paginazione
- Clone dataset (replica plan)
- Audit log per azioni critiche
- Trace ID su tutte le operazioni
- Endpoint audit log (admin)

### Criterio Done
✅ Storico dataset completo  
✅ Filtri funzionanti  
✅ Paginazione implementata  
✅ Clone dataset crea nuovo request  
✅ Audit log registra azioni  
✅ Trace ID presente in log  
✅ Endpoint audit accessibile

**Stima**: 2-3 giorni

---

## 🗑️ Milestone 10 — Lifecycle & Account Deletion
**Obiettivo**: Gestione completa eliminazione account e purge dati.

### Componenti
- Soft delete utente
- Revoca sessioni attive
- Cancellazione abbonamenti (se presenti)
- Job purge schedulato
- Eliminazione dati associati
- Compliance GDPR

### Criterio Done
✅ Account eliminabile (soft delete)  
✅ Sessioni revocate  
✅ Dati non accessibili dopo delete  
✅ Job purge schedulato  
✅ Dati eliminati definitivamente dopo periodo  
✅ Compliance verificata

**Stima**: 2-3 giorni

---

## 🔒 Milestone 11 — Sicurezza & Compliance
**Obiettivo**: Hardening sicurezza e compliance finale.

### Componenti
- Rate limiting su endpoint pubblici
- Input validation DatasetPlan (schema rigido)
- Ownership check su tutte le risorse
- CORS configurazione
- Security headers
- Logging sicuro (no PII in log)
- Backup strategy

### Criterio Done
✅ Rate limiting attivo  
✅ Validazione DatasetPlan rigorosa  
✅ Ownership check ovunque  
✅ CORS configurato  
✅ Security headers presenti  
✅ Logging conforme  
✅ Backup configurato

**Stima**: 2-3 giorni

---

## 🧪 Milestone 12 — Testing & Documentazione
**Obiettivo**: Test completi e documentazione API.

### Componenti
- Test unitari (pytest)
- Test integrazione
- Test smoke su pipeline
- Test state machine
- Documentazione API (OpenAPI/Swagger)
- README tecnico
- Setup guide

### Criterio Done
✅ Test unitari >80% coverage  
✅ Test integrazione passano  
✅ Smoke test pipeline ok  
✅ State machine testata  
✅ Swagger completo  
✅ README aggiornato  
✅ Setup guide funzionante

**Stima**: 3-4 giorni

---

## 📊 Timeline Totale Stimata
**Totale**: ~30-40 giorni lavorativi

### Fasi Critiche
1. **Milestone 0-1** (Bootstrap + Auth): Base solida
2. **Milestone 2-3** (Chat + Orchestration): Core business logic
3. **Milestone 4-5** (Collectors + Export): Funzionalità principale
4. **Milestone 6-7** (Payments + Invoices): Monetizzazione
5. **Milestone 8-12** (Polish + Security + Testing): Qualità e produzione

---

## 🎯 Priorità MVP
Per un MVP funzionante, le milestone essenziali sono:
- ✅ Milestone 0-1: Infrastruttura + Auth
- ✅ Milestone 2-3: Chat + Orchestration
- ✅ Milestone 4-5: Collectors + Export
- ✅ Milestone 6: Payments
- ✅ Milestone 8: Download base

Le milestone 7, 9-12 possono essere completate in seguito per produzione.

