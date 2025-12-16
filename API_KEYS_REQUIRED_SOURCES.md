# 🔑 Fonti che Richiedono Token di Autenticazione

## 📋 Riepilogo Connettori che Richiedono Autenticazione

Questo documento elenca tutte le fonti di dati che richiedono token/API keys per l'accesso, con i link per ottenerli.

---

## 1. 🌍 Copernicus Climate Data Store (CDS)

**Connettore**: `copernicus`  
**Status**: ❌ Richiede autenticazione  
**Tipo**: Account + API Key  
**Client Ufficiale**: `ecmwf-datastores-client`

### Link Utili:
- **Pagina principale**: https://cds.climate.copernicus.eu/
- **Registrazione account**: https://cds.climate.copernicus.eu/user/register
- **API Documentation**: https://cds.climate.copernicus.eu/api-how-to
- **Guida API Key**: https://cds.climate.copernicus.eu/api-how-to#install-the-cds-api-key
- **Client Ufficiale**: https://ecmwf.github.io/ecmwf-datastores-client/
- **GitHub**: https://github.com/ecmwf/ecmwf-datastores-client

### Installazione Client:
```bash
# Con pip
pip install ecmwf-datastores-client

# Con conda
conda install -c conda-forge ecmwf-datastores-client
```

### Come Ottenere l'API Key:
1. Registrati su https://cds.climate.copernicus.eu/user/register
2. Vai su https://cds.climate.copernicus.eu/#!/home
3. Clicca sul tuo profilo (in alto a destra)
4. Vai alla sezione "API key"
5. Copia l'URL (es: `https://cds.climate.copernicus.eu/api`) e la key (formato UUID)

### Configurazione:

**Opzione 1: File di configurazione (consigliato)**
Crea file `~/.ecmwfdatastoresrc`:
```yaml
url: https://cds.climate.copernicus.eu/api
key: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

**Opzione 2: Variabili d'ambiente**
```bash
export ECMWF_DATASTORES_URL="https://cds.climate.copernicus.eu/api"
export ECMWF_DATASTORES_KEY="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

**Opzione 3: Nel codice**
```python
from ecmwf.datastores import Client
client = Client(
    url="https://cds.climate.copernicus.eu/api",
    key="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
)
```

### Esempio di Utilizzo:
```python
from ecmwf.datastores import Client

client = Client()
client.check_authentication()

# Recupera dati
collection_id = "reanalysis-era5-pressure-levels"
request = {
    "product_type": ["reanalysis"],
    "variable": ["temperature"],
    "year": ["2022"],
    "month": ["01"],
    "day": ["01"],
    "time": ["00:00"],
    "pressure_level": ["1000"],
    "data_format": "grib",
    "download_format": "unarchived",
}

client.retrieve(collection_id, request, target="output.grib")
```

---

## 2. 🚀 NASA Earth Data

**Connettore**: `nasa`  
**Status**: ✅ Credenziali configurate  
**Tipo**: NASA Earthdata Login + Bearer Token o Basic Auth

### Link Utili:
- **Pagina principale**: https://www.earthdata.nasa.gov/
- **Registrazione**: https://urs.earthdata.nasa.gov/users/new
- **Dashboard**: https://urs.earthdata.nasa.gov/profile
- **API Documentation**: https://wiki.earthdata.nasa.gov/display/EL/How+To+Access+Data+With+cURL+And+Wget
- **Earthdata Login**: https://urs.earthdata.nasa.gov/

### Credenziali Configurate:
✅ Username e Password salvate in `API_KEYS.md`
✅ Token disponibile (scade 2025-12-14)

**Credenziali**:
- Username: `r.amorooso80`
- Password: `MmdiZD.3Q/63Puj`

### Metodi di Autenticazione:

**Metodo 1: Bearer Token (se disponibile)**
Il token va usato come Bearer token nelle richieste HTTP:
```
Authorization: Bearer <token>
```

**Metodo 2: Basic Auth (username/password)**
Se username/password sono configurate, il connettore userà Basic Auth:
```
Authorization: Basic <base64(username:password)>
```

### Configurazione:
```bash
# Opzione 1: Token (se disponibile)
export NASA_EARTHDATA_TOKEN="<token>"

# Opzione 2: Username/Password (consigliato)
export NASA_EARTHDATA_USERNAME="r.amorooso80"
export NASA_EARTHDATA_PASSWORD="MmdiZD.3Q/63Puj"
```

### Come Ottenere un Nuovo Token:
1. Accedi su https://urs.earthdata.nasa.gov/ con username/password
2. Vai su https://urs.earthdata.nasa.gov/profile
3. Genera un nuovo token se necessario
4. Il token ha una scadenza (di solito 1 anno)
5. Usa il token come Bearer token nelle richieste

