import psycopg2

def get_connection():
    conn = psycopg2.connect(
        host = 'localhost',
        database = 'isizulu_term_lookup',
        user = 'khumbulanimngadi',
        password = ''
    )
    return conn

def test_connection():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM term')
        terms = cursor.fetchall()
        print('Sucess')
        print(f"Found {len(terms)} terms in database")
        for term in terms:
            print(f" - {term[1]} = {term[2]}")
        conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == '__main__':
    test_connection()