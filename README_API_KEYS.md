# 🔑 Gestione API Keys

## 📋 Panoramica

Tutte le API keys dei servizi terzi sono centralizzate nel file `API_KEYS.md` nella root del progetto.

## 🎯 Come Funziona

1. **File Centralizzato**: `API_KEYS.md` contiene tutte le chiavi
2. **Caricamento Automatico**: Il sistema carica automaticamente le chiavi da questo file
3. **Fallback**: Se la chiave non è nel file, viene cercata nelle variabili d'ambiente (`.env`)
4. **Sicurezza**: Il file `API_KEYS.md` è nel `.gitignore` e NON viene committato

## 📝 Struttura File

Il file `API_KEYS.md` ha questa struttura:

```markdown
## 🤖 OpenAI

**API KEY**: 
```
sk-proj-...
```

## 💳 Stripe

**Secret Key**: 
```
sk_test_...
```
```

## 🔧 Utilizzo nel Codice

Le chiavi vengono caricate automaticamente tramite il modulo `core.api_keys.py`:

```python
from core.api_keys import get_openai_api_key

# Carica da API_KEYS.md o da .env
api_key = get_openai_api_key()
```

Oppure vengono caricate automaticamente nella configurazione:

```python
from core.config import settings

# settings.openai_api_key è già popolato da API_KEYS.md o .env
```

## ✅ Servizi Supportati

- ✅ **OpenAI**: API key per GPT-4
- ⏳ **Stripe**: Secret key, Publishable key, Webhook secret (da aggiungere)
- ⏳ **DigitalOcean Spaces**: Access keys (da aggiungere)

## 🚀 Aggiungere una Nuova API Key

1. Apri `API_KEYS.md`
2. Aggiungi una nuova sezione per il servizio:
   ```markdown
   ## 🆕 Nuovo Servizio
   
   **API KEY**: 
   ```
   your-key-here
   ```
   ```
3. Aggiungi una funzione helper in `core/api_keys.py`:
   ```python
   def get_nuovo_servizio_key() -> Optional[str]:
       key = load_api_key("Nuovo Servizio", "API KEY")
       if key:
           return key
       return os.getenv("NUOVO_SERVIZIO_KEY")
   ```
4. Aggiorna `core/config.py` per caricarla automaticamente

## ⚠️ Sicurezza

- **NON committare mai** `API_KEYS.md` nel repository
- Il file è già nel `.gitignore`
- In produzione, usa sempre variabili d'ambiente
- Ruota le chiavi periodicamente

## 📚 Documentazione

Per maggiori dettagli, vedi:
- `API_KEYS.md` - File con tutte le chiavi
- `apps/backend/core/api_keys.py` - Modulo di caricamento
- `apps/backend/core/config.py` - Configurazione che usa le chiavi

