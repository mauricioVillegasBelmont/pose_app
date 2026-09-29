"""
Adaptador de FastAPI.

Recibe el EventBus y el StateRegistry, construye la app y expone
un método `serve()` async para correr dentro del loop principal.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from adapters.api.routes import create_router
from app.state_registry import StateRegistry
from config.settings import APISettings
from domain.ports.event_bus_port import EventBusPort
from infrastructure.logging.logger import get_logger

logger = get_logger("adapters.api")


class FastAPIAdapter:
    """
    Adaptador HTTP que expone la API REST.

    Uso:
        api = FastAPIAdapter(settings, event_bus, registry)
        await api.serve()  # Bloquea hasta shutdown
    """

    def __init__(
        self,
        settings: APISettings,
        event_bus: EventBusPort,
        registry: StateRegistry,
    ):
        self._settings = settings
        self._event_bus = event_bus
        self._registry = registry
        self._app = self._build_app()
        self._server: uvicorn.Server | None = None

    def _build_app(self) -> FastAPI:
        app = FastAPI(
            title="Pose AR API",
            version="0.5.0",
            docs_url="/docs",
            redoc_url="/redoc",
        )
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self._settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        router = create_router(self._event_bus, self._registry)
        app.include_router(router)

        @app.get("/", include_in_schema=False)
        async def root():
            return {"name": "Pose AR API", "docs": "/docs"}

        return app

    @property
    def app(self) -> FastAPI:
        """Acceso para tests con TestClient."""
        return self._app

    async def serve(self) -> None:
        """
        Corre el servidor uvicorn en el loop actual (async).

        Bloquea hasta que se llame a `shutdown()`.
        """
        config = uvicorn.Config(
            app=self._app,
            host=self._settings.host,
            port=self._settings.port,
            log_level="critical",
            access_log=False,
        )
        self._server = uvicorn.Server(config)
        logger.info(
            f"API iniciada en http://{self._settings.host}:{self._settings.port}"
        )
        await self._server.serve()

    async def shutdown(self) -> None:
        """Solicita el shutdown del servidor."""
        if self._server is not None:
            self._server.should_exit = True
            logger.info("API: shutdown solicitado")