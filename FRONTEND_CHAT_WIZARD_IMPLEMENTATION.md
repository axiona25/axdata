# Implementazione Wizard con Chat OpenAI - Frontend

## ✅ Flusso Implementato

### Step 1: Chat Interface
- Utente scrive richiesta in linguaggio naturale
- Chat usa OpenAI con streaming
- OpenAI genera DatasetPlan tramite tool calling
- Frontend estrae DatasetPlan automaticamente

### Step 2: Preview DatasetPlan
- Mostra DatasetPlan generato
- Utente può vedere/modificare
- Conferma per procedere

### Step 3: Conversione e Conferma
- Converte DatasetPlan → DS-SPEC (automatico via backend)
- Mostra DS-SPEC finale
- Utente conferma e crea dataset

---

## 📁 File Creati

### Componenti
1. `apps/frontend/src/components/DatasetWizard.tsx` - Wizard principale
2. `apps/frontend/src/components/DatasetWizardSteps/ChatStep.tsx` - Step 1: Chat
3. `apps/frontend/src/components/DatasetWizardSteps/PreviewStep.tsx` - Step 2: Preview
4. `apps/frontend/src/components/DatasetWizardSteps/ConfirmStep.tsx` - Step 3: Conferma

### Hooks
5. `apps/frontend/src/hooks/useChat.ts` - Hook per chat con streaming
6. `apps/frontend/src/hooks/useCreateDataset.ts` - Hook per creare dataset

### Types
7. `apps/frontend/src/types/dataset.ts` - TypeScript types per DatasetPlan e DS-SPEC

### Backend
8. `apps/backend/api/routers/datasets.py` - Endpoint `POST /api/v1/datasets/convert-plan-to-ds-spec`
9. `apps/backend/api/routers/chat.py` - Streaming migliorato per DatasetPlan extraction

---

## 🔄 Flusso Completo

```
1. Utente clicca "Crea Nuovo Dataset"
   ↓
2. Si apre DatasetWizard modal
   ↓
3. Step 1 - Chat:
   - Utente scrive: "GDP per capita in paesi UE dal 2020 al 2024"
   - Frontend invia a /api/v1/chat/sessions/{id}/messages (streaming)
   - OpenAI interpreta e chiama tool create_dataset_plan
   - Backend estrae DatasetPlan e lo invia nel stream
   - Frontend estrae DatasetPlan e passa a Step 2
   ↓
4. Step 2 - Preview:
   - Mostra DatasetPlan generato
   - Utente può vedere/modificare
   - Clicca "Conferma e Continua"
   ↓
5. Step 3 - Conversione:
   - Frontend chiama /api/v1/datasets/convert-plan-to-ds-spec
   - Backend converte DatasetPlan → DS-SPEC
   - Frontend mostra DS-SPEC finale
   - Utente clicca "Crea Dataset"
   ↓
6. Creazione Dataset:
   - Frontend chiama /api/v1/datasets/from-ds-spec
   - Backend crea dataset e avvia pipeline
   - Frontend chiude wizard e mostra successo
```

---

## 🔧 Integrazione Backend

### Endpoint Chat Streaming
- `POST /api/v1/chat/sessions/{id}/messages/stream`
- Streaming SSE con DatasetPlan extraction
- Invia `dataset_plan` nel stream quando disponibile

### Endpoint Conversione
- `POST /api/v1/datasets/convert-plan-to-ds-spec`
- Input: `{ "plan": DatasetPlan }`
- Output: `DS-SPEC` (dictionary)

### Endpoint Creazione
- `POST /api/v1/datasets/from-ds-spec`
- Input: `{ "ds_spec": DS-SPEC, "chat_session_id": "..." }`
- Output: `{ "dataset_id": "...", ... }`

---

## ✅ Stato Implementazione

- ✅ Wizard component creato
- ✅ Chat step con streaming
- ✅ Preview step
- ✅ Confirm step
- ✅ Hooks per chat e creazione
- ✅ Types TypeScript
- ✅ Endpoint conversione backend
- ✅ Integrazione DatasetPage

**Pronto per test!**
