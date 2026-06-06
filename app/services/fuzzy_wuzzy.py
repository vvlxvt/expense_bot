from typing import Sequence

from rapidfuzz import process, fuzz


async def fuzzy_root(item: str, item_to_category: dict[str, str]) -> dict | None:
    """
    Ищет категорию по fuzzy-совпадению с известными товарами из словаря.

    :param item: название товара из сообщения пользователя
    :param item_to_category: словарь {item: category}
    """
    if not item_to_category:
        return None

    list_items: Sequence[str] = list(item_to_category.keys())

    match = process.extractOne(
        query=item,
        choices=list_items,
        scorer=fuzz.WRatio,
        score_cutoff=85,
    )

    if not match:
        return None

    matched_item, score, _index = match
    return {
        "category": item_to_category[matched_item],
        "matched_item": matched_item,
        "confidence": score / 100,
        "method": "fuzzy",
    }
