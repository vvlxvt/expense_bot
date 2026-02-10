from typing import Optional
import datetime
from sqlalchemy import create_engine, String, Float, Integer, ForeignKey, DateTime, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

from app import config

conf = config.load_config(None)
engine = create_engine(f"sqlite:///{conf.db_path}", echo=False)


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
    cat_id: Mapped[int] = mapped_column(ForeignKey("categories.id"),nullable=False, index=True)


class MainTable(Base):
    __tablename__ = "main"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    created: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now, index=True)
    raw: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"),)


Base.metadata.create_all(bind=engine)
session = Session(engine)

'''
# сделать все наименования трат в нижнем регистре в тч и в словаре
class Category(Base):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True) # Название товара
    cat: Mapped[Optional[str]] = mapped_column(String) # Категория (заполняется вручную)

    def __repr__(self) -> str:
        return f"Category(name={self.name!r}, cat={self.cat!r})"

class MainTable(Base):
    __tablename__ = "main"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    sub_name: Mapped[Optional[str]] = mapped_column(String)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    created: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # cat_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))

def fix_case_and_whitespace():
    """Приводит все наименования в таблицах к нижнему регистру через Python."""
    with Session(engine) as session:
        # Исправляем в MainTable
        items = session.scalars(select(MainTable)).all()
        for item in items:
            if item.name:
                item.name = item.name.strip().lower()

        # Исправляем в Category
        cats = session.scalars(select(Category)).all()
        for cat in cats:
            if cat.name:
                cat.name = cat.name.strip().lower()

        session.commit()
        print("Регистр и пробелы исправлены во всей базе (включая кириллицу).")

fix_case_and_whitespace()
'''