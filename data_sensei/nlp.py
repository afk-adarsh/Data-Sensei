from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


STOP_WORDS = {
    "a",
    "all",
    "an",
    "are",
    "by",
    "do",
    "does",
    "for",
    "from",
    "has",
    "have",
    "in",
    "is",
    "me",
    "of",
    "on",
    "show",
    "tell",
    "the",
    "to",
    "use",
    "uses",
    "using",
    "what",
    "which",
    "who",
    "with",
}


INTENT_KEYWORDS = {
    "COUNT": {"count", "many", "number", "total", "people", "customers"},
    "AVG": {"average", "avg", "mean"},
    "SUM": {"sum", "total", "overall"},
    "MAX": {"maximum", "max", "highest", "largest", "top", "most"},
    "MIN": {"minimum", "min", "lowest", "smallest", "least"},
}


COMPARISON_PHRASES = [
    (
        r"(?:monthly spend|spend|spending|cost|expense|price)\s+(?:is\s+)?(?:greater than|more than|above|over|>)\s+(\d+)",
        "monthly_spend",
        ">",
    ),
    (
        r"(?:monthly spend|spend|spending|cost|expense|price)\s+(?:is\s+)?(?:less than|below|under|<)\s+(\d+)",
        "monthly_spend",
        "<",
    ),
    (
        r"(?:monthly spend|spend|spending|cost|expense|price)\s+(?:is\s+)?(?:equal to|equals|=)\s+(\d+)",
        "monthly_spend",
        "=",
    ),
    (
        r"(?:quantity|units|packs)\s+(?:is\s+)?(?:greater than|more than|above|over|>)\s+(\d+)",
        "quantity_per_month",
        ">",
    ),
    (
        r"(?:quantity|units|packs)\s+(?:is\s+)?(?:less than|below|under|<)\s+(\d+)",
        "quantity_per_month",
        "<",
    ),
    (r"(?:older than|age greater than|age above|age over|age >)\s+(\d+)", "age", ">"),
    (r"(?:younger than|age less than|age below|age under|age <)\s+(\d+)", "age", "<"),
]


@dataclass(frozen=True)
class NLPAnalysis:
    original_text: str
    cleaned_text: str
    tokens: list[str]
    filtered_tokens: list[str]
    lemmas: list[str]
    intent: str
    entities: dict[str, Any] = field(default_factory=dict)


def clean_text(text: str) -> str:
    lowered = text.lower().strip()
    without_punctuation = re.sub(r"[^a-z0-9\s<>=]", " ", lowered)
    return re.sub(r"\s+", " ", without_punctuation).strip()


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9<>=]+", text.lower())


def remove_stop_words(tokens: list[str]) -> list[str]:
    return [token for token in tokens if token not in STOP_WORDS]


def lemmatize_token(token: str) -> str:
    irregular = {
        "consumed": "consume",
        "consumes": "consume",
        "consumption": "consume",
        "customers": "customer",
        "gyms": "gym",
        "people": "person",
        "spending": "spend",
        "supplements": "supplement",
        "using": "use",
    }
    if token in irregular:
        return irregular[token]
    if len(token) > 4 and token.endswith("ies"):
        return f"{token[:-3]}y"
    if len(token) > 4 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


def lemmatize(tokens: list[str]) -> list[str]:
    return [lemmatize_token(token) for token in tokens]


def detect_intent(tokens: list[str], cleaned_text: str) -> str:
    token_set = set(tokens)
    if "average" in token_set or "avg" in token_set or "mean" in token_set:
        return "AVG"
    if "how many" in cleaned_text:
        return "COUNT"
    if "most consumed" in cleaned_text or "consumed the most" in cleaned_text:
        return "MAX"
    if any(w in token_set for w in ("show", "list", "select", "display")):
        if "count" in token_set or "number" in token_set:
            return "COUNT"
        return "SELECT"
    for intent, keywords in INTENT_KEYWORDS.items():
        if token_set & keywords:
            return intent
    return "SELECT"


def _contains_phrase(cleaned_text: str, value: str) -> bool:
    pattern = r"\b" + re.escape(value.lower()) + r"\b"
    return re.search(pattern, cleaned_text) is not None


