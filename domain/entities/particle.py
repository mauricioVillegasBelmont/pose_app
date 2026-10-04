import math
import random
from dataclasses import dataclass


@dataclass
class Particle:
    """Partícula para el sistema de partículas."""

    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    size: float = 5.0
    life: float = 1.0  # 1 = máximo, 0 = muerta
    color: tuple[int, int, int] = (255, 255, 255)

    def update(self, gravity: float = 0.1, damping: float = 0.99):
        """Actualiza física básica (dominio puro)."""
        self.vy += gravity
        self.vx *= damping
        self.vy *= damping
        self.x += self.vx
        self.y += self.vy
        self.life *= 0.995  # Decaimiento gradual

    def is_alive(self) -> bool:
        return self.life > 0.01

    @classmethod
    def create_burst(
        cls, center_x: float, center_y: float, count: int = 20
    ) -> list["Particle"]:
        """Genera una ráfaga de partículas desde un punto (dominio puro)."""
        particles = []
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 5)
            particle = cls(
                x=center_x + random.uniform(-10, 10),
                y=center_y + random.uniform(-10, 10),
                vx=speed * math.cos(angle),  # sets the particle angle direction X
                vy=speed * math.sin(angle),  # sets the particle angle direction Y
                size=random.uniform(3, 8),
                color=(
                    random.randint(100, 255),
                    random.randint(100, 255),
                    random.randint(100, 255),
                ),
            )
            particles.append(particle)
        return particles
