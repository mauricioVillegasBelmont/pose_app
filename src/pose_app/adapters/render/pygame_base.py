"""
Base común para adaptadores de render con Pygame.

NO es un puerto, es un detalle de implementación. Vive en `adapters/`
porque solo aplica a adaptadores Pygame (no a WebSocket, Null, etc.).

Responsabilidades (post-refactor):
- Marcar el renderer como "listo" (idempotente).
- Mantener el FPS objetivo.
- Exponer la surface inyectada por el bootstrap.

NO es responsable de:
- Crear la ventana (`pygame.display.set_mode`).
- Cambiar el caption (`pygame.display.set_caption`).
- Cerrar pygame (`pygame.quit`).

Esos son responsabilidad del composition root del plugin (bootstrap) y del
`PygameSceneManager` (shutdown). Esto garantiza UNA sola ventana por proceso,
independientemente de cuántas capacidades se registren.
"""

from typing import Self

import pygame

from pose_app.infrastructure.logging.logger import get_logger

logger = get_logger("adapters.render.pygame_base")


class PygameBaseAdapter:
    """
    Clase base para adaptadores de Pygame.

    La surface es inyectada por el bootstrap del plugin (una sola ventana
    compartida por todas las capacidades). El adapter no crea ventana ni
    cierra pygame.

    NOTA: No hereda de ningún puerto. Los adaptadores concretos
    (PygameColorRenderer, PygameParticlesRenderer) heredan de esta
    Y del puerto correspondiente.
    """

    def __init__(
        self,
        surface: pygame.Surface,
        target_fps: int = 60,
        title: str = "",
    ) -> None:
        """
        Inicializa el adapter sobre una surface ya existente.

        Args:
            surface: Superficie de Pygame donde dibujar. Inyectada por el
                bootstrap del plugin. NO se crea aquí.
            target_fps: FPS objetivo para el Clock interno.
            title: Nombre legible para logs (NO se aplica a la ventana).
        """
        self._surface = surface
        self._target_fps = target_fps
        self._title = title
        self._running = False

    # ==========================================
    # Ciclo de vida
    # ==========================================

    def _initialize(self) -> None:
        """
        Marca el adapter como listo. Idempotente.

        Asegura que pygame está inicializado (pygame.init es idempotente).
        NO crea ventana. La surface ya fue inyectada por el bootstrap.
        """
        if self._running:
            return

        pygame.init()
        self._running = True

        logger.debug(
            f"Renderer listo | surface={self.width}x{self.height} "
            f"@ {self._target_fps} FPS | {self._title}"
        )

    def close(self) -> None:
        """
        Marca el adapter como cerrado. Idempotente.

        NO llama pygame.quit(): el shutdown de pygame lo gestiona el
        SceneManager (único dueño del ciclo de vida de pygame).
        """
        self._running = False

    # ==========================================
    # API para subclases
    # ==========================================

    @property
    def surface(self) -> pygame.Surface:
        """Surface de dibujo compartida (inyectada por el bootstrap)."""
        return self._surface

    @property
    def screen(self) -> pygame.Surface:
        """Alias de ``surface`` (retrocompatibilidad con código existente)."""
        return self._surface

    @property
    def width(self) -> int:
        return self._surface.get_width()

    @property
    def height(self) -> int:
        return self._surface.get_height()

    @property
    def is_running(self) -> bool:
        return self._running

    # ==========================================
    # Manejo de eventos
    # ==========================================

    def _handle_events(self) -> None:
        """
        Procesa eventos de Pygame comunes.

        Subclases pueden sobrescribir para añadir eventos específicos,
        pero deben llamar a `super()._handle_events()`.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
            elif event.type == pygame.VIDEORESIZE:
                self._on_resize(event.size)

    def _on_resize(self, new_size: tuple[int, int]) -> None:
        """
        Hook de redimensionado. Subclases pueden sobrescribir para
        recrear buffers internos.

        La ventana compartida (``self._surface``) es gestionada por pygame:
        no hay que llamar a ``set_mode`` aquí.
        """
        logger.debug(f"Ventana redimensionada: {new_size}")

    # ==========================================
    # Context manager
    # ==========================================

    def __enter__(self) -> Self:
        self._initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
