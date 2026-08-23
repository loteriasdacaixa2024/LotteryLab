from dataclasses import dataclass
from typing import List, Optional, Union, Any

@dataclass
class LotteryConfig:
    name: str
    db_file: str
    table_name: str
    numbers_to_pick: int
    universe_size: int
    ball_columns: Union[List[str], List[List[str]]]
    min_hits_to_save: int # e.g., 7 for Dia de Sorte
    min_occurences: int = 1 # e.g., 1 occurrence of 7 hits
    secondary_hits: Optional[int] = None # e.g., 6 for Dia de Sorte
    secondary_min_occurences: int = 3 # e.g., 3 occurrences of 6 hits
    is_positional: bool = False # Para loterias tipo Super Sete onde a ordem importa e pode repetir

LOTTERY_CONFIGS = {
    'megasena': LotteryConfig(
        name='Mega-Sena',
        db_file='megasena.db',
        table_name='sorteios',
        numbers_to_pick=6,
        universe_size=60,
        ball_columns=[f'bola{i}' for i in range(1, 7)],
        min_hits_to_save=6,
        min_occurences=1,
        secondary_hits=5,
        secondary_min_occurences=3
    ),
    'lotofacil': LotteryConfig(
        name='Lotofácil',
        db_file='lotofacil.db',
        table_name='sorteios',
        numbers_to_pick=15,
        universe_size=25,
        ball_columns=[f'bola{i}' for i in range(1, 16)],
        min_hits_to_save=15,
        min_occurences=1,
        secondary_hits=14,
        secondary_min_occurences=2
    ),
    'quina': LotteryConfig(
        name='Quina',
        db_file='quina.db',
        table_name='sorteios',
        numbers_to_pick=5,
        universe_size=80,
        ball_columns=[f'bola{i}' for i in range(1, 6)],
        min_hits_to_save=5,
        min_occurences=1,
        secondary_hits=4,
        secondary_min_occurences=5
    ),
    'diadesorte': LotteryConfig(
        name='Dia de Sorte',
        db_file='diadesorte.db',
        table_name='sorteios',
        numbers_to_pick=7,
        universe_size=31,
        ball_columns=[f'bola{i}' for i in range(1, 8)],
        min_hits_to_save=7,
        min_occurences=1,
        secondary_hits=6,
        secondary_min_occurences=3
    ),
    'lotomania': LotteryConfig(
        name='Lotomania',
        db_file='lotomania.db',
        table_name='sorteios',
        numbers_to_pick=20,
        universe_size=100,
        ball_columns=[f'bola{i}' for i in range(1, 21)],
        min_hits_to_save=20,
        min_occurences=1,
        secondary_hits=19,
        secondary_min_occurences=2
    ),
    'supersete': LotteryConfig(
        name='Super Sete',
        db_file='supersete.db',
        table_name='results',
        numbers_to_pick=7,
        universe_size=10,
        ball_columns=[f'col{i}' for i in range(0, 7)],
        min_hits_to_save=5,
        min_occurences=1,
        secondary_hits=4,
        secondary_min_occurences=3,
        is_positional=True
    ),
    'duplasena': LotteryConfig(
        name='Dupla Sena',
        db_file='duplasena.db',
        table_name='sorteios',
        numbers_to_pick=6,
        universe_size=50,
        ball_columns=[
            [f's1_bola{i}' for i in range(1, 7)], # 1º Sorteio
            [f's2_bola{i}' for i in range(1, 7)]  # 2º Sorteio
        ],
        min_hits_to_save=6,
        min_occurences=1,
        secondary_hits=5,
        secondary_min_occurences=3
    ),
    'maismilionaria': LotteryConfig(
        name='Mais Milionária',
        db_file='maismilionaria.db',
        table_name='sorteios',
        numbers_to_pick=6,
        universe_size=50,
        ball_columns=[f'bola{i}' for i in range(1, 7)],
        min_hits_to_save=6,
        min_occurences=1,
        secondary_hits=5,
        secondary_min_occurences=3
    ),
    'timemania': LotteryConfig(
        name='Timemania',
        db_file='timemania.db',
        table_name='sorteios',
        numbers_to_pick=7,
        universe_size=80,
        ball_columns=[f'bola{i}' for i in range(1, 8)],
        min_hits_to_save=7,
        min_occurences=1,
        secondary_hits=6,
        secondary_min_occurences=3
    )
}