def build_comparison_phrases(numeric_columns: list[str] | None = None) -> list[tuple[str, str, str]]:
    if numeric_columns is None:
        return COMPARISON_PHRASES
        
    phrases = []
    for col in numeric_columns:
        friendly_col = col.replace("_", " ")
        synonyms = [col, friendly_col]
        col_lower = col.lower()
        if "spend" in col_lower or "price" in col_lower or "cost" in col_lower:
            synonyms.extend(["spend", "spending", "cost", "expense", "price", "value", "amount"])
        elif "quantity" in col_lower or "units" in col_lower:
            synonyms.extend(["quantity", "units", "packs", "count", "amount"])
        elif "age" in col_lower:
            synonyms.extend(["age", "old", "years"])
        elif "rating" in col_lower:
            synonyms.extend(["rating", "stars", "score"])
            
        synonyms = sorted(list(set(synonyms)), key=len, reverse=True)
        synonyms_pattern = "|".join(re.escape(syn) for syn in synonyms)
        
        # Greater than:
        gt_pattern = rf"(?:{synonyms_pattern})\s+(?:is\s+)?(?:greater than|more than|above|over|>)\s+([0-9.]+)"
        phrases.append((gt_pattern, col, ">"))
        # Less than:
        lt_pattern = rf"(?:{synonyms_pattern})\s+(?:is\s+)?(?:less than|below|under|<)\s+([0-9.]+)"
        phrases.append((lt_pattern, col, "<"))
        # Equal to:
        eq_pattern = rf"(?:{synonyms_pattern})\s+(?:is\s+)?(?:equal to|equals|=)\s+([0-9.]+)"
        phrases.append((eq_pattern, col, "="))
        
    return phrases


def extract_entities(
    cleaned_text: str,
    known_values: dict[str, set[str]],
    comparison_phrases: list[tuple[str, str, str]] | None = None,
) -> dict[str, Any]:
    entities: dict[str, Any] = {}

    for entity_type in known_values.keys():
        matches = sorted(
            value for value in known_values.get(entity_type, set()) if _contains_phrase(cleaned_text, value)
        )
        if matches:
            entities[entity_type] = matches[0]

    comparisons = []
    phrases = comparison_phrases if comparison_phrases is not None else COMPARISON_PHRASES
    for pattern, field_name, operator in phrases:
        for match in re.finditer(pattern, cleaned_text):
            val_str = match.group(1)
            val = float(val_str) if "." in val_str else int(val_str)
            comparisons.append(
                {"field": field_name, "operator": operator, "value": val}
            )

    if comparisons:
        entities["comparisons"] = comparisons

    # Group by detection:
    detected_group_by = None
    for col in known_values.keys():
        col_friendly = col.replace("_", " ")
        patterns = [
            rf"\bby\s+{re.escape(col)}\b",
            rf"\bby\s+{re.escape(col_friendly)}\b",
            rf"\bgroup(?:ed)?\s+by\s+{re.escape(col)}\b",
            rf"\bgroup(?:ed)?\s+by\s+{re.escape(col_friendly)}\b",
            rf"\btop\s+{re.escape(col)}\b",
            rf"\btop\s+{re.escape(col_friendly)}\b",
            rf"\bpopular\s+{re.escape(col)}\b",
            rf"\bpopular\s+{re.escape(col_friendly)}\b"
        ]
        if any(re.search(pat, cleaned_text) for pat in patterns):
            detected_group_by = col
            break

    if detected_group_by:
        entities["group_by"] = detected_group_by
    else:
        # Fallback to Indore gym supplement hardcoded group_by logic
        if "area" in cleaned_text and any(word in cleaned_text for word in ("highest", "top", "most", "by area")):
            entities["group_by"] = "area"
        elif "channel" in cleaned_text or "online" in cleaned_text or "offline" in cleaned_text:
            if "by" in cleaned_text or "split" in cleaned_text:
                entities["group_by"] = "purchase_channel"
        elif "goal" in cleaned_text and ("by" in cleaned_text or "top" in cleaned_text):
            entities["group_by"] = "goal"
        elif any(word in cleaned_text for word in ("most consumed", "popular", "top supplement", "consumed the most")):
            entities["group_by"] = "supplement"

    return entities


def analyze(
    text: str,
    known_values: dict[str, set[str]],
    numeric_columns: list[str] | None = None,
) -> NLPAnalysis:
    cleaned_text = clean_text(text)
    tokens = tokenize(cleaned_text)
    filtered_tokens = remove_stop_words(tokens)
    lemmas = lemmatize(filtered_tokens)
    intent = detect_intent(tokens + lemmas, cleaned_text)
    
    comparison_phrases = build_comparison_phrases(numeric_columns) if numeric_columns is not None else None
    entities = extract_entities(cleaned_text, known_values, comparison_phrases)

    return NLPAnalysis(
        original_text=text,
        cleaned_text=cleaned_text,
        tokens=tokens,
        filtered_tokens=filtered_tokens,
        lemmas=lemmas,
        intent=intent,
        entities=entities,
    )