import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from app.ml.categorizer import categorizer
from app.database.db_manager import DB_Manager
from app.database.functions import get_items_with_categories
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model.pkl"


async def retrain_model(db: DB_Manager):
    async with db.get_session() as session:
        rows = await get_items_with_categories(session)
    if not rows:
        return
    df = pd.DataFrame(rows, columns=["item", "cat_id"])
    exact_dict = dict(zip(df["item"], df["cat_id"]))
    model = Pipeline(
        [
            ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 6))),
            ("clf", LogisticRegression(max_iter=1000)),
        ]
    )
    model.fit(df["item"], df["cat_id"])

    joblib.dump({"model": model, "exact": exact_dict}, MODEL_PATH)

    categorizer.reload()
    print(f"✅ Модель переобучена на {len(df)} записях")
