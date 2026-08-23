# Laboratório de Backtesting de Loterias - LotteryLab

O **LotteryLab** é um motor de backtesting extremamente otimizado, desenvolvido em Python para análise massiva de combinações de loteria contra resultados históricos armazenados em SQLite.

## 🚀 Destaques Técnicos

*   **Bitmasking**: Cada concurso é convertido em um inteiro (`bitmask`), onde cada bit representa um número sorteado. Isso permite comparar combinações usando operações bitwise (`&`) e `bit_count()`, que são extremamente rápidas em Python 3.10+.
*   **Paralelismo**: O motor utiliza `multiprocessing` para dividir as combinações em chunks e processá-los simultaneamente em todos os núcleos da CPU.
*   **Eficiência de Memória**: Embora o processamento seja em memória para velocidade, utilizamos geradores para evitar o carregamento simultâneo de milhões de combinações em formato de lista, economizando RAM.
*   **Flexibilidade**: Suporte para múltiplas loterias apenas alterando o parâmetro `--loteria`.

## 📁 Estrutura do Projeto

*   **`run_backtest.py`**: Ponto de entrada CLI para execução das análises.
*   **`motores/`**
    *   **`backtest_engine.py`**: O "coração" do sistema, contendo a lógica de processamento massivo.
    *   **`lottery_configs.py`**: Configurações modulares para Mega-Sena, Lotofácil, Quina, Dia de Sorte, etc.
*   **`bancos/`**: Pasta contendo os bancos SQLite históricos.
*   **`resultados/`**: O local onde os arquivos CSV e bancos de resultados são salvos.

## 🛠️ Como Executar

Para iniciar um backtesting (exemplo **Dia de Sorte**):

```powershell
python run_backtest.py --loteria diadesorte
```

Para **Mega-Sena**:

```powershell
python run_backtest.py --loteria megasena
```

Você também pode especificar o número de processos para otimizar o uso da CPU:

```powershell
python run_backtest.py --loteria lotofacil --processes 8
```

## 📊 Resultados

Ao final da execução, os resultados serão salvos em:

1.  **`resultados/[loteria]_results.csv`**
2.  **`resultados/results.db`** (Tabela com o nome da loteria)

Os campos gerados são:
*   **numeros**: A combinação analisada.
*   **acertos_maximos**: O maior número de acertos que esta combinação já obteve na história.
*   **hits_main**: Quantidade de ocorrências do acerto máximo/principal (ex: 7 na Dia de Sorte).
*   **hits_sec**: Quantidade de ocorrências do acerto secundário (ex: 6 na Dia de Sorte).
*   **score**: Pontuação calculada para ranqueamento estratégico baseada na frequência de acertos.

---
*Desenvolvido para análise estatística avançada de loterias.*



Aqui está a lista completa e atualizada de todos os comandos para iniciar o backtesting:

Modalidade	    Comando de Execução


Mais Milionária	python run_backtest.py --loteria maismilionaria
Super Sete	    python run_backtest.py --loteria supersete
Lotofácil	    python run_backtest.py --loteria lotofacil
Timemania	    python run_backtest.py --loteria timemania
Quina	        python run_backtest.py --loteria quina
Lotomania	    python run_backtest.py --loteria lotomania
Dupla Sena	    python run_backtest.py --loteria duplasena
Mega-Sena	    python run_backtest.py --loteria megasena
Dia de Sorte	python run_backtest.py --loteria diadesorte



PARTICULARIDADES EM RELAÇÃO AS MODALIDADES...

Para ser transparente e técnico, aqui está como o motor LotteryLab lida com essas particularidades no estágio atual. Como o foco do projeto é otimização extrema e velocidade bruta, tomamos algumas decisões arquiteturais:

