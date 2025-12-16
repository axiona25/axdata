# 📧 Spiegazione: Email FROM vs TO

## 🔍 Differenza Importante

Quando invii un'email, ci sono **due indirizzi diversi**:

### 📤 **FROM (Da)**
- È l'indirizzo **da cui parte l'email**
- È l'indirizzo che vedi quando ricevi l'email (es. "Da: no-reply@axdata.it")
- **DEVE essere verificato su SendGrid** prima di poter inviare
- Esempio: `no-reply@axdata.it` o `support@axdata.it`

### 📥 **TO (A)**
- È l'indirizzo **a cui arriva l'email**
- È l'email dell'utente che si registra
- **NON deve essere verificato** - può essere qualsiasi email
- Esempio: `r.amoroso80@gmail.com` (l'utente che si registra)

## 📝 Esempio Pratico

Quando un utente si registra con email `r.amoroso80@gmail.com`:

1. **Il sistema invia un'email**:
   - **FROM**: `no-reply@axdata.it` (indirizzo aziendale verificato)
   - **TO**: `r.amoroso80@gmail.com` (email dell'utente che si registra)
   - **Oggetto**: "Conferma il tuo account AXDATA"

2. **L'utente riceve l'email**:
   - Vede "Da: no-reply@axdata.it"
   - Vede "A: r.amoroso80@gmail.com"
   - Clicca sul link per verificare l'account

## ⚙️ Configurazione

Nel file `core/config.py`:
```python
email_from: str = "no-reply@axdata.it"  # Indirizzo "from" verificato su SendGrid
```

Questo è l'indirizzo che **devi verificare su SendGrid**, non l'email degli utenti!

## ✅ Cosa Devi Fare

1. **Vai su SendGrid** e verifica l'indirizzo `no-reply@axdata.it` (o un altro indirizzo aziendale)
2. **Oppure** verifica un indirizzo email personale che controlli (es. `tuo-nome@gmail.com`)
3. **Aggiorna** `email_from` in `core/config.py` con l'indirizzo verificato
4. **Gli utenti possono registrarsi con qualsiasi email** - non serve verificare le loro email!

## 🔗 Link Utile

- Verifica Sender su SendGrid: https://app.sendgrid.com/settings/sender_auth/senders
