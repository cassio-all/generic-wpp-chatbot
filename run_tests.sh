#!/bin/bash

# Script para executar testes e gerar relatórios de cobertura

echo "🧪 Executando testes automatizados..."
echo "=================================="

# Ativar ambiente virtual se existir
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Instalar dependências de teste
echo "📦 Instalando dependências de teste..."
pip install -q pytest pytest-asyncio pytest-cov pytest-mock

# Executar testes com cobertura
echo ""
echo "🔍 Executando testes..."
pytest tests/ \
    -v \
    --cov=src \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-report=xml \
    --tb=short

# Verificar resultado
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Todos os testes passaram!"
    echo ""
    echo "📊 Relatórios gerados:"
    echo "  - HTML: htmlcov/index.html"
    echo "  - XML: coverage.xml"
    echo ""
    echo "Para visualizar o relatório HTML:"
    echo "  python -m http.server 8000 --directory htmlcov"
else
    echo ""
    echo "❌ Alguns testes falharam!"
    exit 1
fi
