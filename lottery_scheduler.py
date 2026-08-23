"""
╔══════════════════════════════════════════════════════════════════╗
║           LotteryLab - Robô Agendador de Backtests               ║
║           Autor: Sistema automatizado para Loterias Caixa        ║
╚══════════════════════════════════════════════════════════════════╝

Executa backtest de cada loteria automaticamente nos dias e
horários corretos, antes do sorteio da Caixa Econômica Federal.
"""

import schedule
import subprocess
import time
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# ──────────────────────────────────────────────────────────────────
# CONFIGURAÇÕES GLOBAIS
# ──────────────────────────────────────────────────────────────────

ROOT_DIR   = r"D:\LotteryLab"
PYTHON_EXE = sys.executable          # usa o mesmo Python que rodou este script
LOG_DIR    = Path(ROOT_DIR) / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "scheduler.log"

# ──────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO DO LOG
# ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8",
)

def log(msg: str, level: str = "info"):
    """Grava no arquivo .log e exibe no terminal (se houver)."""
    getattr(logging, level)(msg)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


# ──────────────────────────────────────────────────────────────────
# TABELA DE LOTERIAS
# Formato: "nome_loteria": {"horario": "HH:MM", "dias": [...]}
#
# Dias válidos para schedule:
#   monday / tuesday / wednesday / thursday / friday / saturday / sunday
#
# Referência de sorteios (Caixa) - horários ANTES do sorteio oficial:
#   Mega-Sena      → Ter, Qui, Sáb  → backtest às 18:30
#   Lotofácil      → Seg a Sáb      → backtest às 18:45
#   Quina          → Seg a Sáb      → backtest às 19:00
#   Lotomania      → Seg e Sáb      → backtest às 19:15
#   Timemania      → Ter, Qui, Sáb  → backtest às 18:45
#   Dupla Sena     → Ter, Qui, Sáb  → backtest às 19:00
#   Dia de Sorte   → Ter, Qui, Sáb  → backtest às 18:00  ← âncora (mais cedo)
#   Super Sete     → Seg, Qua, Sex  → backtest às 18:00
#   +Milionária    → Qua, Sáb       → backtest às 18:00
# ──────────────────────────────────────────────────────────────────

LOTERIAS = {
    # ── Terças, Quintas, Sábados ──────────────────────────────────
    "diadesorte": {
        "horario": "18:00",
        "dias": ["tuesday", "thursday", "saturday"],
    },
    "megasena": {
        "horario": "18:30",
        "dias": ["tuesday", "thursday", "saturday"],
    },
    "timemania": {
        "horario": "18:45",
        "dias": ["tuesday", "thursday", "saturday"],
    },
    "duplasena": {
        "horario": "19:00",
        "dias": ["tuesday", "thursday", "saturday"],
    },

    # ── Segunda a Sábado ──────────────────────────────────────────
    "lotofacil": {
        "horario": "18:45",
        "dias": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
    },
    "quina": {
        "horario": "19:00",
        "dias": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
    },

    # ── Segunda e Sábado ─────────────────────────────────────────
    "lotomania": {
        "horario": "19:15",
        "dias": ["monday", "saturday"],
    },

    # ── Segunda, Quarta, Sexta ───────────────────────────────────
    "supersete": {
        "horario": "18:00",
        "dias": ["monday", "wednesday", "friday"],
    },

    # ── Quarta e Sábado ──────────────────────────────────────────
    "maismilionaria": {
        "horario": "18:00",
        "dias": ["wednesday", "saturday"],
    },
}


# ──────────────────────────────────────────────────────────────────
# FUNÇÃO DE EXECUÇÃO DO BACKTEST
# ──────────────────────────────────────────────────────────────────

def run_backtest(loteria: str):
    """Executa python run_backtest.py --loteria <loteria> no diretório raiz."""
    cmd = [PYTHON_EXE, "run_backtest.py", "--loteria", loteria]
    log(f"▶  Iniciando backtest → {loteria.upper()}")

    try:
        resultado = subprocess.run(
            cmd,
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            timeout=600,          # máx 10 minutos por loteria
            encoding="utf-8",
            errors="replace",
        )

        if resultado.returncode == 0:
            log(f"✔  Backtest concluído com SUCESSO → {loteria.upper()}")
        else:
            stderr_resumo = resultado.stderr.strip()[:500] if resultado.stderr else "sem detalhes"
            log(
                f"✘  Backtest FALHOU → {loteria.upper()} "
                f"(código {resultado.returncode}) | {stderr_resumo}",
                level="error",
            )

    except subprocess.TimeoutExpired:
        log(f"✘  TIMEOUT → {loteria.upper()} excedeu 10 minutos.", level="error")

    except FileNotFoundError:
        log(
            f"✘  ERRO: run_backtest.py não encontrado em '{ROOT_DIR}'. "
            "Verifique o caminho ROOT_DIR no script.",
            level="error",
        )

    except Exception as exc:
        log(f"✘  ERRO INESPERADO → {loteria.upper()} | {exc}", level="error")


# ──────────────────────────────────────────────────────────────────
# REGISTRO DOS AGENDAMENTOS
# ──────────────────────────────────────────────────────────────────

DIA_EN_PT = {
    "monday":    "Segunda",
    "tuesday":   "Terça",
    "wednesday": "Quarta",
    "thursday":  "Quinta",
    "friday":    "Sexta",
    "saturday":  "Sábado",
    "sunday":    "Domingo",
}

def registrar_agendamentos():
    """Lê o dicionário LOTERIAS e cadastra todos os jobs no schedule."""
    for loteria, cfg in LOTERIAS.items():
        horario = cfg["horario"]
        dias    = cfg["dias"]

        for dia in dias:
            job_func = lambda l=loteria: run_backtest(l)
            getattr(schedule.every(), dia).at(horario).do(job_func)
            dia_pt = DIA_EN_PT.get(dia, dia)
            log(f"   ✓ Agendado: {loteria.upper():<16} → {dia_pt:<8} às {horario}")

    log("=" * 60)
    log(f"  Total de jobs cadastrados: {len(schedule.jobs)}")
    log("=" * 60)


# ──────────────────────────────────────────────────────────────────
# LOOP PRINCIPAL
# ──────────────────────────────────────────────────────────────────

def main():
    log("=" * 60)
    log("  LotteryLab Scheduler — INICIADO")
    log(f"  Diretório raiz : {ROOT_DIR}")
    log(f"  Logs em        : {LOG_FILE}")
    log(f"  Python         : {PYTHON_EXE}")
    log("=" * 60)

    registrar_agendamentos()
    log("  Robô em espera... (Ctrl+C para encerrar)")

    while True:
        schedule.run_pending()
        time.sleep(30)      # verifica a cada 30 segundos


# ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("  Robô encerrado manualmente pelo usuário.")
