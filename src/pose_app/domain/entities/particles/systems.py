"""
Sistemas ECS-lite para partículas.

Cada sistema tiene una única responsabilidad y no conoce al juego,
al render, a la cámara ni a la pose. Opera exclusivamente sobre
componentes de entidades.

Política de mutación:
    Position  -> mutado in-place (camino caliente, por rendimiento).
    Lifespan  -> reemplazado con dataclasses.replace (contrato frozen).
"""

from collections.abc import Sequence
from dataclasses import dataclass, replace

from pose_app.domain.entities.particle import Particle


@dataclass(frozen=True)
class MovementSystem:
    """
    Integra la posición de las entidades aplicando gravedad y amortiguación.

    Es inmutable en su CONFIGURACIÓN; el ESTADO vive en las entidades.
    No mantiene listas ni memoria entre llamadas.

    Usage:
        MovementSystem(gravity=0.1, damping=0.99).update(particles)
    """

    gravity: float = 0.1
    damping: float = 0.99

    def update(self, particles: Sequence[Particle]) -> None:
        """
        Avanza un tick la física de cada partícula, mutando Position.

        Args:
            particles: Entidades elegibles. Se mutan in-place.

        Note:
            El orden de operaciones replica el Particle.update() legacy:
            gravedad primero, amortiguación segundo, integración al final.
            La gravedad de este tick afecta la posición de este tick.
        """
        for particle in particles:
            position = particle.position

            position.vy += self.gravity
            position.vx *= self.damping
            position.vy *= self.damping

            position.x += position.vx
            position.y += position.vy


@dataclass(frozen=True)
class LifespanSystem:
    """
    Decae el componente Lifespan y retira entidades agotadas.

    Las entidades SIN componente Lifespan se consideran infinitas
    y son ignoradas por update() y conservadas por cull().

    Usage:
        lifespan = LifespanSystem(decay=0.995)
        lifespan.update(particles)
        particles = lifespan.cull(particles)
    """

    decay: float = 0.995

    def update(self, particles: Sequence[Particle]) -> None:
        """
        Reduce current_life de forma multiplicativa.

        Args:
            particles: Entidades a procesar. Las que no tienen Lifespan
                se omiten (selección por componente).

        Note:
            Se usa replace() porque Lifespan es frozen. El componente
            anterior no se modifica: se asigna una nueva instancia
            a particle.lifespan.
        """
        for particle in particles:
            if particle.lifespan is None:
                continue

            remaining = particle.lifespan.current_life * self.decay
            particle.lifespan = replace(
                particle.lifespan,
                current_life=remaining,
            )

    def cull(self, particles: Sequence[Particle]) -> list[Particle]:
        """
        Devuelve una NUEVA lista con las entidades vivas.

        Args:
            particles: Población a filtrar. No se muta.

        Returns:
            Lista de entidades que satisfacen Particle.is_alive().

        Note:
            No borra de la lista de entrada: evita mutar una colección
            mientras se itera y permite a un juego conservar las
            entidades muertas para efectos (fade-out, explosiones).
        """
        return [particle for particle in particles if particle.is_alive()]


@dataclass(frozen=True)
class AnimationSystem:
    """
    Actualiza el estado de los sprites animados.

    Solo procesa partículas que tienen sprite_config y sprite_state.
    """

    def update(self, particles: Sequence[Particle], dt: float) -> None:
        for particle in particles:
            if particle.sprite_config is None or particle.sprite_state is None:
                continue

            config = particle.sprite_config
            state = particle.sprite_state

            # Si es estático, no hacer nada
            if config.fps <= 0.0:
                continue

            frame_duration = 1.0 / config.fps
            state.elapsed_time += dt

            if state.elapsed_time >= frame_duration:
                # Calcular cuántos frames avanzar (por si dt es muy grande)
                frames_to_advance = int(state.elapsed_time / frame_duration)
                state.elapsed_time -= frames_to_advance * frame_duration

                if config.animation_mode == "loop":
                    state.current_frame = (
                        state.current_frame + frames_to_advance
                    ) % config.frame_count
                elif config.animation_mode == "one_shot":
                    state.current_frame = min(
                        state.current_frame + frames_to_advance, config.frame_count - 1
                    )
