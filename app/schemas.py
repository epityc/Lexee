from pydantic import BaseModel, Field


class CalculationRequest(BaseModel):
    formula: str = Field(..., description="Identifiant de la formule (ex: 'vpm', 'tri')")
    variables: dict = Field(..., description="Paramètres de la formule sous forme de dict JSON")

    model_config = {"json_schema_extra": {
        "examples": [
            {
                "formula": "vpm",
                "variables": {
                    "taux_annuel": 5,
                    "nb_periodes": 240,
                    "valeur_actuelle": 200000,
                },
            },
            {
                "formula": "tri",
                "variables": {
                    "flux": [-100000, 30000, 35000, 40000, 45000],
                },
            },
            {
                "formula": "supprespace",
                "variables": {
                    "texte": "  Jean   Dupont  ",
                },
            },
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
            },
        ]
    }}


class CalculationResponse(BaseModel):
    formula: str
    result: dict
    credits_remaining: int


class LoginRequest(BaseModel):
    api_key: str


class ClientInfo(BaseModel):
    id: int
    name: str
    status: str
    credits: int
    plan: str = "free"

    class Config:
        from_attributes = True


class WorkbookCreate(BaseModel):
    name: str = Field("Sans titre", description="Nom du classeur")


class WorkbookUpdate(BaseModel):
    name: str | None = None
    data: dict | None = None
    formulas: dict | None = None


class WorkbookInfo(BaseModel):
    id: int
    name: str
    data: dict
    formulas: dict
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class WorkbookSummary(BaseModel):
    id: int
    name: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
