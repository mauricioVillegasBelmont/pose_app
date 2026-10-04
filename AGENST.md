# Reglas del Proyecto — Pose AR App

Este proyecto sigue **arquitectura hexagonal** con **sistema de plugins**.
Cualquier cambio debe respetar esta arquitectura.

---

## 📚 Documentación obligatoria

Antes de cualquier tarea, **lee estos documentos**:

1. `docs/ports_contract.md` — Contratos de puertos (fuente de verdad).
2. `docs/render_architecture.md` — Nueva arquitectura de render (si existe).

Si algo contradice estos documentos, **detente y pregunta**.

---

## 📚 Documentación de apoyo

1. `docs/directory_structure.md` — Estrucutra actual del proyecto.

---

## 🚫 Zonas prohibidas (NO TOCAR)

- `data/` — Datos de usuarios (JSONs de bootstrap).
- `.env` — Variables de entorno (secretos).
- `logs/` — Archivos de log generados.
- `htmlcov/`, `coverage.xml`, `.coverage` — Artefactos de cobertura.
- `uv.lock` — Lockfile de dependencias (solo `uv add/remove` lo modifica).
- `*.back` — Aerchivos de respaldo para el usuario (se encuentran ignorados en .gitignore).
- Cualquier carpeta `.venv/` o `__pycache__/`.

**Si crees que necesitas tocar algo de esta lista, DETENTE y pregunta.**

---

## ⚠️ Zonas restringidas (consultar antes)

- **Renombrar o eliminar** archivos existentes → siempre preguntar.
- **Modificar interfaces públicas** (puertos, clases exportadas) → siempre preguntar.
- **Añadir dependencias** nuevas → siempre preguntar.
- **Modificar tests existentes** → solo si el refactor lo exige, y explicar por qué.

---

## ✅ Zonas permitidas (libertad con cuidado)

- Crear **archivos nuevos** en carpetas existentes.
- Añadir **tests nuevos**.
- Añadir **métodos nuevos** a clases existentes (sin romper las firmas actuales).
- Actualizar **docstrings** y **comentarios**.
- Refactorizar **implementaciones internas** sin cambiar contratos.

---

## 🔄 Flujo de trabajo obligatorio

**Para cualquier tarea que toque >1 archivo**, sigue este flujo:

1. **Leer** los archivos relevantes + `AGENTS.md` + `docs/ports_contract.md`.
2. **Resumir** el estado actual (3-6 puntos).
3. **Listar** los archivos que vas a tocar (máximo 4 por iteración).
4. **Describir** los pasos numerados del cambio.
5. **Listar** dudas o decisiones ambiguas.
6. **DETENERTE** y esperar confirmación del usuario.

**No escribir código hasta que el usuario diga "adelante".**

Si el usuario pide explícitamente "solo hazlo", salta los pasos 3-6 pero **mantén el resumen (paso 2)**.

---

## 🎯 Reglas específicas de refactor

### Cuando refactorices:

- **Preserva el comportamiento observable**. Los tests existentes deben seguir pasando.
- **Cambios incrementales**. Cada paso debe dejar el proyecto funcionando.
- **No rompas imports públicos**. Si tienes que mover un archivo, actualiza **todos** los imports a la vez.
- **Actualiza los tests rotos**, pero no escribas tests nuevos sin pedirlo.
- **Un commit por paso lógico**. No mezcles cambios no relacionados.

### Cuando crees código nuevo:

- Sigue el **estilo del código existente** (mira archivos similares).
- Usa **tipado estricto** (`list[X]`, `X | None`, no `List`/`Optional`).
- Usa **docstrings** descriptivos con Args/Returns/Raises.
- Añade **logging** apropiado (`logger.debug/info/warning/error`).
- **No dejes TODOs sin contexto**. Si pones uno, explica qué y por qué.

### Cuando refactorices arquitectura:

- **Lee `docs/render_architecture.md` primero**.
- Los **puertos nuevos** deben ser **pequeños y específicos** (una sola responsabilidad).
- **Los puertos viejos** se marcan como deprecados pero **no se eliminan** hasta que todo migre.
- **Los adaptadores** implementan **un puerto específico**, nunca varios a la vez.

---

## 🧪 Testing

- **Antes de cambiar código**, corre `uv run pytest -v` para confirmar verde.
- **Después de cambiar código**, corre `uv run pytest -v` para confirmar que sigue verde.
- Si un test falla por tu cambio, **arréglalo o pregunta**. No lo marques como skip.
- **No borres tests** sin preguntar. Si un test ya no aplica, muévelo o documéntalo.

---

## 🛠️ Comandos útiles del proyecto

```bash
# Tests rápidos
uv run pytest -v

# Tests con cobertura
uv run pytest --cov --cov-report=term-missing

# Solo tests de un módulo
uv run pytest tests/unit/test_X.py -v

# Type checking
uv run mypy --ignore-missing-imports domain app adapters infrastructure config

# Linting + format
uv run ruff check --fix
uv run ruff format

# Correr la app
GAME_TYPE=particles POSE_PROVIDER=mock RENDER_PROVIDER=mock uv run python -m app.main
