import logging
from logging import Logger
from contextlib import asynccontextmanager
from typing import Final, List, Optional, Type, Union, ClassVar

from fastapi import FastAPI
from uvicorn import Config, Server
from pydantic import BaseModel, Field, PrivateAttr

from zephyr.config.manager import ConfigManager
from zephyr.const import BANNER_FILES, CONFIG_DIR_PATH, DEFAULT_BANNER
from zephyr.database.nosql import RedisClient
from zephyr.database.relational.base import BaseDatabase
from zephyr.exception.database import DatabaseNotSupportedException


def l_span(app: FastAPI):
    yield

class Zephyr(BaseModel):


    _instance_: ClassVar["Zephyr"] = None

    _app: Optional[FastAPI] = PrivateAttr(None)
    _config_manager: Optional[ConfigManager] = PrivateAttr(None)
    _database: Optional[BaseDatabase] = PrivateAttr(None)
    _redis: Optional[RedisClient] = PrivateAttr(None)

    logger: Final[Logger] = logging.getLogger(__name__)

    def __new__(cls, *args, **kwargs):
        """Determine whether there is an existing FastAPI instance"""
        if not cls._instance_:
            cls.print_banner()
            instance = super(Zephyr, cls).__new__(cls)
            cls._instance_ = instance
        return cls._instance_

    def __init__(self):
        super().__init__()
        self._config_manager = ConfigManager()
        self._app = self._init_app()
        self._database = self._initialize_database()
        self._redis = self._initialize_redis()

    @property
    def app(self):
        return self._app

    def run(self):
        """Startup server"""
        server_config = self._config_manager.get_config().app.server
        config = Config(**server_config.model_dump())
        server = Server(config)
        server.run()

    def _init_app(self):
        """Initialize the App"""
        app_config = self._config_manager.get_config().app.model_dump()
        return FastAPI(**app_config, lifespan=self.lifespan)

    def _initialize_redis(self) -> Union[RedisClient, None]:
        """initialize Redis"""
        redis_config = self._config_manager.get_config().redis
        if not redis_config:
            return
        return RedisClient(**redis_config.model_dump())

    def _initialize_database(self) -> Union[None, BaseDatabase]:
        """initialize database"""
        database_config = self._config_manager.get_config().database
        if not database_config:
            return
        database_class_list: List[Type[BaseDatabase]] = BaseDatabase.__subclasses__()

        # Find the corresponding database class
        database_class = next(
            (db_class for db_class in database_class_list
             if db_class.database_type() == database_config.database_type),
            None
        )

        if database_class:
            return database_class(
                **database_config.model_dump(exclude={"database_type"})
            )
        else:
            raise DatabaseNotSupportedException(database_config.database_type)
    #
    @staticmethod
    def print_banner():
        """print banner"""
        banner_files_path = [
            CONFIG_DIR_PATH / banner_file for banner_file in BANNER_FILES
        ]
        banner = DEFAULT_BANNER
        for banner_file in banner_files_path:
            if banner_file.exists():
                banner = banner_file.read_text()
                break
        print(banner)

    @staticmethod
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Manage the application lifecycle"""
        try:
            await Zephyr._instance_._initialize_connections()
            Zephyr._log_app_info()
            yield
        except Exception as e:
            Zephyr.logger.error(f"Error during application's lifespan {str(e)}")
        finally:
            await Zephyr._instance_._close_connections()

    async def _initialize_connections(self):
        """Initializes the Redis and database connection pools"""
        if self.redis:
            await self.redis.initialize()
        if self.database:
            await self.database.initialize()

    async def _close_connections(self):
        """Disable Redis and database connection pooling"""
        if self.redis:
            await self.redis.close()
        if self.database:
            await self.database.close()

    @classmethod
    def _log_app_info(cls):
        """Record application information"""
        app_config = cls.config_manager.get_config().app
        cls.logger.info(
            f"Application [{app_config.title}] created successfully: "
            f"[{app_config.description}]; version: [{app_config.version}]"
        )
