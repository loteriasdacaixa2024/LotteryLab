import os
import sqlite3
import pandas as pd
from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta
import threading
import subprocess
import sys
import time

# v1.2 - Sincronização Automática Diária
app = Flask(__name__)

# Configurações do App
PORT = 8082
LOTTERY_LAB_DIR = r'd:\Loterias\LotteryLab'
BANCOS_DIR = os.path.join(LOTTERY_LAB_DIR, 'bancos')
RESULTADOS_DIR = os.path.join(LOTTERY_LAB_DIR, 'resultados')

from lotteries_config import PRIZE_TIERS, get_lottery_config, TEAM_ICONS

def extract_elite_numbers(row, df, num_col):
    """Extrai os números independentemente se estão agrupados em 1 célula (antigo) ou divididos em várias células (novo padrão)."""
    nums = []
    
    # Nova lógica: se a coluna inicial for "D1"
    if num_col and str(num_col).upper() == 'D1':
        for col_name in df.columns:
            if str(col_name).upper().startswith('D') and str(col_name)[1:].strip().isdigit():
                v = row[col_name]
                if pd.notna(v) and str(v).strip() != '':
                    try: nums.append(str(int(float(v))))
                    except (ValueError, TypeError): pass
        if nums:
            return "-".join(nums)

    # Lógica Antiga
    if num_col not in df.columns:
        return ""
    val = row[num_col]
    if pd.isna(val): return ""
    
    if isinstance(val, (int, float)) or (isinstance(val, str) and (str(val).strip().isdigit() or "-" in str(val) or "," in str(val))):
        try:
            start_idx = df.columns.get_loc(num_col)
            for col_name in df.columns[start_idx:]:
                # Para assim que encontrar a próxima coluna nomeada que não seja 'Unnamed'
                if col_name != num_col and not str(col_name).startswith('Unnamed'):
                    break
                v = row[col_name]
                if pd.notna(v) and str(v).strip() != '':
                    try:
                        nums.append(str(int(float(v))))
                    except (ValueError, TypeError):
                        pass
            if nums: return "-".join(nums)
        except KeyError:
            pass
    return str(val)


def get_latest_official_result(lottery_id):
    """Busca o último sorteio oficial no banco de dados SQLite."""
    # Mapeamento simples de ID para nome do arquivo de banco
    # No lottery_configs.py: megasena -> megasena.db
    db_name = f"{lottery_id}.db"
    db_path = os.path.join(BANCOS_DIR, db_name)
    
    if not os.path.exists(db_path):
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Assume tabela 'sorteios' exceto supersete que é 'results'
        if lottery_id == 'supersete':
            table = 'results'
        elif lottery_id == 'federal':
            table = 'sorteios' # Ajustar se necessário
        else:
            table = 'sorteios'
        
        # Pega o sorteio com maior número de concurso
        if lottery_id == 'duplasena':
            # Para Dupla Sena, vamos considerar o 1º sorteio para a conferência básica
            cursor.execute(f"SELECT * FROM {table} ORDER BY concurso DESC LIMIT 1")
        else:
            cursor.execute(f"SELECT * FROM {table} ORDER BY concurso DESC LIMIT 1")
        row = cursor.fetchone()
        
        # Pega os nomes das colunas
        cursor.execute(f"PRAGMA table_info({table})")
        cols = [c[1] for c in cursor.fetchall()]
        conn.close()
        
        if row:
            res = dict(zip(cols, row))
            if lottery_id == 'supersete':
                dezenas = [res.get(f'col{i}') for i in range(7)]
            else:
                drawn_numbers = []
                for k, v in res.items():
                    if 'bola' in k or 'col' in k:
                        drawn_numbers.append(v)
                dezenas = sorted(drawn_numbers)

            return {
                'concurso': res.get('concurso'),
                'data': res.get('data_apuracao') or res.get('data'),
                'dezenas': dezenas
            }
    except Exception as e:
        print(f"Erro ao buscar resultado oficial {lottery_id}: {e}")
    return None

