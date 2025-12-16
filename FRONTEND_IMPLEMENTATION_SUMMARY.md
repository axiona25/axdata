# Frontend - Implementazione Wizard con Chat OpenAI

## ✅ Implementato

### Flusso Corretto (come richiesto)

**Step 1 - Chat Interface**:
- Utente scrive richiesta in linguaggio naturale (es: "GDP per capita in paesi UE dal 2020 al 2024")
- Chat usa OpenAI con streaming (`/api/v1/chat/sessions/{id}/messages/stream`)
- OpenAI interpreta la richiesta e genera DatasetPlan tramite tool calling
- Backend estrae DatasetPlan e lo invia nel stream SSE
- Frontend estrae DatasetPlan automaticamente e passa a Step 2

**Step 2 - Preview**:
- Mostra DatasetPlan generato dall'AI
- Utente può vedere e confermare
- Clicca "Conferma e Continua"

**Step 3 - Conversione e Creazione**:
- Frontend chiama `/api/v1/datasets/convert-plan-to-ds-spec` per convertire DatasetPlan → DS-SPEC
- Mostra DS-SPEC finale
- Utente conferma e crea dataset via `/api/v1/datasets/from-ds-spec`

---

## 📁 File Creati/Modificati

### Frontend (7 nuovi file)
1. ✅ `apps/frontend/src/components/DatasetWizard.tsx` - Wizard principale
2. ✅ `apps/frontend/src/components/DatasetWizardSteps/ChatStep.tsx` - Chat con OpenAI
3. ✅ `apps/frontend/src/components/DatasetWizardSteps/PreviewStep.tsx` - Preview DatasetPlan
4. ✅ `apps/frontend/src/components/DatasetWizardSteps/ConfirmStep.tsx` - Conferma finale
5. ✅ `apps/frontend/src/hooks/useChat.ts` - Hook chat con streaming
6. ✅ `apps/frontend/src/hooks/useCreateDataset.ts` - Hook creazione dataset
7. ✅ `apps/frontend/src/types/dataset.ts` - TypeScript types

### Frontend (1 file modificato)
8. ✅ `apps/frontend/src/pages/DatasetPage.tsx` - Aggiunto button "Crea Nuovo Dataset" e wizard modal

### Backend (2 file modificati)
9. ✅ `apps/backend/api/routers/datasets.py` - Aggiunto endpoint `POST /convert-plan-to-ds-spec`
10. ✅ `apps/backend/api/routers/chat.py` - Migliorato streaming per estrarre DatasetPlan

---

## 🔄 Flusso Dettagliato

```
┌─────────────────────────────────────────────────────────────┐
│ 1. UTENTE CLICCA "Crea Nuovo Dataset"                        │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. DatasetWizard Modal si apre                               │
│    - Step corrente: "chat"                                   │
│    - Crea sessione chat automaticamente                      │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. CHAT STEP                                                 │
│    Utente scrive: "GDP per capita in paesi UE 2020-2024"     │
│    ↓                                                          │
│    Frontend: POST /api/v1/chat/sessions/{id}/messages/stream│
│    ↓                                                          │
│    Backend: OpenAI streaming con tool calling                │
│    ↓                                                          │
│    OpenAI: Genera DatasetPlan tramite create_dataset_plan    │
│    ↓                                                          │
│    Backend: Estrae DatasetPlan e invia nel stream            │
│    ↓                                                          │
│    Frontend: Estrae DatasetPlan da stream                    │
│    ↓                                                          │
│    Frontend: onDatasetPlanGenerated(plan)                    │
│    ↓                                                          │
│    Wizard: setCurrentStep('preview')                         │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. PREVIEW STEP                                              │
│    - Mostra DatasetPlan generato                             │
│    - Utente vede: domain, title, sources, coverage           │
│    - Utente clicca "Conferma e Continua"                     │
│    ↓                                                          │
│    Frontend: convertPlanToDsSpec(plan)                       │
│    ↓                                                          │
│    Frontend: POST /api/v1/datasets/convert-plan-to-ds-spec  │
│    ↓                                                          │
│    Backend: convert_dataset_plan_to_ds_spec(plan)           │
│    ↓                                                          │
│    Backend: Ritorna DS-SPEC                                  │
│    ↓                                                          │
│    Frontend: setDsSpec(dsSpec), setCurrentStep('confirm')    │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. CONFIRM STEP                                              │
│    - Mostra DS-SPEC finale                                   │
│    - Utente clicca "Crea Dataset"                            │
│    ↓                                                          │
│    Frontend: createDataset(dsSpec, chatSessionId)            │
│    ↓                                                          │
│    Frontend: POST /api/v1/datasets/from-ds-spec             │
│    ↓                                                          │
│    Backend: Crea dataset e avvia pipeline                    │
│    ↓                                                          │
│    Frontend: onSuccess(datasetId), chiude wizard             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Caratteristiche Implementate

### Chat Step
- ✅ Chat interface con streaming OpenAI
- ✅ Estrazione automatica DatasetPlan da tool calling
- ✅ Supporto per [DATASET_PLAN] marker nel stream
- ✅ Supporto per JSON code blocks
- ✅ Auto-scroll messaggi
- ✅ Loading states

### Preview Step
- ✅ Visualizzazione DatasetPlan generato
- ✅ Mostra: title, domain, sources, coverage
- ✅ JSON preview collapsible
- ✅ Button "Conferma e Continua"

### Confirm Step
- ✅ Visualizzazione DS-SPEC finale
- ✅ Info su cosa succederà
- ✅ Error handling
- ✅ Button "Crea Dataset" con loading

### Backend
- ✅ Endpoint conversione DatasetPlan → DS-SPEC
- ✅ Streaming migliorato con DatasetPlan extraction
- ✅ Error handling completo

---

## 🔧 Endpoint Backend

### 1. Chat Streaming
```
POST /api/v1/chat/sessions/{session_id}/messages/stream
Body: { "content": "GDP per capita...", "role": "user", "stream": true }
Response: SSE stream con:
  - data: {"content": "..."}
  - data: {"dataset_plan": {...}}  // Quando disponibile
  - data: {"done": true}
```

### 2. Conversione DatasetPlan → DS-SPEC
```
POST /api/v1/datasets/convert-plan-to-ds-spec
Body: { "plan": DatasetPlan }
Response: DS-SPEC (dictionary)
```

### 3. Creazione Dataset
```
POST /api/v1/datasets/from-ds-spec
Body: { "ds_spec": DS-SPEC, "chat_session_id": "..." }
Response: { "dataset_id": "...", ... }
```

---

## ✅ Stato

**Wizard con Chat OpenAI: COMPLETO**

- ✅ Chat interface con streaming
- ✅ Estrazione DatasetPlan automatica
- ✅ Preview DatasetPlan
- ✅ Conversione DatasetPlan → DS-SPEC
- ✅ Creazione dataset
- ✅ Integrazione DatasetPage

**Pronto per test end-to-end!**

---

## 📝 Note

- Il DatasetPlan viene estratto automaticamente dal tool calling di OpenAI
- Se OpenAI non genera DatasetPlan, l'utente può continuare a chattare
- La conversione DatasetPlan → DS-SPEC è automatica e intelligente
- Il wizard gestisce errori e loading states
