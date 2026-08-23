import argparse
import sys
import os
import logging
from motores.lottery_configs import LOTTERY_CONFIGS
from motores.backtest_engine import BacktestEngine

# Configuração de Log para console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Lottery Backtesting Lab')
    parser.add_argument('--loteria', type=str, required=True, 
                        help='Nome da loteria (ex: megasena, lotofacil, quina, diadesorte)')
    parser.add_argument('--processes', type=int, default=None,
                        help='Numero de processos para paralelismo (default: todos os núcleos)')
    
    args = parser.parse_args()
    
    lottery_key = args.loteria.lower().replace('_', '')
    if lottery_key not in LOTTERY_CONFIGS:
        logger.error(f"Loteria '{args.loteria}' não configurada.")
        logger.info(f"Opções disponíveis: {', '.join(LOTTERY_CONFIGS.keys())}")
        sys.exit(1)
        
    config = LOTTERY_CONFIGS[lottery_key]
    
    # Check if DB exists
    db_path = os.path.join('bancos', config.db_file)
    if not os.path.exists(db_path):
        logger.error(f"Banco de dados não encontrado: {db_path}")
        sys.exit(1)
        
    try:
        engine = BacktestEngine(config)
        engine.run(num_processes=args.processes)
        logger.info("Execução concluída com sucesso!")
    except Exception as e:
        logger.exception(f"Erro durante a execução: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