def check_elite_performance(lottery_id):
    """Compara os jogos de elite (Excel) com o último resultado oficial."""
    # Mapeamento do nome do arquivo Excel
    # dia_de_sorte, lotofácil, etc.
    excel_map = {
        'megasena': 'mega_sena_results.xlsx',
        'lotofacil': 'lotofácil_results.xlsx',
        'quina': 'quina_results.xlsx',
        'diadesorte': 'dia_de_sorte_results.xlsx',
        'lotomania': 'lotomania_results.xlsx',
        'supersete': 'super_sete_results.xlsx',
        'duplasena': 'dupla_sena_results.xlsx',
        'maismilionaria': 'mais_milionária_results.xlsx',
        'timemania': 'timemania_results.xlsx'
    }
    
    excel_file = excel_map.get(lottery_id)
    if not excel_file:
        return None
        
    excel_path = os.path.join(RESULTADOS_DIR, excel_file)
    if not os.path.exists(excel_path):
        return None

    official = get_latest_official_result(lottery_id)
    if not official:
        return None

    # Mapeamento de Cores Extraído do lotteries_config.py
    color_map = {
        'megasena': '#1B9A67',
        'lotofacil': '#7B1FA2',
        'quina': '#260184',
        'lotomania': '#E68527',
        'timemania': '#FFF600',
        'diadesorte': '#D4B31A',
        'duplasena': '#BA184A',
        'maismilionaria': '#31357C',
        'supersete': '#A9CF46',
        'federal': '#0065B3',
        'loteca': '#0066B3'
    }

    try:
        import openpyxl
        wb = openpyxl.load_workbook(excel_path, read_only=True)
        total_rows = max(0, wb.active.max_row - 3)
        
        # Lê o Excel (pula as 2 primeiras linhas de cabeçalho do LotteryLab, limitando a 100 linhas para o dashboard)
        df = pd.read_excel(excel_path, skiprows=2, nrows=100)
        
        # A coluna de números costuma se chamar '🎱 Números' ou similar
        # Vamos tentar localizar a coluna que contém os números
        num_col = None
        for col in df.columns:
            if 'Números' in str(col) or 'numeros' in str(col).lower() or str(col).upper() == 'D1':
                num_col = col
                break
        
        if not num_col:
            return None

        drawn_set = set(official['dezenas'])
        hits_count = {i: 0 for i in range(len(official['dezenas']) + 1)}
        
        performed_games = []
        
        # Analisa os top 50 jogos para performance rápida no dashboard
        for _, row in df.head(50).iterrows():
            # Converte string "01-05-10..." ou "01, 05, 10..." para lista de ints
            num_str = extract_elite_numbers(row, df, num_col)
            # Limpa caracteres desnecessários e tenta separar por '-' ou ','
            for char in ['[', ']', '"', "'"]:
                num_str = num_str.replace(char, '')
            
            separator = '-' if '-' in num_str else ','
            nums = [int(n.strip()) for n in num_str.split(separator) if n.strip().isdigit()]
            
            if lottery_id == 'supersete':
                # Conferência POSICIONAL
                acertos = sum(1 for i in range(min(len(nums), len(official['dezenas']))) if nums[i] == official['dezenas'][i])
            else:
                acertos = len(set(nums) & drawn_set)
                
            hits_count[acertos] += 1
            
            if acertos >= (len(nums) // 2): # Só mostra no log se for relevante
                performed_games.append({
                    'numeros': nums,
                    'acertos': acertos
                })

        # Mapeia o nome para exibição bonita
        display_names = {
            'megasena': 'Mega-Sena', 'lotofacil': 'Lotofácil', 'diadesorte': 'Dia de Sorte',
            'quina': 'Quina', 'lotomania': 'Lotomania', 'duplasena': 'Dupla Sena',
            'timemania': 'Timemania', 'supersete': 'Super Sete', 'maismilionaria': '+Milionária',
            'loteca': 'Loteca', 'federal': 'Federal'
        }

        active_hits = [k for k, v in hits_count.items() if v > 0]
        maior_acerto = max(active_hits) if active_hits else 0

        return {
            'loteria': display_names.get(lottery_id, lottery_id.upper()),
            'cor': color_map.get(lottery_id, '#38bdf8'),
            'ultimo_concurso': official['concurso'],
            'data': official['data'],
            'dezenas_sorteadas': official['dezenas'],
            'total_jogos_analisados': total_rows,
            'resumo_acertos': {k: v for k, v in hits_count.items() if v > 0},
            'maior_acerto': maior_acerto,
            'destaques': sorted(performed_games, key=lambda x: x['acertos'], reverse=True)[:5],
            'price': get_lottery_config(lottery_id).price if get_lottery_config(lottery_id) else 0.0
        }
    except Exception as e:
        print(f"Erro ao processar performance {lottery_id}: {e}")
    return None

def get_historical_performance(lottery_id, count=None):
    """Analisa a performance da elite contra os concursos passados (count=None traz todos)."""
    db_name = f"{lottery_id}.db"
    db_path = os.path.join(BANCOS_DIR, db_name)
    
    if not os.path.exists(db_path):
        return []

    excel_map = {
        'megasena': 'mega_sena_results.xlsx', 'lotofacil': 'lotofácil_results.xlsx',
        'quina': 'quina_results.xlsx', 'diadesorte': 'dia_de_sorte_results.xlsx',
        'lotomania': 'lotomania_results.xlsx', 'supersete': 'super_sete_results.xlsx',
        'duplasena': 'dupla_sena_results.xlsx', 'maismilionaria': 'mais_milionária_results.xlsx',
        'timemania': 'timemania_results.xlsx'
    }
    
    excel_file = excel_map.get(lottery_id)
    if not excel_file: return []
    excel_path = os.path.join(RESULTADOS_DIR, excel_file)
    if not os.path.exists(excel_path): return []

    try:
        # Carrega a elite apenas uma vez, limitando a 100 jogos para não engasgar
        df = pd.read_excel(excel_path, skiprows=2, nrows=100)
        num_col = None
        for col in df.columns:
            if 'Números' in str(col) or 'numeros' in str(col).lower() or str(col).upper() == 'D1':
                num_col = col
                break
        if not num_col: return []

        # Preparar dados da elite para comparação rápida
        elite_games = []
        is_pos = (lottery_id == 'supersete')
        for _, row in df.head(100).iterrows(): 
            num_str = extract_elite_numbers(row, df, num_col).replace('[','').replace(']','').replace('"','').replace("'",'')
            sep = '-' if '-' in num_str else ','
            nums_list = [int(n.strip()) for n in num_str.split(sep) if n.strip().isdigit()]
            if is_pos:
                elite_games.append(nums_list) # Mantém lista para posicional
            else:
                elite_games.append(set(nums_list)) # Usa set para as demais

        # Busca concursos passados
        conn = sqlite3.connect(db_path)
        table = 'results' if lottery_id == 'supersete' else 'sorteios'
        
        if count is None:
            query = f"SELECT * FROM {table} ORDER BY concurso DESC"
        else:
            query = f"SELECT * FROM {table} ORDER BY concurso DESC LIMIT {count + 1}"
        history_df = pd.read_sql_query(query, conn)
        conn.close()

        results = []
        all_max_hits: list[int] = []
        l_config = get_lottery_config(lottery_id)
        extra_cols = l_config.extra_cols if l_config else []

        for idx, row in history_df.iterrows():
            if idx == 0: continue # Pula o atual mostrado no topo
            
            # Identificação inteligente de dezenas
            drawn_s1 = []
            drawn_s2 = []
            extra_info = None

            if lottery_id == 'duplasena':
                # s1_bola1..6 e s2_bola1..6
                drawn_s1 = sorted([row[f's1_bola{i}'] for i in range(1, 7)])
                drawn_s2 = sorted([row[f's2_bola{i}'] for i in range(1, 7)])
            elif lottery_id == 'supersete':
                # col0..6
                drawn_s1 = [row[f'col{i}'] for i in range(7)]
            else:
                # Padrão: bola1..N
                drawn_cols = [c for c in history_df.columns if 'bola' in c and 'ordem' not in c]
                drawn_s1 = sorted([row[c] for c in drawn_cols])

            # Extra Info Genérica (baseada no config)
            if extra_cols:
                l_config = get_lottery_config(lottery_id)
                vals = [str(row.get(c, '')) for c in extra_cols]
                
                if lottery_id == 'maismilionaria' and len(vals) >= 2:
                    extra_info = f"{vals[0]} | {vals[1]}"
                elif lottery_id == 'diadesorte':
                    mes_idx = int(vals[0]) if vals[0].isdigit() else 0
                    mes_nome = ["-", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"][mes_idx] if 1 <= mes_idx <= 12 else vals[0]
                    mes_color = l_config.colors.meses.get(mes_idx, "var(--text)") if l_config else "var(--text)"
                    extra_info = f'<span style="background:{mes_color}33; color:{mes_color}; padding: 2px 8px; border-radius: 4px; font-weight: 600; border: 1px solid {mes_color}66;">{mes_nome}</span>'
                elif lottery_id == 'timemania':
                    team_name = vals[0].upper()
                    icon = TEAM_ICONS.get(team_name, "🛡️")
                    extra_info = f"{icon} {vals[0]}"
                else:
                    extra_info = ", ".join(vals)

            # Cálculo de acertos
            max_hits_s1 = 0
            hits_numbers_s1 = []
            
            if is_pos:
                # Super Sete: Conferência Posicional
                for game in elite_games:
                    # Compara índice a índice
                    matches = [i for i in range(min(len(game), len(drawn_s1))) if game[i] == drawn_s1[i]]
                    hits_count = len(matches)
                    if hits_count > max_hits_s1:
                        max_hits_s1 = hits_count
                        # Para posicional, hits_numbers_s1 guardará os ÍNDICES das colunas que acertaram
                        hits_numbers_s1 = matches
            else:
                drawn_set_s1 = set(drawn_s1)
                for game in elite_games:
                    # ensure game is treated as a set to avoid typing warning
                    g_set = game if isinstance(game, set) else set(game)
                    hits = g_set & drawn_set_s1
                    if len(hits) > max_hits_s1:
                        max_hits_s1 = len(hits)
                        hits_numbers_s1 = list(hits)

            display_hits = f"{max_hits_s1}"
            tier_name = PRIZE_TIERS.get(lottery_id, {}).get(max_hits_s1)
            if tier_name: display_hits += f" ({tier_name})"

            if lottery_id == 'duplasena':
                drawn_set_s2 = set(drawn_s2)
                max_hits_s2 = 0
                for game in elite_games:
                    g_set2 = game if isinstance(game, set) else set(game)
                    hits2 = len(g_set2 & drawn_set_s2)
                    if hits2 > max_hits_s2: max_hits_s2 = hits2
                
                tier_s2 = PRIZE_TIERS.get(lottery_id, {}).get(max_hits_s2)
                display_hits = f"S1: {max_hits_s1} | S2: {max_hits_s2}"
                all_max_hits.append(max_hits_s1) # Usa S1 para média
            else:
                all_max_hits.append(max_hits_s1)

            results.append({
                'concurso': int(row['concurso']),
                'data': row.get('data_apuracao') or row.get('data'),
                'resultado': drawn_s1,
                'resultado_s2': drawn_s2 if drawn_s2 else None,
                'dezenas_acertadas': hits_numbers_s1,
                'extra': extra_info,
                'acertos': display_hits
            })
            
        # Estatísticas simples
        stats = {
            'total_analisado': len(all_max_hits),
            'media_acertos': round(float(sum(all_max_hits)) / len(all_max_hits), 2) if all_max_hits else 0.0,
            'maior_acerto': int(max(all_max_hits)) if all_max_hits else 0
        }

        return {'history': results, 'stats': stats, 'price': l_config.price if l_config else 0.0}
    except Exception as e:
        print(f"Erro no histórico {lottery_id}: {e}")
    return {'history': [], 'stats': {}}

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/stats')
def stats():
    loterias = [
        'megasena', 'lotofacil', 'diadesorte', 'quina', 'lotomania',
        'duplasena', 'timemania', 'supersete', 'maismilionaria',
        'loteca', 'federal'
    ]
    results = []
    for lot in loterias:
        perf = check_elite_performance(lot)
        if perf:
            results.append(perf)
    return jsonify(results)

@app.route('/api/history/<lottery_id>')
def history(lottery_id):
    # Demora muito carregar o completo, limitando a 200 últimos concursos
    data = get_historical_performance(lottery_id, count=200)
    return jsonify(data)

@app.route('/api/elite/<lottery_id>')
def get_elite_games(lottery_id):
    """Retorna a lista de jogos de elite para exibição na web."""
    excel_map = {
        'megasena': 'mega_sena_results.xlsx', 'lotofacil': 'lotofácil_results.xlsx',
        'quina': 'quina_results.xlsx', 'diadesorte': 'dia_de_sorte_results.xlsx',
        'lotomania': 'lotomania_results.xlsx', 'supersete': 'super_sete_results.xlsx',
        'duplasena': 'dupla_sena_results.xlsx', 'maismilionaria': 'mais_milionária_results.xlsx',
        'timemania': 'timemania_results.xlsx'
    }
    excel_file = excel_map.get(lottery_id)
    if not excel_file: return jsonify([])
    excel_path = os.path.join(RESULTADOS_DIR, excel_file)
    if not os.path.exists(excel_path): return jsonify([])

    try:
        df = pd.read_excel(excel_path, skiprows=2, nrows=100)
        num_col = None
        for col in df.columns:
            if 'Números' in str(col) or 'numeros' in str(col).lower() or str(col).upper() == 'D1':
                num_col = col
                break
        if not num_col: return jsonify([])

        games = []
        # Retorna os top 100 para não sobrecarregar o browser
        for _, row in df.head(100).iterrows():
            num_str = extract_elite_numbers(row, df, num_col).replace('[','').replace(']','').replace('"','').replace("'",'')
            sep = '-' if '-' in num_str else ','
            nums = [n.strip() for n in num_str.split(sep) if n.strip().isdigit()]
            games.append(nums)
        
        l_config = get_lottery_config(lottery_id)
        return jsonify({
            'games': games,
            'price': l_config.price if l_config else 0.0
        })
    except Exception as e:
        print(f"Erro ao buscar elite {lottery_id}: {e}")
    return jsonify([])

@app.route('/api/export-elite/<lottery_id>')
def export_elite_txt(lottery_id):
    """Gera um arquivo .txt com os jogos de elite para download."""
    excel_map = {
        'megasena': 'mega_sena_results.xlsx', 'lotofacil': 'lotofácil_results.xlsx',
        'quina': 'quina_results.xlsx', 'diadesorte': 'dia_de_sorte_results.xlsx',
        'lotomania': 'lotomania_results.xlsx', 'supersete': 'super_sete_results.xlsx',
        'duplasena': 'dupla_sena_results.xlsx', 'maismilionaria': 'mais_milionária_results.xlsx',
        'timemania': 'timemania_results.xlsx'
    }
    excel_file = excel_map.get(lottery_id)
    if not excel_file: return "Arquivo não encontrado", 404
    excel_path = os.path.join(RESULTADOS_DIR, excel_file)
    if not os.path.exists(excel_path): return "Arquivo não encontrado", 404

    try:
        df = pd.read_excel(excel_path, skiprows=2)
        num_col = None
        for col in df.columns:
            if 'Números' in str(col) or 'numeros' in str(col).lower() or str(col).upper() == 'D1':
                num_col = col
                break
        if not num_col: return "Coluna de números não encontrada", 404

        content = []
        meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        teams = []
        for k in TEAM_ICONS.keys():
            if '/' in k:
                parts = k.split('/')
                teams.append(parts[0].title() + '/' + parts[1])
            else:
                teams.append(k.title())
        trevos_pairs = [(1,2), (1,3), (1,4), (2,3), (2,4), (3,4)]

        for idx, (_, row) in enumerate(df.iterrows()):
            num_str = extract_elite_numbers(row, df, num_col).replace('[','').replace(']','').replace('"','').replace("'",'')
            sep = '-' if '-' in num_str else ','
            nums = [n.strip().zfill(2) for n in num_str.split(sep) if n.strip().isdigit()]
            
            if lottery_id == 'diadesorte':
                nums.append(meses[idx % len(meses)])
            elif lottery_id == 'timemania':
                if teams:
                    nums.append(teams[idx % len(teams)])
            elif lottery_id == 'maismilionaria':
                pair = trevos_pairs[idx % len(trevos_pairs)]
                nums.extend([str(pair[0]), str(pair[1])])
                
            content.append(" ".join(nums))

        from flask import Response
        output = "\n".join(content)
        return Response(
            output,
            mimetype="text/plain",
            headers={"Content-disposition": f"attachment; filename=elite_{lottery_id}.txt"}
        )
    except Exception as e:
        return f"Erro ao exportar: {e}", 500

@app.route('/api/sync-all', methods=['POST'])
def sync_all():
    """Dispara o processo de sincronização e backtest em segundo plano."""
    def run_task():
        try:
            subprocess.run([sys.executable, "super_sync_elite.py"], cwd=LOTTERY_LAB_DIR)
        except Exception as e:
            print(f"Erro no sync global: {e}")

    thread = threading.Thread(target=run_task)
    thread.start()
    return jsonify({"status": "A sincronização incremental e o cálculo da elite foram iniciados. Isso pode levar alguns minutos."})

def auto_sync_check():
    """Verifica se é necessário rodar o sync automático (após as 21:30 ou de manhã se atrasado)."""
    sync_file = os.path.join(LOTTERY_LAB_DIR, '.last_sync')
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')
    
    last_sync_date = ""
    if os.path.exists(sync_file):
        with open(sync_file, 'r') as f:
            last_sync_date = f.read().strip()

    # Se já sincronizou hoje, não faz nada
    if last_sync_date == today:
        return

    should_sync = False
    # Sincroniza se for o momento exato após as 21:35
    if now.hour > 21 or (now.hour == 21 and now.minute >= 35):
        should_sync = True
    # Mas se for de dia (ex: ligou o PC agora de manhã) e ele NÃO sincronizou ontem!
    elif last_sync_date != yesterday:
        should_sync = True

    if should_sync:
        print(f"[{now.strftime('%H:%M:%S')}] Iniciando auto-sync inteligente (Sorteios atrasados ou concluídos)...")
        def task():
            try:
                subprocess.run([sys.executable, "super_sync_elite.py"], cwd=LOTTERY_LAB_DIR)
                with open(sync_file, 'w') as f:
                    # Se rodou de manhã recuperando o de ontem, só marca "ontem". Deixa livre para as 21:35 rodar de novo hoje à noite!
                    f.write(yesterday if now.hour < 21 else today)
            except Exception as e:
                print(f"Erro no auto-sync: {e}")
        threading.Thread(target=task).start()

def scheduler_thread():
    while True:
        try:
            auto_sync_check()
        except: pass
        time.sleep(3600)

if __name__ == '__main__':
    # Cria pasta templates se não existir
    templates_dir = os.path.join(os.getcwd(), 'templates')
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
        
    # Inicia o agendador em background
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        threading.Thread(target=scheduler_thread, daemon=True).start()

    print(f"Iniciando Dashboard de Assertividade na porta {PORT}...")
    app.run(host='0.0.0.0', port=PORT, debug=False)
