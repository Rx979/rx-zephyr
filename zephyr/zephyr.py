import importlib
import logging
import site
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Final, List, Optional, Type, Union

from fastapi import FastAPI
from uvicorn import Config, Server

from zephyr.config.manager import ConfigManager
from zephyr.const import BANNER_FILES, CONFIG_DIR_PATH, DEFAULT_BANNER
from zephyr.database.nosql import RedisClient
from zephyr.database.relational.base import BaseDatabase
from zephyr.exception.database import DatabaseNotSupportedException
from zephyr.router import ZephyrRouter


class Zephyr:

    logger: Final[logging.Logger] = logging.getLogger(__name__)

    def __init__(self):
        self._app: Optional[FastAPI] = None
        self._database: Optional[BaseDatabase] = None
        self._redis: Optional[RedisClient] = None
        self._config_manager: Optional[ConfigManager] = None

    @property
    def app(self) -> Optional[FastAPI]:
        return self._app

    @property
    def redis(self) -> Optional[RedisClient]:
        return self._redis

    @property
    def database(self) -> Optional[BaseDatabase]:
        return self._database

    def run(self):
        """Startup server"""
        self._initialize_app()
        server_config = self._config_manager.app_config.app.server
        app = self._factory_initialize if server_config.factory else self._app

        config = Config(app=app, **server_config.model_dump())
        server = Server(config)
        server.run()

    def _initialize_app(self):
        """Initialize the App"""
        self.print_banner()
        self._config_manager = ConfigManager()
        app_config = self._config_manager.app_config.app.model_dump()
        app = FastAPI(**app_config, lifespan=self.lifespan)
        self._initialize_router(app)
        self._app = app
        return self._app

    def _initialize_router(self, app: FastAPI, path: Path = Path().parent.absolute()):
        """Register router for FastAPI, skipping third-party packages and virtual environments."""
        if not isinstance(app, FastAPI):
            raise ValueError("The parameter app must be FastAPI")

        startup_module = Path(__file__).stem
        site_packages = self._get_site_packages()
        virtual_env_path = self._get_virtual_env_path()

        for item in path.iterdir():
            if self._is_third_party_or_virtualenv(item, site_packages, virtual_env_path):
                continue

            if item.is_dir():
                self._initialize_router(app, item)
            elif item.is_file() and item.suffix == ".py":
                self._import_module(app, item, path, startup_module)

    def _initialize_redis(self) -> Optional[RedisClient]:
        """Initialize Redis"""
        redis_config = self._config_manager.app_config.redis
        if not redis_config:
            return None
        return RedisClient(**redis_config.model_dump())

    def _initialize_database(self) -> Optional[BaseDatabase]:
        """Initialize database"""
        database_config = self._config_manager.app_config.database
        if not database_config:
            return None

        database_class = self._find_database_class(database_config.database_type)
        if database_class:
            return database_class(**database_config.model_dump(exclude={"database_type"}))
        else:
            raise DatabaseNotSupportedException(database_config.database_type)

    @staticmethod
    def _factory_initialize() -> FastAPI:
        """Factory initialization for the app"""
        factory_zephyr = Zephyr()
        return factory_zephyr._initialize_app()

    @staticmethod
    def print_banner():
        """Print application banner"""
        banner_files_path = [CONFIG_DIR_PATH / banner_file for banner_file in BANNER_FILES]
        banner = next((banner_file.read_text() for banner_file in banner_files_path if banner_file.exists()), DEFAULT_BANNER)
        print(banner)

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """Manage the application lifecycle"""
        self._database = self._initialize_database()
        self._redis = self._initialize_redis()

        try:
            await self._initialize_connections()
            self._log_app_info()
            yield
        except Exception as e:
            self.logger.error(f"Error during application's lifespan {str(e)}")
        finally:
            await self._close_connections()

    async def _initialize_connections(self):
        """Initialize Redis and database connection pools"""
        if self.redis:
            await self.redis.initialize()
        if self.database:
            await self.database.initialize()

    async def _close_connections(self):
        """Close Redis and database connection pools"""
        if self.redis:
            await self.redis.close()
        if self.database:
            await self.database.close()

    def _log_app_info(self):
        """Log application information"""
        app_config = self._config_manager.app_config.app
        self.logger.info(f"Application [{app_config.title}] created successfully: "
                         f"[{app_config.description}]; version: [{app_config.version}]")

    # def _load_config(self):
    #     """Load configuration manager"""
    #     self._config_manager = ConfigManager()

    @staticmethod
    def _get_site_packages() -> set:
        """Get all site-packages directories"""
        return {Path(p).resolve() for p in site.getsitepackages()}

    @staticmethod
    def _get_virtual_env_path() -> Optional[Path]:
        """Get the virtual environment path if active"""
        return Path(sys.prefix).resolve() if sys.prefix != sys.base_prefix else None

    @staticmethod
    def _is_third_party_or_virtualenv(item: Path, site_packages: set, virtual_env_path: Optional[Path]) -> bool:
        """Check if the path is a third-party or virtual environment"""
        return any(item.resolve().is_relative_to(p) for p in site_packages) or \
               (virtual_env_path and item.resolve().is_relative_to(virtual_env_path))

    def _import_module(self, app: FastAPI, item: Path, base_path: Path, startup_module: str):
        """Dynamically import a module and register routers"""
        relative_path = item.relative_to(base_path)
        module_name = ".".join(relative_path.with_suffix("").parts)

        if module_name in sys.modules or module_name == startup_module:
            return

        try:
            module = importlib.import_module(module_name)
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, ZephyrRouter):
                    app.include_router(attr)
            sys.modules.pop(module_name, None)
        except Exception as e:
            self.logger.error(f"Failed to register router: {str(e)}")

    @staticmethod
    def _find_database_class(db_type: str) -> Optional[Type[BaseDatabase]]:
        """Find the corresponding database class by database type"""
        return next((db_class for db_class in BaseDatabase.__subclasses__() if db_class.database_type() == db_type), None)
