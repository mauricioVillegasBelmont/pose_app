"""
Adaptador de FastAPI.

Encapsula la creación de la app FastAPI, CORS, y el servidor uvicorn.
"""

import threading

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from adapters.api.routes import create_router
from config.settings import APISettings
from domain.ports.state_port import StatePort
from infrastructure.logging.logger import get_logger

logger = get_logger("adapters.api")


class FastAPIAdapter:
    """
    Adaptador que expone la aplicación vía HTTP REST.

    Uso:
        adapter = FastAPIAdapter(settings.api, state)
        adapter.start()  # No bloqueante
        ...
        adapter.stop()
    """

    def __init__(self, settings: APISettings, state: StatePort):
        self._settings = settings
        self._state = state
        self._app: FastAPI | None = None
        self._server: uvicorn.Server | None = None
        self._thread: threading.Thread | None = None

        self._build_app()

    def _build_app(self) -> None:
        """Construye la aplicación FastAPI con middleware y rutas."""
        self._app = FastAPI(
            title="Pose AR API",
            description="API para interactuar con el juego de pose + partículas",
            version="0.4.0",
            docs_url="/docs",
            redoc_url="/redoc",
        )

        # CORS
        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=self._settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Incluye las rutas
        router = create_router(self._state)
        self._app.include_router(router)

        # Root endpoint
        @self._app.get("/", include_in_schema=False)
        def root():
            return {
                "name": "Pose AR API",
                "docs": "/docs",
                "health": "/api/v1/health",
            }

        logger.info("App FastAPI construida")

    def start(self) -> None:
        """
        Inicia el servidor en un thread separado (no bloquea).
        """
        if self._thread is not None and self._thread.is_alive():
            logger.warning("El servidor ya está corriendo")
            return

        config = uvicorn.Config(
            app=self._app,
            host=self._settings.host,
            port=self._settings.port,
            log_level="warning",  # Uvicorn tiene su propio logger
            access_log=False,
        )

        self._server = uvicorn.Server(config)

        self._thread = threading.Thread(
            target=self._server.run,
            daemon=True,  # Muere cuando el main termina
            name="api-server"
        )
        self._thread.start()

        logger.info(
            f"API iniciada en http://{self._settings.host}:{self._settings.port}"
        )
        logger.info(f"Docs disponibles en http://localhost:{self._settings.port}/docs")

    def stop(self) -> None:
        """Detiene el servidor."""
        if self._server is not None:
            logger.info("Deteniendo API...")
            self._server.should_exit = True

        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None

        logger.info("API detenida")

    @property
    def app(self) -> FastAPI:
        """Acceso directo a la app (útil para tests con TestClient)."""
        assert self._app is not None
        return self._app