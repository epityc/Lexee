# Nexus Grid

**AI version of Excel** — Moteur de calcul SaaS avec 112 formules protégées, API REST et dashboard interactif.

## Architecture

```
Nexus-Grid/
├── app/                  # Backend FastAPI
│   ├── main.py           # API + serveur de fichiers statiques
│   ├── config.py         # Configuration (DATABASE_URL)
│   ├── database.py       # SQLAlchemy engine & session
│   ├── models.py         # Modèle Client (API key, crédits)
│   ├── schemas.py        # Schémas Pydantic
│   ├── auth.py           # Authentification X-Api-Key
│   └── engine/
│       └── logic.py      # 112 formules protégées
├── frontend/             # Next.js 14 + Tailwind CSS
│   └── src/
│       ├── app/          # Pages (login, dashboard)
│       ├── components/   # Sidebar, ExcelGrid, ThemePicker
│       └── lib/api.ts    # Client API
├── tests/                # Tests pytest
├── admin.py              # CLI administration clients
├── Dockerfile            # Build multi-stage (Node + Python)
├── docker-compose.yml
└── railway.toml          # Déploiement Railway
```

## Démarrage rapide

### Docker (recommandé)

```bash
docker compose up --build
# → http://localhost:8000
```

### Manuel

```bash
# Backend
pip install -r requirements.txt

# Créer un client
python admin.py add "MonEntreprise" 1000
python admin.py activate 1

# Lancer
uvicorn app.main:app --reload --port 8000

# Frontend (optionnel, pour le build statique)
cd frontend && npm install && npm run build
cp -r out/ ../app/static/
```

## API

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/health` | GET | Health check |
| `/api/auth/login` | POST | Connexion avec clé API |
| `/api/me` | GET | Info client |
| `/api/formulas` | GET | Liste des formules |
| `/api/calculate` | POST | Exécuter une formule |

Header requis : `X-Api-Key: ng_xxx...`

## Tests

```bash
python -m pytest tests/ -v
```
