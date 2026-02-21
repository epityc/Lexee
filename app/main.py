import os
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.routing import APIRouter
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.auth import get_current_client
from app.database import get_db, init_db
from app.engine.logic import FORMULA_META, FORMULAS
from app.models import Client
from app.schemas import (
    CalculationRequest,
    CalculationResponse,
    ClientInfo,
    LoginRequest,
)

# ─────────────────────────────────────────────────────────────────────────────
# API Router — toutes les routes métier sous /api
# ─────────────────────────────────────────────────────────────────────────────
api = APIRouter(prefix="/api")


@api.get("/health")
def health():
    return {"status": "ok"}


@api.post("/auth/login", response_model=ClientInfo)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.api_key == payload.api_key).first()
    if client is None:
        raise HTTPException(status_code=401, detail="Clé API invalide.")
    return client


@api.get("/me", response_model=ClientInfo)
def me(client: Client = Depends(get_current_client)):
    return client


@api.get("/formulas")
def list_formulas(client: Client = Depends(get_current_client)):
    return {"formulas": FORMULA_META}


@api.post("/calculate", response_model=CalculationResponse)
def calculate(
    payload: CalculationRequest,
    client: Client = Depends(get_current_client),
    db: Session = Depends(get_db),
):
    formula_fn = FORMULAS.get(payload.formula)
    if formula_fn is None:
        raise HTTPException(
            status_code=404,
            detail=f"Formule '{payload.formula}' introuvable. "
            f"Formules disponibles : {list(FORMULAS.keys())}",
        )

    try:
        result = formula_fn(payload.variables)
    except KeyError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Variable manquante : {exc}",
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Erreur dans les variables fournies : {exc}",
        )

    # Décrémenter les crédits
    client.credits -= 1
    db.commit()
    db.refresh(client)

    return CalculationResponse(
        formula=payload.formula,
        result=result,
        credits_remaining=client.credits,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Application FastAPI
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Lexee — Calculation Engine",
    description=(
        "Moteur de calcul opaque : envoyez vos variables, "
        "recevez vos résultats. Les formules restent protégées."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


# Enregistrer le routeur API
app.include_router(api)

# ─────────────────────────────────────────────────────────────────────────────
# Servir le frontend statique (Next.js export) — uniquement si le dossier existe
# ─────────────────────────────────────────────────────────────────────────────
STATIC_DIR = Path(__file__).resolve().parent / "static"

if STATIC_DIR.is_dir():
    # Servir les fichiers statiques Next.js (_next/*, images, etc.)
    app.mount("/_next", StaticFiles(directory=STATIC_DIR / "_next"), name="next-static")

    # Catch-all : pour toute route non-API, servir le fichier HTML correspondant
    # ou index.html comme fallback SPA
    @app.get("/{full_path:path}")
    async def serve_frontend(request: Request, full_path: str):
        # Fichier statique exact (favicon.ico, images, etc.)
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)

        # Page Next.js exportée (ex: /dashboard → dashboard.html)
        html_path = STATIC_DIR / f"{full_path}.html"
        if html_path.is_file():
            return FileResponse(html_path)

        # Sous-dossier avec index.html (ex: /dashboard/ → dashboard/index.html)
        index_path = STATIC_DIR / full_path / "index.html"
        if index_path.is_file():
            return FileResponse(index_path)

        # Fallback → index.html (SPA)
        fallback = STATIC_DIR / "index.html"
        if fallback.is_file():
            return FileResponse(fallback)

        return JSONResponse(status_code=404, content={"detail": "Not found"})
