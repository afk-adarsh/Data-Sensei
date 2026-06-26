from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from data_sensei.nlp import NLPAnalysis


TABLE_NAME = "gym_supplement_consumption"


@dataclass(frozen=True)
class SQLQuery:
    display_sql: str
    executable_sql: str
    parameters: tuple[Any, ...]


AGGREGATE_SELECTS = {
    "COUNT": "COUNT(*) AS customer_count",
    "AVG": "ROUND(AVG(monthly_spend), 2) AS average_monthly_spend",
    "SUM": "SUM(monthly_spend) AS total_monthly_spend",
    "MAX": "MAX(monthly_spend) AS highest_monthly_spend",
    "MIN": "MIN(monthly_spend) AS lowest_monthly_spend",
}


TEXT_FIELDS = (
    "area",
    "gym_name",
    "supplement",
    "category",
    "gender",
    "goal",
    "purchase_channel",
    "month",
)


def _literal(value: Any) -> str:
    if isinstance(value, str):
        display_value = value.title()
        return "'" + display_value.replace("'", "''") + "'"
    return str(value)


def _where_clause(
    entities: dict[str, Any],
    text_fields: list[str] = TEXT_FIELDS
) -> tuple[str, list[Any], list[str]]:
    clauses: list[str] = []
    parameters: list[Any] = []
    display_clauses: list[str] = []

    for field_name in text_fields:
        if field_name in entities:
            value = entities[field_name]
            clauses.append(f"{field_name} = ? COLLATE NOCASE")
            parameters.append(value)
            display_clauses.append(f"{field_name} = {_literal(value)}")

    for comparison in entities.get("comparisons", []):
        field_name = comparison["field"]
        operator = comparison["operator"]
        value = comparison["value"]
        clauses.append(f"{field_name} {operator} ?")
        parameters.append(value)
        display_clauses.append(f"{field_name} {operator} {value}")

    if not clauses:
        return "", parameters, display_clauses

    return " WHERE " + " AND ".join(clauses), parameters, display_clauses


def _display_sql(executable_sql: str, parameters: list[Any]) -> str:
    display_sql = executable_sql
    for parameter in parameters:
        display_sql = display_sql.replace("?", _literal(parameter), 1)
    return display_sql


def _contains_word(text: str, word: str) -> bool:
    import re
    pattern = r"\b" + re.escape(word.lower().replace("_", " ")) + r"\b"
    return re.search(pattern, text.lower()) is not None


def _metric_for_question(
    analysis: NLPAnalysis,
    numeric_columns: list[str],
    default_numeric_col: str
) -> tuple[str, str]:
    target_col = None
    for col in numeric_columns:
        if _contains_word(analysis.cleaned_text, col):
            target_col = col
            break
    if not target_col:
        for col in numeric_columns:
            col_lower = col.lower()
            if "price" in col_lower or "spend" in col_lower or "cost" in col_lower:
                if any(kw in analysis.cleaned_text for kw in ["price", "spend", "cost", "value"]):
                    target_col = col
                    break
            elif "rating" in col_lower:
                if any(kw in analysis.cleaned_text for kw in ["rating", "stars", "score"]):
                    target_col = col
                    break
            elif "count" in col_lower:
                if any(kw in analysis.cleaned_text for kw in ["count", "number"]):
                    target_col = col
                    break
    if not target_col:
        target_col = default_numeric_col
        
    text = analysis.cleaned_text
    if "quantity" in text or "consume" in analysis.lemmas or "consumed" in text:
        qty_col = next((c for c in numeric_columns if "quantity" in c.lower() or "unit" in c.lower() or "count" in c.lower()), target_col)
        return qty_col, f"SUM({qty_col})"
    if "customer" in analysis.lemmas or "people" in text or "how many" in text:
        return "*", "COUNT(*)"
        
    if analysis.intent == "AVG":
        return target_col, f"AVG({target_col})"
    elif analysis.intent == "COUNT":
        return "*", "COUNT(*)"
    return target_col, f"SUM({target_col})"


def generate_sql(
    analysis: NLPAnalysis,
    table_name: str = TABLE_NAME,
    text_columns: list[str] | None = None,
    numeric_columns: list[str] | None = None,
    default_numeric_col: str = "monthly_spend"
) -> SQLQuery:
    if text_columns is None:
        text_columns = list(TEXT_FIELDS)
    if numeric_columns is None:
        numeric_columns = ["monthly_spend", "quantity_per_month", "age"]

    where_clause, parameters, display_clauses = _where_clause(analysis.entities, text_columns)
    group_by = analysis.entities.get("group_by")

    if group_by:
        target_col, metric = _metric_for_question(analysis, numeric_columns, default_numeric_col)
        alias = "total_quantity" if "quantity" in metric.lower() or "count" in metric.lower() else "total_value"
        executable_sql = (
            f"SELECT {group_by}, {metric} AS {alias} "
            f"FROM {table_name}{where_clause} "
            f"GROUP BY {group_by} ORDER BY {alias} DESC;"
        )
        return SQLQuery(
            display_sql=_display_sql(executable_sql, parameters),
            executable_sql=executable_sql,
            parameters=tuple(parameters),
        )

    target_col = None
    for col in numeric_columns:
        if _contains_word(analysis.cleaned_text, col):
            target_col = col
            break
    if not target_col:
        for col in numeric_columns:
            col_lower = col.lower()
            if "spend" in col_lower or "price" in col_lower or "cost" in col_lower:
                if any(kw in analysis.cleaned_text for kw in ["spend", "price", "cost", "value"]):
                    target_col = col
                    break
            elif "rating" in col_lower:
                if any(kw in analysis.cleaned_text for kw in ["rating", "stars"]):
                    target_col = col
                    break
    if not target_col:
        target_col = default_numeric_col

    if analysis.intent == "COUNT":
        executable_sql = f"SELECT COUNT(*) AS customer_count FROM {table_name}{where_clause};"
    elif analysis.intent == "AVG":
        executable_sql = f"SELECT ROUND(AVG({target_col}), 2) AS average_{target_col} FROM {table_name}{where_clause};"
    elif analysis.intent == "SUM":
        executable_sql = f"SELECT SUM({target_col}) AS total_{target_col} FROM {table_name}{where_clause};"
    elif analysis.intent == "MAX":
        if any(word in analysis.cleaned_text for word in ("most", "popular", "consumed")) and any(c for c in text_columns if "supplement" in c or "product" in c):
            text_col = next((c for c in text_columns if "supplement" in c or "product" in c or "name" in c), text_columns[0])
            qty_col = next((c for c in numeric_columns if "quantity" in c or "count" in c), target_col)
            executable_sql = (
                f"SELECT {text_col}, SUM({qty_col}) AS total_quantity "
                f"FROM {table_name}{where_clause} "
                f"GROUP BY {text_col} ORDER BY total_quantity DESC LIMIT 5;"
            )
        else:
            executable_sql = f"SELECT * FROM {table_name}{where_clause} ORDER BY {target_col} DESC LIMIT 1;"
    elif analysis.intent == "MIN":
        executable_sql = f"SELECT * FROM {table_name}{where_clause} ORDER BY {target_col} ASC LIMIT 1;"
    else:
        executable_sql = f"SELECT * FROM {table_name}{where_clause} ORDER BY {target_col} DESC;"

    display_sql = _display_sql(executable_sql, parameters)
    return SQLQuery(
        display_sql=display_sql,
        executable_sql=executable_sql,
        parameters=tuple(parameters),
    )