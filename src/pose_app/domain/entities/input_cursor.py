"""
Cursor de interacción del usuario.

Representa un punto de interacción (mano, pie, cadera, etc.) con configuración
visual y de colisión. No es una entidad ECS porque no participa en sistemas
de física/animación, pero tiene componentes visuales similares a Particle.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pose_app.domain.entities.particles.components import SpriteConfig, SpriteState


@dataclass(frozen=True)
class CursorAppearance:
    """
    Configuración visual del cursor (similar a Appearance de Particle).

    Attributes:
        size: Tamaño visual en píxeles. Debe ser > 0.
        color: Color RGB (tupla de 3 enteros en rango 0-255).
        padding_x: Margen visual horizontal (no afecta colisión).
        padding_y: Margen visual vertical (no afecta colisión).
    """

    size: float = 40.0
    color: tuple[int, int, int] = (255, 255, 0)
    padding_x: float = 0.0
    padding_y: float = 0.0

    def __post_init__(self) -> None:
        """Valida que los valores sean correctos."""
        if self.size <= 0:
            raise ValueError(f"CursorAppearance size must be positive, got {self.size}")
        if not (
            0 <= self.color[0] <= 255
            and 0 <= self.color[1] <= 255
            and 0 <= self.color[2] <= 255
        ):
            raise ValueError(
                f"CursorAppearance color must be RGB (0-255), got {self.color}"
            )


@dataclass(frozen=True)
class CursorCollision:
    """
    Configuración de colisión del cursor.

    Attributes:
        radius: Radio de colisión en porcentaje del mínimo de pantalla (0-100).
                Se multiplica por min(screen_w, screen_h) / 100 para obtener píxeles.
    """

    radius: float = 20.0

    def __post_init__(self) -> None:
        """Valida que el radio sea positivo."""
        if self.radius <= 0:
            raise ValueError(
                f"CursorCollision radius must be positive, got {self.radius}"
            )


@dataclass
class InputCursor:
    """
    Cursor de interacción del usuario.

    Representa un punto de interacción (mano, pie, cadera, etc.) con:
    - Estado de posición (última posición conocida, visibilidad)
    - Configuración visual (appearance, sprite opcional)
    - Configuración de colisión (radio)

    No es una entidad ECS porque no participa en sistemas de física/animación,
    pero tiene componentes visuales similares a Particle para consistencia.

    Attributes:
        cursor_id: Identificador único (ej: "left_hand", "right_hand", "feet").
        position: Posición (x, y) normalizada 0-1. Mutable, se actualiza cada frame.
        is_visible: Estado de visibilidad. Mutable.
        last_seen: Timestamp de última detección (segundos). Mutable.
        appearance: Configuración visual (frozen).
        collision: Configuración de colisión (frozen).
        sprite_config: Configuración de sprite animado (opcional, frozen).
        sprite_state: Estado del sprite (mutable, se actualiza en animación).
    """

    cursor_id: str

    # Estado de posición (mutable)
    position: tuple[float, float] | None = None
    is_visible: bool = False
    last_seen: float = 0.0

    # Configuración visual (frozen)
    appearance: CursorAppearance = field(default_factory=CursorAppearance)
    collision: CursorCollision = field(default_factory=CursorCollision)

    # Sprite opcional (similar a Particle)
    sprite_config: SpriteConfig | None = None
    sprite_state: SpriteState | None = None

    def update(
        self,
        new_position: tuple[float, float] | None,
        current_time: float,
        timeout: float,
    ) -> None:
        """
        Actualiza la posición y gestiona el timeout de visibilidad.

        Args:
            new_position: Nueva posición (x, y) normalizada, o None si no se detecta.
            current_time: Timestamp actual (segundos).
            timeout: Segundos antes de considerar el cursor como perdido.
        """
        if new_position is not None:
            # Cursor detectado: actualizar posición y timestamp
            self.position = new_position
            self.is_visible = True
            self.last_seen = current_time
        elif current_time - self.last_seen > timeout:
            # Cursor perdido por timeout: marcar como invisible
            self.is_visible = False
            self.position = None
        # Si no ha pasado el timeout, mantener la última posición (persistencia)

    def get_position_pixels(
        self, screen_w: int, screen_h: int
    ) -> tuple[float, float] | None:
        """
        Convierte la posición normalizada a píxeles.

        Args:
            screen_w: Ancho de pantalla en píxeles.
            screen_h: Alto de pantalla en píxeles.

        Returns:
            (x, y) en píxeles, o None si no hay posición.
        """
        if self.position is None:
            return None
        return (self.position[0] * screen_w, self.position[1] * screen_h)

    def get_collision_radius_pixels(self, screen_w: int, screen_h: int) -> float:
        """
        Obtiene el radio de colisión en píxeles.

        Usa el mínimo de screen_w/screen_h para mantener consistencia.

        Args:
            screen_w: Ancho de pantalla en píxeles.
            screen_h: Alto de pantalla en píxeles.

        Returns:
            Radio de colisión en píxeles.
        """
        return self.collision.radius * min(screen_w, screen_h) / 100.0
