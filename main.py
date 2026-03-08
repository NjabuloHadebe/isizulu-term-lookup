from database import get_connection
from fastapi import FastAPI

app = FastAPI()

@app.get("/")

def home():
    return{'message': 'isiZulu Term lookup is running'}

@app.get('/search/{keyword}')
def search_term(keyword: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = "SELECT englishWord, isiZuluWord, definition FROM term WHERE LOWER(englishWord) = LOWER(%s)"
        cursor.execute(query, (keyword,))

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                "found": True,
                "englishWord": result[0],
                "isiZuluWord": result[1],
                "definition": result[2]
            }
        else:
            return {
                "found": False,
                "message": f"Term '{keyword}' not found. Would you like to suggest it?"
            }
            
    except Exception as e:
        return {"error": str(e)}
