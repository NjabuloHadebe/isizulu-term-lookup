# isiZulu Term Lookup System

A web API that allows users to search for isiZulu translations 
and definitions of academic terms.

## Developer
Njabulo Hadebe — AI Engineer in progress

## Tech Stack
- Python
- FastAPI
- PostgreSQL + pgvector
- Render (deployment)

## How to Run Locally

1. Clone the repository
2. Install dependencies: pip install -r requirements.txt
3. Run: uvicorn main:app --reload
4. Open: http://127.0.0.1:8000

## API Endpoints

- GET / — Home
- GET /search/{keyword} — Search for a term