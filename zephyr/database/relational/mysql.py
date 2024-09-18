from typing import override

from sqlalchemy.dialects.mysql import insert

from zephyr.database.relational.base import BaseDatabase, BaseEntity


class MySQLDatabase(BaseDatabase):

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        *args,
        **kwargs
    ):
        super().__init__(host, port, username, password, database, *args, **kwargs)

    @property
    def database_type(self) -> str:
        return "mysql"

    @property
    def database_url_template(self) -> str:
        return "mysql+aiomysql://{username}:{password}@{host}:{port}/{database}"

    @override
    async def insert_or_update(self, table: BaseEntity, **kwargs):
        stmt = insert(table).on_duplicate_key_update(kwargs)
        return await self.execute(stmt)
