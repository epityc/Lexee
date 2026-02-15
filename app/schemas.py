from pydantic import BaseModel


class CalculationRequest(BaseModel):
    formula: str
    variables: dict

    model_config = {"json_schema_extra": {
        "examples": [
            {
                "formula": "rentabilite_immobiliere",
                "variables": {
                    "prix_achat": 200000,
                    "loyer_mensuel": 900,
                    "charges_annuelles": 2500,
                    "cout_travaux": 15000,
                    "taux_interet": 3.5,
                    "duree_emprunt": 20,
                    "apport": 30000,
                },
            }
        ]
    }}


class CalculationResponse(BaseModel):
    formula: str
    result: dict
    credits_remaining: int
