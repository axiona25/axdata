# 🌍 Setup Copernicus Climate Data Store

## 📋 Panoramica

Il connettore Copernicus usa il client ufficiale **ECMWF Data Stores Client** (`ecmwf-datastores-client`) per accedere ai dati del Copernicus Climate Data Store.

## 🔧 Installazione

### Con pip:
```bash
pip install ecmwf-datastores-client
```

### Con conda:
```bash
conda install -c conda-forge ecmwf-datastores-client
```

## 🔑 Configurazione API Key / Token

Copernicus supporta due metodi di autenticazione:

### Metodo 1: ECMWF Data Stores Client (CDS - Climate Data Store)

Per il **Climate Data Store (CDS)**, usa il client ufficiale `ecmwf-datastores-client`.

#### Passo 1: Registrazione
1. Vai su https://cds.climate.copernicus.eu/user/register
2. Crea un account
3. Verifica la tua email

#### Passo 2: Ottenere API Key
1. Accedi su https://cds.climate.copernicus.eu/#!/home
2. Clicca sul tuo profilo (in alto a destra)
3. Vai alla sezione **"API key"**
4. Copia:
   - **URL**: `https://cds.climate.copernicus.eu/api`
   - **Key**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` (formato UUID)

#### Passo 3: Configurare le Credenziali

**Opzione A: File di configurazione (consigliato)**

Crea il file `~/.ecmwfdatastoresrc`:
```yaml
url: https://cds.climate.copernicus.eu/api
key: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

**Opzione B: Variabili d'ambiente**

Aggiungi al tuo `.env` o esporta:
```bash
export ECMWF_DATASTORES_URL="https://cds.climate.copernicus.eu/api"
export ECMWF_DATASTORES_KEY="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

**Opzione C: Nel codice (solo per test)**

```python
from ecmwf.datastores import Client

client = Client(
    url="https://cds.climate.copernicus.eu/api",
    key="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
)
```

---

### Metodo 2: OAuth2 Token (CDSE - Copernicus Data Space Ecosystem)

Per il **Copernicus Data Space Ecosystem (CDSE)**, usa OAuth2 per ottenere un access token.

#### Passo 1: Ottenere Access Token

Usa questo comando per ottenere il token:

```bash
export ACCESS_TOKEN=$(curl -d 'client_id=cdse-public' \
                    -d 'username=<username>' \
                    -d 'password=<password>' \
                    -d 'grant_type=password' \
                    'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token' | \
                    python3 -m json.tool | grep "access_token" | awk -F\" '{print $4}')
```

Sostituisci:
- `<username>`: Il tuo username Copernicus
- `<password>`: La tua password Copernicus

#### Passo 2: Usare il Token

Il token può essere usato nelle richieste HTTP come Bearer token:

```bash
# Verifica il token
echo $ACCESS_TOKEN

# Usa il token in una richiesta
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
     "https://dataspace.copernicus.eu/api/v1/data/products/..."
```

#### Passo 3: Configurare come Variabile d'Ambiente

Per usarlo nel progetto, aggiungi al file `.env`:

```bash
COPERNICUS_CDSE_ACCESS_TOKEN=<your_access_token>
```

Oppure esporta direttamente:

```bash
export COPERNICUS_CDSE_ACCESS_TOKEN="<your_access_token>"
```

**Nota**: Il token OAuth2 ha una scadenza. Per ottenere un nuovo token, esegui di nuovo il comando curl sopra.

## ✅ Verifica Configurazione

Test rapido:
```python
from ecmwf.datastores import Client

client = Client()
client.check_authentication()  # Dovrebbe funzionare senza errori
print("✅ Autenticazione riuscita!")
```

## 📖 Esempi di Utilizzo

### Esempio 1: Lista Collection Disponibili
```python
from ecmwf.datastores import Client

client = Client()
collections = client.get_collections(sortby="update")

for collection in collections:
    print(f"{collection.id}: {collection.title}")
```

### Esempio 2: Recuperare Metadata di una Collection
```python
collection = client.get_collection("reanalysis-era5-pressure-levels")
print(f"Title: {collection.title}")
print(f"Description: {collection.description}")
print(f"Date range: {collection.begin_datetime} to {collection.end_datetime}")
```

### Esempio 3: Scaricare Dati
```python
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

# Download diretto (blocca fino al completamento)
client.retrieve(collection_id, request, target="output.grib")

# Oppure submit asincrono
remote = client.submit(collection_id, request)
# ... fai altre cose ...
remote.download("output.grib")
```

## 🔗 Link Utili

- **Pagina principale**: https://cds.climate.copernicus.eu/
- **Documentazione API**: https://cds.climate.copernicus.eu/api-how-to
- **Client Documentation**: https://ecmwf.github.io/ecmwf-datastores-client/
- **GitHub Client**: https://github.com/ecmwf/ecmwf-datastores-client
- **Registrazione**: https://cds.climate.copernicus.eu/user/register

## ⚠️ Note Importanti

1. **Rate Limiting**: Copernicus CDS ha limiti di rate. Non fare troppe richieste simultanee.
2. **Formato Dati**: I dati vengono scaricati in formato GRIB o NetCDF, non JSON.
3. **Dimensione**: I dataset possono essere molto grandi. Assicurati di avere spazio sufficiente.
4. **Tempo di Elaborazione**: Alcune richieste possono richiedere tempo per essere elaborate.

## 🐛 Troubleshooting

### Errore: "Authentication failed"
- Verifica che l'API key sia corretta
- Controlla che il file `~/.ecmwfdatastoresrc` abbia il formato corretto
- Verifica che le variabili d'ambiente siano impostate correttamente

### Errore: "Collection not found"
- Verifica che il `collection_id` sia corretto
- Usa `client.get_collections()` per vedere le collection disponibili

### Errore: "Invalid request"
- Verifica che tutti i parametri richiesti siano presenti
- Usa `client.apply_constraints()` per vedere i valori disponibili

---

**Ultimo aggiornamento**: 2024-12-14

