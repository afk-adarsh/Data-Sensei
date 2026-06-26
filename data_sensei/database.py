from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd


SUPPLEMENT_CONSUMPTION = [
    (1, "Aarav", 24, "Male", "Vijay Nagar", "FitZone Indore", "Whey Protein", "Protein", 3200, 2, "Muscle Gain", "Offline Store", "January"),
    (2, "Nisha", 27, "Female", "Palasia", "Iron Temple", "Creatine", "Performance", 1100, 1, "Strength", "Online", "January"),
    (3, "Rohan", 22, "Male", "Bhawarkuan", "Alpha Fitness", "Mass Gainer", "Protein", 2800, 2, "Weight Gain", "Offline Store", "January"),
    (4, "Meera", 31, "Female", "Annapurna", "Pulse Gym", "Multivitamin", "Wellness", 850, 1, "General Fitness", "Pharmacy", "January"),
    (5, "Kabir", 29, "Male", "Rau", "Beast Factory", "Pre Workout", "Performance", 1800, 1, "Energy", "Online", "January"),
    (6, "Isha", 26, "Female", "Saket", "FitZone Indore", "Whey Protein", "Protein", 3000, 2, "Fat Loss", "Online", "February"),
    (7, "Dev", 34, "Male", "Rajendra Nagar", "Powerhouse Gym", "Fish Oil", "Wellness", 950, 1, "Recovery", "Pharmacy", "February"),
    (8, "Tanvi", 23, "Female", "Vijay Nagar", "Anytime Fitness", "BCAA", "Performance", 1500, 1, "Recovery", "Offline Store", "February"),
    (9, "Samar", 28, "Male", "Palasia", "Iron Temple", "Whey Protein", "Protein", 3400, 2, "Muscle Gain", "Online", "February"),
    (10, "Pooja", 30, "Female", "MG Road", "Pulse Gym", "Fat Burner", "Weight Management", 1600, 1, "Fat Loss", "Online", "February"),
    (11, "Harsh", 21, "Male", "Bhawarkuan", "Alpha Fitness", "Creatine", "Performance", 1200, 1, "Strength", "Offline Store", "March"),
    (12, "Aditi", 25, "Female", "Annapurna", "Zen Fitness", "Whey Protein", "Protein", 2900, 1, "Muscle Gain", "Online", "March"),
    (13, "Yash", 32, "Male", "Rau", "Beast Factory", "Mass Gainer", "Protein", 3100, 2, "Weight Gain", "Offline Store", "March"),
    (14, "Kavya", 24, "Female", "Saket", "Anytime Fitness", "Multivitamin", "Wellness", 900, 1, "General Fitness", "Pharmacy", "March"),
    (15, "Mihir", 35, "Male", "Rajendra Nagar", "Powerhouse Gym", "Pre Workout", "Performance", 1900, 1, "Energy", "Offline Store", "March"),
    (16, "Sanya", 28, "Female", "Vijay Nagar", "FitZone Indore", "Collagen", "Wellness", 1400, 1, "Recovery", "Online", "April"),
    (17, "Arjun", 26, "Male", "Palasia", "Iron Temple", "Creatine", "Performance", 1150, 1, "Strength", "Online", "April"),
    (18, "Ritika", 33, "Female", "MG Road", "Pulse Gym", "Whey Protein", "Protein", 3100, 1, "Fat Loss", "Offline Store", "April"),
    (19, "Neil", 23, "Male", "Bhawarkuan", "Alpha Fitness", "Mass Gainer", "Protein", 3000, 2, "Weight Gain", "Online", "April"),
    (20, "Dia", 29, "Female", "Annapurna", "Zen Fitness", "BCAA", "Performance", 1450, 1, "Recovery", "Offline Store", "April"),
    (21, "Varun", 31, "Male", "Rau", "Beast Factory", "Whey Protein", "Protein", 3600, 2, "Muscle Gain", "Online", "May"),
    (22, "Simran", 22, "Female", "Saket", "Anytime Fitness", "Fat Burner", "Weight Management", 1550, 1, "Fat Loss", "Online", "May"),
    (23, "Manav", 27, "Male", "Rajendra Nagar", "Powerhouse Gym", "Creatine", "Performance", 1250, 1, "Strength", "Offline Store", "May"),
    (24, "Esha", 30, "Female", "Vijay Nagar", "FitZone Indore", "Fish Oil", "Wellness", 1000, 1, "General Fitness", "Pharmacy", "May"),
    (25, "Laksh", 25, "Male", "Palasia", "Iron Temple", "Pre Workout", "Performance", 2100, 1, "Energy", "Online", "May"),
    (26, "Rhea", 34, "Female", "MG Road", "Pulse Gym", "Collagen", "Wellness", 1500, 1, "Recovery", "Online", "June"),
    (27, "Om", 24, "Male", "Bhawarkuan", "Alpha Fitness", "Whey Protein", "Protein", 3300, 2, "Muscle Gain", "Offline Store", "June"),
    (28, "Tara", 26, "Female", "Annapurna", "Zen Fitness", "Multivitamin", "Wellness", 800, 1, "General Fitness", "Pharmacy", "June"),
    (29, "Kunal", 29, "Male", "Rau", "Beast Factory", "Mass Gainer", "Protein", 3400, 2, "Weight Gain", "Offline Store", "June"),
    (30, "Avni", 27, "Female", "Saket", "Anytime Fitness", "BCAA", "Performance", 1650, 1, "Recovery", "Online", "June"),
    (31, "Parth", 36, "Male", "Rajendra Nagar", "Powerhouse Gym", "Whey Protein", "Protein", 3500, 1, "Muscle Gain", "Offline Store", "July"),
    (32, "Kiara", 23, "Female", "Vijay Nagar", "FitZone Indore", "Fat Burner", "Weight Management", 1700, 1, "Fat Loss", "Online", "July"),
    (33, "Reyansh", 28, "Male", "Palasia", "Iron Temple", "Creatine", "Performance", 1300, 1, "Strength", "Online", "July"),
    (34, "Myra", 25, "Female", "MG Road", "Pulse Gym", "Whey Protein", "Protein", 3050, 1, "Fat Loss", "Offline Store", "July"),
    (35, "Vivaan", 30, "Male", "Bhawarkuan", "Alpha Fitness", "Pre Workout", "Performance", 2000, 1, "Energy", "Offline Store", "July"),
    (36, "Anika", 32, "Female", "Annapurna", "Zen Fitness", "Collagen", "Wellness", 1450, 1, "Recovery", "Online", "August"),
    (37, "Dhruv", 26, "Male", "Rau", "Beast Factory", "Whey Protein", "Protein", 3700, 2, "Muscle Gain", "Online", "August"),
    (38, "Sara", 29, "Female", "Saket", "Anytime Fitness", "Fish Oil", "Wellness", 950, 1, "General Fitness", "Pharmacy", "August"),
    (39, "Aryan", 24, "Male", "Rajendra Nagar", "Powerhouse Gym", "Mass Gainer", "Protein", 3200, 2, "Weight Gain", "Offline Store", "August"),
    (40, "Zoya", 28, "Female", "Vijay Nagar", "FitZone Indore", "Creatine", "Performance", 1200, 1, "Strength", "Online", "August"),
]


