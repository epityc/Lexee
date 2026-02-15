from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Client


def get_current_client(
    x_api_key: str = Header(..., description="Clé API du client"),
    db: Session = Depends(get_db),
) -> Client:
    """Dépendance FastAPI : valide la clé API et les droits du client."""

    client = db.query(Client).filter(Client.api_key == x_api_key).first()

    if client is None:
        raise HTTPException(status_code=401, detail="Clé API invalide.")

    if client.status != "active":
        raise HTTPException(
            status_code=402,
            detail="Compte inactif — paiement en attente. Contactez l'administrateur.",
        )

    if client.credits <= 0:
        raise HTTPException(
            status_code=429,
            detail="Crédits épuisés. Veuillez recharger votre compte.",
        )

    return client
