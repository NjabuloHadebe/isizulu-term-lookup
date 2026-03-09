# import_terms.py
# Imports all CSV term files into Supabase
# Developer: Njabulo Hadebe

import os
import csv
import glob
import io
from dotenv import load_dotenv
from database import get_connection

load_dotenv()

# Map exact filenames to clean discipline names
DISCIPLINE_MAP = {
    'Anatomy 2 Term List.csv':                       'Anatomy 2',
    'Anatomy Term list.csv':                         'Anatomy',
    'Architecture Term List.csv':                    'Architecture',
    'Biodiversity Term List.csv':                    'Biodiversity',
    'Computer Sciences Termlist.csv':                'Computer Science',
    'Conversation termlist.csv':                     'Conversation',
    'Criminology Term List.csv':                     'Criminology',
    'Dentistry.csv':                                 'Dentistry',
    'Economics Term List (DAC).csv':                 'Economics',
    'Environmental Studies Term List.csv':           'Environmental Studies',
    'Film studies.csv':                              'Film Studies',
    'IT Term List.csv':                              'Information Technology',
    'Law 2 Term List.csv':                           'Law 2',
    'Life Science Term list (DAC).csv':              'Life Science',
    'Linguistics(Linguistics).csv':                  'Linguistics',
    'Mathematics Term List.csv':                     'Mathematics',
    'Municipal Solid Waste management termlist.csv': 'Waste Management',
    'Music termlist.csv':                            'Music',
    'Nursing Term List.csv':                         'Nursing',
    'Physics Term List.csv':                         'Physics',
    'Research Term List.csv':                        'Research',
    'signag.csv':                                    'Signage',
    'Social Science Term List.csv':                  'Social Science',
    'Social Work Term List.csv':                     'Social Work',
}


def try_read(filepath):
    """Try multiple encodings, return (content_string, encoding_used)."""
    for encoding in ['utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']:
        try:
            with open(filepath, encoding=encoding) as f:
                content = f.read()
            return content, encoding
        except (UnicodeDecodeError, Exception):
            continue
    with open(filepath, encoding='utf-8', errors='replace') as f:
        return f.read(), 'utf-8-replace'


def get_value(row, *keys):
    """Try multiple possible column name variations (case-insensitive, strip spaces)."""
    row_lower = {(k.strip().lower() if k else ''): v for k, v in row.items()}
    for key in keys:
        # Direct match
        val = row.get(key)
        if val is not None:
            return val.strip()
        # Case-insensitive + stripped match
        val = row_lower.get(key.strip().lower())
        if val is not None:
            return val.strip()
    return ''


def import_csv(filepath, discipline):
    conn = get_connection()
    cursor = conn.cursor()

    inserted = 0
    skipped = 0

    filename = os.path.basename(filepath)
    content, encoding = try_read(filepath)

    # Auto-detect delimiter
    first_lines = content[:2048]
    delimiter = ';' if first_lines.count(';') > first_lines.count(',') else ','

    # Special cases
    if filename == 'Dentistry.csv':
        # No header — inject one
        content = 'English Term;English Definition;IsiZulu Term;IsiZulu Definition\n' + content
        delimiter = ';'

    elif filename == 'signag.csv':
        # First line is "signage" title — remove it
        lines = content.splitlines()
        content = '\n'.join(lines[1:])

    f = io.StringIO(content)
    reader = csv.DictReader(f, delimiter=delimiter)

    for row in reader:
        if row is None:
            skipped += 1
            continue

        english = get_value(row,
            'English Term', 'English Terms',
            'English term', 'English terms'
        )
        isizulu = get_value(row,
            'IsiZulu Term', 'IsiZulu Terms',
            'Isizulu Term', 'Isizulu Terms',
            'IsiZulu Equivalent', 'Isizulu Equivalent',
            'Amagama NgesiZulu'
        )
        en_def = get_value(row, 'English Definition', 'English definition')
        zu_def = get_value(row,
            'IsiZulu Definition', 'Isizulu Definition',
            'IsiZulu definition'
        )

        if not english or not isizulu:
            skipped += 1
            continue

        try:
            cursor.execute("""
                INSERT INTO term (englishword, isizuluword, english_definition, isizulu_definition, discipline)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (english, isizulu, en_def or None, zu_def or None, discipline))
            inserted += 1
        except Exception as e:
            conn.rollback()
            print(f"  ⚠️  Error on '{english}': {e}")
            skipped += 1

    conn.commit()
    conn.close()
    print(f"  ✅ {discipline}: {inserted} inserted, {skipped} skipped")


def import_all(folder):
    csv_files = glob.glob(os.path.join(folder, '*.csv'))

    if not csv_files:
        print("❌ No CSV files found in folder!")
        return

    print(f"Found {len(csv_files)} CSV files\n")

    for filepath in sorted(csv_files):
        filename = os.path.basename(filepath)
        discipline = DISCIPLINE_MAP.get(filename, filename.replace('.csv', '').strip())
        print(f"📂 Importing: {filename}  →  '{discipline}'")
        import_csv(filepath, discipline)

    print("\n🎉 All done!")


if __name__ == "__main__":
    import_all('terms_data')