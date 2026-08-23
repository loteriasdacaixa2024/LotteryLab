import subprocess
import os
import sys
import time
import requests
import sqlite3

LOTTERY_LAB_DIR = os.path.dirname(os.path.abspath(__file__))
BANCOS_DIR = os.path.join(LOTTERY_LAB_DIR, 'bancos')
CAIXA_API_BASE = "https://servicebus2.caixa.gov.br/portaldeloterias/api"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def process_lottery_data(lottery_id, data):
    """Extrai os campos necessários conforme o esquema de cada loteria."""
    num_data = {
        'concurso': data.get('numero'),
        'data': data.get('dataApuracao'),
        'dezenas': data.get('listaDezenas', []),
        'ordem': data.get('listaDezenasOrdemSorteio', [])
    }
    
    # Se a ordem não vier (acontece as vezes), usamos as dezenas ordenadas
    if not num_data['ordem']:
        num_data['ordem'] = num_data['dezenas']

    if lottery_id == 'megasena':
        # ['concurso', 'data_apuracao', 'bola1..6', 'ordem1..6']
        balls = sorted([int(n) for n in num_data['dezenas']])
        orders = [int(n) for n in num_data['ordem']]
        return [num_data['concurso'], num_data['data']] + balls + orders

    elif lottery_id == 'lotofacil':
        # ['concurso', 'data_apuracao', 'bola1..15', 'ordem1..15']
        balls = sorted([int(n) for n in num_data['dezenas']])
        orders = [int(n) for n in num_data['ordem']]
        return [num_data['concurso'], num_data['data']] + balls + orders

    elif lottery_id == 'diadesorte':
        # ['concurso', 'data_apuracao', 'bola1..7', 'ordem1..7', 'mes_sorte']
        balls = sorted([int(n) for n in num_data['dezenas']])
        orders = [int(n) for n in num_data['ordem']]
        mes = data.get('nomeTimeCoracaoMesSorte', '')
        # Converter nome do mês para número se possível, ou salvar como está se a coluna for texto
        # (vimos que a coluna mes_sorte existe, vamos assumir que aceita o que vier da API)
        return [num_data['concurso'], num_data['data']] + balls + orders + [mes]

    elif lottery_id == 'quina':
        # ['concurso', 'data_apuracao', 'bola1..5', 'ordem1..5']
        balls = sorted([int(n) for n in num_data['dezenas']])
        orders = [int(n) for n in num_data['ordem']]
        return [num_data['concurso'], num_data['data']] + balls + orders

    elif lottery_id == 'lotomania':
        # ['concurso', 'data_apuracao', 'bola1..20', 'ordem1..20']
        balls = sorted([int(n) for n in num_data['dezenas']])
        orders = [int(n) for n in num_data['ordem']]
        return [num_data['concurso'], num_data['data']] + balls + orders

    elif lottery_id == 'timemania':
        # ['concurso', 'data_apuracao', 'bola1..7', 'ordem1..7', 'time_coracao']
        balls = sorted([int(n) for n in num_data['dezenas']])
        orders = [int(n) for n in num_data['ordem']]
        time_c = data.get('nomeTimeCoracaoMesSorte', '')
        return [num_data['concurso'], num_data['data']] + balls + orders + [time_c]

    elif lottery_id == 'duplasena':
        # ['concurso', 'data_apuracao', 's1_bola1..6', 's1_ordem1..6', 's2_bola1..6', 's2_ordem1..6']
        s1_balls = sorted([int(n) for n in num_data['dezenas']])
        s1_orders = [int(n) for n in num_data['ordem']]
        s2_balls_raw = data.get('listaDezenasSegundoSorteio', [])
        s2_balls = sorted([int(n) for n in s2_balls_raw]) if s2_balls_raw else [0]*6
        s2_orders = [int(n) for n in s2_balls_raw] if s2_balls_raw else [0]*6
        return [num_data['concurso'], num_data['data']] + s1_balls + s1_orders + s2_balls + s2_orders

    elif lottery_id == 'maismilionaria':
        # ['concurso', 'data_apuracao', 'bola1..6', 'ordem1..6', 'trevo1', 'trevo2']
        balls = sorted([int(n) for n in num_data['dezenas']])
        orders = [int(n) for n in num_data['ordem']]
        trevos = [int(t) for t in data.get('listaTrvosSorteio', [])] if data.get('listaTrvosSorteio') else [0, 0]
        return [num_data['concurso'], num_data['data']] + balls + orders + trevos

    elif lottery_id == 'supersete':
        # Tabela results: ['id', 'concurso', 'data', 'col0..6', ...]
        cols = [int(n) for n in num_data['dezenas']]
        return [num_data['concurso'], num_data['data']] + cols

    return None

