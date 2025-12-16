# 📧 Setup SendGrid - Guida Completa

## ⚠️ Problema Attuale

SendGrid richiede che l'indirizzo email "from" sia verificato prima di poter inviare email. L'errore che vedi è:
```
The from address does not match a verified Sender Identity
```

## ✅ Soluzione: Verifica Sender Identity su SendGrid

### Opzione 1: Single Sender Verification (Consigliato per Test)

1. **Vai su SendGrid Dashboard**:
   - Accedi a https://app.sendgrid.com/

2. **Vai a Sender Authentication**:
   - Menu laterale → **Settings** → **Sender Authentication**
   - Oppure vai direttamente: https://app.sendgrid.com/settings/sender_auth/senders

3. **Crea un Single Sender**:
   - Clicca su **"Create a Sender"**
   - Compila il form:
     - **From Email**: `r.amoroso80@gmail.com` (o un altro indirizzo email che controlli)
     - **From Name**: `AXDATA` (o il nome che preferisci)
     - **Reply To**: `r.amoroso80@gmail.com`
     - **Address**: Il tuo indirizzo fisico (richiesto per verificazione)
     - **City, State, Country**: I tuoi dati
   - Clicca **"Create"**

4. **Verifica l'Email**:
   - SendGrid invierà un'email di verifica all'indirizzo che hai specificato
   - Apri l'email e clicca sul link di verifica
   - Una volta verificato, lo stato diventerà "Verified"

5. **Aggiorna la Configurazione**:
   - Assicurati che `email_from` in `core/config.py` corrisponda all'indirizzo verificato
   - Riavvia il backend

### Opzione 2: Domain Authentication (Per Produzione)

Se vuoi usare `no-reply@axdata.it`:

1. **Vai a Domain Authentication**:
   - Menu → **Settings** → **Sender Authentication** → **Domain Authentication**
   - Clicca **"Authenticate Your Domain"**

2. **Inserisci il Dominio**:
   - Dominio: `axdata.it` (o il tuo dominio)

3. **Configura i Record DNS**:
   - SendGrid ti fornirà i record DNS da aggiungere:
     - **CNAME records** per DKIM
     - **TXT record** per SPF
     - **TXT record** per DMARC (opzionale ma consigliato)

4. **Aggiungi i Record DNS**:
   - Vai al pannello di controllo del tuo dominio
   - Aggiungi i record DNS forniti da SendGrid
   - Attendi la propagazione DNS (può richiedere fino a 48 ore)

5. **Verifica il Dominio**:
   - Torna su SendGrid e clicca **"Verify"**
   - Una volta verificato, puoi usare qualsiasi indirizzo `@axdata.it`

## 🔧 Configurazione Backend

Dopo aver verificato l'indirizzo email su SendGrid:

1. **Aggiorna `core/config.py`**:
   ```python
   email_from: str = "r.amoroso80@gmail.com"  # Usa l'indirizzo verificato
   ```

2. **Riavvia il Backend**:
   ```bash
   # Arresta il backend
   lsof -ti:8000 | xargs kill -9
   
   # Riavvia
   cd apps/backend
   source venv/bin/activate
   python run.py
   ```

## ✅ Verifica Funzionamento

Dopo la configurazione, prova a registrare un nuovo utente. Dovresti vedere nei log:
```
✅ Email service enabled. SMTP: smtp.sendgrid.net:587, From: r.amoroso80@gmail.com
✅ Verification email sent successfully to ...
```

E l'email dovrebbe arrivare nella casella di posta.

## 📝 Note Importanti

- **Single Sender**: Puoi verificare fino a 100 indirizzi email (piano gratuito)
- **Domain Authentication**: Una volta verificato il dominio, puoi usare qualsiasi indirizzo su quel dominio
- **Spam**: Le email da indirizzi non verificati vengono rifiutate da SendGrid
- **Test**: Per i test, usa Single Sender Verification con un indirizzo email che controlli

## 🔗 Link Utili

- Dashboard SendGrid: https://app.sendgrid.com/
- Sender Authentication: https://app.sendgrid.com/settings/sender_auth
- Documentazione: https://sendgrid.com/docs/for-developers/sending-email/sender-identity/
