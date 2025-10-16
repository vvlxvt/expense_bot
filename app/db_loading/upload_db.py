import pandas as pd
import json
from sqlalchemy import (
    create_engine,
    Column,
    DateTime,
    String,
    MetaData,
    Table,
    Integer,
    text,
)
from db_loading.fuzzy_wuzzy import find_cat, pars_message, del_user
from db_loading.dictionary import Dic_df

with open("../data/result1.json", "r", encoding="utf-8") as file:
    chat_data = json.load(file)  # загрузка json из файла

engine = create_engine(f"sqlite:///../data/master.db")
metadata = MetaData()
main_table = Table(
    "main",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("date", DateTime),
    Column("text", String),
    Column("name", String),
    Column("price", String),
    Column("from_id", String),
    Column("cat", String),
)
category_table = Table(
    "category",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String),
    Column("cat", String),
)

metadata.create_all(engine)

# преобразую вложенные JSON данных в обьект DataFrame
df = pd.json_normalize(chat_data["messages"])

# создаю новый dataframe содержащий необходимые столбцы, используя копию данных, а не ссылку
selected_columns_df = df[["date", "text", "from_id"]].copy()

# преобразую время в объект datetime
selected_columns_df["date"] = pd.to_datetime(selected_columns_df["date"])

# разделяю ячейки с несколькими строчками на ячейки со сдвигом вниз
# метод assign() для временного изменения столбца 'text', после чего вызывает explode() с авто установкой индексов
selected_columns_df = selected_columns_df.assign(
    text=df["text"].str.split("\n")
).explode("text", ignore_index=True)

new_df = selected_columns_df.copy()

# Применяем функцию распарсить к столбцу 'text' и добавляем результат в два новых столбца
new_df[["name", "price"]] = new_df["text"].apply(lambda x: pd.Series(pars_message(x)))

# заменяю пустые значения на message
new_df["name"] = new_df["name"].fillna("без категории")

# # применяю свою функцию к столбцу text результат возвращаю в sub_name
new_df["sub_name"] = new_df["name"].map(find_cat)
new_df["from_id"] = new_df["from_id"].map(del_user)

# переименовываю столбцы
new_df = new_df.rename(columns={"text": "raw", "date": "created", "from_id": "user_id"})

new_df["id"] = range(1, len(new_df) + 1)
# меняю порядок столбцов таблица
new_df = new_df[["id", "name", "sub_name", "price", "created", "raw", "user_id"]]

# Сохранение DataFrame в базу данных
new_df.to_sql("main", con=engine, if_exists="replace", index=False)
Dic_df.to_sql("category", con=engine, if_exists="replace", index=False)
