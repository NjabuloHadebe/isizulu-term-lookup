"""
generate_definitions.py
Generates English definitions for all terms in Supabase using GPT-3.5-turbo
Developer: Njabulo Hadebe
"""

import os
import time
import psycopg2
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ── CONNECTIONS ─────────────────────────────────────────────
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    sslmode="require",
    connect_timeout=10
)
cursor = conn.cursor()

# ── FETCH TERMS WITHOUT DEFINITIONS ─────────────────────────
cursor.execute("""
    SELECT id, englishword, isizuluword, discipline
    FROM term
    WHERE english_definition IS NULL OR english_definition = ''
    ORDER BY discipline, englishword
""")
terms = cursor.fetchall()

print(f"📚 Found {len(terms)} terms needing definitions\n")

# ── GENERATE DEFINITIONS ─────────────────────────────────────
def get_definition(english_word, isizulu_word, discipline):
    prompt = f"""Write a clear, concise academic definition for the term "{english_word}" in the field of {discipline}.
The isiZulu translation is "{isizulu_word}".
Write 1-2 sentences only. No bullet points. Plain text only."""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=120,
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

# ── PROCESS IN BATCHES ───────────────────────────────────────
batch_size = 20
total = len(terms)
success = 0
failed = 0

for i, (term_id, english, isizulu, discipline) in enumerate(terms):
    try:
        definition = get_definition(english, isizulu, discipline or "General")

        cursor.execute("""
            UPDATE term
            SET english_definition = %s
            WHERE id = %s
        """, (definition, term_id))

        # Commit every batch
        if (i + 1) % batch_size == 0:
            conn.commit()
            print(f"  ✅ {i+1}/{total} done — last: {english}")

        success += 1

        # Rate limit: 3 requests per second to be safe
        time.sleep(0.35)

    except Exception as e:
        failed += 1
        print(f"  ❌ Failed: {english} — {e}")
        conn.rollback()
        time.sleep(1)

# Final commit
conn.commit()
cursor.close()
conn.close()

print(f"\n🎉 Done! {success} definitions added, {failed} failed.")
print(f"💰 Estimated cost: ${success * 0.000035:.4f}")