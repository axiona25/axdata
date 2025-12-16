# 🔧 Quick Fix - Risoluzione Immediata

## Problema: "ModuleNotFoundError: No module named 'uvicorn'"

### Soluzione Rapida

```bash
# 1. Vai nella cartella backend
cd apps/backend

# 2. Attiva il virtual environment (se non già attivo)
source venv/bin/activate

# 3. Verifica che il venv sia attivo (dovresti vedere (venv) nel prompt)
which python  # Dovrebbe mostrare .../apps/backend/venv/bin/python

# 4. Installa tutte le dipendenze
pip install --upgrade pip
pip install -r requirements.txt

# 5. Verifica che uvicorn sia installato
python -c "import uvicorn; print('✅ Uvicorn installato correttamente')"

# 6. Ora puoi avviare il backend
python run.py
```

### Se il venv non esiste

```bash
cd apps/backend

# Crea il venv
python3 -m venv venv

# Attivalo
source venv/bin/activate

# Installa dipendenze
pip install --upgrade pip
pip install -r requirements.txt

# Avvia
python run.py
```

### Verifica Setup Completo

```bash
# Backend
cd apps/backend
source venv/bin/activate
python -c "import uvicorn, fastapi, sqlalchemy; print('✅ Tutte le dipendenze installate')"

# Frontend
cd apps/frontend
npm list --depth=0 | head -5
```
