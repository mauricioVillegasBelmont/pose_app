# Cobertura de tests - Baseline

> **Fecha**: 10-11-2026
> **Commit**: 8a7f69b (merge `feature/refactor/render-migrate-legacy`)
> **Total**: 79.51% (2720/3421 líneas; incluye `scripts/`)

## Cobertura por capa

| Capa | Cobertura |
|------|-----------|
| domain/ | 84.9% (1041/1226) |
| app/ | 82.0% (301/367) |
| adapters/ | 81.8% (1086/1327) |
| infrastructure/ | 63.0% (199/316) |
| config/ | 98.9% (93/94) |

## Archivos con cobertura < 70% (candidatos a mejorar)

| Archivo | Cobertura | Notas |
|---------|-----------|-------|
| domain/games/particles/main.py | 64.8% (94/145) | Loop de juego; difícil de cubrir sin integración |
| adapters/render/pygame_particles.py | 56.9% (74/130) | Render pygame; requiere surface real |
| infrastructure/di/container.py | 66.7% (80/120) | Composition root; cubierto por tests de integración |
| domain/games/color/main.py | 51.4% (55/107) | Loop de juego |
| adapters/render/pygame_input_cursor.py | 58.3% (49/84) | Render pygame |
| infrastructure/logging/logger.py | 47.0% (31/66) | Configuración de logging |
| adapters/render/pygame_hud.py | 39.6% (21/53) | Render pygame |
| app/plugins/color_plugin.py | 69.4% (34/49) | Bootstrap de pygame |
| app/plugins/gestures_plugin.py | 64.6% (31/48) | Bootstrap de pygame |
| adapters/render/pygame_scene.py | 59.6% (28/47) | SceneManager pygame |

## Archivos con 0% (revisar si son código muerto)

| Archivo | Acción |
|---------|--------|
| scripts/check_coverage.py | Script de CI; excluido del umbral por diseño |
| scripts/probe_camera.py | Script manual; excluido del umbral por diseño |

## Próximos pasos

- [ ] Añadir tests para los archivos con < 70% (prioridad: `infrastructure/` al 63.0%).
- [ ] Revisar los scripts con 0%: son herramientas manuales, no código muerto.
- [ ] Mantener el umbral mínimo por capa definido en `scripts/check_coverage.py`.
