@echo off
REM Script de Inicialização Inteligente - Libras Learning
title Libras Learning - Inicializacao

setlocal EnableDelayedExpansion

echo.
echo ================================
echo   LIBRAS LEARNING WEB APP
echo ================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python nao encontrado!
    echo.
    echo Instale Python 3.8+ em: https://python.org
    echo.
    pause
    exit /b 1
)

echo ✅ Python encontrado
python --version

REM Verificar se estamos no diretório correto
if not exist "app.py" (
    echo.
    echo ❌ Arquivo app.py nao encontrado!
    echo ⚠️ Certifique-se de estar na pasta correta
    echo.
    echo Pasta atual: %CD%
    echo.
    pause
    exit /b 1
)

echo ✅ Arquivos encontrados

REM Verificar/instalar dependências
echo.
echo 📦 Verificando dependencias...
pip install flask flask-session flask-cors opencv-python mediapipe pandas numpy scikit-learn pillow >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ Problemas ao instalar dependencias
    echo Tentando novamente...
    pip install --upgrade pip
    pip install -r requirements.txt
)

echo ✅ Dependencias verificadas

REM Verificar se porta 5000 está livre
netstat -an | find ":5000" >nul
if %errorlevel% equ 0 (
    echo.
    echo ⚠️ Porta 5000 em uso!
    echo Tentando parar processos Python...
    taskkill /f /im python.exe >nul 2>&1
    echo ✅ Processos limpos
    timeout /t 2 >nul
)

REM Criar diretórios necessários
if not exist "flask_session" mkdir flask_session
if not exist "static\uploads" mkdir static\uploads
if not exist "templates" mkdir templates
if not exist "static\css" mkdir static\css
if not exist "static\js" mkdir static\js

echo ✅ Estrutura de pastas verificada

REM Testar importação básica
echo.
echo 🔬 Testando configuracao...
python -c "import flask; print('Flask OK')" 2>nul
if %errorlevel% neq 0 (
    echo ❌ Erro ao importar Flask
    echo Reinstalando Flask...
    pip install --force-reinstall flask
)

REM Decidir qual versão executar
set USE_SIMPLE=N
if exist "teste_simples.py" (
    echo.
    echo Qual versão deseja executar?
    echo [1] Versão completa com ML e câmera
    echo [2] Versão simples para teste
    echo.
    choice /c 12 /n /m "Digite 1 ou 2: "
    if !errorlevel! equ 2 set USE_SIMPLE=Y
)

echo.
echo 🚀 Iniciando aplicacao...
echo.

if "!USE_SIMPLE!"=="Y" (
    echo Executando versão SIMPLES para teste...
    echo ➡️ Acesse: http://127.0.0.1:5000
    echo ➡️ Para parar: Ctrl+C
    echo.
    python teste_simples.py
) else (
    echo Executando versão COMPLETA...
    echo ➡️ Acesse: http://127.0.0.1:5000
    echo ➡️ Para parar: Ctrl+C
    echo.
    echo Aguardando inicializacao...
    timeout /t 3 >nul
    python app.py
)

if %errorlevel% neq 0 (
    echo.
    echo ❌ Erro ao iniciar aplicacao!
    echo.
    echo DIAGNOSTICO:
    echo 1. Verifique se nao ha erros de sintaxe
    echo 2. Tente executar: python teste_simples.py
    echo 3. Verifique o firewall/antivirus
    echo 4. Execute: python diagnostico.py
    echo.
    echo Pressione qualquer tecla para tentar versao simples...
    pause >nul
    
    if exist "teste_simples.py" (
        echo Tentando versao simples...
        python teste_simples.py
    )
)

echo.
echo 🏁 Aplicacao finalizada
pause