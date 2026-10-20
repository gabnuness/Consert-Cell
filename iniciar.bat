@echo off
title Consert Cell - Gestao TI
cd /d "%~dp0"

echo =======================================================
echo         Iniciando o Sistema Consert Cell (TI)
echo =======================================================
echo.

if exist "venv\Scripts\activate.bat" (
    echo Ativando ambiente virtual (venv)...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo Ativando ambiente virtual (.venv)...
    call .venv\Scripts\activate.bat
) else (
    echo [1/2] Criando ambiente virtual Python (venv)...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo [2/2] Instalando dependencias...
    pip install -r requirements.txt
)

echo.
echo Iniciando servidor... O navegador abrira automaticamente em:
echo http://127.0.0.1:5000
echo.

python app.py

pause
