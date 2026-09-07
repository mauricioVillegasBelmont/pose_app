## Puertos
- `CameraPort`: get_frame() -> np.ndarray
- `PoseEstimatorPort`: estimate(frame) -> List[PoseLandmark]
- `RenderPort`: render(scene) -> None
- `GameLogicPort`: process(landmarks) -> scene_data  # Opción 2

## Adaptadores
- Entrada: WebcamAdapter, MediapipeAdapter
- Salida:
  - PygameParticlesAdapter (para juego A)
  - PygameColorAdapter (para juego B)
  - FastAPIAdapter (para control remoto)

## Casos de Uso
- ParticlesGameUC (usa CameraPort, PoseEstimatorPort, RenderPort)
- ColorGameUC (usa CameraPort, PoseEstimatorPort, RenderPort)