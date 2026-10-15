"""
Generación de partículas del juego.

Algoritmo de spawn con restricciones geométricas:
- Todas dentro del Workspace.
- Ninguna a menos de min_distance de otra.
- Determinista con rng inyectable.
- Fallo silencioso si no cabe (retorna menos de count).
"""

import math
import random

from domain.entities.particle import Particle
from domain.games.particles.geometry import Workspace


def spawn_particles(
    count: int,
    workspace: Workspace,
    screen_width: int,
    screen_height: int,
    rng: random.Random,
    min_distance: float = 0.15,
    particle_size: float = 20.0,
    particle_color: tuple[int, int, int] = (255, 200, 50),
    max_attempts_per_particle: int = 20,
) -> list[Particle]:
    """
    Genera hasta `count` partículas dentro del workspace.

    Intenta colocar cada partícula respetando una distancia mínima
    normalizada con las ya colocadas. Si tras `max_attempts_per_particle`
    intentos no encuentra un sitio, deja de intentar esa partícula
    (retorna menos de `count`). Esto evita loops infinitos cuando el
    workspace está muy lleno.

    Args:
        count: número máximo de partículas a generar.
        workspace: zona normalizada donde aparecen.
        screen_width: ancho de pantalla en píxeles (para convertir).
        screen_height: alto de pantalla en píxeles.
        rng: generador aleatorio inyectable (para determinismo).
        min_distance: distancia mínima normalizada entre partículas.
        particle_size: tamaño base en píxeles.
        particle_color: color RGB base.
        max_attempts_per_particle: intentos por partícula antes de rendirse.

    Returns:
        Lista de partículas (puede tener menos de `count`).

    Raises:
        ValueError: si `count < 0`, `screen_width <= 0`,
                    `screen_height <= 0`, o `min_distance < 0`.

    Contrato:
        - Todas las partículas están dentro del workspace.
        - Ninguna está a menos de `min_distance` normalizado de otra.
        - Partículas tienen velocidad inicial 0.
        - Partículas tienen vida 1.0.
        - Coordenadas en píxeles.
    """
    if count < 0:
        raise ValueError(f"count debe ser >= 0, recibido: {count}")
    if screen_width <= 0:
        raise ValueError(f"screen_width debe ser > 0, recibido: {screen_width}")
    if screen_height <= 0:
        raise ValueError(f"screen_height debe ser > 0, recibido: {screen_height}")
    if min_distance < 0:
        raise ValueError(f"min_distance debe ser >= 0, recibido: {min_distance}")

    if count == 0:
        return []

    particles: list[Particle] = []

    for _ in range(count):
        placed = False
        for _attempt in range(max_attempts_per_particle):
            nx, ny = workspace.random_point(rng)

            too_close = False
            for existing in particles:
                ex_norm = existing.x / screen_width
                ey_norm = existing.y / screen_height

                dx = nx - ex_norm
                dy = ny - ey_norm
                distance = math.hypot(dx, dy)

                if distance < min_distance:
                    too_close = True
                    break

            if too_close:
                continue

            particle = Particle(
                x=nx * screen_width,
                y=ny * screen_height,
                vx=0.0,
                vy=0.0,
                size=particle_size,
                life=1.0,
                color=particle_color,
            )
            particles.append(particle)
            placed = True
            break

        if not placed:
            break

    return particles
