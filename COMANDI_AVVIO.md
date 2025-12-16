# 🚀 Comandi Avvio - AXDATA

Questo documento contiene i comandi per avviare il backend e il frontend del progetto AXDATA.

## 📋 Prerequisiti

- Python 3.9+ installato
- Node.js 18+ installato
- PostgreSQL in esecuzione (via Docker Compose o installazione locale)
- Redis in esecuzione (via Docker Compose o installazione locale)
- Variabili d'ambiente configurate (file `.env`)

## API 
Github: https://github.com/axiona25/axdata
Token: [CONFIGURARE IL TOKEN GITHUB NELLE VARIABILI D'AMBIENTE]

## 🔧 Setup Iniziale (Prima Volta)

### 1. Setup Backend

```bash
# Dalla root del progetto
cd apps/backend

# Crea virtual environment (se non esiste)
python3 -m venv venv

# Attiva virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# Installa dipendenze
pip install --upgrade pip
pip install -r requirements.txt

# Applica migrazioni DB (include tabella app_assets per il logo AXDATA)
alembic upgrade head

# Verifica installazione
python -c "import uvicorn; print('✅ Uvicorn installato')"
```

### 2. Setup Frontend

```bash
# Dalla root del progetto
cd apps/frontend

# Installa dipendenze
npm install

# Verifica installazione
npm list --depth=0
```

## 🛑 Arrestare Servizi Esistenti

Prima di avviare i servizi, verifica e arresta eventuali processi attivi sulle porte 8000 (backend) e 3000 (frontend).

### macOS / Linux

```bash
# Verifica processi sulla porta 8000 (backend)
lsof -ti:8000

# Verifica processi sulla porta 3000 (frontend)
lsof -ti:3000

# Arresta processi sulla porta 8000
lsof -ti:8000 | xargs kill -9

# Arresta processi sulla porta 3000
lsof -ti:3000 | xargs kill -9

# Oppure in un unico comando per entrambe le porte
lsof -ti:8000,3000 | xargs kill -9 2>/dev/null || echo "Nessun processo da arrestare"
```

### Windows (PowerShell)

```powershell
# Verifica processi sulla porta 8000
netstat -ano | findstr :8000

# Verifica processi sulla porta 3000
netstat -ano | findstr :3000

# Arresta processo sulla porta 8000 (sostituisci PID con il numero del processo)
taskkill /PID <PID> /F

# Arresta processo sulla porta 3000 (sostituisci PID con il numero del processo)
taskkill /PID <PID> /F
```

## 🔧 Avvio Backend (Porta 8000)

**⚠️ IMPORTANTE**: Assicurati di avere attivato il virtual environment prima di avviare il backend!

```bash
# Attiva virtual environment (se non già attivo)
cd apps/backend
source venv/bin/activate  # macOS/Linux
# oppure: venv\Scripts\activate  # Windows

# Verifica che uvicorn sia installato
python -c "import uvicorn" || pip install -r requirements.txt
```

### Opzione 1: Usando run.py (Consigliato)

```bash
# Dalla root del progetto
cd apps/backend

# Assicurati che il venv sia attivo
source venv/bin/activate  # macOS/Linux

# Avvia backend
python run.py
```

### Opzione 2: Usando uvicorn direttamente

```bash
# Dalla root del progetto
cd apps/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Opzione 3: Con variabili d'ambiente personalizzate

```bash
cd apps/backend
API_PORT=8000 python run.py
```

Il backend sarà disponibile su: **http://localhost:8000**

Documentazione API: **http://localhost:8000/docs**

## 🎨 Avvio Frontend (Porta 3000)

### Primo avvio (installazione dipendenze)

```bash
# Dalla root del progetto
cd apps/frontend
npm install
npm run dev
```

### Avvii successivi

```bash
# Dalla root del progetto
cd apps/frontend
npm run dev
```

Il frontend sarà disponibile su: **http://localhost:3000**

## 🐳 Avvio Servizi di Supporto (Docker Compose)

Se usi Docker Compose per PostgreSQL, Redis e MinIO:

```bash
# Dalla root del progetto
cd infra
docker-compose up -d

# Verifica che i servizi siano attivi
docker-compose ps
```

## 📝 Script di Avvio Completo (macOS/Linux)

Crea uno script `start.sh` nella root del progetto:

```bash
#!/bin/bash

# Colori per output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🛑 Arrestando servizi esistenti...${NC}"
lsof -ti:8000,3000 | xargs kill -9 2>/dev/null || echo "Nessun processo da arrestare"

echo -e "${YELLOW}🐳 Avviando servizi Docker...${NC}"
cd infra && docker-compose up -d && cd ..

echo -e "${YELLOW}⏳ Attendere 5 secondi per l'avvio dei servizi...${NC}"
sleep 5

echo -e "${GREEN}🚀 Avviando Backend sulla porta 8000...${NC}"
cd apps/backend

# Attiva virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo -e "${RED}❌ Virtual environment non trovato!${NC}"
    echo -e "${YELLOW}Creando virtual environment...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Verifica che uvicorn sia installato
python -c "import uvicorn" 2>/dev/null || {
    echo -e "${YELLOW}Installando dipendenze...${NC}"
    pip install -r requirements.txt
}

python run.py &
BACKEND_PID=$!
cd ../..

echo -e "${GREEN}🎨 Avviando Frontend sulla porta 3000...${NC}"
cd apps/frontend

# Verifica che node_modules esista
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installando dipendenze frontend...${NC}"
    npm install
fi

npm run dev &
FRONTEND_PID=$!
cd ../..

echo -e "${GREEN}✅ Servizi avviati!${NC}"
echo -e "Backend: http://localhost:8000 (PID: $BACKEND_PID)"
echo -e "Frontend: http://localhost:3000 (PID: $FRONTEND_PID)"
echo -e "API Docs: http://localhost:8000/docs"
echo -e "\n${YELLOW}Premi Ctrl+C per arrestare tutti i servizi${NC}"

# Funzione per cleanup al termine
cleanup() {
    echo -e "\n${YELLOW}🛑 Arrestando servizi...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    lsof -ti:8000,3000 | xargs kill -9 2>/dev/null
    echo -e "${GREEN}✅ Servizi arrestati${NC}"
    exit 0
}

# Trap per catturare Ctrl+C
trap cleanup SIGINT SIGTERM

# Attendi che i processi finiscano
wait
```

Rendi eseguibile lo script:

```bash
chmod +x start.sh
```

Esegui con:

```bash
./start.sh
```

## 🔍 Verifica Servizi Attivi

### Controlla porte in uso

```bash
# macOS/Linux
lsof -i :8000
lsof -i :3000

# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :3000
```

### Testa connessioni

```bash
# Test backend
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000
```

## 🐛 Troubleshooting

### Porta già in uso

```bash
# Trova il processo che usa la porta
lsof -i :8000
lsof -i :3000

# Arresta il processo (sostituisci PID)
kill -9 <PID>
```

### Backend non si avvia

1. **Verifica che il virtual environment sia attivo**:
   ```bash
   cd apps/backend
   source venv/bin/activate  # macOS/Linux
   which python  # Dovrebbe mostrare il path del venv
   ```

2. **Installa/Reinstalla dipendenze**:
   ```bash
   cd apps/backend
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Verifica che uvicorn sia installato**:
   ```bash
   python -c "import uvicorn; print('✅ OK')"
   ```

4. Verifica che PostgreSQL e Redis siano attivi
5. Controlla il file `.env` nella cartella `apps/backend`
6. Controlla i log per errori

### Errore "ModuleNotFoundError: No module named 'uvicorn'"

```bash
# Soluzione: Installa le dipendenze nel venv
cd apps/backend
source venv/bin/activate
pip install -r requirements.txt
```

### Errore "pyenv: uvicorn: command not found"

Questo significa che stai usando pyenv ma uvicorn non è nel PATH. Usa Python dal venv:

```bash
cd apps/backend
source venv/bin/activate
python run.py  # Usa 'python' non 'uvicorn' direttamente
```

### Frontend non si avvia

1. Verifica che Node.js sia installato: `node --version`
2. Reinstalla dipendenze: `cd apps/frontend && rm -rf node_modules && npm install`
3. Verifica che la porta 3000 sia libera
4. Controlla il file `.env` nella cartella `apps/frontend`

### Errori di connessione tra frontend e backend

1. Verifica che `VITE_API_BASE_URL` in `apps/frontend/.env` sia `http://localhost:8000`
2. Se non esiste il file `.env`, crealo con:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   ```
3. Il default è già configurato su `http://localhost:8000` nel codice

## 📚 Comandi Utili

### Backend

```bash
# Avvia in modalità produzione (senza reload)
cd apps/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Avvia con log dettagliati
uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level debug

# Esegui migrazioni database
cd apps/backend
alembic upgrade head
```

### Frontend

```bash
# Build per produzione
cd apps/frontend
npm run build

# Preview build produzione
npm run preview

# Lint del codice
npm run lint
```

## 🔄 Riavvio Rapido

```bash
# Arresta tutto
lsof -ti:8000,3000 | xargs kill -9 2>/dev/null

# Avvia backend (con venv attivo)
cd apps/backend
source venv/bin/activate  # macOS/Linux
python run.py &

# Avvia frontend (in un altro terminale)
cd apps/frontend
npm run dev &
```

## ⚡ Comandi Rapidi per Terminali Separati

### Terminale 1 - Backend

```bash
cd apps/backend
source venv/bin/activate
python run.py
```

### Terminale 2 - Frontend

```bash
cd apps/frontend
npm run dev
```

---

**Nota**: Assicurati di avere tutte le variabili d'ambiente configurate correttamente prima di avviare i servizi. Vedi `README.md` per i dettagli sulla configurazione.
