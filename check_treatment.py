import sqlite3
try:
    conn = sqlite3.connect('offline.db')
    cursor = conn.cursor()
    cursor.execute('SELECT medicine FROM treatment LIMIT 1')
    row = cursor.fetchone()
    if row:
        print(f"SAMPLE_MEDICINE_DATA: {row[0]}")
    else:
        print("NO_TREATMENT_DATA")
    conn.close()
except Exception as e:
    print(e)
