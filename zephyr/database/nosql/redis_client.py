from typing import Optional, Union, override
from urllib.parse import quote_plus

from redis.asyncio import ConnectionPool, Redis, RedisError

from zephyr.database.nosql.base import NoSQLClient


class RedisClient(NoSQLClient):

    def __init__(
        self,
        host: str,
        port: int,
        username: Union[str, None] = None,
        password: Union[str, None] = None,
        database: int = 0,
        *args,
        **kwargs,
    ):
        super().__init__(host, port, username, password, database, *args, **kwargs)
        self.connection_pool: Union[ConnectionPool, None] = None
        self.redis: Union[Redis, None] = None

    @property
    def database_type(self) -> str:
        return "redis"

    @property
    def database_url_template(self) -> str:
        return "redis://{auth}@{host}:{port}/{database}"

    async def initialize(self):
        """initial connection"""

        # 构造auth部分
        if self.username and self.password:
            auth = f"{quote_plus(self.username)}:{quote_plus(self.password)}"
        elif not self.username and self.password:
            auth = f":{quote_plus(self.password)}"
        elif self.username and not self.password:
            auth = f"{quote_plus(self.username)}"
        else:
            auth = ""

        # 格式化url template
        url = self.database_url_template.format(
            auth=auth, host=self.host, port=self.port, database=self.database
        )

        self.connection_pool = ConnectionPool.from_url(url, **self.kwargs)
        self.redis = Redis.from_pool(self.connection_pool)
        await self.validate_connection()

    async def close(self):
        """close the connection"""
        if self.redis:
            await self.redis.aclose(close_connection_pool=True)
            self._logger_.info("关闭 Redis 连接池")

    @override
    async def validate_connection(self):
        """verify that the connection is valid"""
        try:
            response = await self.redis.ping()
            if response:
                self._logger_.info(
                    f"Redis 连接成功 [{self.host}:{self.port}/{self.database}]"
                )
            else:
                raise RedisError()
        except RedisError as e:
            self._logger_.error(f"Redis 连接失败: {str(e)}")

    async def flush_db(self):
        """delete all keys"""
        return await self.redis.flushdb()

    async def exists(
        self,
        key: Union[str, bytes, memoryview],
    ):
        """
        check whether the key exists

        Args:
            key: the key name

        Returns:
            true or false
        """
        return bool(await self.redis.exists(key))

    async def get(
        self,
        key: Union[str, bytes, memoryview],
    ):
        """
        get the value

        Args:
            key: the key

        Returns:
            the value of the key
        """
        return await self.redis.get(key)

    async def set(
        self,
        key: Union[str, bytes, memoryview],
        value: Union[bytes, memoryview, str, int, float],
        expired: Optional[int] = None,
    ):
        """
        set the key and value
        Args:
            key: the key name
            value: the value to set
            expired: the expiration time

        Returns:
            Any
        """
        return await self.redis.set(key, value, ex=expired)
