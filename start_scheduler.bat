@echo off
REM ═══════════════════════════════════════════════════════════════
REM  LotteryLab Scheduler — Iniciador Automático (Windows)
REM
REM  INSTRUÇÕES DE USO — LEIA ANTES DE EXECUTAR:
REM
REM  1. DEPENDÊNCIA:
REM       pip install schedule
REM
REM  2. COLOQUE OS ARQUIVOS EM:
REM       D:\LotteryLab\lottery_scheduler.py
REM       D:\LotteryLab\start_scheduler.bat   ← este arquivo
REM
REM  3. PARA INICIAR JUNTO COM O WINDOWS (sem abrir nada):
REM
REM     a) Pressione  Win + R  e digite:
REM           shell:startup
REM        (abre a pasta de inicialização do Windows)
REM
REM     b) Dentro dessa pasta, crie um ATALHO para este .bat:
REM           → Clique direito → Novo → Atalho
REM           → Localização: D:\LotteryLab\start_scheduler.bat
REM           → Nome: LotteryLab Scheduler
REM
REM     c) Clique com botão direito no atalho criado → Propriedades
REM           → "Executar": altere para "Minimizado"
REM           → OK
REM
REM     Pronto! O robô vai iniciar invisível toda vez que o
REM     Windows ligar, sem abrir nenhuma janela.
REM
REM  4. VERIFICANDO SE ESTÁ RODANDO:
REM       Abra o Gerenciador de Tarefas (Ctrl+Shift+Esc)
REM       → aba "Detalhes" → procure por "pythonw.exe"
REM
REM  5. PARA PARAR O ROBÔ:
REM       No Gerenciador de Tarefas, encerre o processo "pythonw.exe"
REM       (ou o processo python que estiver rodando o scheduler)
REM
REM  6. LOGS — Verifique se tudo está funcionando em:
REM       D:\LotteryLab\logs\scheduler.log
REM ═══════════════════════════════════════════════════════════════

REM — Define o diretório raiz do projeto
set ROOT=D:\LotteryLab

REM — Muda para o diretório raiz
cd /d "%ROOT%"

REM — Instala a dependência caso ainda não esteja instalada
REM   (silencioso, apenas na primeira vez que precisar)
pip install schedule --quiet >nul 2>&1

REM — Inicia o robô de forma INVISÍVEL usando pythonw.exe
REM   (pythonw não abre janela de console)
start "" pythonw "%ROOT%\lottery_scheduler.py"

REM — Encerra este .bat imediatamente (sem deixar janela aberta)
exit
