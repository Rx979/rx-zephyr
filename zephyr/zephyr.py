import logging
from contextlib import asynccontextmanager
from logging import Logger
from typing import Final, List, Optional, Type, Union, ClassVar

from fastapi import FastAPI
from uvicorn import Config, Server

from zephyr.config.manager import ConfigManager
from zephyr.const import BANNER_FILES, CONFIG_DIR_PATH, DEFAULT_BANNER
from zephyr.database.nosql import RedisClient
from zephyr.database.relational.base import BaseDatabase
from zephyr.exception.database import DatabaseNotSupportedException
from zephyr.meta import SingletonMeta


class Zephyr(metaclass=SingletonMeta):

    logger: Final[Logger] = logging.getLogger(__name__)

    def __init__(self):
        self.print_banner()
        self._config_manager = ConfigManager()
        self._app = self._init_app()
        self._database = self._initialize_database()
        self._redis = self._initialize_redis()

    @property
    def config_manager(self) -> ConfigManager:
        return self._config_manager

    @property
    def app(self) -> Optional[FastAPI]:
        return self._app

    @property
    def redis(self) -> Optional[RedisClient]:
        return self._redis

    @property
    def database(self) -> Optional[BaseDatabase]:
        return self._database

    @config_manager.setter
    def config_manager(self, config_manager: ConfigManager) -> None:
        if not config_manager:
            self._config_manager = config_manager
        return

    @app.setter
    def app(self, app: FastAPI) -> None:
        if not app:
            self._app = app
        return

    @redis.setter
    def redis(self, redis: RedisClient) -> None:
        if not redis:
            self._redis = redis
        return

    @database.setter
    def database(self, database: BaseDatabase) -> None:
        if not database:
            self._database = database
        return


    def run(self):
        """Startup server"""
        server_config = self._config_manager.get_config().app.server
        config = Config(lifespan='on', **server_config.model_dump())
        server = Server(config)
        server.run()

    def _init_app(self):
        """Initialize the App"""
        app_config = self._config_manager.get_config().app.model_dump()
        return FastAPI(**app_config, lifespan=Zephyr.lifespan)

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
        instance = Zephyr()
        try:
            await instance._initialize_connections()
            instance._log_app_info()
            yield
        except Exception as e:
            instance.logger.error(f"Error during application's lifespan {str(e)}")
        finally:
            await instance._close_connections()

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

    def _log_app_info(self):
        """Record application information"""
        app_config = self.config_manager.get_config().app
        self.logger.info(
            f"Application [{app_config.title}] created successfully: "
            f"[{app_config.description}]; version: [{app_config.version}]"
        )
