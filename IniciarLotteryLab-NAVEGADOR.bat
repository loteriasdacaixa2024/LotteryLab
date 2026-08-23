@echo off
TITLE LotteryLab Live - Dashboard
cd /d "D:\Loterias\LotteryLab"

echo ====================================================
echo    INICIANDO LOTTERYLAB LIVE - PORTA 8082
echo ====================================================
echo.

:: Ativa o ambiente virtual
call venv\Scripts\activate

:: Verifica se a ativacao funcionou
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Nao foi possivel ativar o venv. Verifique se ele existe em D:\LotteryLab\venv
    pause
    exit /b
)

echo [OK] Ambiente Virtual Ativado.
echo [OK] Abrindo navegador em http://localhost:8082
echo.

:: Pequeno delay para o flask subir antes de abrir o browser
start http://localhost:8082

:: Executa o app
python app_conferidor.py

pause
