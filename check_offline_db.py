import sqlite3

def check_db():
    try:
        with open("db_schema.txt", "w", encoding="utf-8") as f:
            conn = sqlite3.connect('offline.db')
            cursor = conn.cursor()
            
            # List tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            f.write(f"Tables: {tables}\n")
            
            for table in tables:
                t = table[0]
                f.write(f"\n--- Schema for {t} ---\n")
                cursor.execute(f"PRAGMA table_info({t})")
                columns = cursor.fetchall()
                for col in columns:
                    f.write(f"{col}\n")
                    
                f.write(f"--- First 3 rows of {t} ---\n")
                cursor.execute(f"SELECT * FROM {t} LIMIT 3")
                rows = cursor.fetchall()
                for row in rows:
                    f.write(f"{row}\n")
                    
            conn.close()
            print("Done writing to db_schema.txt")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
