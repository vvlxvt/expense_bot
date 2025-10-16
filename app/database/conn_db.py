from sqlalchemy import create_engine, MetaData, Table, func
from sqlalchemy.orm import Session, registry, DeclarativeBase
from app import config

conf = config.load_config(None)
DB_PATH = conf.db_path
engine = create_engine(f"sqlite:///{DB_PATH}")

# Создаём` объект MetaData
meta = MetaData()

# Создаю объект registry
mapper_registry = registry()

# Получаю объекты Table
main_table = Table("main", meta, autoload_with=engine)
dict_table = Table("category", meta, autoload_with=engine)


class MainTable:
    pass


class DictTable:
    pass


mapper_registry.map_imperatively(
    MainTable, main_table
)  # установить соответствие (маппинг) между ORM-классом MyTable
mapper_registry.map_imperatively(
    DictTable, dict_table
)  # и существующей таблицей table в базе данных


class Base(DeclarativeBase):
    pass


Base.metadata.create_all(bind=engine)

# Создаём` сессию для работы с базой данных
session = Session(engine)
