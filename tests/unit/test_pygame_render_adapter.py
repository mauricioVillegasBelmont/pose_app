# tests/unit/test_pygame_render_adapter.py
import unittest
from unittest.mock import MagicMock, patch

from adapters.render.pygame_render_adapter import PygameRenderAdapter
from domain.entities.particle import Particle


class TestPygameRenderAdapter(unittest.TestCase):

    def setUp(self):
        # Parchea pygame antes de instanciar
        patcher = patch('adapters.render.pygame_render_adapter.pygame')
        self.mock_pygame = patcher.start()
        self.addCleanup(patcher.stop)

        # Simula display.set_mode
        self.mock_surface = MagicMock()
        self.mock_pygame.display.set_mode.return_value = self.mock_surface

        self.adapter = PygameRenderAdapter(
            width=800, height=600, title="Test"
        )

    def test_init_configures_display(self):
        """__init__ debe configurar el display de pygame."""
        self.mock_pygame.display.set_mode.assert_called_once()
        self.mock_pygame.display.set_caption.assert_called_with("Test")

    def test_render_particles_draws_each_particle(self):
        """render_particles debe dibujar cada partícula."""
        # Arrange
        particles = [
            Particle(x=100, y=200, life=1.0),
            Particle(x=150, y=250, life=0.5),
        ]

        # Act
        self.adapter.render_particles(particles)

        # Assert: se llamó draw.circle al menos 2 veces
        self.assertGreaterEqual(
            self.mock_pygame.draw.circle.call_count, 2
        )

    def test_render_particles_with_empty_list(self):
        """render_particles con lista vacía no debe crashear."""
        # Act / Assert
        try:
            self.adapter.render_particles([])
        except Exception as e:
            self.fail(f"No debe crashear con lista vacía: {e}")

    def test_close_quits_pygame(self):
        """close() debe llamar pygame.quit()."""
        # Act
        self.adapter.close()

        # Assert
        self.mock_pygame.quit.assert_called_once()


if __name__ == "__main__":
    unittest.main()