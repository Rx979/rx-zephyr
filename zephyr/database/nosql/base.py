import logging
from abc import ABC, abstractmethod
from typing import Union


class NoSQLClient(ABC):

    _logger_: logging.Logger = logging.getLogger(__name__)

    def __init__(
        self,
        host: str,
        port: int,
        username: Union[str, None] = None,
        password: Union[str, None] = None,
        database: Union[str, int, None] = None,
        *args,
        **kwargs
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.args = args
        self.kwargs = kwargs

    @property
    @abstractmethod
    def database_type(self) -> str:
        """
        返回数据库的类型。

        Returns:
            str: 数据库类型。
        """
        pass

    @property
    @abstractmethod
    def database_url_template(self) -> str:
        """数据库URL模板，子类需实现。

        Returns:
            str: 数据库连接URL模板。
        """
        pass

    @abstractmethod
    async def initialize(self):
        """初始化连接"""
        pass

    @abstractmethod
    async def close(self):
        """关闭连接"""
        pass

    async def validate_connection(self):
        """验证链接是否成功，子类可以选择性重写"""
        pass
