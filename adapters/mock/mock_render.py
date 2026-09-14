"""Mock temporal"""
from domain.entities.color import RGBColor
from domain.entities.particle import Particle
from domain.entities.pose_landmark import PoseLandmark
from domain.ports.render_port import RenderPort


class MockRenderAdapter(RenderPort):
    """Mock que solo imprime en consola (para pruebas sin GUI)."""

    def render_particles(self, particles: list[Particle]) -> None:
        print(f"Renderizando {len(particles)} partículas")
        if particles:
            print(f"  Primera partícula: ({particles[0].x:.1f}, {particles[0].y:.1f})")

    def render_background(self, color: RGBColor, landmarks: list[PoseLandmark]) -> None:
        print(f"Fondo de color: {color.to_hex()}")
        print(f"  {len(landmarks)} landmarks visibles")

    def show(self) -> None:
        print("Mostrando ventana (mock)")

    def close(self) -> None:
        print("Cerrando ventana (mock)")