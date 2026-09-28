from collections.abc import Callable

from domain.entities.color import RGBColor
from domain.entities.pose_landmark import PoseLandmark
from domain.ports.camera_port import CameraPort
from domain.ports.pose_estimator_port import PoseEstimatorPort
from domain.ports.render_port import ColorRenderPort
from domain.ports.state_port import StatePort
from infrastructure.logging.logger import get_logger

logger = get_logger("use_cases.color_game")


class ColorGame:
    """Caso de uso: juego que cambia color de fondo según la pose."""

    # Paletas de colores predefinidas (reglas de negocio)
    PALETTES = {
        'fire': [RGBColor(255, 0, 0), RGBColor(255, 165, 0), RGBColor(255, 255, 0)],
        'ocean': [RGBColor(0, 0, 255), RGBColor(0, 128, 255), RGBColor(0, 255, 255)],
        'forest': [RGBColor(0, 100, 0), RGBColor(34, 139, 34), RGBColor(0, 255, 127)],
        'neon': [RGBColor(255, 0, 255), RGBColor(0, 255, 255), RGBColor(255, 255, 0)]
    }

    def __init__(
        self,
        camera: CameraPort,
        pose_estimator: PoseEstimatorPort,
        renderer: ColorRenderPort,
        state: StatePort | None = None,
        palette_name: str = 'fire'
    ):
        self._camera = camera
        self._pose_estimator = pose_estimator
        self._renderer = renderer
        self._state = state
        self._palette_name = palette_name
        self._palette = self.PALETTES.get(palette_name, self.PALETTES['fire'])
        self._current_color: RGBColor = self._palette[0]
        self._last_landmarks: list[PoseLandmark] = []

    def run(self, should_stop: Callable[[], bool] | None = None) -> None:
        """
        Bucle principal del juego.
        Args:
            should_stop: Callback que indica si se debe detener el loop.
                        Si es None, corre hasta KeyboardInterrupt.
        """
        should_stop = should_stop or (lambda: False)

        self._camera.start()
        logger.info("Juego de colores iniciado")

        try:
            while not should_stop():
                # 1. Procesa comandos pendientes
                self._process_commands()

                # 2. Frame
                frame = self._camera.get_frame()
                if frame is None:
                    continue

                # 3. Estimar pose
                landmarks = self._pose_estimator.estimate(frame)
                self._last_landmarks = landmarks

                # 4. Actualiza estado compartido
                if self._state:
                    self._state.update_game_data("background_color", color)  # noqa: F821
                    self._state.update_game_data("current_palette", self._current_palette_name)

                # 5. Calcular color basado en pose
                color = self._calculate_color_from_pose(landmarks)
                self._current_color = color

                # 6. Renderizar fondo con el color calculado
                self._renderer.render_background(color, landmarks)

        except KeyboardInterrupt:
            self._camera.stop()
            self._renderer.close()

        finally:
            try:
                self._renderer.close()
            except Exception as e:
                logger.error(f"Error cerrando renderer: {e}")
            logger.info(
                f"Juego color terminado. Frames: {self._frame_count}"
            )

    def _process_commands(self) -> None:
        """Consume comandos pendientes del estado compartido."""
        if self._state is None:
            return

        commands = self._state.drain_commands()
        for cmd in commands:
            if cmd.action == "change_palette":
                palette_name = cmd.payload.get("palette")
                if palette_name in self.PALETTES:
                    self._palette = self.PALETTES[palette_name]
                    self._palette_name = palette_name
                    logger.info(f"Paleta cambiada a: {palette_name}")
                else:
                    logger.warning(f"Paleta desconocida: {palette_name}")
            elif cmd.action == "reset_particles":
                logger.debug(f"Comando ignorado por ColorGame: {cmd.action}")
            else:
                logger.warning(f"Comando desconocido: {cmd.action}")

    def _calculate_color_from_pose(self, landmarks: list[PoseLandmark]) -> RGBColor:
        """
        Regla de negocio: calcula color según posición de manos y cabeza.
        - Mano izquierda arriba → rojo
        - Mano derecha arriba → azul
        - Cabeza centrada → verde
        """
        if not landmarks:
            return self._palette[0]

        # Busca landmarks específicos (nombres según Mediapipe)
        left_wrist = self._find_landmark(landmarks, 'left_wrist')
        right_wrist = self._find_landmark(landmarks, 'right_wrist')
        nose = self._find_landmark(landmarks, 'nose')

        # Calcula factores de mezcla (0-1)
        red_factor = 0.0
        blue_factor = 0.0
        green_factor = 0.0

        if left_wrist and left_wrist.is_visible():
            # Si la mano izquierda está arriba (y < 0.4), más rojo
            red_factor = max(0, 1 - left_wrist.y * 2.5)  # 0.4 → 0, 0.0 → 1

        if right_wrist and right_wrist.is_visible():
            blue_factor = max(0, 1 - right_wrist.y * 2.5)

        if nose and nose.is_visible():
            # Si la cabeza está centrada (x ~0.5), más verde
            green_factor = 1 - abs(nose.x - 0.5) * 3  # 0.5 → 1, 0.0 → 0

        # Mezcla colores de la paleta según factores
        color = self._mix_palette(red_factor, green_factor, blue_factor)
        return color

    def _find_landmark(self, landmarks: list[PoseLandmark], name: str) -> PoseLandmark | None:
        """Busca un landmark por nombre."""
        for lm in landmarks:
            if lm.name and lm.name.lower() == name.lower():
                return lm
        return None

    def _mix_palette(self, r: float, g: float, b: float) -> RGBColor:
        """Mezcla colores de la paleta según factores RGB."""
        # Normaliza factores
        total = r + g + b
        if total == 0:
            return self._palette[0]

        r /= total
        g /= total
        b /= total

        # Interpola entre los colores de la paleta según el factor dominante
        if r >= g and r >= b:
            return RGBColor.interpolate(self._palette[0], self._palette[1], r)
        elif g >= b:
            return RGBColor.interpolate(self._palette[1], self._palette[2], g)
        else:
            return RGBColor.interpolate(self._palette[2], self._palette[0], b)