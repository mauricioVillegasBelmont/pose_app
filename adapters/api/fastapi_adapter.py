"""Adaptador de FastAPI."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from adapters.api.auth_routes import create_auth_router
from adapters.api.routes import create_router
from adapters.api.user_routes import create_user_router
from adapters.auth.credentials_auth_provider import CredentialsAuthProvider
from adapters.auth.json_bootstrap import bootstrap_from_json
from app.state_registry import StateRegistry
from config.settings import Settings
from domain.ports.event_bus_port import EventBusPort
from infrastructure.auth.jwt_service import JWTService
from infrastructure.logging.logger import get_logger

logger = get_logger("adapters.api.fastapi_adapter")


class FastAPIAdapter:
    """Adaptador HTTP."""

    def __init__(
        self,
        settings: Settings,  # ← Cambio: Settings completo, no solo APISettings
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

        # CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self._settings.api.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # === DEPENDENCIAS EN app.state ===
        app.state.settings = self._settings

        # === Bootstrap usuarios ===
        user_repo, identity_repo = bootstrap_from_json("data/users.json")

        # === Repositorios y servicios de autenticación ===
        app.state.user_repository = user_repo
        app.state.identity_repository = identity_repo
        app.state.auth_adapter = CredentialsAuthProvider(
            user_repository=user_repo,
            identity_repository=identity_repo,
        )
        app.state.jwt_service = JWTService(self._settings.jwt)

        # Routers
        app.include_router(create_auth_router())
        app.include_router(create_user_router())  # ← NUEVO
        app.include_router(create_router(self._event_bus, self._registry))

        @app.get("/", include_in_schema=False)
        async def root():
            return {"name": "Pose AR API", "docs": "/docs"}

        return app

    @property
    def app(self) -> FastAPI:
        return self._app

    async def serve(self) -> None:
        config = uvicorn.Config(
            app=self._app,
            host=self._settings.api.host,
            port=self._settings.api.port,
            log_level="warning",
            access_log=False,
        )
        self._server = uvicorn.Server(config)
        logger.info(
            f"API iniciada en http://{self._settings.api.host}:"
            f"{self._settings.api.port}"
        )
        await self._server.serve()

    async def shutdown(self) -> None:
        if self._server is not None:
            self._server.should_exit = True
            logger.info("API: shutdown solicitado")
