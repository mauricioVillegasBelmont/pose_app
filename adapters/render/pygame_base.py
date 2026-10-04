"""
Base común para adaptadores de render con Pygame.

NO es un puerto, es un detalle de implementación. Vive en `adapters/`
porque solo aplica a adaptadores Pygame (no a WebSocket, Null, etc.).

Responsabilidades:
- Inicializar Pygame (ventana, reloj).
- Manejar eventos comunes (cerrar ventana, redimensionar).
- Proveer acceso thread-safe a la superficie de dibujo.
- Cerrar limpiamente.
"""

import pygame

from infrastructure.logging.logger import get_logger

logger = get_logger("adapters.render.pygame_base")


class PygameBaseAdapter:
    """
    Clase base para adaptadores de Pygame.

    NOTA: No hereda de ningún puerto. Los adaptadores concretos
    (PygameParticlesAdapter, PygameColorAdapter) heredan de esta
    Y del puerto correspondiente.
    """

    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        title: str = "Pose AR",
        target_fps: int = 60,
    ):
        self._width = width
        self._height = height
        self._title = title
        self._target_fps = target_fps

        self._screen: pygame.Surface | None = None
        self._clock: pygame.time.Clock | None = None
        self._running: bool = False

    # ==========================================
    # Ciclo de vida
    # ==========================================

    def _initialize(self) -> None:
        """
        Inicializa Pygame si no está inicializado.

        Es idempotente: llamarlo varias veces no hace nada extra.
        """
        if self._screen is not None:
            return

        pygame.init()
        self._screen = pygame.display.set_mode(
            (self._width, self._height),
            pygame.RESIZABLE,
        )
        pygame.display.set_caption(self._title)
        self._clock = pygame.time.Clock()
        self._running = True

        logger.info(
            f"Pygame iniciado: {self._width}x{self._height} "
            f"@ {self._target_fps} FPS | {self._title}"
        )

    def show(self) -> None:
        """
        Mantiene la ventana activa hasta que se cierre.

        Útil cuando el juego NO está corriendo en un loop propio,
        pero quieres que la ventana siga visible.
        """
        self._initialize()

        while self._running:
            self._handle_events()
            if self._clock is not None:
                self._clock.tick(self._target_fps)

    def close(self) -> None:
        """
        Cierra la ventana y libera recursos de Pygame.

        Idempotente: llamarlo varias veces no falla.
        """
        self._running = False

        if self._screen is not None:
            pygame.quit()
            self._screen = None
            self._clock = None
            logger.info(f"Pygame cerrado: {self._title}")

    # ==========================================
    # API para subclases
    # ==========================================

    @property
    def screen(self) -> pygame.Surface:
        """
        Superficie principal de dibujo.

        Raises:
            RuntimeError: si se llama antes de `_initialize()`.
        """
        if self._screen is None:
            raise RuntimeError("Pygame no inicializado. Llama a _initialize() primero.")
        return self._screen

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def is_running(self) -> bool:
        return self._running

    def flush(self) -> None:
        """
        Actualiza la pantalla y aplica el límite de FPS.

        Debe llamarse al final de cada render.
        """
        pygame.display.flip()
        if self._clock is not None:
            self._clock.tick(self._target_fps)

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
        Maneja el redimensionado de la ventana.

        Subclases pueden sobrescribir si necesitan recrear buffers.
        """
        self._width, self._height = new_size
        if self._screen is not None:
            self._screen = pygame.display.set_mode(new_size, pygame.RESIZABLE)
        logger.debug(f"Ventana redimensionada: {new_size}")

    # ==========================================
    # Context manager
    # ==========================================

    def __enter__(self):
        self._initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
