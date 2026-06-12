# экспериментальный класс для подключения к бд асинхронно
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


class DB_Manager:
    def __init__(self, url: str, echo: bool = False):
        """Create an async SQLAlchemy engine and session factory."""
        self.engine = create_async_engine(url=url, echo=echo)
        self.session_factory = async_sessionmaker(
            bind=self.engine, expire_on_commit=False
        )

    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        """Yield an async session and commit or roll back the transaction."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
