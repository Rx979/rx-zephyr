import logging
from abc import ABC, abstractmethod
from typing import Any, Union

from pandas import DataFrame, Series
from sqlalchemy.engine.result import Result
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import Delete, Insert, Select, Update, text


class BaseEntity(DeclarativeBase, AsyncAttrs):
    """基础Entity，所有数据库表对应的实体类应继承自此类。"""

    pass


class BaseDatabase(ABC):
    """
    抽象的数据库管理类，支持异步操作，使用SQLAlchemy ORM。

    子类必须实现 `database_type` 和 `database_url_template` 属性。
    """

    logger: logging.Logger = logging.getLogger(__name__)

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        *args,
        **kwargs,
    ) -> None:
        """
        初始化数据库连接信息。

        Args:
            host (str): 数据库主机地址。
            port (int): 数据库端口号。
            username (str): 数据库用户名。
            password (str): 数据库密码。
            database (str): 数据库名称。
            *args: 额外的参数。
            **kwargs: 额外的关键字参数，用于传递到引擎配置。
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.args = args
        self.kwargs = kwargs
        self.engine: Union[AsyncEngine, None] = None
        self.session_maker: Union[async_sessionmaker, None] = None

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

    @property
    def database_url(self) -> str:
        """生成数据库连接URL。

        Returns:
            str: 数据库连接的完整URL。
        """
        return self.database_url_template.format(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            database=self.database,
        )

    async def initialize(self) -> None:
        """
        初始化数据库连接，创建引擎和会话工厂。

        Raises:
            SQLAlchemyError: 如果连接失败。
        """
        try:
            name = self.kwargs.pop("name", self.database)
            self.engine = create_async_engine(
                self.database_url,
                **self.kwargs,
            )
            self.session_maker = async_sessionmaker(
                bind=self.engine, expire_on_commit=False, **self.kwargs
            )
            self.logger.info(
                f"[{name}] 连接成功，数据库类型:【{self.database_type}】，Host：{self.host}，Port：{self.port}"
            )
        except SQLAlchemyError as e:
            self.logger.error(f"数据库连接初始化失败: {e}")
            raise

    async def close(self) -> None:
        """关闭数据库连接，释放连接池中的所有连接。"""
        if self.engine:
            await self.engine.dispose()
            self.logger.info(f"数据库 {self.database} 的连接已关闭")

    async def execute(
        self, statement: Union[str, Select, Insert, Update, Delete]
    ) -> Result[Any]:
        """执行SQL语句，支持字符串SQL和ORM语句。

        Args:
            statement (Union[str, Select, Insert, Update, Delete]): 要执行的SQL语句或ORM操作。

        Returns:
            Result[Any]: SQLAlchemy执行结果。

        Raises:
            SQLAlchemyError: 如果执行失败。
        """
        try:
            if isinstance(statement, str):
                statement = text(statement)
            async with self.session_maker() as session:
                async with session.begin():
                    result = await session.execute(statement)
                    return result
        except SQLAlchemyError as e:
            self.logger.error(f"执行SQL时出错: {e}")
            raise

    async def _fetch_results(
        self, statement: Union[str, Select], size: int = None
    ) -> DataFrame:
        """执行SQL并返回结果集，转换为DataFrame。

        Args:
            statement (Union[str, Select]): 要执行的SQL或ORM查询。
            size (int, optional): 限制结果集的大小。默认不限制。

        Returns:
            DataFrame: 查询结果集。
        """
        result = await self.execute(statement)
        if size:
            rows = result.fetchmany(size)
        else:
            rows = result.fetchall()
        columns = result.keys()
        return DataFrame(rows, columns=list(columns))

    async def select(self, statement: Union[str, Select]) -> DataFrame:
        """执行查询并返回所有结果。

        Args:
            statement (Union[str, Select]): SQL查询语句或ORM Select对象。

        Returns:
            DataFrame: 查询结果集。
        """
        return await self._fetch_results(statement)

    async def select_one(self, statement: Union[str, Select]) -> Union[Series, None]:
        """执行查询并返回单条记录。

        Args:
            statement (Union[str, Select]): SQL查询语句或ORM Select对象。

        Returns:
            Union[Series, None]: 查询结果的单条记录。
        """
        result = await self.execute(statement)
        row = result.fetchone()
        return Series(data=row) if row else None

    async def select_many(self, statement: Union[str, Select], size: int) -> DataFrame:
        """执行查询并返回指定数量的记录。

        Args:
            statement (Union[str, Select]): SQL查询语句或ORM Select对象。
            size (int): 要获取的记录数量。

        Returns:
            DataFrame: 查询结果集。
        """
        return await self._fetch_results(statement, size)

    async def update_one(self, statement: Union[str, Update]) -> Result[Any]:
        """更新单条记录。

        Args:
            statement (Union[str, Update]): 要执行的SQL更新语句或ORM Update对象。

        Returns:
            Result[Any]: SQLAlchemy执行结果。
        """
        return await self.execute(statement)

    async def update_many(self, statement: Union[str, Update]) -> Result[Any]:
        """更新多条记录。

        Args:
            statement (Union[str, Update]): 要执行的SQL更新语句或ORM Update对象。

        Returns:
            Result[Any]: SQLAlchemy执行结果。
        """
        return await self.execute(statement)

    async def insert(self, statement: Union[str, Insert]) -> Result[Any]:
        """插入单条记录。

        Args:
            statement (Union[str, Insert]): 要执行的SQL插入语句或ORM Insert对象。

        Returns:
            Result[Any]: SQLAlchemy执行结果。
        """
        return await self.execute(statement)

    async def insert_many(self, statement: Union[str, Insert]) -> Result[Any]:
        """插入多条记录。

        Args:
            statement (Union[str, Insert]): 要执行的SQL插入语句或ORM Insert对象。

        Returns:
            Result[Any]: SQLAlchemy执行结果。
        """
        return await self.execute(statement)

    async def insert_or_update(self, table: BaseEntity, **kwargs):
        """
        更新或插入方法，由于不同数据库会有不同的 insert_or_update 的实现，所以子类可以选择性重写该方法。

        Args:
            table (BaseEntity): 表实体类
            **kwargs: 需要更新的数据

        Returns:
            Result[Any]: SQLAlchemy执行结果。
        """
        pass

    async def delete(self, statement: Union[str, Delete]) -> Result[Any]:
        """删除记录。

        Args:
            statement (Union[str, Delete]): 要执行的SQL删除语句或ORM Delete对象。

        Returns:
            Result[Any]: SQLAlchemy执行结果。
        """
        return await self.execute(statement)
