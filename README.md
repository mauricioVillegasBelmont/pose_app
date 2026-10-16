# Pose AR App

[![CI](https://github.com/mauricioVillegasBelmont/pose_app/actions/workflows/ci.yml/badge.svg)](https://github.com/mauricioVillegasBelmont/pose_app/actions/workflows/ci.yml)
[![Slow Tests](https://github.com/mauricioVillegasBelmont/pose_app/actions/workflows/slow-tests.yml/badge.svg)](https://github.com/mauricioVillegasBelmont/pose_app/actions/workflows/slow-tests.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

Aplicación de realidad aumentada con juegos controlados por pose humana.
Usa **Mediapipe** para estimar la pose y **Pygame/OpenCV** para captura y render.

Arquitectura **hexagonal** (puertos y adaptadores) con un **sistema de plugins**:
cada juego vive en su propio plugin autocontenido y se registra automáticamente.

## ✨ Juegos incluidos

| `GAME_TYPE` | Descripción |
|-------------|-------------|
| `particles` | Sistema de partículas que reacciona a los landmarks |
| `color`     | Fondo de color según la pose (paletas: `fire`, `ocean`, `forest`, `neon`) |
| `gestures`  | Detecta y cuenta gestos con las manos |

---

## 📦 Requisitos

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** (gestor de entorno y dependencias)
- **Webcam** (opcional: `ENVIRONMENT=testing` usa una cámara simulada)

---

## 🚀 Instalación

```bash
# Crea el entorno e instala runtime + dev
uv sync --dev

# Solo runtime (producción)
uv sync
```

> El grupo `dev` (pytest, mypy, ruff, hypothesis…) se instala con `--dev`.

### Configuración

Copia la plantilla de variables de entorno y ajusta los valores:

```bash
cp .env.example .env
```

Variables más relevantes (ver `.env.example` para la lista completa):

| Variable | Valores | Descripción |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` \| `production` \| `testing` | En `testing` usa cámara mock |
| `GAME_TYPE` | `particles` \| `color` \| `gestures` | Juego a ejecutar |
| `POSE_PROVIDER` | `mediapipe` \| `mock` | Estimador de pose |
| `RENDER_PROVIDER` | `pygame` \| `mock` | Renderizador |
| `CAMERA_ID` | `0`, `1`, … | Índice de webcam |
| `API_ENABLED` | `true` \| `false` | Levanta la API REST (puerto `API_PORT`) |
| `JWT_SECRET_KEY` | string (≥32 chars) | **Obligatorio** para firmar tokens |

---

## ▶️ Ejecutar la aplicación

Entry point: `pose_app.app.main`.

```bash
# Con cámara real + Mediapipe + ventana Pygame
uv run python -m pose_app.app.main

# Sin cámara física (cámara simulada), sin ventana
ENVIRONMENT=testing GAME_TYPE=particles POSE_PROVIDER=mock RENDER_PROVIDER=mock \
  uv run python -m pose_app.app.main

# Cambia de juego
GAME_TYPE=color uv run python -m pose_app.app.main
GAME_TYPE=gestures uv run python -m pose_app.app.main
```

La app corre el juego y la API REST en paralelo hasta recibir `SIGINT`/`SIGTERM`.

---

## 🌐 API REST

Con `API_ENABLED=true`, la API queda en `http://localhost:8000/api/v1`.

| Método | Endpoint | Auth | Descripción |
|--------|----------|------|-------------|
| `GET`  | `/health` | — | Estado del servicio |
| `POST` | `/auth/token` | — | Login (form) → token JWT |
| `GET`  | `/auth/me` | ✅ | Usuario autenticado |
| `GET`  | `/state` | ✅ | Snapshot de todos los juegos |
| `GET`  | `/state/{game_id}` | — | Snapshot de un juego |
| `GET`  | `/stats` | — | Estadísticas de los juegos |
| `POST` | `/commands/reset-particles` | — | Publica `GameResetRequested` |
| `POST` | `/commands/change-palette` | — | Publica `PaletteChangeRequested` |
| `GET/PATCH/POST` | `/users/me`, `/users/me/password` | ✅ | Perfil self-service |
| `GET/POST/PATCH/DELETE` | `/users`, `/users/{id}` | ✅ admin | CRUD de usuarios |

Los usuarios se cargan al arrancar desde `data/users.json` (bootstrap).

```bash
# 1. Obtener token (credenciales definidas en data/users.json)
curl -X POST http://localhost:8000/api/v1/auth/token \
  -d "username=<usuario>&password=<password>"

# 2. Consultar el estado (requiere Bearer token)
curl http://localhost:8000/api/v1/state \
  -H "Authorization: Bearer <access_token>"

# 3. Comando: cambiar paleta del juego color
curl -X POST http://localhost:8000/api/v1/commands/change-palette \
  -H "Content-Type: application/json" \
  -d '{"palette": "ocean"}'
```

---

## 🧪 Testing

```bash
# Suite rápida (los tests marcados "slow" se omiten por defecto)
uv run pytest -v

# Solo un archivo/módulo
uv run pytest tests/unit/test_webcam_adapter.py -v

# Tests lentos (inicializan Mediapipe real)
uv run pytest -m slow -v
```

### Cobertura

```bash
# Reporte en terminal + XML
uv run pytest --cov --cov-report=term-missing --cov-report=xml

# Verificar umbrales por capa (requiere coverage.xml)
uv run python scripts/check_coverage.py

# O todo de una vez
./scripts/coverage_check.sh
```

```bash
# Abrir el reporte HTML (tras --cov-report=html)
xdg-open htmlcov/index.html      # Linux
open htmlcov/index.html          # macOS
explorer.exe htmlcov/index.html  # WSL / Windows
```

---

## 🎨 Calidad de código

```bash
uv run ruff format .   # Formato
uv run ruff check .    # Lint
uv run mypy .          # Type checking
```

El proyecto usa **pre-commit**; los hooks corren automáticamente:

```bash
uv run pre-commit install
```

---

## 🗂️ Estructura del proyecto

```
src/pose_app/
├── domain/          # Lógica pura (sin frameworks): entidades, puertos, juegos
│   ├── entities/    # PoseLandmark, Particle, RGBColor, User, Identity…
│   ├── ports/       # Contratos (CameraPort, PoseEstimatorPort, render…)
│   ├── games/       # Juegos: particles, color, gestures (estado + lógica)
│   └── events/      # Eventos de dominio
├── app/             # Orquestación: main, plugins, container, registries
├── adapters/        # Implementaciones de los puertos
│   ├── camera/      # WebcamAdapter (OpenCV)
│   ├── pose/        # MediapipeAdapter (Tasks API)
│   ├── render/      # Adaptadores Pygame + overlays
│   ├── mock/        # Cámara/pose/render simulados (testing)
│   ├── api/         # FastAPI (rutas, schemas, dependencias)
│   └── auth/        # Autenticación y repositorios en memoria
├── infrastructure/  # DI, logging, errores, event bus, JWT
└── config/          # Settings (pydantic-settings)

tests/
├── unit/            # Tests aislados con mocks
├── integration/     # End-to-end (plugins, API, mediapipe)
├── property/        # Property-based tests (hypothesis)
└── manual/          # Scripts manuales (no corren en CI)
```

**Regla de oro**: el dominio no conoce frameworks. Los adaptadores implementan
puertos y son lo único que sabe de OpenCV, Mediapipe, Pygame o FastAPI.

---

## 📚 Documentación adicional

| Documento | Contenido |
|-----------|-----------|
| `docs/ports_contract.md` | Contratos de todos los puertos (fuente de verdad) |
| `docs/render_architecture.md` | Arquitectura de render (capacidades + SceneManager) |
| `docs/adding_a_game_plugin.md` | Guía paso a paso para añadir un juego |
| `docs/code_style.md` | Guía de estilos y tipado |
| `docs/directory_structure.md` | Estructura detallada del proyecto |
| `AGENTS.md` | Reglas y flujo de trabajo del proyecto |

---

## 🔌 WSL (webcam vía USB/IP)

Para pasar la webcam desde Windows a WSL:

```powershell
usbipd list
usbipd attach --wsl --busid <BUSID>
```

---

## 📥 Dependencias

```bash
uv add <paquete>           # Runtime → pyproject + uv.lock
uv add --dev <paquete>     # Desarrollo
uv lock --upgrade          # Actualiza todo
uv lock --upgrade-package <paquete>   # Solo un paquete
```
