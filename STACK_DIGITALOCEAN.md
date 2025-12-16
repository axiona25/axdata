# 🚀 Stack Tecnologico — DigitalOcean Ready

## 📋 Principio Fondamentale
**Tutto deve essere configurabile via variabili d'ambiente. Zero hardcoding. Plug-and-play da sviluppo a produzione.**

---

## 🗄️ Database: PostgreSQL

### Sviluppo
- **Docker**: `postgres:15-alpine` (locale)
- **Connection String**: `postgresql://user:pass@localhost:5432/dataset_portal`

### Produzione (DigitalOcean)
- **DigitalOcean Managed PostgreSQL**
- **Connection String**: Fornito da DO (con SSL)
- **Vantaggi**: Backup automatici, high availability, scaling

### Configurazione
```python
# .env
DATABASE_URL=postgresql://user:pass@localhost:5432/dataset_portal  # dev
# DATABASE_URL=postgresql://user:pass@db-do-user-xxx.db.ondigitalocean.com:25060/dataset_portal?sslmode=require  # prod
```

### Libreria
- **SQLAlchemy 2.x** (ORM)
- **Alembic** (migrazioni)
- **psycopg2** o **asyncpg** (driver)

**✅ Compatibilità**: 100% - Stesso codice, cambia solo connection string

---

## 🔴 Cache & Queue: Redis

### Sviluppo
- **Docker**: `redis:7-alpine` (locale)
- **Connection String**: `redis://localhost:6379/0`

### Produzione (DigitalOcean)
- **DigitalOcean Managed Redis**
- **Connection String**: Fornito da DO (con TLS)
- **Vantaggi**: Backup automatici, high availability, scaling

### Configurazione
```python
# .env
REDIS_URL=redis://localhost:6379/0  # dev
# REDIS_URL=rediss://user:pass@redis-do-user-xxx.db.ondigitalocean.com:25061/0  # prod (rediss = TLS)
```

### Libreria
- **redis-py** (client Redis)
- **Celery** (task queue) - usa Redis come broker
- **hiredis** (opzionale, per performance)

**✅ Compatibilità**: 100% - Stesso codice, cambia solo connection string

---

## 📦 Object Storage: S3-Compatible

### Sviluppo
- **MinIO** (Docker): `minio/minio:latest`
- **Endpoint**: `http://localhost:9000`
- **API**: S3-compatible al 100%

### Produzione (DigitalOcean)
- **DigitalOcean Spaces**
- **Endpoint**: `https://{region}.digitaloceanspaces.com`
- **API**: S3-compatible al 100%

### Configurazione
```python
# .env
# Sviluppo (MinIO)
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY_ID=minioadmin
S3_SECRET_ACCESS_KEY=minioadmin
S3_BUCKET=dataset-portal-dev
S3_REGION=us-east-1  # MinIO ignora, ma serve per boto3

# Produzione (DO Spaces)
# S3_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com
# S3_ACCESS_KEY_ID={DO_SPACES_KEY}
# S3_SECRET_ACCESS_KEY={DO_SPACES_SECRET}
# S3_BUCKET=dataset-portal-prod
# S3_REGION=nyc3
```

### Libreria
- **boto3** (AWS SDK, compatibile S3)
- **botocore** (dipendenza boto3)
- **Configurazione**:
  ```python
  import boto3
  from botocore.config import Config
  
  s3_client = boto3.client(
      's3',
      endpoint_url=os.getenv('S3_ENDPOINT_URL'),  # None per AWS, URL per MinIO/DO
      aws_access_key_id=os.getenv('S3_ACCESS_KEY_ID'),
      aws_secret_access_key=os.getenv('S3_SECRET_ACCESS_KEY'),
      region_name=os.getenv('S3_REGION'),
      config=Config(signature_version='s3v4')
  )
  ```

**✅ Compatibilità**: 100% - Stesso codice, cambiano solo env vars

---

## 🤖 AI Chat: OpenAI

### Sviluppo & Produzione
- **OpenAI API** (servizio esterno)
- **Endpoint**: `https://api.openai.com/v1`
- **Nessuna differenza** tra dev e prod

### Configurazione
```python
# .env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview  # o gpt-4, gpt-3.5-turbo
```

### Libreria
- **openai** (Python SDK ufficiale)
- **Streaming support** per chat

**✅ Compatibilità**: 100% - Stesso codice sempre

---

## 💳 Pagamenti: Stripe

### Sviluppo & Produzione
- **Stripe API** (servizio esterno)
- **Test Mode**: Usare chiavi test in dev
- **Live Mode**: Usare chiavi live in prod

### Configurazione
```python
# .env
# Sviluppo
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_test_...

# Produzione
# STRIPE_SECRET_KEY=sk_live_...
# STRIPE_PUBLISHABLE_KEY=pk_live_...
# STRIPE_WEBHOOK_SECRET=whsec_...
```

### Libreria
- **stripe** (Python SDK ufficiale)

**✅ Compatibilità**: 100% - Stesso codice, cambiano solo chiavi

---

## 🐍 Backend: FastAPI

### Sviluppo
- **Locale**: `uvicorn app.main:app --reload`
- **Porta**: 8000 (o configurabile)

### Produzione (DigitalOcean)
- **DigitalOcean App Platform** (consigliato)
  - Deploy automatico da Git
  - Auto-scaling
  - HTTPS incluso
