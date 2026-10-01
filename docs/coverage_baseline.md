# Cobertura de tests - Baseline

> **Fecha**: [fecha]
> **Commit**: [hash]
> **Total**: [XX.XX%]

## Cobertura por capa

| Capa | Cobertura |
|------|-----------|
| domain/ | XX% |
| app/ | XX% |
| adapters/ | XX% |
| infrastructure/ | XX% |
| config/ | XX% |

## Archivos con cobertura < 70% (candidatos a mejorar)

| Archivo | Cobertura | Notas |
|---------|-----------|-------|
| adapters/camera/webcam_adapter.py | 62% | Requiere hardware, difícil de testear |
| ... | | |

## Archivos con 0% (revisar si son código muerto)

| Archivo | Acción |
|---------|--------|
| ... | ¿Eliminar? ¿Testear? |

## Próximos pasos

- [ ] Añadir tests para [archivos con < 70%]
- [ ] Investigar archivos con 0%
- [ ] Definir umbral mínimo por capa (5.5.4)