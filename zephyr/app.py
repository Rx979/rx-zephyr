import logging
from contextlib import asynccontextmanager
from typing import Type, Union

from fastapi import FastAPI
from uvicorn import Config, Server

from config.manager import ConfigManager
from const import BANNER_FILES, CONFIG_DIR_PATH
from zephyr.database.nosql import RedisClient
from zephyr.database.relational import MySQLDatabase, PostgresqlDatabase
from zephyr.database.relational.base import BaseDatabase


class App:

    _app_: Union[FastAPI, None] = None

    _config_manager_: Union[ConfigManager, None] = None

    _database_: Union[BaseDatabase, None] = None

    _redis_: Union[RedisClient, None] = None

    _logger_: Union[logging.Logger, None] = None

    def __new__(cls, *args, **kwargs):
        App.print_banner()
        if cls._config_manager_ is None:
            cls._config_manager_ = ConfigManager()

        cls._init_app()

        return cls

    @classmethod
    def run(cls):
        """启动服务器"""
        server_config = cls._config_manager_.get_config().app.server
        config = Config(**server_config.model_dump())
        server = Server(config)
        server.run()

    @classmethod
    def app(cls):
        return cls._app_

    @classmethod
    def _init_app(cls):
        """初始化App"""
        if cls._app_:
            return cls._app_

        # 初始化app
        app_config = cls._config_manager_.get_config()
        cls._logger_ = logging.getLogger(__name__)

        if app_config.redis:
            cls._redis_ = RedisClient(**app_config.redis.model_dump())

        # TODO 可能可以使用动态代理初始化
        if app_config.database:
            database_config = app_config.database
            database_class: Type[BaseDatabase] = (
                MySQLDatabase
                if database_config.database_type == "mysql"
                else PostgresqlDatabase
            )
            cls._database_ = database_class(**database_config.model_dump(exclude={'database_type'}))

        app = FastAPI(**app_config.app.model_dump(), lifespan=cls.lifespan)
        cls._app_ = app

    @staticmethod
    def print_banner():
        banner_files_path = [
            CONFIG_DIR_PATH / banner_file for banner_file in BANNER_FILES
        ]
        banner = r"""
            .______      ___   ___ ___   ___ ___   ___
            |   _  \     \  \ /  / \  \ /  / \  \ /  /
            |  |_)  |     \  V  /   \  V  /   \  V  / 
            |      /       >   <     >   <     >   <  
            |  |\  \----. /  .  \   /  .  \   /  .  \ 
            | _| `._____|/__/ \__\ /__/ \__\ /__/ \__\
        """
        for banner_file in banner_files_path:
            if banner_file.exists():
                banner = banner_file.read_text()
                break
        print(banner)

    @staticmethod
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # 初始化连接池
        if App._redis_:
            await App._redis_.initialize()

        if App._database_:
            await App._database_.initialize()
        App._logger_.info(
            f"创建 {App._config_manager_.get_config().app.title} 应用成功: [{App._config_manager_.get_config().app.description}]; version: [{App._config_manager_.get_config().app.version}]"
        )

        yield
        # 关闭连接池
        if App._redis_:
            await App._redis_.close()
        if App._database_:
            await App._database_.close()
