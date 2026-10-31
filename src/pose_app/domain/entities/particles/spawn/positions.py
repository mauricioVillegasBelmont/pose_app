"""
Estrategias de posicionamiento para el spawn de partículas.

Incluye una estrategia aleatoria con separación mínima y una estrategia
determinista basada en una grilla. Ambas implementan el protocolo
``PositionStrategy``.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from pose_app.domain.entities.particle import Particle
from pose_app.domain.games.particles.geometry import Workspace


@dataclass(frozen=True)
class RandomPositionStrategy:
    """Genera posiciones aleatorias evitando solapamientos.

    Cada intento elige un punto uniforme dentro del workspace y lo acepta
    solo si respeta la distancia mínima respecto a las partículas existentes.

    Attributes:
        min_distance: Distancia mínima normalizada (0-1) entre partículas.
        max_attempts: Número máximo de intentos antes de rendirse.
    """

    min_distance: float = 0.15
    max_attempts: int = 100

    def calculate_position(
        self,
        index: int,
        existing_particles: list[Particle],
        workspace: Workspace,
        screen_w: int,
        screen_h: int,
        rng: random.Random,
    ) -> tuple[float, float]:
        """Calcula una posición aleatoria válida en píxeles.

        Args:
            index: Índice de la partícula dentro del lote de spawn.
            existing_particles: Partículas ya creadas; se evita acercarse a ellas.
            workspace: Región normalizada donde pueden aparecer partículas.
            screen_w: Ancho de pantalla en píxeles.
            screen_h: Alto de pantalla en píxeles.
            rng: Generador aleatorio inyectable para tests deterministas.

        Returns:
            Coordenadas ``(x, y)`` en píxeles.

        Raises:
            ValueError: Si no se encuentra una posición válida tras
                ``max_attempts`` intentos.
        """
        x_min = workspace.x_min * screen_w
        x_max = workspace.x_max * screen_w
        y_min = workspace.y_min * screen_h
        y_max = workspace.y_max * screen_h
        min_distance_px = self.min_distance * min(screen_w, screen_h)

        for _ in range(self.max_attempts):
            x = rng.uniform(x_min, x_max)
            y = rng.uniform(y_min, y_max)
            if self._is_valid_position(
                x,
                y,
                existing_particles,
                min_distance_px,
            ):
                return (x, y)

        raise ValueError(
            f"Could not find valid position after {self.max_attempts} attempts"
        )

    def _is_valid_position(
        self,
        x: float,
        y: float,
        existing_particles: list[Particle],
        min_distance_px: float,
    ) -> bool:
        """Comprueba si un punto respeta la separación mínima."""
        min_distance_sq = min_distance_px * min_distance_px
        for particle in existing_particles:
            dx = x - particle.position.x
            dy = y - particle.position.y
            if dx * dx + dy * dy < min_distance_sq:
                return False
        return True


@dataclass(frozen=True)
class GridPositionStrategy:
    """Coloca partículas en el centro de las celdas de una grilla.

    La grilla se distribuye uniformemente sobre el workspace. La selección
    es determinista e ignora el generador aleatorio.

    Attributes:
        rows: Número de filas de la grilla.
        cols: Número de columnas de la grilla.
    """

    rows: int
    cols: int

    def calculate_position(
        self,
        index: int,
        existing_particles: list[Particle],
        workspace: Workspace,
        screen_w: int,
        screen_h: int,
        rng: random.Random,
    ) -> tuple[float, float]:
        """Calcula el centro de la celda correspondiente a ``index``.

        Args:
            index: Índice de la partícula dentro de la grilla.
            existing_particles: Ignorado; la grilla es determinista.
            workspace: Región normalizada donde pueden aparecer partículas.
            screen_w: Ancho de pantalla en píxeles.
            screen_h: Alto de pantalla en píxeles.
            rng: Ignorado; la posición es determinista.

        Returns:
            Coordenadas ``(x, y)`` en píxeles.

        Raises:
            ValueError: Si ``index`` excede la capacidad de la grilla.
        """
        if index >= self.rows * self.cols:
            raise ValueError(f"index {index} exceeds grid capacity")

        row = index // self.cols
        col = index % self.cols

        x_min = workspace.x_min * screen_w
        x_max = workspace.x_max * screen_w
        y_min = workspace.y_min * screen_h
        y_max = workspace.y_max * screen_h

        cell_width = (x_max - x_min) / self.cols
        cell_height = (y_max - y_min) / self.rows

        x = x_min + (col + 0.5) * cell_width
        y = y_min + (row + 0.5) * cell_height
        return (x, y)
