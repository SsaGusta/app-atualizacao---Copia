@echo off
REM Script de Deploy para Windows - Libras Learning Web App

setlocal EnableDelayedExpansion

echo 🚀 Iniciando deploy da Libras Learning Web App...

if "%1"=="" goto :show_help
if "%1"=="help" goto :show_help
if "%1"=="dev" goto :run_dev
if "%1"=="prod" goto :run_prod
if "%1"=="build" goto :build_only
if "%1"=="stop" goto :stop_app
if "%1"=="logs" goto :show_logs
if "%1"=="clean" goto :clean_up
if "%1"=="status" goto :check_status

:show_help
echo.
echo Uso: %0 [OPCAO]
echo.
echo Opcoes:
echo   dev        Executar em modo desenvolvimento
echo   prod       Executar em modo producao com Docker
echo   build      Apenas construir imagens Docker
echo   stop       Parar aplicacao
echo   logs       Mostrar logs
echo   clean      Limpar containers e imagens
echo   status     Verificar status da aplicacao
echo   help       Mostrar esta ajuda
echo.
goto :end

:check_dependencies
echo 🔍 Verificando dependencias...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python nao encontrado. Instale Python 3.11 ou superior.
    exit /b 1
)

pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip nao encontrado. Instale pip.
    exit /b 1
)

if "%1"=="prod" (
    docker --version >nul 2>&1
    if !errorlevel! neq 0 (
        echo ❌ Docker nao encontrado. Instale Docker para producao.
        exit /b 1
    )
)

echo ✅ Dependencias verificadas!
goto :eof

:setup_environment
echo ⚙️ Configurando ambiente...

if not exist ".env" (
    echo 📝 Criando arquivo .env...
    copy ".env.example" ".env"
    echo ⚠️ IMPORTANTE: Edite o arquivo .env com suas configuracoes!
)

if not exist "flask_session" mkdir flask_session
if not exist "static\uploads" mkdir static\uploads
if not exist "data" mkdir data
if not exist "logs" mkdir logs

echo ✅ Ambiente configurado!
goto :eof

:run_dev
echo 🔧 Executando em modo desenvolvimento...

call :check_dependencies
if %errorlevel% neq 0 goto :end

call :setup_environment

echo 📦 Instalando dependencias Python...
pip install -r requirements.txt

echo 🌐 Iniciando servidor de desenvolvimento...
set FLASK_ENV=development
set FLASK_DEBUG=1
python app.py
goto :end

:run_prod
echo 🏭 Executando em modo producao...

call :check_dependencies prod
if %errorlevel% neq 0 goto :end

call :setup_environment

echo 🐳 Construindo e executando com Docker...
docker-compose up -d --build

echo ✅ Aplicacao rodando em producao!
echo 🌐 Acesse: http://localhost:5000
echo 📊 Logs: docker-compose logs -f
goto :end

:build_only
echo 🔨 Construindo imagens Docker...

call :check_dependencies prod
if %errorlevel% neq 0 goto :end

docker-compose build

echo ✅ Imagens construidas com sucesso!
goto :end

:stop_app
echo ⏹️ Parando aplicacao...

docker-compose down >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Containers Docker parados!
)

taskkill /f /im python.exe >nul 2>&1
taskkill /f /im gunicorn.exe >nul 2>&1

echo ✅ Aplicacao parada!
goto :end

:show_logs
echo 📋 Mostrando logs...

docker-compose ps >nul 2>&1
if %errorlevel% equ 0 (
    docker-compose logs -f
) else (
    echo ⚠️ Nenhum container Docker rodando.
    if exist "app.log" (
        type app.log
    ) else (
        echo ⚠️ Nenhum arquivo de log encontrado.
    )
)
goto :end

:clean_up
echo 🧹 Limpando containers e imagens...

docker-compose down --rmi all --volumes --remove-orphans
docker system prune -f

echo ✅ Limpeza concluida!
goto :end

:check_status
echo 📊 Status da aplicacao:
echo.

docker-compose ps >nul 2>&1
if %errorlevel% equ 0 (
    echo 🐳 Docker: ✅ Rodando
    docker-compose ps
) else (
    echo 🐳 Docker: ❌ Parado
)

tasklist /fi "imagename eq python.exe" | find "python.exe" >nul
if %errorlevel% equ 0 (
    echo 🐍 Python: ✅ Rodando
) else (
    echo 🐍 Python: ❌ Parado
)

netstat -an | find ":5000" >nul
if %errorlevel% equ 0 (
    echo 🌐 Porta 5000: ✅ Em uso
) else (
    echo 🌐 Porta 5000: ❌ Livre
)
goto :end

:end
echo.
echo 🎉 Operacao concluida!
pause