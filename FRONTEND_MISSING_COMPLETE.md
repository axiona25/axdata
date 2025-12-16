# Cosa Manca Lato Frontend - Analisi Completa

## 📊 Stato Attuale Frontend

**Esistente:**
- ✅ Struttura base React + TypeScript + Vite
- ✅ Autenticazione (Login, Register, Password Reset)
- ✅ Layout e navigazione base
- ✅ Dashboard con statistiche mock
- ✅ DatasetPage con lista dataset mock
- ✅ BillingPage base
- ✅ ProfilePage base

**Mancante:**
- ❌ Integrazione reale con backend API
- ❌ Wizard per creare dataset (DS-SPEC)
- ❌ Chat per creazione dataset
- ❌ Visualizzazione dataset con tab Provenance/Quality/Compliance
- ❌ Progress tracking pipeline
- ❌ Download dataset
- ❌ Integrazione pagamenti

---

## ❌ Componenti Critici Mancanti

### 1. 🔴 Wizard Creazione Dataset con Chat OpenAI (CRITICO)

**Problema**: Non esiste un modo per creare dataset dal frontend

**Flusso corretto**:
1. **Step 1 - Chat Interface**: Utente scrive richiesta in linguaggio naturale
   - Chat usa OpenAI per interpretare la richiesta
   - OpenAI genera DatasetPlan tramite tool calling
   - Frontend mostra preview del DatasetPlan generato
2. **Step 2 - Preview e Conferma**: Utente vede e può modificare
   - Mostra DatasetPlan generato (settore, dimensioni, variabili, etc.)
   - Utente può modificare o confermare
3. **Step 3 - Conversione e Invio**: 
   - Converte DatasetPlan → DS-SPEC (automatico)
   - Invia DS-SPEC a backend per creare dataset

**Cosa serve**:
- Modal/Wizard con chat integrata
- Chat interface con streaming OpenAI
- Estrazione DatasetPlan da tool calling
- Preview DatasetPlan generato
- Conversione DatasetPlan → DS-SPEC
- Validazione e invio

**Endpoint backend**: 
- `POST /api/v1/chat/sessions` - Crea sessione chat
- `POST /api/v1/chat/sessions/{id}/messages` - Invia messaggio (streaming, tool calling)
- `POST /api/v1/datasets/from-ds-spec` - Crea dataset da DS-SPEC

**File da creare**:
- `apps/frontend/src/components/DatasetWizard.tsx` - Wizard principale
- `apps/frontend/src/components/DatasetWizardSteps/ChatStep.tsx` - Step 1: Chat
- `apps/frontend/src/components/DatasetWizardSteps/PreviewStep.tsx` - Step 2: Preview
- `apps/frontend/src/components/DatasetWizardSteps/ConfirmStep.tsx` - Step 3: Conferma
- `apps/frontend/src/components/ChatInterface.tsx` - Componente chat riutilizzabile
- `apps/frontend/src/hooks/useChat.ts` - Hook per chat con streaming
- `apps/frontend/src/hooks/useDatasetPlan.ts` - Hook per gestire DatasetPlan

**Priorità**: 🔴 CRITICO - Senza questo gli utenti non possono creare dataset

---

### 2. 🔴 Visualizzazione Dataset Dettaglio (CRITICO)

**Problema**: DatasetPage mostra solo lista, nessun dettaglio

**Cosa serve**:
- Pagina dettaglio dataset (`/dashboard/datasets/:id`)
- Tab navigation:
  - **Overview**: Metadata, schema, record count
  - **Provenance**: Sources, API endpoints, timeline, transformations, reproducibility
  - **Quality**: Score, completeness, missing values, outliers, cross-validation, notes
  - **Compliance**: Usage rights, licenses, PII check, jurisdiction, notes
  - **Data Preview**: Anteprima dati (primi 100 record)
- Download button (signed URL)
- Progress indicator se in elaborazione

**Endpoint backend**: 
- `GET /api/v1/datasets/{id}` - Dettagli dataset
- `GET /api/v1/datasets/{id}/progress` - Progress pipeline
- `GET /api/v1/datasets/{id}/download` - Signed URL download

**File da creare**:
- `apps/frontend/src/pages/DatasetDetailPage.tsx`
- `apps/frontend/src/components/DatasetTabs/ProvenanceTab.tsx`
- `apps/frontend/src/components/DatasetTabs/QualityTab.tsx`
- `apps/frontend/src/components/DatasetTabs/ComplianceTab.tsx`
- `apps/frontend/src/components/DatasetTabs/OverviewTab.tsx`
- `apps/frontend/src/components/DatasetTabs/DataPreviewTab.tsx`

