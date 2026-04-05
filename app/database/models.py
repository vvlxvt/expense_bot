import datetime
import enum
from sqlalchemy import Enum as SAEnum

from sqlalchemy import (
    create_engine,
    String,
    Float,
    Integer,
    ForeignKey,
    DateTime,
    func,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, relationship


class Base(DeclarativeBase):
    pass


class CatTable(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cat: Mapped[str] = mapped_column(String, nullable=False, unique=True)


class DictTable(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    cat_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"), nullable=False, index=True
    )


class MainTable(Base):
    __tablename__ = "main"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    created: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.now, index=True
    )
    raw: Mapped[str] = mapped_column(String, nullable=False)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )

    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"),
    )


class UserTable(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=True)
    # deposit как кэш для быстрого доступа
    deposit: Mapped[float] = mapped_column(Float, default=0.0)


# class TransactionTable(Base):
#     __tablename__ = "transactions"
#
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     user_id: Mapped[int] = mapped_column(
#         ForeignKey("users.id"), nullable=False, index=True
#     )
#     amount: Mapped[float] = mapped_column(Float, nullable=False)
#     created: Mapped[datetime.datetime] = mapped_column(
#         DateTime, default=datetime.datetime.now, index=True
#     )


# Base.metadata.create_all(bind=engine)
# session = Session(engine)
