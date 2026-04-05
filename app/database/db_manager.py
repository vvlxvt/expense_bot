# экспериментальный класс для подключения к бд асинхронно
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


class DB_Manager:
    def __init__(self, url: str, echo: bool = False):
        self.engine = create_async_engine(url=url, echo=echo)
        self.session_factory = async_sessionmaker(
            bind=self.engine, expire_on_commit=False
        )

    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# async def main():
#
#     db = DB_Manager("sqlite+aiosqlite:///C:/users/vital/downloads/master.db", True)
#     async with db.get_session() as session:
#         result = await session.execute(select(UserTable))
#         users = result.scalars().all()
#         for user in users:
#             print({k: v for k, v in user.__dict__.items() if not k.startswith("_")})
#
#
# # Запуск через asyncio
# import asyncio
#
# if __name__ == "__main__":
#     asyncio.run(main())
