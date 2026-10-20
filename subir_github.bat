@echo off
title Consert Cell - Enviar para GitHub
cd /d "%~dp0"

echo =======================================================
echo          Enviando Consert Cell para o GitHub
echo =======================================================
echo.

git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCESSO] Repositorio enviado com sucesso para o GitHub!
    echo Acesse: https://github.com/gabnuness/Consert-Cell
) else (
    echo.
    echo [AVISO] Se o repositorio ainda nao foi criado no GitHub,
    echo crie-o primeiro em: https://github.com/new?name=Consert-Cell
    echo e depois execute este arquivo novamente.
)

echo.
pause
