import sqlite3
import os

BANCOS_DIR = r'd:\LotteryLab\bancos'
loterias = [
    'megasena', 'lotofacil', 'diadesorte', 'quina', 'lotomania',
    'duplasena', 'timemania', 'supersete', 'maismilionaria'
]

for lot in loterias:
    db_path = os.path.join(BANCOS_DIR, f"{lot}.db")
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        table = 'results' if lot == 'supersete' else 'sorteios'
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            cols = [c[1] for c in cursor.fetchall()]
            print(f"{lot}: {cols}")
        except:
            print(f"{lot}: Error reading table {table}")
        conn.close()
    else:
        print(f"{lot}: DB not found")
