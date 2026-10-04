# app/state_contract.py
"""
Contrato de datos publicados por cada juego.

Este archivo NO es código ejecutable, es documentación viva.

ParticlesGame publica:
    - "particles": List[Particle]       (máximo 100 en snapshot)
    - "particles_count": int

ColorGame publica:
    - "background_color": RGBColor
    - "current_palette": str            (nombre: "fire", "ocean", ...)

Comandos soportados por cada juego:

ParticlesGame:
    - "reset_particles" {}              → Vacía lista de partículas

ColorGame:
    - "change_palette" {"palette": str} → Cambia la paleta activa

Comandos desconocidos son ignorados silenciosamente por cada juego.
"""
