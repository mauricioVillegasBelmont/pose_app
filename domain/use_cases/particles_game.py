from domain.entities.particle import Particle
from domain.entities.pose_landmark import PoseLandmark
from domain.ports.camera_port import CameraPort
from domain.ports.pose_estimator_port import PoseEstimatorPort
from domain.ports.render_port import RenderPort


class ParticlesGame:
    """Caso de uso: juego de partículas que reaccionan a la pose."""

    def __init__(
        self,
        camera: CameraPort,
        pose_estimator: PoseEstimatorPort,
        renderer: RenderPort,
        gravity: float = 0.1,
        burst_radius: float = 50.0
    ):
        self._camera = camera
        self._pose_estimator = pose_estimator
        self._renderer = renderer
        self._gravity = gravity
        self._burst_radius = burst_radius
        self._particles: list[Particle] = []
        self._last_landmarks: list[PoseLandmark] = []

    def run(self) -> None:
        """Bucle principal del juego."""
        self._camera.start()

        try:
            while True:
                frame = self._camera.get_frame()
                if frame is None:
                    continue

                # 1. Estimar pose
                landmarks = self._pose_estimator.estimate(frame)
                self._last_landmarks = landmarks

                # 2. Generar partículas desde puntos clave
                self._spawn_particles_from_landmarks(landmarks)

                # 3. Actualizar física de partículas
                self._update_particles()

                # 4. Renderizar
                self._renderer.render_particles(self._particles)

        except KeyboardInterrupt:
            self._camera.stop()
            self._renderer.close()

    def _spawn_particles_from_landmarks(self, landmarks: list[PoseLandmark]) -> None:
        """Genera partículas desde los puntos clave visibles."""
        for landmark in landmarks:
            if landmark.is_visible():
                # Convierte coordenadas normalizadas a píxeles aproximados
                px = landmark.x * 640  # Asume resolución de render
                py = landmark.y * 480

                # Genera ráfaga de partículas
                new_particles = Particle.create_burst(
                    px, py,
                    count=5  # Pocas partículas para no saturar
                )
                self._particles.extend(new_particles)

        # Limita el número de partículas (evita memory leak)
        if len(self._particles) > 2000:
            self._particles = self._particles[-1500:]

    def _update_particles(self) -> None:
        """Actualiza todas las partículas y elimina las muertas."""
        for particle in self._particles:
            particle.update(gravity=self._gravity)

        # Filtra partículas vivas
        self._particles = [p for p in self._particles if p.is_alive()]

    def reset(self) -> None:
        """Reinicia el sistema de partículas."""
        self._particles.clear()