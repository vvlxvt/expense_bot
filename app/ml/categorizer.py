import joblib
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model.pkl"
THRESHOLD = 0.16


@lru_cache(maxsize=1)
def _load_model():
    with open(MODEL_PATH, "rb") as f:
        return joblib.load(f)


class Categorizer:
    def predict(self, item_name: str) -> dict:
        data = _load_model()

        # Слой 1: точное совпадение
        if item_name in data["exact"]:
            return {
                "cat_id": data["exact"][item_name],
                "confidence": 1.0,
                "method": "exact",
            }

        # Слой 2: ml
        proba = data["model"].predict_proba([item_name])
        confidence = float(proba.max())
        cat_id = int(data["model"].classes_[proba.argmax()])

        if confidence >= THRESHOLD:
            return {"cat_id": cat_id, "confidence": confidence, "method": "ml"}
        else:
            return {"cat_id": None, "confidence": confidence, "method": "manual"}

    def reload(self):
        _load_model.cache_clear()


categorizer = Categorizer()
