#!/usr/bin/env bash
# Corre tests + cobertura + verificación de umbrales.
# Uso: ./scripts/coverage_check.sh

set -e

echo "🧪 Corriendo tests con cobertura..."
if uv run pytest \
    --cov=. \
    --cov-report=term-missing \
    --cov-report=xml || false
then
    echo "✅ Tests pasaron"
else
    echo "⚠️  Tests fallaron o coverage por debajo del umbral de pytest-cov"
fi

echo "---------"
echo "📊 Verificando umbrales..."
uv run python scripts/check_coverage.py
