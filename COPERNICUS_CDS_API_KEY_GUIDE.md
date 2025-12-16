# 🔑 Guida Completa: Come Trovare l'API Key di Copernicus CDS

## 📋 Informazioni Preliminari

**Credenziali**:
- Username/Email: `r.amoroso80@gmail.com`
- Password: `L_kKZKh*2hp&9q4`

## ⚠️ IMPORTANTE: Due Sistemi Disponibili

Copernicus CDS supporta **due sistemi di autenticazione**:

1. **CDS API tradizionale** (`cdsapi` Python library) - usa file `.cdsapirc`
2. **ECMWF Data Stores Client** (`ecmwf-datastores-client`) - usa file `.ecmwfdatastoresrc`

Il nostro connettore usa il **sistema moderno** (`ecmwf-datastores-client`), ma l'API key si trova nello stesso posto.

## 🔍 Metodo 1: Tramite Profilo Utente (Tradizionale)

### Passo 1: Accedi al Portale
1. Vai su: https://cds.climate.copernicus.eu/
2. Clicca su **"Login"** in alto a destra
3. Inserisci le credenziali:
   - Email: `r.amoroso80@gmail.com`
   - Password: `L_kKZKh*2hp&9q4`

### Passo 2: Vai al Profilo
1. Dopo il login, clicca sul tuo **nome utente** in alto a destra (dovrebbe apparire invece di "Login")
2. Dal menu a discesa, seleziona **"My profile"** o **"Profile"**

### Passo 3: Cerca la Sezione API Key
Nella pagina del profilo, cerca una delle seguenti sezioni:
- **"API key"**
- **"Personal Access Token"**
- **"API credentials"**
- **"Show API key"**

**⚠️ Nota**: Secondo la [documentazione ufficiale ECMWF Confluence](https://confluence.ecmwf.int/pages/viewpage.action?pageId=55116796), l'API key si trova nella **pagina del profilo CDS**. Potrebbe essere necessario:
1. Completare il profilo utente (first-access)
2. Accettare le licenze dei dataset di interesse
3. Poi la sezione API key diventerà visibile

### Passo 4: Copia le Informazioni
Dovresti vedere qualcosa come:
```
url: https://cds.climate.copernicus.eu/api
key: <PERSONAL-ACCESS-TOKEN>
```

Oppure (formato tradizionale):
```
url: https://cds.climate.copernicus.eu/api/v2
key: <username>:<token>
```

**Formato per ECMWF Data Stores Client**:
```
url: https://cds.climate.copernicus.eu/api
key: <PERSONAL-ACCESS-TOKEN>
```

## 🔍 Metodo 2: Tramite Pagina API How-To

### Passo 1: Accedi e Vai alla Pagina API
1. Fai login come sopra
2. Vai su: https://cds.climate.copernicus.eu/api-how-to
3. Cerca un link o pulsante che dice **"Show your API key"** o **"Get your API key"**

## 🔍 Metodo 3: Verifica se il Token è già Generato

A volte il token viene generato automaticamente al primo accesso. Prova a:

1. Vai su: https://cds.climate.copernicus.eu/api-how-to
2. Cerca nella pagina istruzioni o link per visualizzare la tua API key
3. Potrebbe esserci un pulsante **"Show API key"** o simile

## 🔍 Metodo 4: Tramite URL Diretto (se disponibile)

Prova ad accedere direttamente a:
- https://cds.climate.copernicus.eu/user/profile
- https://cds.climate.copernicus.eu/user/api-key
- https://cds.climate.copernicus.eu/#!/app/profile

## ⚠️ Note Importanti

1. **Completa il Profilo**: Se vedi una pagina "first-access" o "Activate your profile", completa prima quella configurazione. Potrebbe essere necessario completare il profilo prima di vedere l'API key.

2. **Formato del Token**: 
   - Il formato potrebbe essere: `username:token` (due parti separate da `:`)
   - Oppure solo il token: `<PERSONAL-ACCESS-TOKEN>`
   - L'URL potrebbe essere `/api` o `/api/v2`

3. **Se Non Vedi la Sezione**:
   - Prova a completare il profilo utente (first-access)
   - Controlla se ci sono tab o sezioni collassate nella pagina del profilo
   - Cerca nella pagina "API How-To" per link diretti

## 📝 Configurazione Completata ✅

**API Key Configurata**:
- **URL**: `https://cds.climate.copernicus.eu/api`
- **Key**: `e2594876-b436-4f9c-a779-cbef3df1bf31`

**File creato**: `~/.ecmwfdatastoresrc` (per `ecmwf-datastores-client`)

```bash
cat > ~/.ecmwfdatastoresrc << EOF
url: https://cds.climate.copernicus.eu/api
key: e2594876-b436-4f9c-a779-cbef3df1bf31
EOF

chmod 600 ~/.ecmwfdatastoresrc
```

**✅ Test Completato**: Il connettore Copernicus funziona correttamente e può recuperare dati dal CDS!

**⚠️ Nota**: Se usi il client tradizionale `cdsapi`, il file si chiama `~/.cdsapirc` invece di `~/.ecmwfdatastoresrc`.

Oppure configura le variabili d'ambiente:
```bash
export ECMWF_DATASTORES_URL="https://cds.climate.copernicus.eu/api"
export ECMWF_DATASTORES_KEY="<IL_TUO_TOKEN_QUI>"
```

## 🆘 Se Continui a Non Trovarlo

1. **Completa il profilo**: Assicurati di aver completato la configurazione iniziale del profilo (first-access)
2. **Accetta le licenze**: Potrebbe essere necessario accettare le licenze dei dataset prima che l'API key sia visibile
3. **Controlla la documentazione ufficiale**: 
   - https://cds.climate.copernicus.eu/api-how-to
   - [ECMWF Confluence Knowledge Base](https://confluence.ecmwf.int/pages/viewpage.action?pageId=55116796)
4. **Cerca nel Forum**: https://cds.climate.copernicus.eu/forum
5. **Contatta il supporto**: Potrebbe essere necessario contattare il supporto CDS se l'API key non è visibile

## 📚 Riferimenti

- [ECMWF Confluence - CAMS and C3S Knowledge Base](https://confluence.ecmwf.int/pages/viewpage.action?pageId=55116796)
- [CDS API How-To](https://cds.climate.copernicus.eu/api-how-to)
- [ECMWF Data Stores Client Documentation](https://ecmwf.github.io/ecmwf-datastores-client/)

## 💡 Alternativa: Usa CDSE invece di CDS

Se non riesci a trovare l'API key per CDS, puoi usare **CDSE (Data Space Ecosystem)** che usa OAuth2 e le credenziali sono già configurate:

```bash
export COPERNICUS_CDSE_USERNAME="r.amoroso80@gmail.com"
export COPERNICUS_CDSE_PASSWORD="*4Nmzt4=?55KtcL"
```

Il connettore genererà automaticamente il token quando necessario.