1. Dia de Sorte (Mês) e Timemania (Time)
Comportamento: O motor ignora o "Mês da Sorte" e o "Time do Coração".
Por que?: No backtesting de combinações massivas, o objetivo é encontrar padrões nas dejenas. O Mês e o Time são sorteios independentes com probabilidade fixa (1/12 e 1/80). Eles funcionam como um "bônus" e não alteram a lógica combinatória das dezenas principais. Removê-los permite que o motor processe milhões de dezenas a mais por segundo.
2. Mais Milionária (Trevos)
Comportamento: O motor foca exclusivamente nos 6 números principais (campo de 1 a 50).
Por que?: O desafio matemático da Mais Milionária reside na combinação das 6 dezenas. Os trevos (1 a 6) são uma variável externa. O laboratório identifica quais combinações de 6 números são historicamente mais fortes. No backtest, o acerto de "6+0" (6 números e nenhum trevo) é o que estamos rastreando para gerar o ranking.
3. Super 7 (A particularidade Crítica)
Comportamento Atual: O motor trata como um conjunto de 7 números.
Atenção: O Super 7 é posicional (um número de 0 a 9 para cada uma das 7 colunas).
Ajuste Técnico: Para um backtest 100% fiel ao Super 7, a comparação precisa ser "posição por posição". No motor atual, ele conta se o número existe na combinação, mas não necessariamente se ele está na coluna correta.
Dica: Se o seu foco for o Super 7 especificamente, eu posso atualizar o motor para usar uma "Máscara Posicional de 70 bits" (10 bits por coluna), mantendo a velocidade do bitwise mas respeitando a regra das colunas.
4. Dupla Sena (Oportunidade Dupla)
Comportamento: Conforme implementamos, ele carrega ambos os sorteios (1º e 2º) para a memória como se fossem concursos independentes.
Resultado: Isso dobra a base de dados. Se uma combinação "X" acertou 6 pontos no segundo sorteio do concurso 1000, ela terá o mesmo peso de ter acertado no primeiro sorteio. Isso é ideal para identificar "combinações de sorte" que costumam aparecer com frequência na modalidade.
Resumo da Filosofia do Laboratório:
O LotteryLab "limpa" o que é puramente sorte bônus (Mês, Time, Trevos) para focar na matriz estatística das dezenas. Isso é o que permite analisar trilhões de possibilidades em tempo recorde.

Você gostaria que eu fizesse o ajuste de "Máscara Posicional" para o Super 7 ser 100% preciso nas colunas, ou o foco atual na frequência de números já atende sua estratégia?


REQUERIMENTS.TXT
O LotteryLab foi projetado para ser "zero dependência". Como o foco é a velocidade de execução pura, utilizei apenas módulos nativos da Biblioteca Padrão do Python 3.11+ (sqlite3, multiprocessing, itertools, etc.).

Isso significa que você não precisa instalar nada via pip para o motor funcionar. Basta ter o Python instalado.

Criei o arquivo 

requirements.txt
 apenas para documentar isso e deixá-lo como base caso você decida expandir o laboratório com ferramentas como pandas ou numpy no futuro.

Como configurar o seu ambiente:

Criar o venv (opcional, já que não há dependências):
powershell
python -m venv venv

Ativar o venv:
powershell
.\venv\Scripts\activate

Executar o backtest diretamente:
powershell
python run_backtest.py --loteria [nome_da_loteria]

## 📈 O que acontece após a execução?

Ao rodar um comando de backtesting, o motor segue este fluxo:

1.  **Carregamento Ultra-Rápido**: O sistema conecta ao banco SQLite da loteria escolhida, lê todos os concursos históricos e os converte instantaneamente em **Bitmasks** na memória RAM.
2.  **Processamento Massivo**: 
    *   O Python inicia múltiplos processos (um para cada núcleo do seu processador).
    *   As milhões de combinações possíveis são geradas e comparadas contra os milhares de resultados históricos usando operações matemáticas de baixo nível (`bitwise`).
    *   O console exibirá o progresso a cada **1.000.000 de combinações** processadas, para que você acompanhe a velocidade.
3.  **Filtragem Inteligente**: Apenas as combinações que atendem aos critérios mínimos (ex: pelo menos 1 vez 7 acertos ou 3 vezes 6 acertos na Dia de Sorte) são mantidas. Isso evita que você perca tempo com combinações "fracas".
4.  **Geração de Arquivos de Saída**:
    *   **CSV Customizado**: Um arquivo `.csv` é criado na pasta `resultados/` com o ranking das melhores combinações, pronto para abrir no Excel.
    *   **Banco de Dados de Elite**: O banco `resultados/results.db` é atualizado. Se você rodar a Mega-Sena, uma tabela `megasena` será criada com todos os dados técnicos e scores.
5.  **Score Estratégico**: Cada linha terá um `score` calculado. Quanto maior o score, mais frequente e "quente" é aquela combinação historicamente em relação aos acertos principais e secundários.

**Dica**: Após o término, o console mostrará o **tempo total gasto** e a **quantidade de combinações de elite** encontradas.