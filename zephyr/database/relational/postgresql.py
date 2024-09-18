from typing import override

from sqlalchemy.dialects.postgresql import insert

from zephyr.database.relational.base import BaseDatabase, BaseEntity


class PostgresqlDatabase(BaseDatabase):

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
        return "postgresql"

    @property
    def database_url_template(self) -> str:
        return "postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"

    @override
    async def insert_or_update(self, table: BaseEntity, **kwargs):

        # 将主键或唯一约束列取出，以便在冲突时使用
        primary_key_columns = [key.name for key in table.__table__.primary_key]

        # 构建插入语句
        stmt = insert(table).values(kwargs)

        # 在主键或唯一约束冲突时更新除主键以外的列
        update_dict = {
            col: stmt.excluded[col] for col in kwargs if col not in primary_key_columns
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=primary_key_columns,  # 冲突检测依据的列
            set_=update_dict,  # 冲突时更新的列和值
        )

        # 执行 SQL 语句
        return await self.execute(stmt)
