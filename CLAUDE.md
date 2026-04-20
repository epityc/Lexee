# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run all tests
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_v18_formulas.py -v

# Run a single test
python -m pytest tests/test_v5_formulas.py::test_groupby_count -v

# Start dev server
uvicorn app.main:app --reload --port 8000

# Verify formula registry integrity
python -c "from app.engine.logic import FORMULAS, FORMULA_META; assert len(FORMULAS) == len(FORMULA_META); print(f'{len(FORMULAS)} formulas OK')"

# Check for key collisions before adding formulas
python -c "from app.engine.logic import FORMULAS; keys = ['new_key_1', 'new_key_2']; print([k for k in keys if k in FORMULAS])"

# Admin CLI
python admin.py add "ClientName" 1000
python admin.py activate 1
python admin.py credits 1 500
python admin.py list
```

## Architecture

**Nexus Grid** is a credit-based SaaS calculation engine (FastAPI + SQLAlchemy) that exposes ~493 Excel-equivalent formulas via REST API. Formula source code is never exposed to clients.

### Formula Engine (`app/engine/`)

The engine is the core of the application:

- **`logic.py`** — Contains v1-v4 formula implementations inline (~112 functions), plus two registries:
  - `FORMULAS: dict[str, callable]` — Maps formula key to function. Each function has signature `(v: dict) -> dict`.
  - `FORMULA_META: dict` — Maps formula key to metadata (name, description, category, variables with types/required/placeholders). Used by the frontend and `/api/formulas` endpoint.
- **`_v5.py` through `_v18.py`** — Versioned modules containing formula implementations added in groups. Imported by `logic.py` and registered in both dictionaries.
- **`_stat_helpers.py`** — Shared statistical utility functions.

**Adding new formulas pattern:**
1. Create function in the appropriate `_v*.py` file: `def formule_name(v: dict) -> dict:`
2. Register in `FORMULAS` dict in `logic.py`: `"key": _vN.formule_name,`
3. Register in `FORMULA_META` dict with category, description, and variable definitions
4. Update count assertions in ALL test files' `test_registre_complet*` smoke tests
5. Add tests in corresponding `tests/test_v*_formulas.py`

**Count assertion update:** Every test file has a smoke test asserting the exact total formula count. When adding formulas, update ALL of these (use a targeted Python script, NOT sed, to avoid corrupting unrelated numeric values in test files).

### API Layer (`app/`)

- **`main.py`** — FastAPI app, all routes under `/api`, serves static frontend from `app/static/`
- **`auth.py`** — `X-Api-Key` header authentication via `get_current_client()`
- **`models.py`** — Single `Client` model (id, name, api_key, status, credits, created_at)
- **`schemas.py`** — Pydantic models: `CalculationRequest` (formula + variables), `CalculationResponse`
- **`config.py`** — DATABASE_URL configuration
- **`database.py`** — SQLAlchemy engine and session management

Each `/api/calculate` call deducts 1 credit from the authenticated client.

### Frontend (`frontend/`)

Next.js 14 + Tailwind CSS static export. Built separately, output copied to `app/static/`. The backend serves it with SPA fallback routing.

## Conventions

- Formula functions are named `formule_<name>` in Python, registered as lowercase keys in FORMULAS
- All comments, variable names in formulas, and metadata descriptions are in French
- Complex number formulas use Excel's "a+bi" string format with `_parse_complex`/`_format_complex` helpers in `_v18.py`
- Financial formulas use 30/360 day count convention by default
- Tests are organized by version group (`test_v3_formulas.py` through `test_v18_formulas.py`)
- No external scientific libraries (no scipy/numpy) — pure Python implementations (e.g., Bessel functions use series expansions)
