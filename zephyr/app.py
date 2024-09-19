import logging
from contextlib import asynccontextmanager
from typing import Final, List, Optional, Type

from fastapi import FastAPI
from uvicorn import Config, Server

from zephyr.config.manager import ConfigManager
from zephyr.const import BANNER_FILES, CONFIG_DIR_PATH, DEFAULT_BANNER
from zephyr.database.nosql import RedisClient
from zephyr.database.relational.base import BaseDatabase
from zephyr.exception.database import DatabaseNotSupportedException


class App:
    _app_: Optional[FastAPI] = None
    _config_manager_: Optional[ConfigManager] = None
    _database_: Optional[BaseDatabase] = None
    _redis_: Optional[RedisClient] = None
    _logger_: Final[logging.Logger] = logging.getLogger(__name__)

    def __new__(cls, *args, **kwargs):
        """Determine whether there is an existing FastAPI instance"""
        if not cls._app_:
            cls._init_app()  # 初始化 app
        return cls

    @classmethod
    def run(cls):
        """Startup server"""
        server_config = cls._config_manager_.get_config().app.server
        config = Config(**server_config.model_dump())
        server = Server(config)
        server.run()

    @classmethod
    def app(cls):
        """Return the initialized FastAPI instance"""
        return cls._app_

    @classmethod
    def _init_app(cls):
        """Initialize the App"""
        if cls._app_:
            return
        cls.print_banner()
        if not cls._config_manager_:
            cls._config_manager_ = ConfigManager()

        app_config = cls._config_manager_.get_config()

        cls._initialize_redis(app_config.redis)
        cls._initialize_database(app_config.database)

        cls._app_ = FastAPI(**app_config.app.model_dump(), lifespan=cls.lifespan)

    @classmethod
    def _initialize_redis(cls, redis_config):
        """initialize Redis"""
        if redis_config:
            cls._redis_ = RedisClient(**redis_config.model_dump())

    @classmethod
    def _initialize_database(cls, database_config):
        """initialize database"""
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
            cls._database_ = database_class(
                **database_config.model_dump(exclude={"database_type"})
            )
        else:
            raise DatabaseNotSupportedException(database_config.database_type)

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
            await App._initialize_connections()
            App._log_app_info()
            yield
        except Exception as e:
            App._logger_.error(f"Error during application's lifespan {str(e)}")
        finally:
            await App._close_connections()

    @classmethod
    async def _initialize_connections(cls):
        """Initializes the Redis and database connection pools"""
        if cls._redis_:
            await cls._redis_.initialize()
        if cls._database_:
            await cls._database_.initialize()

    @classmethod
    async def _close_connections(cls):
        """Disable Redis and database connection pooling"""
        if cls._redis_:
            await cls._redis_.close()
        if cls._database_:
            await cls._database_.close()

    @classmethod
    def _log_app_info(cls):
        """Record application information"""
        app_config = cls._config_manager_.get_config().app
        cls._logger_.info(
            f"Application [{app_config.title}] created successfully: "
            f"[{app_config.description}]; version: [{app_config.version}]"
        )
