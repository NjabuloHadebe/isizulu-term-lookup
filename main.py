# main.py
# isiZulu Term Lookup System
# Developer: Njabulo Hadebe

from database import get_connection
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── HOME ────────────────────────────────────────────────────
@app.get("/")
def home():
    return {"message": "isiZulu Term Lookup is running"}


# ── SEARCH ──────────────────────────────────────────────────
@app.get("/search/{keyword}")
def search_term(keyword: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT englishword, isizuluword, english_definition, discipline
            FROM term
            WHERE LOWER(englishword) = LOWER(%s)
            OR LOWER(isizuluword) = LOWER(%s)
            LIMIT 1
        """, (keyword, keyword))
        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                "found": True,
                "englishWord": result[0],
                "isiZuluWord": result[1],
                "definition": result[2],
                "discipline": result[3]
            }
        else:
            return {
                "found": False,
                "message": f"Term '{keyword}' not found. Would you like to suggest it?"
            }
    except Exception as e:
        return {"error": str(e)}


# ── ALL TERMS (paginated, filterable) ───────────────────────
@app.get("/terms")
def get_terms(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    discipline: Optional[str] = Query(None),
    letter: Optional[str] = Query(None)
):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        offset = (page - 1) * limit

        conditions = []
        params = []

        if discipline:
            conditions.append("LOWER(discipline) = LOWER(%s)")
            params.append(discipline)

        if letter:
            conditions.append("LOWER(englishword) LIKE %s")
            params.append(letter.lower() + "%")

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        cursor.execute(f"SELECT COUNT(*) FROM term {where}", params)
        total = cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT englishword, isizuluword, english_definition, discipline
            FROM term {where}
            ORDER BY englishword ASC
            LIMIT %s OFFSET %s
        """, params + [limit, offset])

        rows = cursor.fetchall()
        conn.close()

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
            "terms": [
                {
                    "english_word": r[0],
                    "isizulu_word": r[1],
                    "definition": r[2],
                    "discipline": r[3]
                }
                for r in rows
            ]
        }
    except Exception as e:
        return {"error": str(e)}


# ── DISCIPLINES ──────────────────────────────────────────────
@app.get("/disciplines")
def get_disciplines():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT discipline, COUNT(*) as term_count
            FROM term
            WHERE discipline IS NOT NULL
            GROUP BY discipline
            ORDER BY discipline ASC
        """)
        rows = cursor.fetchall()
        conn.close()
        return {
            "disciplines": [{"name": r[0], "count": r[1]} for r in rows]
        }
    except Exception as e:
        return {"error": str(e)}


# ── SUGGEST A TERM ───────────────────────────────────────────
class SuggestionRequest(BaseModel):
    english_word: str
    isizulu_word: Optional[str] = None
    definition: Optional[str] = None

@app.post("/suggest")
def suggest_term(suggestion: SuggestionRequest):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO comment (text, type, fk_userid, fk_termid, fk_adminid)
            VALUES (%s, %s, NULL, NULL, NULL)
        """, (
            f"SUGGESTION — English: {suggestion.english_word} | "
            f"isiZulu: {suggestion.isizulu_word or 'not provided'} | "
            f"Definition: {suggestion.definition or 'not provided'}",
            "suggestion"
        ))
        conn.commit()
        conn.close()
        return {"success": True, "message": "Thank you! Your suggestion has been received."}
    except Exception as e:
        return {"error": str(e)}


# ── ANALYTICS TRACK ──────────────────────────────────────────
@app.post("/analytics")
async def track_event(payload: dict):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO analytics (event_type, term_searched, discipline_viewed, session_id)
            VALUES (%s, %s, %s, %s)
        """, (
            payload.get("event_type"),
            payload.get("term_searched"),
            payload.get("discipline_viewed"),
            payload.get("session_id")
        ))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}


# ── ANALYTICS SUMMARY ────────────────────────────────────────
@app.get("/analytics/summary")
def analytics_summary():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Total unique visitors
        cursor.execute("""
            SELECT COUNT(DISTINCT session_id) FROM analytics
            WHERE event_type = 'visit'
        """)
        total_visitors = cursor.fetchone()[0]

        # Visitors today
        cursor.execute("""
            SELECT COUNT(DISTINCT session_id) FROM analytics
            WHERE event_type = 'visit'
            AND DATE(visited_at) = CURRENT_DATE
        """)
        today_visitors = cursor.fetchone()[0]

        # Total terms in database
        cursor.execute("SELECT COUNT(*) FROM term")
        total_terms = cursor.fetchone()[0]

        # Total successful searches
        cursor.execute("""
            SELECT COUNT(*) FROM analytics
            WHERE event_type = 'search_found'
        """)
        total_searches = cursor.fetchone()[0]

        # Top 5 searched terms
        cursor.execute("""
            SELECT term_searched, COUNT(*) as cnt
            FROM analytics
            WHERE event_type = 'search_found'
            AND term_searched IS NOT NULL
            GROUP BY term_searched
            ORDER BY cnt DESC
            LIMIT 5
        """)
        top_terms = [{"term": r[0], "count": r[1]} for r in cursor.fetchall()]

        # Top 5 missing terms (searched but not found)
        cursor.execute("""
            SELECT term_searched, COUNT(*) as cnt
            FROM analytics
            WHERE event_type = 'search_missing'
            AND term_searched IS NOT NULL
            GROUP BY term_searched
            ORDER BY cnt DESC
            LIMIT 5
        """)
        missing_terms = [{"term": r[0], "count": r[1]} for r in cursor.fetchall()]

        conn.close()

        return {
            "total_visitors": total_visitors,
            "today_visitors": today_visitors,
            "total_terms": total_terms,
            "total_searches": total_searches,
            "top_terms": top_terms,
            "missing_terms": missing_terms
        }
    
    
    except Exception as e:
        return {"error": str(e)}
    

# ── AUTOCOMPLETE ─────────────────────────────────────────────
@app.get("/autocomplete")
def autocomplete(q: str = Query(..., min_length=2)):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT englishword, isizuluword, discipline
            FROM term
            WHERE LOWER(englishword) LIKE LOWER(%s)
            OR LOWER(isizuluword) LIKE LOWER(%s)
            ORDER BY englishword ASC
            LIMIT 6
        """, (q + "%", q + "%"))
        rows = cursor.fetchall()
        conn.close()
        return {
            "results": [
                {"english_word": r[0], "isizulu_word": r[1], "discipline": r[2]}
                for r in rows
            ]
        }
    except Exception as e:
        return {"error": str(e)}