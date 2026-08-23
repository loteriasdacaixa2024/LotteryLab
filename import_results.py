import sqlite3
import csv
import os

def recover_megasena():
    csv_path = os.path.join('resultados', 'mega-sena_results.csv')
    db_path = os.path.join('resultados', 'results.db')
    
    if not os.path.exists(csv_path):
        print(f"Erro: Arquivo {csv_path} não encontrado.")
        return

    print(f"Recuperando dados de {csv_path} para o banco de dados...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Nome da tabela corrigido (sem hífen)
    table_name = "mega_sena"
    
    cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    cursor.execute(f'CREATE TABLE "{table_name}" (numeros TEXT, acertos_maximos INTEGER, hits_main INTEGER, hits_sec INTEGER, score REAL)')
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        batch = []
        for row in reader:
            batch.append((
                row['numeros'],
                int(row['acertos_maximos']),
                int(row['hits_main']),
                int(row['hits_sec']),
                float(row['score'])
            ))
            
    cursor.executemany(f'INSERT INTO "{table_name}" VALUES (?, ?, ?, ?, ?)', batch)
    conn.commit()
    conn.close()
    
    print(f"Sucesso! {len(batch)} combinações importadas para a tabela '{table_name}'.")

if __name__ == "__main__":
    recover_megasena()
