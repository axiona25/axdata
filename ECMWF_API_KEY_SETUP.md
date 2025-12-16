# 🔑 Come Ottenere l'API Key per Copernicus CDS

## 📋 Informazioni Credenziali

**Username**: `r.amoroso80@gmail.com`  
**Password**: `L_kKZKh*2hp&9q4`

## 🔐 Passaggi per Ottenere l'API Key

### 1. Accedi al Portale Copernicus CDS

Vai su: https://cds.climate.copernicus.eu/user/login

Inserisci le credenziali:
- **Username/Email**: `r.amoroso80@gmail.com`
- **Password**: `L_kKZKh*2hp&9q4`

### 2. Ottieni l'API Key

Dopo il login:

1. Vai su: https://cds.climate.copernicus.eu/#!/home
2. Clicca sul tuo profilo (in alto a destra)
3. Vai alla sezione **"API key"** o **"Show API key"**
4. Copia:
   - **URL**: `https://cds.climate.copernicus.eu/api`
   - **Key**: `<PERSONAL-ACCESS-TOKEN>` (il tuo Personal Access Token)

### 3. Configura l'API Key

**Opzione A: File di configurazione (consigliato)**

Crea il file `~/.ecmwfdatastoresrc`:

```bash
cat > ~/.ecmwfdatastoresrc << EOF
url: https://cds.climate.copernicus.eu/api
key: <PERSONAL-ACCESS-TOKEN>
EOF

chmod 600 ~/.ecmwfdatastoresrc
```

**⚠️ IMPORTANTE**: Sostituisci `<PERSONAL-ACCESS-TOKEN>` con il tuo token personale ottenuto dal portale CDS.

**Opzione B: Variabili d'ambiente**

Aggiungi al file `.env` del collector o esporta:

```bash
export ECMWF_DATASTORES_URL="https://cds.climate.copernicus.eu/api"
export ECMWF_DATASTORES_KEY="<PERSONAL-ACCESS-TOKEN>"
```

**⚠️ IMPORTANTE**: Sostituisci `<PERSONAL-ACCESS-TOKEN>` con il tuo token personale.

### 4. Test della Configurazione

Esegui il test:

```bash
python3 scripts/test_nasa_copernicus.py
```

## 🔄 Alternative: CDSE (Data Space Ecosystem)

Se preferisci usare CDSE invece di CDS, le credenziali CDSE sono già configurate:

```bash
export COPERNICUS_CDSE_USERNAME="r.amoroso80@gmail.com"
export COPERNICUS_CDSE_PASSWORD="*4Nmzt4=?55KtcL"
```

Il connettore genererà automaticamente il token OAuth2 quando necessario.

## ⚠️ Note

- L'API Key è diversa dallo username/password
- L'API Key viene utilizzata direttamente nelle richieste API
- Mantieni l'API Key segreta e non committarla nel repository
- Il file `~/.ecmwfdatastoresrc` è nel tuo home directory (`/Users/r.amoroso/.ecmwfdatastoresrc`)

## 🔗 Link Utili

- **CDS Portal**: https://cds.climate.copernicus.eu/
- **Documentazione API**: https://cds.climate.copernicus.eu/api-how-to
- **ecmwf-datastores-client**: https://github.com/ecmwf/ecmwf-datastores-client

