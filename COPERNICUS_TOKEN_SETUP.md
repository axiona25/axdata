# 🌍 Setup Token Copernicus - Metodo OAuth2 (CDSE)

## 📋 Panoramica

Per accedere al **Copernicus Data Space Ecosystem (CDSE)**, puoi usare un token OAuth2 invece del file di configurazione statico.

## 🔑 Ottenere il Token

### Metodo: Comando cURL

Esegui questo comando sostituendo `<username>` e `<password>` con le tue credenziali Copernicus:

```bash
export ACCESS_TOKEN=$(curl -d 'client_id=cdse-public' \
                    -d 'username=<username>' \
                    -d 'password=<password>' \
                    -d 'grant_type=password' \
                    'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token' | \
                    python3 -m json.tool | grep "access_token" | awk -F\" '{print $4}')
```

### Verifica il Token

Per vedere il token ottenuto:

```bash
echo $ACCESS_TOKEN
```

Dovresti vedere un token JWT lungo che inizia con `eyJ...`

## 💾 Salvare le Credenziali

### Opzione 1: Username e Password (Consigliato - Auto-genera Token)

Il connettore può generare automaticamente il token usando username e password:

**File .env del collector:**
```bash
COPERNICUS_CDSE_USERNAME=r.amoroso80@gmail.com
COPERNICUS_CDSE_PASSWORD=*4Nmzt4=?55KtcL
```

Oppure variabili d'ambiente:
```bash
export COPERNICUS_CDSE_USERNAME="r.amoroso80@gmail.com"
export COPERNICUS_CDSE_PASSWORD="*4Nmzt4=?55KtcL"
```

Il connettore genererà automaticamente il token quando necessario.

### Opzione 2: Token Manuale (Variabile d'Ambiente)

```bash
export COPERNICUS_CDSE_ACCESS_TOKEN="$ACCESS_TOKEN"
```

**Nota**: Questo token scade dopo un periodo di tempo. Per ottenerne uno nuovo, esegui di nuovo il comando curl.

### Opzione 3: File .env con Token

Aggiungi al file `.env` del collector:

```bash
COPERNICUS_CDSE_ACCESS_TOKEN=<your_access_token_here>
```

### Opzione 3: Script di Rinnovo Automatico

Crea uno script `get_copernicus_token.sh`:

```bash
#!/bin/bash

USERNAME="<your_username>"
PASSWORD="<your_password>"

TOKEN=$(curl -s -d 'client_id=cdse-public' \
             -d "username=$USERNAME" \
             -d "password=$PASSWORD" \
             -d 'grant_type=password' \
             'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token' | \
             python3 -m json.tool | grep "access_token" | awk -F\" '{print $4}')

export COPERNICUS_CDSE_ACCESS_TOKEN="$TOKEN"
echo "Token ottenuto: ${TOKEN:0:20}..."
```

Rendi eseguibile e usa:

```bash
chmod +x get_copernicus_token.sh
source get_copernicus_token.sh
```

## 🔐 Sicurezza

⚠️ **IMPORTANTE**: 
- Non committare mai il file `.env` con le password
- Non condividere il token in pubblico
- Il token ha una scadenza (solitamente 1 ora o più)
- Usa sempre variabili d'ambiente invece di hardcodare il token nel codice

## 📖 Uso del Token

Il connettore Copernicus userà automaticamente il token se è disponibile nella variabile d'ambiente `COPERNICUS_CDSE_ACCESS_TOKEN`.

Il token viene usato come Bearer token nelle richieste HTTP:

```
Authorization: Bearer <your_access_token>
```

## 🔄 Rinnovo Token

Quando il token scade, esegui di nuovo il comando curl per ottenere un nuovo token e aggiorna la variabile d'ambiente o il file `.env`.

Puoi anche creare un cron job per rinnovare automaticamente il token:

```bash
# Aggiungi a crontab (rinnova ogni 6 ore)
0 */6 * * * source /path/to/get_copernicus_token.sh >> /var/log/copernicus_token.log 2>&1
```

## 🔗 Link Utili

- **CDSE Portal**: https://dataspace.copernicus.eu/
- **Identity Provider**: https://identity.dataspace.copernicus.eu/
- **Documentazione**: https://documentation.dataspace.copernicus.eu/

---

**Ultimo aggiornamento**: 2024-12-14

