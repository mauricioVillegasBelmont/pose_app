import pygame

from domain.entities.color import RGBColor
from domain.entities.particle import Particle
from domain.entities.pose_landmark import PoseLandmark
from domain.ports.render_port import RenderPort


class PygameRenderAdapter(RenderPort):
    """
    Adaptador de renderizado usando Pygame.

    Características:
    - Ventana redimensionable
    - Modo partículas: renderiza círculos con alpha blending
    - Modo color: fondo sólido + esqueleto superpuesto
    - FPS limitado a 60
    """

    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        title: str = "Pose + Particles",
        background_color: RGBColor = RGBColor(20, 20, 30)
    ):
        """
        Args:
            width: Ancho de la ventana
            height: Alto de la ventana
            title: Título de la ventana
            background_color: Color de fondo predeterminado
        """
        self._width = width
        self._height = height
        self._title = title
        self._background_color = background_color

        self._screen: pygame.Surface | None = None
        self._clock: pygame.time.Clock | None = None
        self._running: bool = False

        # Buffer de partículas para optimizar renderizado
        self._particle_surface: pygame.Surface | None = None

        print(f"🎨 Pygame inicializado: {width}x{height}")

    def _initialize(self) -> None:
        """Inicializa Pygame si no está ya inicializado."""
        if self._screen is not None:
            return

        pygame.init()
        self._screen = pygame.display.set_mode(
            (self._width, self._height),
            pygame.RESIZABLE  # Permite redimensionar
        )
        pygame.display.set_caption(self._title)
        self._clock = pygame.time.Clock()
        self._running = True

        # Fondo inicial
        self._screen.fill(self._background_color.to_rgb_tuple())
        pygame.display.flip()

    def render_particles(self, particles: list[Particle]) -> None:
        """
        Renderiza un sistema de partículas en la ventana.

        Args:
            particles: Lista de partículas a renderizar
        """
        self._initialize()

        if not self._running:
            return

        # Limpia la pantalla con color de fondo
        self._screen.fill(self._background_color.to_rgb_tuple())

        # Opcional: dibuja landmarks (los pasamos como None por ahora)
        self._draw_particles(particles)

        # Actualiza la pantalla
        pygame.display.flip()
        self._clock.tick(60)  # Limita a 60 FPS

        # Maneja eventos de Pygame
        self._handle_events()

    def render_background(
        self,
        color: RGBColor,
        landmarks: list[PoseLandmark]
    ) -> None:
        """
        Renderiza un fondo de color sólido + esqueleto.

        Args:
            color: Color del fondo
            landmarks: Landmarks para dibujar el esqueleto
        """
        self._initialize()

        if not self._running:
            return

        # Fondo con el color calculado
        self._screen.fill(color.to_rgb_tuple())

        # Dibuja el esqueleto si hay landmarks
        if landmarks:
            self._draw_skeleton(landmarks)

        # Actualiza pantalla
        pygame.display.flip()
        self._clock.tick(60)

        # Maneja eventos
        self._handle_events()

    def show(self) -> None:
        """
        Muestra la ventana y mantiene el loop abierto.
        Bloquea hasta que se cierre la ventana.
        """
        self._initialize()

        while self._running:
            self._handle_events()
            self._clock.tick(30)  # Bajo consumo cuando está inactiva

    def close(self) -> None:
        """Cierra la ventana y libera recursos."""
        self._running = False
        if self._screen is not None:
            pygame.quit()
            self._screen = None
            print("🎨 Pygame cerrado")

    def _handle_events(self) -> None:
        """Maneja eventos de Pygame (cierre, redimension, teclas)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
                self.close()
            elif event.type == pygame.VIDEORESIZE:
                # Actualiza dimensiones al redimensionar
                self._width, self._height = event.size
                if self._screen:
                    self._screen = pygame.display.set_mode(
                        event.size, pygame.RESIZABLE
                    )

    def _draw_particles(self, particles: list[Particle]) -> None:
        """
        Dibuja partículas como círculos con alpha blending.

        Args:
            particles: Lista de partículas
        """
        if not particles:
            return

        # Crear una superficie para alpha blending
        if self._particle_surface is None:
            self._particle_surface = pygame.Surface(
                (self._width, self._height),
                pygame.SRCALPHA  # Soporta transparencia
            )
        else:
            # Limpia la superficie de partículas
            self._particle_surface.fill((0, 0, 0, 0))

        # Dibuja cada partícula con transparencia
        for particle in particles:
            # Convierte coordenadas normalizadas a píxeles
            x = int(particle.x)
            y = int(particle.y)

            # Tamaño según vida (partículas más viejas son más pequeñas)
            size = int(particle.size * particle.life)
            if size < 1:
                continue

            # Color con transparencia (alpha = vida)
            alpha = int(200 * particle.life)
            color = (
                min(255, particle.color[0]),
                min(255, particle.color[1]),
                min(255, particle.color[2]),
                alpha
            )

            # Dibuja círculo con anti-aliasing
            pygame.draw.circle(
                self._particle_surface,
                color,
                (x, y),
                size
            )

        # Mezcla la superficie de partículas con la pantalla
        self._screen.blit(self._particle_surface, (0, 0))

    def _draw_skeleton(self, landmarks: list[PoseLandmark]) -> None:
        """
        Dibuja el esqueleto conectando landmarks.

        Args:
            landmarks: Lista de landmarks visibles
        """
        if not landmarks:
            return

        # Convierte a diccionario para acceso rápido por nombre
        lm_dict = {lm.name: lm for lm in landmarks if lm.name}

        # Conexiones del esqueleto (pares de landmarks)
        connections = [
            # Brazos
            ('left_shoulder', 'left_elbow'),
            ('left_elbow', 'left_wrist'),
            ('right_shoulder', 'right_elbow'),
            ('right_elbow', 'right_wrist'),
            # Hombros
            ('left_shoulder', 'right_shoulder'),
            # Piernas
            ('left_hip', 'left_knee'),
            ('left_knee', 'left_ankle'),
            ('right_hip', 'right_knee'),
            ('right_knee', 'right_ankle'),
            # Cadera
            ('left_hip', 'right_hip'),
            # Torso
            ('left_shoulder', 'left_hip'),
            ('right_shoulder', 'right_hip'),
            # Cabeza
            ('left_shoulder', 'nose'),
            ('right_shoulder', 'nose'),
        ]

        # Dibuja conexiones (líneas blancas)
        for name1, name2 in connections:
            if name1 in lm_dict and name2 in lm_dict:
                lm1 = lm_dict[name1]
                lm2 = lm_dict[name2]

                if lm1.is_visible() and lm2.is_visible():
                    x1 = int(lm1.x * self._width)
                    y1 = int(lm1.y * self._height)
                    x2 = int(lm2.x * self._width)
                    y2 = int(lm2.y * self._height)

                    pygame.draw.line(
                        self._screen,
                        (255, 255, 255),  # Blanco
                        (x1, y1),
                        (x2, y2),
                        2
                    )

        # Dibuja puntos (círculos verdes)
        for lm in landmarks:
            if lm.is_visible():
                x = int(lm.x * self._width)
                y = int(lm.y * self._height)
                pygame.draw.circle(
                    self._screen,
                    (0, 255, 0),  # Verde
                    (x, y),
                    5
                )


# Extensión para RGBColor: método para convertir a tupla RGB
def rgb_to_tuple(self) -> tuple[int, int, int]:
    """Convierte RGBColor a tupla para Pygame."""
    return (self.r, self.g, self.b)

# Monkey-patch (o lo añades como método en la clase RGBColor)
RGBColor.to_rgb_tuple = rgb_to_tuple