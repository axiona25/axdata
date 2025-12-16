# Analisi Progetto — Portale Web “Dataset On-Demand” per Ricercatori (Cursor Build Spec)

## 1. Scopo del progetto
Realizzare un portale web che consenta a ricercatori, università e professionisti di **richiedere, generare e acquistare dataset** in modo semplice e guidato tramite una **chat in linguaggio naturale**.

Il portale deve trasformare una richiesta descritta a parole (es. “indicatori macroeconomici UE 2000–2024”) in un processo automatico che:
1) analizza la necessità del ricercatore tramite chat (OpenAI)  
2) genera un **DatasetPlan** strutturato (query e steps)  
3) esegue la raccolta dati via **API Collector** (fonti ufficiali e pubbliche)  
4) normalizza e struttura i dati secondo standard di settore  
5) produce un dataset esportabile in formati standard  
6) abilita pagamento e fatturazione  
7) salva tutto nello storico utente (download e audit)

Valore aggiunto: **zero curva di apprendimento** (niente ETL complessi), processo trasparente, ripetibile, con provenance e metadati.

---

## 2. Risultato atteso (deliverable funzionali)
### 2.1 Frontend (React)
- Registrazione/login
- Dashboard e profilo
- Chat (OpenAI) con streaming
- Pagina “richiesta dataset” con progress pipeline (stati, errori, log)
- Storico dataset generati con download
- Sezione billing: pagamenti, fatture/ricevute, metodi pagamento
- Cancellazione account + annullamento abbonamenti (se previsti)

### 2.2 Backend (Python)
- Auth sicura (JWT + refresh, RBAC minimo)
- Chat sessions/messages
- Dataset requests + pipeline steps + progress
- Job queue per lavori lunghi
- Export + signed URL download
- Stripe Checkout + webhook idempotenti (+ PayPal opzionale)
- Generazione PDF fatture/ricevute
- Audit log

### 2.3 API Collector (servizio separato)
- Connettori modulari per fonti
- Retry/rate-limit/caching/logging
- Output standard (records + metadata + provenance)
- Salvataggio raw in storage + metadata in DB

### 2.4 Database + Storage
- **PostgreSQL**: Docker (dev) → DigitalOcean Managed Database (prod) - connection string via env
- **Redis**: Docker (dev) → DigitalOcean Managed Database (prod) - connection string via env
- **Object Storage**: MinIO (dev) → DigitalOcean Spaces (prod) - boto3 S3-compatible, tutto via env vars
- **Principio**: Plug-and-play dev→prod, zero hardcoding, solo variabili d'ambiente

---

## 3. Pillar funzionali
### A) Account
- registrazione/login, modifica profilo, reset password
- eliminazione account (soft delete + purge schedulato)
- gestione consensi/contratto (ToS/Privacy)

### B) Chat (OpenAI)
- raccolta requisiti
- produce **DatasetPlan JSON** (domain, fonti, query, trasformazioni, output)
- tool calling verso backend per creare pipeline ripetibile e tracciata

### C) API Collector
- connettori per fonti (MVP: World Bank, Eurostat, PubMed)
- error handling e audit
- standardizzazione output

### D) DB per dominio/settore
- catalogo domain + connectors + schemi
- versioning dataset
- ripetibilità (ricostruzione con stesso plan)

### E) Standard internazionali dataset
- manifest + data dictionary + provenance sempre presenti
- normalizer plugin-based per domain

### F) Pagamenti & Billing
- pay-per-dataset (MVP)
- Stripe: Visa/Mastercard + Apple Pay + Google Pay
- PayPal opzionale
- blocco download finché non risulta “paid”

### G) Storico utente
- lista dataset, stati, download, fatture
- clone dataset (replica plan)

### H) Export
- CSV, JSON, Parquet (minimo) + opzionale Excel
- bundle sempre con manifest/dictionary/provenance

### I) Compliance & lifecycle
- fatture/ricevute PDF
- annullamento abbonamento (se presente)
- revoca metodi pagamento tramite provider portal
- purge dati post-delete

---

## 4. Requisiti non funzionali
- Scalabilità: pipeline asincrona (queue + workers)
- Osservabilità: log step, trace id, metriche base
- Sicurezza: JWT, signed URL, isolamento tenant, webhook idempotenti
- Trasparenza e provenance
- Manutenibilità: plugin connectors + plugin normalizers

---

## 5. MVP (prima release)
- Auth + profilo
- Chat OpenAI → DatasetPlan
- Orchestrazione pipeline (collect→normalize→export)
- 3 connettori: WorldBank, Eurostat, PubMed
- Export CSV/JSON/Parquet + manifest/dictionary
- Stripe + storico dataset + ricevuta/fattura PDF
- Eliminazione account (soft delete)

---

## 6. Definizione di “Done”
- Utente si registra
- Crea dataset via chat
- Pipeline produce file
- Paga e scarica
- Vede fattura/ricevuta
- Ritrova tutto nello storico
- Può cancellare account