**Priorità**: 🔴 CRITICO - Senza questo gli utenti non possono vedere i loro dataset

---

### 3. 🔴 Integrazione API Backend (CRITICO)

**Problema**: Frontend usa dati mock, nessuna integrazione reale

**Cosa serve**:
- Service layer per chiamate API
- TypeScript types per DS-SPEC, Dataset, etc.
- React Query hooks per data fetching
- Error handling e loading states
- Cache management

**File da creare/modificare**:
- `apps/frontend/src/lib/datasetApi.ts` - API calls per dataset
- `apps/frontend/src/hooks/useDatasets.ts` - React Query hooks
- `apps/frontend/src/hooks/useDatasetDetail.ts`
- `apps/frontend/src/hooks/useCreateDataset.ts`
- `apps/frontend/src/types/dataset.ts` - TypeScript types
- `apps/frontend/src/types/dsSpec.ts` - DS-SPEC types

**Priorità**: 🔴 CRITICO - Senza questo il frontend non funziona

---

### 4. 🔴 Progress Tracking Pipeline (IMPORTANTE)

**Problema**: Nessun modo di vedere lo stato di elaborazione

**Cosa serve**:
- Componente progress bar con step
- Timeline visuale degli step
- Real-time updates (polling o WebSocket)
- Error display se pipeline fallisce
- Log viewer per debugging

**Endpoint backend**: `GET /api/v1/datasets/{id}/progress`

**File da creare**:
- `apps/frontend/src/components/PipelineProgress.tsx`
- `apps/frontend/src/components/PipelineTimeline.tsx`
- `apps/frontend/src/hooks/usePipelineProgress.ts`

**Priorità**: 🟡 IMPORTANTE - UX migliore

---

### 5. 🟡 Chat per Creazione Dataset (IMPORTANTE)

**Problema**: Non esiste chat per creare dataset in linguaggio naturale

**Cosa serve**:
- Chat interface con OpenAI
- Streaming response
- Estrazione DatasetPlan da chat
- Conversione DatasetPlan → DS-SPEC
- Preview e conferma prima di creare

**Endpoint backend**: 
- `POST /api/v1/chat/sessions` - Crea sessione
- `POST /api/v1/chat/sessions/{id}/messages` - Invia messaggio (streaming)

**File da creare**:
- `apps/frontend/src/pages/ChatPage.tsx`
- `apps/frontend/src/components/ChatInterface.tsx`
- `apps/frontend/src/components/ChatMessage.tsx`
- `apps/frontend/src/hooks/useChat.ts`
- `apps/frontend/src/hooks/useChatStream.ts`

**Priorità**: 🟡 IMPORTANTE - Feature principale del prodotto

---

### 6. 🟡 Download Dataset (IMPORTANTE)

**Problema**: Nessun modo di scaricare dataset

**Cosa serve**:
- Button download nella lista e dettaglio
- Gestione signed URL
- Progress download
- Gestione errori (file non disponibile, etc.)

**Endpoint backend**: `GET /api/v1/datasets/{id}/download`

**File da creare/modificare**:
- `apps/frontend/src/hooks/useDownloadDataset.ts`
- Modificare `DatasetPage.tsx` e `DatasetDetailPage.tsx`

**Priorità**: 🟡 IMPORTANTE - Funzionalità core

---

### 7. 🟡 Integrazione Pagamenti (IMPORTANTE)

**Problema**: BillingPage esiste ma non integrata

**Cosa serve**:
- Integrazione Stripe Checkout
- Redirect a Stripe per pagamento
- Webhook handling (backend)
- Visualizzazione invoice/receipt
- Gestione package credits

**Endpoint backend**: 
- `POST /api/v1/billing/checkout`
- `GET /api/v1/billing/invoices`

**File da creare/modificare**:
- `apps/frontend/src/components/StripeCheckout.tsx`
- `apps/frontend/src/hooks/useCheckout.ts`
- Modificare `BillingPage.tsx`

**Priorità**: 🟡 IMPORTANTE - Monetizzazione

---

### 8. 🟢 Miglioramenti UX (OPZIONALE)

**Cosa serve**:
- Loading skeletons
- Empty states
- Error boundaries
- Toast notifications
- Confirmation dialogs
- Form validation migliorata

**Priorità**: 🟢 OPZIONALE - Nice to have

---

## 🎯 Priorità di Implementazione

