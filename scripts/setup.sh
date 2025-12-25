#!/bin/bash

# Setup script for PIX WhatsApp Automation

set -e

echo "🚀 Iniciando setup do PIX WhatsApp Automation..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Criando arquivo .env..."
    cp .env.example .env
    echo "⚠️  Por favor, configure as variáveis de ambiente no arquivo .env"
else
    echo "✅ Arquivo .env já existe"
fi

# Check if running with Docker
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "🐳 Docker detectado"
    read -p "Deseja executar com Docker? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🐳 Iniciando containers Docker..."
        docker-compose up --build -d
        echo "✅ Aplicação rodando em http://localhost:8000"
        echo "📚 Documentação disponível em http://localhost:8000/docs"
        exit 0
    fi
fi

# Local setup
echo "💻 Configurando ambiente local..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.11+ é necessário. Versão atual: $python_version"
    exit 1
fi

echo "✅ Python $python_version detectado"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Ativando ambiente virtual..."
source venv/bin/activate

# Install dependencies
echo "📚 Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Setup concluído!"
echo ""
echo "Para iniciar a aplicação:"
echo "  1. Ative o ambiente virtual: source venv/bin/activate"
echo "  2. Configure as variáveis no arquivo .env"
echo "  3. Execute: python -m src.main"
echo ""
echo "Ou use: make dev"
