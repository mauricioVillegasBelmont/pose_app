# Pose AR App

[![CI](https://github.com/TU_USUARIO/TU_REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/TU_USUARIO/TU_REPO/actions/workflows/ci.yml)
[![Slow Tests](https://github.com/TU_USUARIO/TU_REPO/actions/workflows/slow-tests.yml/badge.svg)](https://github.com/TU_USUARIO/TU_REPO/actions/workflows/slow-tests.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

## open for wsl

```powershell
usbipd list
usbipd attach --wsl --busid <BUSID>
```

## install

### Setup inicial (una vez)
```bash
# Migrar tu proyecto a uv
uv init --no-readme        # Si no tienes pyproject.toml
# O si ya tienes pyproject.toml:
uv sync                    # Lee el .toml y crea .venv + uv.lock
```

### Añadir dependencias
```bash
# Runtime
uv add mediapipe opencv-python pygame fastapi uvicorn

# Dev
uv add --dev pytest pytest-asyncio pytest-cov pytest-forked hypothesis mypy ruff
uv actualiza pyproject.toml automáticamente y regenera uv.lock.
```

### Instalar entorno
```bash
uv sync                    # Instala runtime
uv sync --extra dev        # Instala runtime + dev
```

### Ejecutar cosas
```bash
uv run pytest -v           # Corre pytest con el entorno
uv run python -m app.main  # Corre la app
```

### Actualizar dependencias
```bash
uv lock --upgrade                    # Actualiza todo
uv lock --upgrade-package requests   # Solo una
```

### 🔄 Cómo coexistir con requirements.txt
uv puede exportar a requirements.txt para compatibilidad:

```bash
uv export --format requirements-txt > requirements.txt
uv export --format requirements-txt --extra dev > requirements-dev.txt
```

Así, tu CI/CD puede seguir usando requirements.txt mientras tú desarrollas con uv.

---

## Testing

**Testing an unique file**

| uv run pytest `<path>` -v

```bash
uv run pytest -v
```


### Testing demo Games
```bash
# run a game
GAME_TYPE=particles POSE_PROVIDER=mock RENDER_PROVIDER=mock uv run python -m app.main
# run a game
GAME_TYPE=color POSE_PROVIDER=mock RENDER_PROVIDER=mock uv run python -m app.main
# run a game
GAME_TYPE=gestures POSE_PROVIDER=mock RENDER_PROVIDER=mock uv run python -m app.main
```
**then:**
```bash
curl http://localhost:8000/api/v1/state

curl -X POST http://localhost:8000/api/v1/commands/change-palette \
  -H "Content-Type: application/json" \
  -d '{"palette": "ocean"}'
```


### Test coverage
```bash
pytest --cov=. --cov-report=term-missing --cov-report=html --cov-report=xml
```

```bash
# Linux
xdg-open htmlcov/index.html

# Mac
open htmlcov/index.html

# WSL / Windows
explorer.exe htmlcov/index.html
```

### Test coverage verification
```bash
# 1. Corre coverage
uv run pytest --cov=. --cov-report=xml

# 2. Corre el script
uv run python scripts/check_coverage.py

#o solo corre
./scripts/coverage_check.sh
```
