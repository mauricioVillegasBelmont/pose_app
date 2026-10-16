from dataclasses import dataclass


@dataclass(frozen=True)
class RGBColor:
    """Color en espacio RGB (dominio puro)."""

    r: int  # 0-255
    g: int
    b: int

    def __post_init__(self):
        """Validación de dominio: los valores deben estar en rango."""
        for channel, name in [(self.r, "r"), (self.g, "g"), (self.b, "b")]:
            if not (0 <= channel <= 255):
                raise ValueError(
                    f"Channel {name} must be between 0 and 255, got {channel}"
                )

    def to_hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    def to_rgb_tuple(self):
        return (self.r, self.g, self.b)

    @classmethod
    def interpolate(
        cls, color1: "RGBColor", color2: "RGBColor", t: float
    ) -> "RGBColor":
        """Interpolación lineal entre dos colores (regla de negocio)."""
        t = max(0.0, min(1.0, t))  # Clamp
        return cls(
            r=int(color1.r + (color2.r - color1.r) * t),
            g=int(color1.g + (color2.g - color1.g) * t),
            b=int(color1.b + (color2.b - color1.b) * t),
        )
