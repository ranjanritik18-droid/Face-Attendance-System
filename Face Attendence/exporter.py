import csv
from config import DB_PATH
import sqlite3

try:
    import pandas as pd
    import openpyxl
    PANDAS_OK = True
except Exception:
    PANDAS_OK = False

def export_file(path, start=None, end=None):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            q = """
            SELECT a.id, a.person, a.timestamp, a.date, a.session_id, s.name
            FROM attendance a
            LEFT JOIN sessions s ON a.session_id = s.id
            """
            params = []
            if start and end:
                q += " WHERE date BETWEEN ? AND ?"; params = [start, end]
            elif start:
                q += " WHERE date >= ?"; params = [start]
            elif end:
                q += " WHERE date <= ?"; params = [end]
            q += " ORDER BY date, session_id, timestamp"
            cur.execute(q, params)
            rows = cur.fetchall()
    except Exception as e:
        return False, f"Database error: {e}"

    headers = ["id", "person", "timestamp", "date", "session_id", "session_name"]
    if PANDAS_OK:
        try:
            df = pd.DataFrame(rows, columns=headers)
            if path.lower().endswith(".xlsx"):
                df.to_excel(path, index=False, engine="openpyxl")
            else:
                df.to_csv(path, index=False)
            return True, None
        except Exception as e:
            # fallback csv
            pass

    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(headers); w.writerows(rows)
        return True, None
    except Exception as e:
        return False, f"CSV write error: {e}"