SCHEMA = "gym_supplement_consumption(id, customer_name, age, gender, area, gym_name, supplement, category, monthly_spend, quantity_per_month, goal, purchase_channel, month)"


DASHBOARD_QUESTIONS = [
    "Which supplement is consumed the most in Indore?",
    "What is the average monthly spend on whey protein?",
    "Show supplement consumption in Vijay Nagar",
    "How many people use creatine?",
    "Which area has the highest supplement spend?",
    "Show customers spending more than 3000",
]


def connect(database_path: str | Path = "data/supplements_indore.db") -> sqlite3.Connection:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(connection: sqlite3.Connection) -> None:
    connection.execute("DROP TABLE IF EXISTS gym_supplement_consumption")
    connection.execute(
        """
        CREATE TABLE gym_supplement_consumption (
            id INTEGER PRIMARY KEY,
            customer_name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            area TEXT NOT NULL,
            gym_name TEXT NOT NULL,
            supplement TEXT NOT NULL,
            category TEXT NOT NULL,
            monthly_spend INTEGER NOT NULL,
            quantity_per_month INTEGER NOT NULL,
            goal TEXT NOT NULL,
            purchase_channel TEXT NOT NULL,
            month TEXT NOT NULL
        )
        """
    )
    connection.executemany(
        """
        INSERT INTO gym_supplement_consumption
            (id, customer_name, age, gender, area, gym_name, supplement, category,
             monthly_spend, quantity_per_month, goal, purchase_channel, month)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        SUPPLEMENT_CONSUMPTION,
    )
    connection.commit()


def fetch_distinct_values(
    connection: sqlite3.Connection,
    table_name: str = "gym_supplement_consumption",
    columns: list[str] | None = None,
) -> dict[str, set[str]]:
    if columns is None:
        columns = [
            "area", "gym_name", "supplement", "category",
            "gender", "goal", "purchase_channel", "month"
        ]
        
    values: dict[str, set[str]] = {col: set() for col in columns}
    for column in columns:
        # Secure against basic injection, though column names are assumed safe
        safe_col = "".join(c for c in column if c.isalnum() or c == "_")
        safe_table = "".join(c for c in table_name if c.isalnum() or c == "_")
        
        rows = connection.execute(
            f"SELECT DISTINCT {safe_col} FROM {safe_table}"
        ).fetchall()
        values[column] = {str(row[0]).lower() for row in rows if row[0] is not None}
    return values


def execute_query(
    connection: sqlite3.Connection,
    sql: str,
    parameters: tuple[Any, ...] = (),
) -> list[dict[str, Any]]:
    cursor = connection.execute(sql, parameters)
    return [dict(row) for row in cursor.fetchall()]


def clean_numeric_column(series: pd.Series) -> pd.Series:
    non_nulls = series.dropna()
    if non_nulls.empty:
        return series
    
    if pd.api.types.is_numeric_dtype(series):
        return series
        
    # Clean whitespace, currency symbols (₹, $, €, £ etc.), commas, percent signs
    cleaned = non_nulls.astype(str).str.replace(r'[₹$€£,%\s]', '', regex=True)
    numeric_converted = pd.to_numeric(cleaned, errors='coerce')
    
    if len(non_nulls) > 0 and (numeric_converted.notna().sum() / len(non_nulls)) >= 0.8:
        cleaned_all = series.astype(str).str.replace(r'[₹$€£,%\s]', '', regex=True)
        # Preserve original NaN values
        cleaned_all = cleaned_all.mask(series.isna())
        return pd.to_numeric(cleaned_all, errors='coerce')
    
    return series


def generate_example_questions(df: pd.DataFrame, numeric_cols: list[str], categorical_cols: list[str]) -> list[str]:
    questions = []
    
    if categorical_cols:
        cat = categorical_cols[0]
        sample_vals = df[cat].dropna().unique()
        if len(sample_vals) > 0:
            val = sample_vals[0]
            questions.append(f"Show data where {cat} is {val}")
            
        if numeric_cols:
            num = numeric_cols[0]
            questions.append(f"Show total {num} by {cat}")
            
        if len(sample_vals) > 0 and len(numeric_cols) > 0:
            val = sample_vals[0]
            num = numeric_cols[0]
            questions.append(f"What is the average {num} for {cat} {val}?")
            
    if numeric_cols:
        num = numeric_cols[0]
        median_val = df[num].median()
        if not pd.isna(median_val):
            if median_val == int(median_val):
                median_val = int(median_val)
            else:
                median_val = round(float(median_val), 1)
            questions.append(f"Show records where {num} is greater than {median_val}")
            
    if numeric_cols:
        num = numeric_cols[0]
        questions.append(f"Which record has the highest {num}?")
        
    questions.append("How many records are in the database?")
    return questions


def load_csv_to_sqlite(
    csv_path_or_buffer: Any,
    connection: sqlite3.Connection,
    table_name: str = "dataset_table"
) -> dict[str, Any]:
    df = pd.read_csv(csv_path_or_buffer)
    
    cleaned_cols = {}
    for col in df.columns:
        # Clean column name to be SQL-safe (replace special characters/spaces with underscores)
        safe_col = col.strip().lower().replace(" ", "_")
        safe_col = "".join(c for c in safe_col if c.isalnum() or c == "_")
        cleaned_cols[safe_col] = clean_numeric_column(df[col])
        
    cleaned_df = pd.DataFrame(cleaned_cols)
    
    # Save to SQLite (if_exists="replace" handles dropping the table safely)
    cleaned_df.to_sql(table_name, connection, if_exists="replace", index=False)
    connection.commit()
    
    columns = cleaned_df.columns.tolist()
    numeric_columns = [col for col in columns if pd.api.types.is_numeric_dtype(cleaned_df[col])]
    text_columns = [col for col in columns if col not in numeric_columns]
    
    known_values = {}
    categorical_columns = []
    for col in text_columns:
        # Categorical columns should have reasonable cardinality
        unique_vals = cleaned_df[col].dropna().unique()
        if len(unique_vals) <= 300:
            categorical_columns.append(col)
            known_values[col] = {str(val).strip().lower() for val in unique_vals if str(val).strip()}
            
    default_numeric_col = None
    for col in numeric_columns:
        col_lower = col.lower()
        if any(kw in col_lower for kw in ["spend", "price", "cost", "total", "amount", "value", "quantity"]):
            default_numeric_col = col
            break
    if not default_numeric_col and numeric_columns:
        default_numeric_col = numeric_columns[0]
        
    default_categorical_col = None
    if categorical_columns:
        default_categorical_col = categorical_columns[0]
    elif text_columns:
        default_categorical_col = text_columns[0]
        
    dashboard_questions = generate_example_questions(cleaned_df, numeric_columns, categorical_columns)
    
    return {
        "table_name": table_name,
        "columns": columns,
        "numeric_columns": numeric_columns,
        "text_columns": text_columns,
        "categorical_columns": categorical_columns,
        "known_values": known_values,
        "default_numeric_col": default_numeric_col,
        "default_categorical_col": default_categorical_col,
        "dashboard_questions": dashboard_questions,
    }