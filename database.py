# database.py
# isiZulu Term Lookup System
# Developer: Njabulo Hadebe
from dotenv import load_dotenv
load_dotenv()
import psycopg2
import os

def get_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432"),
        sslmode="require",
        connect_timeout=10
    )
    return conn

def test_connection():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM term")
        terms = cursor.fetchall()
        print("Connection successful!")
        print(f"Found {len(terms)} terms in database")
        for term in terms:
            print(f"  - {term[1]} = {term[2]}")
        conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_connection()
