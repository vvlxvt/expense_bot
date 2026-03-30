import datetime

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
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from app.config import engine


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
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"),
    )


Base.metadata.create_all(bind=engine)
session = Session(engine)
