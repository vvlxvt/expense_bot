from rapidfuzz import process, fuzz

match = process.extractOne(
    item_name, data["exact"].keys(), scorer=fuzz.WRatio, score_cutoff=85
)

if match:
    return {
        "cat_id": data["exact"][match[0]],
        "confidence": match[1] / 100,
        "method": "fuzzy",
    }
