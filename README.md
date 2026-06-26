# Data-Sensei

Data-Sensei is a natural language to SQL dashboard for synthetic gym supplement consumption data in Indore. It demonstrates a complete NLP pipeline: preprocessing, tokenization, stop-word removal, lemmatization, intent detection, entity extraction, SQL generation, SQLite execution, and dashboard display.

## Features

- Generates a synthetic Indore supplement-consumption dataset.
- Tracks area, gym, supplement, category, monthly spend, quantity, goal, purchase channel, and month.
- Converts natural-language questions into SQL.
- Supports filtered records, counts, averages, totals, highest values, and grouped ranking queries.
- Displays KPIs and charts in a Streamlit dashboard.
- Shows NLP details so the project is easy to explain for an NLP assignment.

## Example Questions

- `Which supplement is consumed the most in Indore?`
- `What is the average monthly spend on whey protein?`
- `Show supplement consumption in Vijay Nagar`
- `How many people use creatine?`
- `Which area has the highest supplement spend?`
- `Show customers spending more than 3000`

## Project Structure

```text
Data-Sensei/
  app.py
  data_sensei/
    database.py
    nlp.py
    pipeline.py
    sql_generator.py
  tests/
    test_pipeline.py
  requirements.txt
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run The Dashboard

```bash
streamlit run app.py
```

The app automatically creates and seeds `data/supplements_indore.db` on startup.

## Run Tests

```bash
python -m unittest discover -s tests
```

## Dataset Schema

```sql
gym_supplement_consumption(
  id,
  customer_name,
  age,
  gender,
  area,
  gym_name,
  supplement,
  category,
  monthly_spend,
  quantity_per_month,
  goal,
  purchase_channel,
  month
)
```

## NLP Pipeline

1. Text preprocessing converts input to lowercase and removes punctuation.
2. Tokenization splits the cleaned query into words.
3. Stop-word removal keeps meaningful terms.
4. Lemmatization normalizes forms such as `supplements` to `supplement`.
5. Intent detection identifies `SELECT`, `COUNT`, `AVG`, `SUM`, `MAX`, or `MIN`.
6. Entity extraction finds areas, supplements, categories, goals, channels, months, and numeric filters.
7. SQL generation builds a parameterized SQLite query.
8. The dashboard displays generated SQL, query results, NLP details, KPIs, and charts.

## Note

The dataset is synthetic and designed for classroom demonstration. It should be presented as generated sample data, not as a real survey of Indore consumers.