---

## 3. 🛰️ ESA (European Space Agency)

**Connettore**: `esa`  
**Status**: ❌ Richiede autenticazione  
**Tipo**: Account + API Key

### Link Utili:
- **Pagina principale**: https://www.esa.int/
- **ESA Data Portal**: https://earth.esa.int/
- **Copernicus Open Access Hub**: https://scihub.copernicus.eu/
- **Registrazione SciHub**: https://scihub.copernicus.eu/dhus/#/self-registration

### Come Ottenere l'API Key:
1. Per Copernicus Sentinel data: registrati su https://scihub.copernicus.eu/dhus/#/self-registration
2. Per altri dataset ESA: verifica su https://earth.esa.int/
3. Ottieni username e password per l'autenticazione

---

## 4. 🧮 Wolfram Data Repository

**Connettore**: `wolfram`  
**Status**: ❌ Richiede API Key  
**Tipo**: Wolfram API Key

### Link Utili:
- **Pagina principale**: https://www.wolfram.com/
- **Wolfram Cloud**: https://www.wolframcloud.com/
- **API Documentation**: https://reference.wolfram.com/language/guide/WolframCloud.html
- **Registrazione**: https://account.wolfram.com/login/create

### Come Ottenere l'API Key:
1. Registrati su https://account.wolfram.com/login/create
2. Vai su https://www.wolframcloud.com/
3. Crea un'applicazione
4. Ottieni l'API Key dalla dashboard

---

## 5. 💰 World Inequality Database (WID)

**Connettore**: `wid`  
**Status**: ❌ 403 Forbidden (potrebbe richiedere autenticazione)  
**Tipo**: Possibile API Key o registrazione

### Link Utili:
- **Pagina principale**: https://wid.world/
- **Data Portal**: https://wid.world/data/
- **API Documentation**: https://wid.world/documentation/
- **Contatti**: https://wid.world/contact/

### Note:
- WID potrebbe richiedere registrazione per l'accesso API
- Contatta il team WID per informazioni su accesso programmatico

---

## 6. 👔 ILO (International Labour Organization)

**Connettore**: `ilo`  
**Status**: ❌ 403 Forbidden (potrebbe richiedere autenticazione)  
**Tipo**: Possibile registrazione

### Link Utili:
- **Pagina principale**: https://www.ilo.org/
- **ILOSTAT**: https://ilostat.ilo.org/
- **Data Portal**: https://ilostat.ilo.org/data/
- **API Documentation**: https://ilostat.ilo.org/data/

### Note:
- ILO potrebbe richiedere registrazione per accesso API
- Verifica su https://ilostat.ilo.org/ per accesso programmatico

---

## 7. 🏥 CDC (Centers for Disease Control and Prevention)

**Connettore**: `cdc`  
**Status**: ❌ Dataset ID non trovati  
**Tipo**: Socrata API (potrebbe richiedere App Token)

### Link Utili:
- **Pagina principale**: https://data.cdc.gov/
- **Socrata API Docs**: https://dev.socrata.com/
- **CDC Data Catalog**: https://data.cdc.gov/browse

### Note:
- CDC usa Socrata API
- Alcuni dataset potrebbero richiedere App Token
- Registrati su https://dev.socrata.com/register per ottenere App Token

---

## 📝 Configurazione API Keys nel Progetto

Una volta ottenute le API keys, aggiungile al file `API_KEYS.md`:

```markdown
## Copernicus
- **API URL**: <your-url>
- **API Key**: <your-key>

## NASA
- **Earthdata Username**: <username>
- **Earthdata Password**: <password>
- **API Key**: <api-key> (se disponibile)

## ESA
- **Username**: <username>
- **Password**: <password>

## Wolfram
- **API Key**: <api-key>

## CDC (Socrata)
- **App Token**: <app-token> (opzionale)
```

---

## 🔍 Connettori da Verificare

Questi connettori potrebbero richiedere autenticazione ma non è ancora confermato:

- **ECB**: Potrebbe richiedere registrazione per alcuni dataset
- **IMF**: Potrebbe richiedere registrazione per accesso API completo
- **UN Data**: Potrebbe richiedere registrazione
- **WMO**: Potrebbe richiedere registrazione

---

## ✅ Connettori che NON Richiedono Autenticazione

Questi connettori funzionano senza autenticazione:

- ✅ CERN Open Data
- ✅ ClinicalTrials.gov
- ✅ Eurostat
- ✅ Global Carbon Project
- ✅ NOAA
- ✅ OECD
- ✅ OpenML
- ✅ PANGAEA
- ✅ PubMed
- ✅ UCI ML
- ✅ WHO GHO
- ✅ WorldBank

---

**Ultimo aggiornamento**: 2024-12-14

