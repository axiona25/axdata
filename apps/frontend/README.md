# AXDATA Frontend

Frontend React per il portale AXDATA, sviluppato con Vite, TypeScript, Tailwind CSS e React Router.

## 🎨 Design

Il frontend segue lo stile del mockup AXDATA con:
- **Dark Theme**: Sfondo scuro (#1A1E24) con accenti blu (#3B82F6) e arancione (#F59E0B)
- **Font**: Inter (Google Fonts)
- **UI/UX**: Design moderno con bordi arrotondati, card e modali

## 🚀 Setup

### Prerequisiti
- Node.js 18+
- npm o yarn

### Installazione

```bash
cd apps/frontend
npm install
```

### Configurazione

Crea un file `.env` nella root del frontend:

```env
VITE_API_BASE_URL=http://localhost:8001
```

### Avvio

```bash
npm run dev
```

Il frontend sarà disponibile su `http://localhost:5173`

## 📁 Struttura

```
src/
├── components/          # Componenti riutilizzabili
│   └── RegistrationWizard.tsx
├── lib/                # Utilities e API client
│   ├── api.ts         # Axios client configurato
│   └── auth.ts        # API di autenticazione
├── pages/              # Pagine dell'applicazione
│   ├── LoginPage.tsx
│   ├── RegisterPage.tsx
│   ├── ForgotPasswordPage.tsx
│   ├── ResetPasswordPage.tsx
│   └── VerifyEmailPage.tsx
├── App.tsx            # Componente principale con routing
├── main.tsx           # Entry point
└── index.css          # Stili globali Tailwind
```

## 🔐 Pagine di Autenticazione

### Login
- `/login` - Pagina di login con email e password

### Registrazione
- `/register` - Pagina di registrazione con wizard modale a 3 step:
  1. **Step 1**: Nome, Cognome, Email, Cellulare, Password (con validazione)
  2. **Step 2**: Data di Nascita, Indirizzo, Nazione, Nazionalità, Lingua
  3. **Step 3**: Metodo di Pagamento

### Recupero Password
- `/forgot-password` - Richiesta reset password via email
- `/reset-password?token=...` - Reset password con token

### Verifica Email
- `/verify-email?token=...` - Verifica email con token

## 🛠️ Tecnologie

- **React 19** - Framework UI
- **TypeScript** - Type safety
- **Vite** - Build tool veloce
- **Tailwind CSS** - Styling utility-first
- **React Router** - Routing
- **React Hook Form** - Gestione form
- **Zod** - Validazione schema
- **TanStack Query** - State management e data fetching
- **Axios** - HTTP client
- **Lucide React** - Icone

## 📝 Note

- I token JWT vengono salvati in `localStorage`
- Il refresh token viene gestito automaticamente tramite interceptor Axios
- Le email di verifica e reset password devono essere implementate nel backend (attualmente solo log)