def sync_missing_results(lottery_id):
    """Busca e insere apenas os resultados faltantes para a loteria."""
    db_path = os.path.join(BANCOS_DIR, f"{lottery_id}.db")
    if not os.path.exists(db_path):
        log(f"Banco {lottery_id}.db não encontrado.")
        return False

    table = 'results' if lottery_id == 'supersete' else 'sorteios'
    
    # 1. Obter o mais recente local
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT MAX(concurso) FROM {table}")
    local_latest = cursor.fetchone()[0] or 0
    
    # 2. Consultar a API da Caixa para ver o último no servidor
    url_base = f"{CAIXA_API_BASE}/{lottery_id}"
    try:
        r = requests.get(url_base, timeout=15, verify=False)
        if r.status_code != 200:
            log(f"Erro ao acessar API para {lottery_id}")
            return False
        data = r.json()
        api_latest = data.get('numero', 0)
        
        if api_latest <= local_latest:
            log(f"{lottery_id} já está atualizada (Local: {local_latest} | API: {api_latest})")
            return False
            
        log(f"Sincronizando {lottery_id}: Faltam {api_latest - local_latest} concursos.")
        
        # 3. Buscar um por um os faltantes
        for contest in range(local_latest + 1, api_latest + 1):
            log(f"Baixando {lottery_id} concurso #{contest}...")
            # Pequeno delay para não sobrecarregar a API
            time.sleep(0.5)
            
            resp = requests.get(f"{url_base}/{contest}", timeout=10, verify=False)
            if resp.status_code != 200:
                log(f"Falha ao baixar concurso {contest}")
                continue
                
            c_data = resp.json()
            row_to_insert = process_lottery_data(lottery_id, c_data)
            
            if row_to_insert:
                # Obter nomes das colunas (exceto ID se for autoincrement)
                cursor.execute(f"PRAGMA table_info({table})")
                all_cols = [c[1] for c in cursor.fetchall()]
                
                # Para Super Sete, 'id' é o primeiro. Para outros, concurso é o primeiro.
                cols_to_use = all_cols[1:] if lottery_id == 'supersete' else all_cols
                
                # Garantir que temos o número certo de valores (algumas tabelas tem Rateio/Arrecadação no final)
                # Se row_to_insert tiver menos que cols_to_use, completamos com None/Zero
                diff = len(cols_to_use) - len(row_to_insert)
                if diff > 0:
                    row_to_insert += [None] * diff
                elif diff < 0:
                    row_to_insert = row_to_insert[:len(cols_to_use)]

                placeholders = ",".join(["?"] * len(cols_to_use))
                cols_str = ",".join(cols_to_use)
                
                query = f"INSERT OR IGNORE INTO {table} ({cols_str}) VALUES ({placeholders})"
                cursor.execute(query, row_to_insert)
                conn.commit()
                log(f"Concurso {contest} inserido.")
        
        return True
    except Exception as e:
        log(f"Erro em {lottery_id}: {e}")
        return False
    finally:
        conn.close()

def run_sync_all():
    loterias = [
        'megasena', 'lotofacil', 'diadesorte', 'quina', 'lotomania',
        'duplasena', 'timemania', 'supersete', 'maismilionaria'
    ]
    
    log("--- INICIANDO SINCRONIZAÇÃO INCREMENTAL ---")
    sync_needed = []
    for lot in loterias:
        if sync_missing_results(lot):
            sync_needed.append(lot)
        
    log("--- INICIANDO ATUALIZAÇÃO DA ELITE (BACKTESTS) ---")
    
    # Se a chamada foi manual via Dashboard (Sincronizar Tudo), o usuário pode estar querendo forçar
    # Porém, como a execução completa de todas as elites demora MUITO,
    # vamos limitar a rodar a Engine APENAS para os bancos que receberam novos sorteios.
    if not sync_needed:
        log("Nenhum novo sorteio baixado! Nenhuma recriação imediata de backup Alvo necessária.")
        
    for loteria in sync_needed:
        log(f"Processando Elite e congelando Backup Alvo Futuro para: {loteria.upper()}...")
        try:
            cmd = [sys.executable, "run_backtest.py", "--loteria", loteria, "--processes", "4"]
            subprocess.run(cmd, cwd=LOTTERY_LAB_DIR, check=True)
            log(f"Sucesso: {loteria} elite gerada e backup alvo criado!")
        except Exception as e:
            log(f"Erro ao atualizar elite {loteria}: {e}")

    log("--- PROCESSO GLOBAL CONCLUÍDO ---")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    run_sync_all()
