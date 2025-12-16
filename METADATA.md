# Metadati Progetto AXDATA

## Informazioni Generali

**Nome Progetto**: AXDATA  
**Versione**: 1.0.0  
**Data Creazione**: 2024-12-16  
**Licenza**: Proprietaria  
**Repository**: https://github.com/axiona25/axdata

## Descrizione

AXDATA è una piattaforma completa per la creazione, gestione e distribuzione di dataset standardizzati. Il sistema utilizza 8 template universali per normalizzare dati provenienti da fonti pubbliche diverse, garantendo conformità FAIR e DCAT.

## Architettura

### Stack Tecnologico

**Backend**:
- Python 3.9+
- FastAPI
- PostgreSQL
- Redis
- Celery
- Alembic (migrazioni DB)
- Pydantic v2

**Frontend**:
- React 19
- TypeScript
- Vite
- Tailwind CSS
- Axios
- React Router v7

**Infrastruttura**:
- Docker Compose
- MinIO (S3-compatible storage)
- PostgreSQL
- Redis

### Struttura Progetto

```
AX_Dataset/
├── apps/
│   ├── backend/          # API FastAPI
│   ├── frontend/         # React Application
│   └── collector/        # Data Collection Services
├── infra/                # Docker Compose configs
├── scripts/              # Utility scripts
└── docs/                 # Documentazione
```

## Componenti Principali

### Backend

1. **DS-SPEC v1**: Specifica interna per richieste dataset
2. **Source Selection Engine**: Selezione automatica fonti dati
3. **Template Decision Engine**: Scelta template appropriato
4. **Pipeline Orchestration**: Orchestrazione flusso dati
5. **Domain Normalizers**: Normalizzazione per dominio (SDMX, CDISC, FAIR)
6. **Template Transformers**: Trasformazione in 8 template standardizzati
7. **Data Packaging**: Creazione bundle dataset con metadata

### Frontend

1. **DatasetWizard**: Wizard multi-step per creazione dataset
2. **Chat Interface**: Integrazione OpenAI per generazione DatasetPlan
3. **Dataset Management**: Gestione lista e dettagli dataset
4. **Authentication**: Sistema autenticazione e autorizzazione

## Fonti Dati Supportate

Il sistema supporta 26 fonti dati pubbliche configurate:

- ISTAT (Istituto Nazionale di Statistica)
- Eurostat
- World Bank
- OECD
- UN Data
- NASA
- NOAA
- Copernicus
- E altri...

Ogni fonte ha un manifest JSON che descrive:
- Endpoint API
- Parametri supportati
- Formato dati
- Metadati disponibili

## Template Dataset

Il sistema supporta 8 template universali:

1. **Tabular**: Dati tabellari standard
2. **Time Series**: Serie temporali
3. **Cross-Sectional**: Dati cross-sectional
4. **Longitudinal/Panel**: Dati panel/longitudinal
5. **Geospatial**: Dati geospaziali
6. **Textual/Document**: Dati testuali/documenti
7. **Event-Based**: Dati event-based
8. **Knowledge-Enriched/Hybrid**: Dati arricchiti/ibridi

## Standard e Compliance

- **FAIR Principles**: Findable, Accessible, Interoperable, Reusable
- **DCAT**: Data Catalog Vocabulary
- **SDMX**: Statistical Data and Metadata Exchange
- **CDISC**: Clinical Data Interchange Standards Consortium

## API Endpoints

### Autenticazione
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/register`
- `GET /api/v1/auth/me`

### Chat
- `POST /api/v1/chat/sessions`
- `POST /api/v1/chat/sessions/{id}/messages/stream`

### Dataset
- `POST /api/v1/datasets/from-ds-spec`
- `POST /api/v1/datasets/convert-plan-to-ds-spec`
- `GET /api/v1/datasets`
- `GET /api/v1/datasets/{id}`

Documentazione completa: http://localhost:8000/docs

## Configurazione

### Variabili d'Ambiente Backend

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/axdata
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=your_key_here
SECRET_KEY=your_secret_key
```

### Variabili d'Ambiente Frontend

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Installazione

Vedi `COMANDI_AVVIO.md` per istruzioni complete di setup e avvio.

## Contributori

- Team AXDATA

## Supporto

Per supporto e domande, consultare la documentazione o aprire un issue su GitHub.