### 🔴 Critico (Blocca funzionalità)
1. **Wizard Creazione Dataset** - Senza questo non si possono creare dataset
2. **Visualizzazione Dataset Dettaglio** - Senza questo non si vedono i dataset
3. **Integrazione API Backend** - Senza questo il frontend non funziona

### 🟡 Importante (Migliora UX)
4. **Progress Tracking** - Mostra stato elaborazione
5. **Chat per Creazione** - Feature principale
6. **Download Dataset** - Funzionalità core
7. **Integrazione Pagamenti** - Monetizzazione

### 🟢 Opzionale (Nice to have)
8. **Miglioramenti UX** - Polish finale

---

## 📋 Checklist Implementazione

### Fase 1: Core Funzionalità (CRITICO)
- [ ] Creare `DatasetWizard.tsx` con 5 step
- [ ] Creare `DatasetDetailPage.tsx` con tab navigation
- [ ] Creare `datasetApi.ts` con tutte le chiamate API
- [ ] Creare TypeScript types per DS-SPEC e Dataset
- [ ] Integrare `DatasetPage.tsx` con API reale
- [ ] Test end-to-end: crea dataset → visualizza → download

### Fase 2: Feature Avanzate (IMPORTANTE)
- [ ] Creare `ChatPage.tsx` con streaming
- [ ] Creare `PipelineProgress.tsx` con real-time updates
- [ ] Integrare download con signed URL
- [ ] Integrare Stripe Checkout
- [ ] Test completo flusso utente

### Fase 3: Polish (OPZIONALE)
- [ ] Loading states
- [ ] Error handling migliorato
- [ ] Toast notifications
- [ ] Empty states
- [ ] Animazioni

---

## 🧩 Mappatura UI ↔ Backend

| Funzionalità Frontend | Endpoint Backend | Stato |
|----------------------|------------------|-------|
| **Creazione Dataset** | `POST /api/v1/datasets/from-ds-spec` | ❌ Non integrato |
| **Lista Dataset** | `GET /api/v1/datasets` | ❌ Non integrato |
| **Dettaglio Dataset** | `GET /api/v1/datasets/{id}` | ❌ Non integrato |
| **Progress Pipeline** | `GET /api/v1/datasets/{id}/progress` | ❌ Non integrato |
| **Download Dataset** | `GET /api/v1/datasets/{id}/download` | ❌ Non integrato |
| **Chat** | `POST /api/v1/chat/sessions/{id}/messages` | ❌ Non integrato |
| **Checkout** | `POST /api/v1/billing/checkout` | ❌ Non integrato |

---

## 📊 Stato Attuale vs Target

| Componente | Stato Attuale | Target | Gap |
|------------|---------------|--------|-----|
| **Wizard Creazione** | ❌ Non esiste | ✅ Multi-step wizard | 100% |
| **Visualizzazione Dataset** | ⚠️ Solo lista mock | ✅ Dettaglio completo con tab | 80% |
| **Integrazione API** | ❌ Nessuna | ✅ Completa | 100% |
| **Progress Tracking** | ❌ Non esiste | ✅ Real-time progress | 100% |
| **Chat** | ❌ Non esiste | ✅ Chat con streaming | 100% |
| **Download** | ❌ Non funziona | ✅ Signed URL download | 100% |
| **Pagamenti** | ⚠️ Pagina base | ✅ Stripe integrato | 70% |

---

## 🚀 Raccomandazione

**Per avere un sistema completo funzionante, implementare in ordine:**

1. ✅ **Fase 1 - Core (CRITICO)**:
   - Wizard creazione dataset
   - Visualizzazione dettaglio con tab
   - Integrazione API completa
   - **Tempo stimato**: 2-3 giorni

2. ✅ **Fase 2 - Feature (IMPORTANTE)**:
   - Progress tracking
   - Download
   - Chat (se prioritario)
   - Pagamenti
   - **Tempo stimato**: 2-3 giorni

3. ✅ **Fase 3 - Polish (OPZIONALE)**:
   - UX improvements
   - **Tempo stimato**: 1 giorno

**Totale stimato**: 5-7 giorni per sistema completo

---

## ✅ Conclusione

**Frontend: 30% Completo**

Manca principalmente:
- ❌ Wizard creazione dataset (CRITICO)
- ❌ Visualizzazione dettaglio dataset (CRITICO)
- ❌ Integrazione API backend (CRITICO)
- ❌ Progress tracking (IMPORTANTE)
- ❌ Chat (IMPORTANTE)
- ❌ Download (IMPORTANTE)

**Con Fase 1 implementata, il sistema sarà funzionante end-to-end.**
