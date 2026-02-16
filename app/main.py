from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

app = FastAPI(
    title="Lexee — Calculation Engine",
    description=(
        "Moteur de calcul opaque : envoyez vos variables, "
        "recevez vos résultats. Les formules restent protégées."
    ),
    version="1.0.0",
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


# ---------------------------------------------------------------------------
# Health-check
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Auth — login (valide la clé et renvoie les infos client)
# ---------------------------------------------------------------------------
@app.post("/auth/login", response_model=ClientInfo)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.api_key == payload.api_key).first()
    if client is None:
        raise HTTPException(status_code=401, detail="Clé API invalide.")
    return client


# ---------------------------------------------------------------------------
# Client info
# ---------------------------------------------------------------------------
@app.get("/me", response_model=ClientInfo)
def me(client: Client = Depends(get_current_client)):
    return client


# ---------------------------------------------------------------------------
# Liste des formules (métadonnées uniquement, JAMAIS le code)
# ---------------------------------------------------------------------------
@app.get("/formulas")
def list_formulas(client: Client = Depends(get_current_client)):
    return {"formulas": FORMULA_META}


# ---------------------------------------------------------------------------
# Endpoint principal — calcul
# ---------------------------------------------------------------------------
@app.post("/calculate", response_model=CalculationResponse)
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
