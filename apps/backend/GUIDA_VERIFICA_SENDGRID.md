# 🔧 Guida Passo-Passo: Verifica Sender su SendGrid

## ⚠️ Problema Attuale

SendGrid sta rifiutando l'invio email con questo errore:
```
The from address does not match a verified Sender Identity
```

Questo significa che **devi verificare l'indirizzo email "from"** prima di poter inviare email.

## ✅ Soluzione: Verifica Single Sender Identity

### Passo 1: Accedi a SendGrid
1. Vai su https://app.sendgrid.com/
2. Fai login con il tuo account SendGrid

### Passo 2: Vai a Sender Authentication
1. Nel menu laterale sinistro, clicca su **"Settings"** (⚙️)
2. Nella sezione "Sender Authentication", clicca su **"Single Sender Verification"**
3. Oppure vai direttamente: https://app.sendgrid.com/settings/sender_auth/senders

### Passo 3: Crea un Nuovo Sender
1. Clicca sul pulsante **"Create a Sender"** (in alto a destra)
2. Compila il form con questi dati:

   **Informazioni Email:**
   - **From Email**: `r.amoroso80@gmail.com` ⚠️ **DEVE essere questo indirizzo**
   - **From Name**: `AXDATA` (o qualsiasi nome)
   - **Reply To**: `r.amoroso80@gmail.com`
   
   **Informazioni Azienda:**
   - **Company Address**: Il tuo indirizzo fisico completo
   - **City**: La tua città
   - **State**: Il tuo stato/provincia
   - **Country**: Il tuo paese
   - **Zip Code**: Il tuo CAP

3. Clicca su **"Create"**

### Passo 4: Verifica l'Email
1. SendGrid invierà un'email di verifica a `r.amoroso80@gmail.com`
2. **Controlla la casella email** (anche spam/promozioni)
3. Apri l'email da SendGrid
4. Clicca sul link **"Verify Single Sender"** o il pulsante di verifica
5. Torna su SendGrid e verifica che lo stato sia cambiato da "Pending" a **"Verified"** ✅

### Passo 5: Verifica lo Stato
1. Torna su https://app.sendgrid.com/settings/sender_auth/senders
2. Dovresti vedere `r.amoroso80@gmail.com` con stato **"Verified"** (verde)
3. Se è ancora "Pending", clicca su "Resend Verification Email"

## 🔄 Dopo la Verifica

Una volta verificato il sender:
1. **Riavvia il backend** (se è in esecuzione):
   ```bash
   lsof -ti:8000 | xargs kill -9
   cd apps/backend
   source venv/bin/activate
   python run.py
   ```

2. **Prova a registrare un nuovo utente**
3. L'email dovrebbe arrivare correttamente

## ❓ Problemi Comuni

### "Non ricevo l'email di verifica"
- Controlla la cartella **Spam/Promozioni**
- Aspetta qualche minuto (può richiedere fino a 5-10 minuti)
- Clicca su "Resend Verification Email" su SendGrid

### "Lo stato rimane Pending"
- Assicurati di aver cliccato sul link nell'email di verifica
- Controlla che l'email sia arrivata alla casella corretta
- Prova a eliminare il sender e ricrearlo

### "Vedo ancora l'errore dopo la verifica"
- Assicurati che `email_from` in `core/config.py` sia esattamente `r.amoroso80@gmail.com`
- Riavvia il backend completamente
- Verifica che il sender su SendGrid sia effettivamente "Verified" (non "Pending")

## 📸 Screenshot di Riferimento

Dopo la verifica, dovresti vedere qualcosa del genere su SendGrid:

```
Single Sender Verification
┌─────────────────────────────────────────┐
│ From Email: r.amoroso80@gmail.com      │
│ Status: ✅ Verified                     │
│ From Name: AXDATA                      │
│ Created: [data]                        │
└─────────────────────────────────────────┘
```

## 🔗 Link Diretti

- **Single Sender Verification**: https://app.sendgrid.com/settings/sender_auth/senders
- **Dashboard SendGrid**: https://app.sendgrid.com/
- **Documentazione**: https://sendgrid.com/docs/for-developers/sending-email/sender-identity/

---

**Nota**: Se dopo aver seguito tutti questi passaggi l'email non funziona ancora, possiamo passare all'API SendGrid invece di SMTP, che potrebbe essere più flessibile.
