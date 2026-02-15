# Lexee — Calculation Engine SaaS

Moteur de calcul opaque : envoyez vos variables via API, recevez vos résultats.
Les formules restent protégées et ne sont jamais exposées.

## Structure du projet

```
Lexee/
├── app/
│   ├── __init__.py
│   ├── config.py          # Configuration (DATABASE_URL)
│   ├── database.py        # Connexion SQLAlchemy + helpers
│   ├── models.py          # Modèle Client (SQLite)
│   ├── schemas.py         # Schémas Pydantic (request/response)
│   ├── auth.py            # Dépendance d'authentification par X-API-KEY
│   ├── main.py            # Application FastAPI + endpoints
│   └── engine/
│       ├── __init__.py
│       └── logic.py       # Formules protégées (BlackBox)
├── admin.py               # Script CLI d'administration
├── requirements.txt
└── .gitignore
```

## Installation

```bash
pip install -r requirements.txt
```

## Lancer le serveur

```bash
uvicorn app.main:app --reload
```

Documentation interactive : http://127.0.0.1:8000/docs

## Administration

```bash
# Créer un client (statut: pending_payment)
python admin.py add "Acme Corp" 100

# Activer après réception du virement
python admin.py activate 1

# Ajouter des crédits
python admin.py credits 1 500

# Lister tous les clients
python admin.py list
```

## Utilisation de l'API

```bash
curl -X POST http://127.0.0.1:8000/calculate \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: lx_votre_cle_ici" \
  -d '{
    "formula": "rentabilite_immobiliere",
    "variables": {
      "prix_achat": 200000,
      "loyer_mensuel": 900,
      "charges_annuelles": 2500,
      "cout_travaux": 15000,
      "taux_interet": 3.5,
      "duree_emprunt": 20,
      "apport": 30000
    }
  }'
```
