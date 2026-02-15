from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_client
from app.database import get_db, init_db
from app.engine.logic import FORMULAS
from app.models import Client
from app.schemas import CalculationRequest, CalculationResponse

app = FastAPI(
    title="Lexee — Calculation Engine",
    description=(
        "Moteur de calcul opaque : envoyez vos variables, "
        "recevez vos résultats. Les formules restent protégées."
    ),
    version="0.1.0",
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
# Liste des formules disponibles (noms uniquement, pas le code)
# ---------------------------------------------------------------------------
@app.get("/formulas")
def list_formulas(client: Client = Depends(get_current_client)):
    return {"formulas": list(FORMULAS.keys())}


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