- **Alternativa**: Droplet con Docker/Nginx

### Configurazione
```python
# .env
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development  # o production
CORS_ORIGINS=http://localhost:3000  # dev
# CORS_ORIGINS=https://yourdomain.com  # prod
```

**✅ Compatibilità**: 100% - Stesso codice, deploy diverso

---

## 🔄 Task Queue: Celery

### Sviluppo
- **Worker locale**: `celery -A app.workers.celery_app worker --loglevel=info`
- **Broker**: Redis locale

### Produzione (DigitalOcean)
- **DigitalOcean App Platform**: Worker separato
- **Alternativa**: Droplet dedicato per workers
- **Broker**: Redis managed DO

### Configurazione
```python
# .env (stesso Redis URL usato per cache)
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}
```

**✅ Compatibilità**: 100% - Stesso codice, cambia solo Redis URL

---

## 📝 Variabili d'Ambiente Complete

### Template `.env.example`
```bash
# Environment
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dataset_portal

# Redis
REDIS_URL=redis://localhost:6379/0

# Object Storage (S3-compatible)
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY_ID=minioadmin
S3_SECRET_ACCESS_KEY=minioadmin
S3_BUCKET=dataset-portal-dev
S3_REGION=us-east-1

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_test_...

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# API
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000

# Celery
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# Signed URLs
SIGNED_URL_TTL=3600  # 1 ora in secondi

# Logging
LOG_LEVEL=INFO
```

---

## 🐳 Docker Compose (Sviluppo)

### `docker-compose.yml`
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: dataset_user
      POSTGRES_PASSWORD: dataset_pass
      POSTGRES_DB: dataset_portal
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dataset_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"  # API
      - "9001:9001"  # Console
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

---

## 🚀 Deploy su DigitalOcean

### Opzione 1: App Platform (Consigliato)
1. **PostgreSQL**: Creare Managed Database
2. **Redis**: Creare Managed Database
3. **Spaces**: Creare bucket
4. **App**: Deploy backend da Git
5. **Worker**: Deploy Celery worker separato

### Opzione 2: Droplets
1. **PostgreSQL**: Managed Database (come sopra)
2. **Redis**: Managed Database (come sopra)
3. **Spaces**: Creare bucket
4. **Droplet**: Setup Docker, deploy app + worker

### Checklist Deploy
- [ ] Variabili ambiente configurate in DO App Platform
- [ ] Connection string PostgreSQL (con SSL)
- [ ] Connection string Redis (con TLS)
- [ ] Credenziali DO Spaces configurate
- [ ] Chiavi Stripe live configurate
- [ ] Chiave OpenAI configurata
- [ ] CORS origins aggiornati
- [ ] Healthcheck endpoint verificato

---

## ✅ Compatibilità Matrix

| Servizio | Dev | Prod (DO) | Compatibilità |
|----------|-----|-----------|---------------|
| **PostgreSQL** | Docker | Managed DB | ✅ 100% (connection string) |
| **Redis** | Docker | Managed DB | ✅ 100% (connection string) |
| **Storage** | MinIO | DO Spaces | ✅ 100% (boto3 S3-compatible) |
| **OpenAI** | API | API | ✅ 100% (stesso) |
| **Stripe** | Test keys | Live keys | ✅ 100% (stesso codice) |
| **Backend** | Locale | App Platform | ✅ 100% (stesso codice) |
| **Celery** | Locale | Worker separato | ✅ 100% (stesso codice) |

---

## 🎯 Principi di Implementazione

1. **Zero Hardcoding**: Tutto via env vars
2. **S3-Compatible**: Usare sempre boto3, mai librerie MinIO-specific
3. **Connection Strings**: Standard PostgreSQL/Redis, supporto SSL/TLS
4. **Error Handling**: Gestire differenze dev/prod (es. SSL required in prod)
5. **Logging**: Differenziare per ambiente (dev: verbose, prod: info)

---

## 📚 Librerie Python Richieste

```txt
# Database
sqlalchemy>=2.0.0
alembic>=1.13.0
psycopg2-binary>=2.9.9  # o asyncpg per async

# Redis & Queue
redis>=5.0.0
celery>=5.3.0

# Storage (S3-compatible)
boto3>=1.34.0
botocore>=1.34.0

# API
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# OpenAI
openai>=1.12.0

# Stripe
stripe>=7.0.0

# Auth
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4  # o argon2-cffi

# HTTP Client (per collector)
httpx>=0.26.0
tenacity>=8.2.0  # retry logic
```

---

## 🔒 Sicurezza in Produzione

### Checklist
- [ ] SSL/TLS abilitato per PostgreSQL (sslmode=require)
- [ ] TLS abilitato per Redis (rediss://)
- [ ] HTTPS per DO Spaces (endpoint URL)
- [ ] JWT secret key forte e random
- [ ] CORS origins limitati al dominio produzione
- [ ] Rate limiting configurato
- [ ] Logging senza PII (no password, no token)

---

## 📝 Note Finali

**Tutto è progettato per essere plug-and-play:**
- Cambi solo le variabili d'ambiente
- Nessuna modifica al codice
- Stesso codice funziona in dev e prod
- DigitalOcean Managed Services = zero gestione infrastruttura

**Prossimo passo**: Implementare tutto con questa configurazione fin dall'inizio!

