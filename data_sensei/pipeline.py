from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from data_sensei.database import (
    connect,
    execute_query,
    fetch_distinct_values,
    initialize_database,
)
from data_sensei.nlp import NLPAnalysis, analyze
from data_sensei.sql_generator import SQLQuery, generate_sql


@dataclass(frozen=True)
class QueryResult:
    analysis: NLPAnalysis
    sql: SQLQuery
    rows: list[dict[str, Any]]


class QueryPipeline:
    def __init__(
        self,
        database_path: str | Path = "data/supplements_indore.db",
        connection: sqlite3.Connection | None = None,
    ) -> None:
        self.connection = connection or connect(database_path)
        initialize_database(self.connection)
        
        # Default metadata for Gym Supplement Consumption
        self.table_name = "gym_supplement_consumption"
        self.columns = [
            "id", "customer_name", "age", "gender", "area", "gym_name",
            "supplement", "category", "monthly_spend", "quantity_per_month",
            "goal", "purchase_channel", "month"
        ]
        self.numeric_columns = ["age", "monthly_spend", "quantity_per_month"]
        self.text_columns = [
            "customer_name", "gender", "area", "gym_name", "supplement",
            "category", "goal", "purchase_channel", "month"
        ]
        self.categorical_columns = [
            "gender", "area", "gym_name", "supplement", "category",
            "goal", "purchase_channel", "month"
        ]
        self.known_values = fetch_distinct_values(self.connection)
        self.default_numeric_col = "monthly_spend"
        self.default_categorical_col = "supplement"
        self.dashboard_questions = [
            "Which supplement is consumed the most in Indore?",
            "What is the average monthly spend on whey protein?",
            "Show supplement consumption in Vijay Nagar",
            "How many people use creatine?",
            "Which area has the highest supplement spend?",
            "Show customers spending more than 3000",
        ]

    def load_csv(self, csv_path_or_buffer: Any, table_name: str = "dataset_table") -> None:
        from data_sensei.database import load_csv_to_sqlite
        meta = load_csv_to_sqlite(csv_path_or_buffer, self.connection, table_name)
        
        self.table_name = meta["table_name"]
        self.columns = meta["columns"]
        self.numeric_columns = meta["numeric_columns"]
        self.text_columns = meta["text_columns"]
        self.categorical_columns = meta["categorical_columns"]
        self.known_values = meta["known_values"]
        self.default_numeric_col = meta["default_numeric_col"]
        self.default_categorical_col = meta["default_categorical_col"]
        self.dashboard_questions = meta["dashboard_questions"]

    def run(self, question: str) -> QueryResult:
        if not question.strip():
            raise ValueError("Please enter a natural language question.")

        analysis = analyze(
            question,
            known_values=self.known_values,
            numeric_columns=self.numeric_columns
        )
        sql = generate_sql(
            analysis,
            table_name=self.table_name,
            text_columns=self.text_columns,
            numeric_columns=self.numeric_columns,
            default_numeric_col=self.default_numeric_col
        )
        rows = execute_query(self.connection, sql.executable_sql, sql.parameters)
        return QueryResult(analysis=analysis, sql=sql, rows=rows)

    def dataset(self) -> list[dict[str, Any]]:
        return execute_query(self.connection, f"SELECT * FROM {self.table_name}")

    def dashboard_metrics(self) -> dict[str, Any]:
        if self.table_name == "gym_supplement_consumption":
            rows = execute_query(
                self.connection,
                """
                SELECT
                    COUNT(*) AS customers,
                    SUM(monthly_spend) AS total_spend,
                    ROUND(AVG(monthly_spend), 2) AS average_spend,
                    SUM(quantity_per_month) AS total_units
                FROM gym_supplement_consumption
                """,
            )
            return rows[0]
            
        num_cols = self.numeric_columns
        avg_col = self.default_numeric_col
        
        selects = ["COUNT(*) AS total_records"]
        if avg_col:
            selects.append(f"ROUND(AVG({avg_col}), 2) AS average_value")
            selects.append(f"SUM({avg_col}) AS total_value")
            
        sec_col = next((c for c in num_cols if c != avg_col), None)
        if sec_col:
            selects.append(f"ROUND(AVG({sec_col}), 2) AS secondary_value")
        elif avg_col:
            selects.append(f"MAX({avg_col}) AS max_value")
            
        query_str = f"SELECT {', '.join(selects)} FROM {self.table_name}"
        rows = execute_query(self.connection, query_str)
        return rows[0] if rows else {}

    def grouped(self, dimension: str, metric: str = "monthly_spend") -> list[dict[str, Any]]:
        if self.table_name == "gym_supplement_consumption":
            allowed_dimensions = {
                "area",
                "supplement",
                "category",
                "goal",
                "purchase_channel",
                "month",
            }
            if dimension not in allowed_dimensions:
                raise ValueError(f"Unsupported dashboard dimension: {dimension}")

            if metric == "quantity_per_month":
                select_metric = "SUM(quantity_per_month) AS total_quantity"
                order_column = "total_quantity"
            elif metric == "count":
                select_metric = "COUNT(*) AS customer_count"
                order_column = "customer_count"
            else:
                select_metric = "SUM(monthly_spend) AS total_spend"
                order_column = "total_spend"

            return execute_query(
                self.connection,
                f"""
                SELECT {dimension}, {select_metric}
                FROM gym_supplement_consumption
                GROUP BY {dimension}
                ORDER BY {order_column} DESC
                """,
            )
            
        if dimension not in self.columns:
            raise ValueError(f"Dimension {dimension} not found in dataset columns.")
            
        if metric == "count":
            select_metric = "COUNT(*) AS count_value"
            order_column = "count_value"
        else:
            if metric not in self.numeric_columns:
                metric = self.default_numeric_col or self.numeric_columns[0]
            select_metric = f"SUM({metric}) AS sum_value"
            order_column = "sum_value"
            
        return execute_query(
            self.connection,
            f"""
            SELECT {dimension}, {select_metric}
            FROM {self.table_name}
            GROUP BY {dimension}
            ORDER BY {order_column} DESC
            LIMIT 20
            """,
        )