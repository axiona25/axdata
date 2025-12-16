# 📧 Configurazione Email con SendGrid

Questo documento descrive come configurare l'invio di email tramite SendGrid SMTP per il backend AXDATA.

## 🔧 Configurazione

### 1. Ottieni la SendGrid API Key

1. Registrati su [SendGrid](https://sendgrid.com/)
2. Vai su **Settings** → **API Keys**
3. Crea una nuova API Key con permessi **Mail Send**
4. Copia la chiave API generata

### 2. Configurazione nel Backend

#### Opzione A: File API_KEYS.md (Consigliato)

Aggiungi la sezione SendGrid nel file `API_KEYS.md` nella root del progetto:

```markdown
## 📧 SendGrid

**API KEY**:
```
SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### Opzione B: Variabili d'Ambiente

Aggiungi nel file `.env`:

```env
# SendGrid Email Configuration
EMAIL_ENABLED=true
EMAIL_SMTP_HOST=smtp.sendgrid.net
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=apikey
EMAIL_SMTP_PASSWORD=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EMAIL_USE_TLS=true
EMAIL_FROM=no-reply@axdata.it
```

### 3. Configurazione DNS per Evitare SPAM

Per evitare che le email finiscano in SPAM, configura nel pannello DNS del tuo dominio:

#### SPF Record
Aggiungi un record TXT:
```
v=spf1 include:sendgrid.net ~all
```

#### DKIM Record
1. Vai su SendGrid → **Settings** → **Sender Authentication**
2. Configura il dominio
3. Aggiungi i record CNAME forniti da SendGrid nel tuo DNS

#### DMARC Record
Aggiungi un record TXT:
```
v=DMARC1; p=quarantine; rua=mailto:dmarc@axdata.it
```

## 📝 Variabili di Configurazione

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `EMAIL_ENABLED` | `true` | Abilita/disabilita l'invio email |
| `EMAIL_SMTP_HOST` | `smtp.sendgrid.net` | Host SMTP SendGrid |
| `EMAIL_SMTP_PORT` | `587` | Porta SMTP (TLS) |
| `EMAIL_SMTP_USER` | `apikey` | Username SMTP (fisso per SendGrid) |
| `EMAIL_SMTP_PASSWORD` | - | SendGrid API Key (richiesto) |
| `EMAIL_USE_TLS` | `true` | Usa TLS per la connessione |
| `EMAIL_FROM` | `no-reply@axdata.it` | Indirizzo email mittente |

## 🧪 Test

Per testare l'invio email, puoi:

1. **Registrare un nuovo utente** - Dovrebbe ricevere email di verifica
2. **Richiedere reset password** - Dovrebbe ricevere email di reset
3. **Verificare i log** - Controlla i log del backend per errori

## 🔍 Troubleshooting

### Email non vengono inviate

1. Verifica che `EMAIL_SMTP_PASSWORD` sia configurato correttamente
2. Controlla i log del backend per errori SMTP
3. Verifica che `EMAIL_ENABLED=true`
4. Controlla che la SendGrid API Key abbia permessi "Mail Send"

### Email finiscono in SPAM

1. Configura SPF, DKIM e DMARC nel DNS
2. Verifica che il dominio sia autenticato in SendGrid
3. Evita contenuti che triggerano filtri spam
4. Usa un indirizzo email verificato come mittente

### Errori SMTP

- **535 Authentication failed**: API Key non valida o scaduta
- **Connection timeout**: Verifica firewall/network
- **TLS errors**: Verifica che `EMAIL_USE_TLS=true` e porta 587

## 📚 Documentazione SendGrid

- [SendGrid SMTP Documentation](https://docs.sendgrid.com/for-developers/sending-email/getting-started-smtp)
- [SendGrid API Keys](https://docs.sendgrid.com/ui/account-and-settings/api-keys)
- [Sender Authentication](https://docs.sendgrid.com/ui/account-and-settings/how-to-set-up-domain-authentication)
