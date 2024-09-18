from typing import Union, override
from urllib.parse import quote_plus

from motor.motor_asyncio import AsyncIOMotorClient

from zephyr.database.nosql.base import NoSQLClient


class MongoClient(NoSQLClient):

    def __init__(
        self,
        host: str = "localhost",
        port: int = 27017,
        username: Union[str, None] = None,
        password: Union[str, None] = None,
        database: Union[str, None] = None,
        *args,
        **kwargs,
    ):
        super().__init__(host, port, username, password, database, *args, **kwargs)
        self.mongo_client: Union[AsyncIOMotorClient, None] = None

    @property
    def database_type(self) -> str:
        return "mongodb"

    @property
    def database_url_template(self) -> str:
        return "mongodb://{auth}@{host}:{port}/{database}"

    async def initialize(self):
        """初始化连接"""

        # 构造auth部分
        if self.username and self.password:
            auth = f"{quote_plus(self.username)}:{quote_plus(self.password)}"
        elif not self.username and self.password:
            auth = f":{quote_plus(self.password)}"
        elif self.username and not self.password:
            auth = f"{quote_plus(self.username)}"
        else:
            auth = ""
        url = self.database_url_template.format(
            auth=auth,
            host=self.host,
            port=self.port,
            database=f"{self.database}" if self.database else "",
        )
        if self.kwargs:
            options = "&".join([f"{key}={value}" for key, value in self.kwargs.items()])
            url += f"?{options}"

        self.mongo_client = AsyncIOMotorClient(url)
        await self.validate_connection()

    async def close(self):
        """关闭连接"""

        if self.mongo_client:
            self.mongo_client.close()

    @override
    async def validate_connection(self):
        try:
            await self.mongo_client["admin"].command("ping")
            self._logger_.info(
                f"Mongodb 连接成功 [{self.host}:{self.port}/{self.database}]"
            )
        except Exception as e:
            self._logger_.error(f"Mongodb 连接失败: {str(e)}")
