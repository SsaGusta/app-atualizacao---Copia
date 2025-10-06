#!/bin/bash

# Script de Deploy para Libras Learning Web App
# Este script automatiza o processo de deploy da aplicação

set -e  # Exit on any error

echo "🚀 Iniciando deploy da Libras Learning Web App..."

# Função para mostrar help
show_help() {
    echo "Uso: $0 [OPÇÃO]"
    echo ""
    echo "Opções:"
    echo "  dev        Executar em modo desenvolvimento"
    echo "  prod       Executar em modo produção com Docker"
    echo "  build      Apenas construir imagens Docker"
    echo "  stop       Parar aplicação"
    echo "  logs       Mostrar logs"
    echo "  clean      Limpar containers e imagens"
    echo "  help       Mostrar esta ajuda"
    echo ""
}

# Função para verificar dependências
check_dependencies() {
    echo "🔍 Verificando dependências..."
    
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 não encontrado. Instale Python 3.11 ou superior."
        exit 1
    fi
    
    if ! command -v pip &> /dev/null; then
        echo "❌ pip não encontrado. Instale pip."
        exit 1
    fi
    
    if [ "$1" = "prod" ] && ! command -v docker &> /dev/null; then
        echo "❌ Docker não encontrado. Instale Docker para produção."
        exit 1
    fi
    
    echo "✅ Dependências verificadas!"
}

# Função para setup do ambiente
setup_environment() {
    echo "⚙️ Configurando ambiente..."
    
    # Criar .env se não existir
    if [ ! -f .env ]; then
        echo "📝 Criando arquivo .env..."
        cp .env.example .env
        echo "⚠️ IMPORTANTE: Edite o arquivo .env com suas configurações!"
    fi
    
    # Criar diretórios necessários
    mkdir -p flask_session static/uploads data logs
    echo "✅ Ambiente configurado!"
}

# Função para executar em desenvolvimento
run_dev() {
    echo "🔧 Executando em modo desenvolvimento..."
    
    check_dependencies
    setup_environment
    
    echo "📦 Instalando dependências Python..."
    pip install -r requirements.txt
    
    echo "🌐 Iniciando servidor de desenvolvimento..."
    export FLASK_ENV=development
    export FLASK_DEBUG=1
    python app.py
}

# Função para executar em produção
run_prod() {
    echo "🏭 Executando em modo produção..."
    
    check_dependencies "prod"
    setup_environment
    
    echo "🐳 Construindo e executando com Docker..."
    docker-compose up -d --build
    
    echo "✅ Aplicação rodando em produção!"
    echo "🌐 Acesse: http://localhost:5000"
    echo "📊 Logs: docker-compose logs -f"
}

# Função para apenas construir
build_only() {
    echo "🔨 Construindo imagens Docker..."
    
    check_dependencies "prod"
    docker-compose build
    
    echo "✅ Imagens construídas com sucesso!"
}

# Função para parar aplicação
stop_app() {
    echo "⏹️ Parando aplicação..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose down
        echo "✅ Containers Docker parados!"
    fi
    
    # Matar processos Python do app
    pkill -f "python app.py" || true
    pkill -f "gunicorn" || true
    
    echo "✅ Aplicação parada!"
}

# Função para mostrar logs
show_logs() {
    echo "📋 Mostrando logs..."
    
    if [ -f docker-compose.yml ] && docker-compose ps | grep -q "Up"; then
        docker-compose logs -f
    else
        echo "⚠️ Nenhum container Docker rodando."
        if [ -f app.log ]; then
            tail -f app.log
        else
            echo "⚠️ Nenhum arquivo de log encontrado."
        fi
    fi
}

# Função para limpeza
clean_up() {
    echo "🧹 Limpando containers e imagens..."
    
    docker-compose down --rmi all --volumes --remove-orphans || true
    docker system prune -f || true
    
    echo "✅ Limpeza concluída!"
}

# Função para verificar status
check_status() {
    echo "📊 Status da aplicação:"
    echo ""
    
    # Verificar se está rodando com Docker
    if command -v docker-compose &> /dev/null; then
        if docker-compose ps | grep -q "Up"; then
            echo "🐳 Docker: ✅ Rodando"
            docker-compose ps
        else
            echo "🐳 Docker: ❌ Parado"
        fi
    fi
    
    # Verificar se está rodando diretamente
    if pgrep -f "python app.py" > /dev/null; then
        echo "🐍 Python: ✅ Rodando"
    else
        echo "🐍 Python: ❌ Parado"
    fi
    
    # Verificar porta
    if netstat -tuln 2>/dev/null | grep -q ":5000 "; then
        echo "🌐 Porta 5000: ✅ Em uso"
    else
        echo "🌐 Porta 5000: ❌ Livre"
    fi
}

# Main script
case "$1" in
    "dev")
        run_dev
        ;;
    "prod")
        run_prod
        ;;
    "build")
        build_only
        ;;
    "stop")
        stop_app
        ;;
    "logs")
        show_logs
        ;;
    "clean")
        clean_up
        ;;
    "status")
        check_status
        ;;
    "help"|"")
        show_help
        ;;
    *)
        echo "❌ Opção inválida: $1"
        show_help
        exit 1
        ;;
esac

echo ""
echo "🎉 Operação concluída!"