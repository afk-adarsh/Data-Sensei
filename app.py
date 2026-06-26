from __future__ import annotations

import pandas as pd
import streamlit as st

from data_sensei.database import SCHEMA
from data_sensei.pipeline import QueryPipeline


@st.cache_resource
def get_pipeline() -> QueryPipeline:
    return QueryPipeline()


def frame_from_rows(rows: list[dict[str, object]]) -> pd.DataFrame:
    return pd.DataFrame(rows)


st.set_page_config(page_title="Data-Sensei", page_icon="DS", layout="wide")

pipeline = get_pipeline()

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.header("Select Dataset")
    dataset_option = st.selectbox(
        "Active Dataset",
        [
            "Gym Supplement Consumption (Indore)",
            "Amazon Sales Dataset (Preloaded)",
            "Upload Custom CSV File..."
        ]
    )

    uploaded_file = None
    
    # 📖 NLP Methods & Concepts
    with st.sidebar.expander("ℹ️ NLP Methods & Concepts"):
        st.markdown(
            """
**NLP Pipeline Overview**
- **Cleaning & Normalization**: lower‑casing, punctuation removal.
- **Tokenization**: splits the query into word tokens.
- **Stop‑word Filtering**: removes common words.
- **Lemmatization**: reduces tokens to their base form.
- **Intent Detection**: classifies the query into `SELECT`, `AGGREGATE`, `COUNT`, etc.
- **Entity Extraction**: identifies column names, values, and comparison operators.
- **Dynamic Value Matching**: maps known dataset values to user‑provided terms.
"""
        )
    
    if dataset_option == "Upload Custom CSV File...":
        uploaded_file = st.file_uploader("Upload your business CSV dataset", type=["csv"])

    # Load the selected dataset into the pipeline
    if dataset_option == "Gym Supplement Consumption (Indore)":
        if st.session_state.get("loaded_dataset") != "gym":
            pipeline.__init__()  # Reset to default
            st.session_state["loaded_dataset"] = "gym"
            st.session_state["question"] = pipeline.dashboard_questions[0]
            
    elif dataset_option == "Amazon Sales Dataset (Preloaded)":
        if st.session_state.get("loaded_dataset") != "amazon":
            try:
                pipeline.load_csv("data/amazon.csv", table_name="amazon_sales")
                st.session_state["loaded_dataset"] = "amazon"
                st.session_state["question"] = pipeline.dashboard_questions[0]
            except Exception as e:
                st.error(f"Error loading Amazon dataset: {e}")
                
    elif dataset_option == "Upload Custom CSV File..." and uploaded_file is not None:
        file_id = f"custom_{uploaded_file.name}_{uploaded_file.size}"
        if st.session_state.get("loaded_dataset_id") != file_id:
            try:
                pipeline.load_csv(uploaded_file, table_name="custom_dataset")
                st.session_state["loaded_dataset"] = "custom"
                st.session_state["loaded_dataset_id"] = file_id
                st.session_state["question"] = pipeline.dashboard_questions[0]
            except Exception as e:
                st.error(f"Error parsing uploaded file: {e}")

    # Generate schema view dynamically
    try:
        cursor = pipeline.connection.execute(f"PRAGMA table_info({pipeline.table_name})")
        schema_rows = cursor.fetchall()
        schema_lines = []
        for r in schema_rows:
            col_name = r[1]
            col_type = r[2]
            schema_lines.append(f"    {col_name} {col_type}")
        active_schema = f"{pipeline.table_name}(\n" + ",\n".join(schema_lines) + "\n)"
    except Exception:
        active_schema = SCHEMA if dataset_option == "Gym Supplement Consumption (Indore)" else "Table details unavailable"

    st.header("Dataset Schema")
    st.code(active_schema, language="sql")
    
    if dataset_option == "Gym Supplement Consumption (Indore)":
        st.caption("Synthetic classroom dataset generated for Indore supplement-consumption analysis.")
    elif dataset_option == "Amazon Sales Dataset (Preloaded)":
        st.caption("Amazon Sales Dataset from archive.zip featuring products, categories, pricing, ratings, and reviews.")
    else:
        st.caption("Custom user uploaded CSV dataset loaded into dynamic SQLite instance.")

    st.header("Ask A Question")
    selected_question = st.radio(
        "Examples",
        pipeline.dashboard_questions,
        label_visibility="collapsed",
    )

# ----------------- MAIN LAYOUT -----------------
st.title("Data-Sensei 🧠")
if dataset_option == "Gym Supplement Consumption (Indore)":
    st.caption("Natural Language Dashboard for Gym Supplement Consumption in Indore")
elif dataset_option == "Amazon Sales Dataset (Preloaded)":
    st.caption("Natural Language Dashboard for Amazon Sales Dataset")
else:
    st.caption(f"Natural Language Dashboard for Custom Dataset: {uploaded_file.name if uploaded_file else 'No file uploaded'}")

# Load Metrics
try:
    metrics = pipeline.dashboard_metrics()
except Exception as e:
    metrics = {}
    st.error(f"Error loading metrics: {e}")

# Render KPI Cards
metric_cols = st.columns(4)
if metrics:
    if pipeline.table_name == "gym_supplement_consumption":
        metric_cols[0].metric("Consumers", f"{metrics.get('customers', 0)}")
        metric_cols[1].metric("Monthly Spend", f"₹{metrics.get('total_spend', 0):,}")
        metric_cols[2].metric("Avg Spend", f"₹{metrics.get('average_spend', 0.0):,.0f}")
        metric_cols[3].metric("Units / Month", f"{metrics.get('total_units', 0)}")
    else:
        total_records = metrics.get("total_records", 0)
        avg_val = metrics.get("average_value", 0.0) or 0.0
        tot_val = metrics.get("total_value", 0.0) or 0.0
        
        avg_col_name = (pipeline.default_numeric_col or "Value").replace("_", " ").title()
        metric_cols[0].metric("Total Records", f"{total_records:,}")
        metric_cols[1].metric(f"Avg {avg_col_name}", f"₹{avg_val:,.2f}" if "price" in avg_col_name.lower() or "spend" in avg_col_name.lower() else f"{avg_val:,.2f}")
        metric_cols[2].metric(f"Total {avg_col_name}", f"₹{tot_val:,.0f}" if "price" in avg_col_name.lower() or "spend" in avg_col_name.lower() else f"{tot_val:,.0f}")
        
        if "secondary_value" in metrics:
            sec_col_name = next((c for c in pipeline.numeric_columns if c != pipeline.default_numeric_col), "Secondary").replace("_", " ").title()
            sec_val = metrics.get("secondary_value", 0.0) or 0.0
            metric_cols[3].metric(f"Avg {sec_col_name}", f"{sec_val:,.2f}")
        elif "max_value" in metrics:
            max_val = metrics.get("max_value", 0.0) or 0.0
            metric_cols[3].metric(f"Max {avg_col_name}", f"{max_val:,.2f}")
        else:
            metric_cols[3].metric("Total Columns", f"{len(pipeline.columns)}")

# Render Charts
if pipeline.table_name == "gym_supplement_consumption":
    chart_col, area_col = st.columns([1.2, 1])
    
    with chart_col:
        st.subheader("Top Supplements By Monthly Consumption")
        supplement_quantity = frame_from_rows(pipeline.grouped("supplement", "quantity_per_month"))
        st.bar_chart(supplement_quantity, x="supplement", y="total_quantity", use_container_width=True)
    
    with area_col:
        st.subheader("Area-Wise Supplement Spend")
        area_spend = frame_from_rows(pipeline.grouped("area", "monthly_spend"))
        st.bar_chart(area_spend, x="area", y="total_spend", use_container_width=True)
    
    second_chart_col, channel_col = st.columns([1, 1])
    
    with second_chart_col:
        st.subheader("Category Spend")
        category_spend = frame_from_rows(pipeline.grouped("category", "monthly_spend"))
        st.bar_chart(category_spend, x="category", y="total_spend", use_container_width=True)
    
    with channel_col:
        st.subheader("Purchase Channel Split")
        channel_count = frame_from_rows(pipeline.grouped("purchase_channel", "count"))
        st.bar_chart(channel_count, x="purchase_channel", y="customer_count", use_container_width=True)
else:
    # Render Dynamic Dashboard Charts
    st.markdown("---")
    chart_col1, chart_col2 = st.columns([1.1, 1])
    
    with chart_col1:
        st.subheader("📊 Interactive Chart")
        
        # Determine options
        cat_options = pipeline.categorical_columns or pipeline.text_columns or pipeline.columns
        num_options = ["Count of Records"] + pipeline.numeric_columns
        
        c1, c2, c3 = st.columns(3)
        with c1:
            group_col = st.selectbox("Group By (X-axis)", cat_options, key="int_group_col")
        with c2:
            val_col = st.selectbox("Metric (Y-axis)", num_options, key="int_val_col")
        with c3:
            is_count = (val_col == "Count of Records")
            agg_type = st.selectbox(
                "Aggregation",
                ["COUNT"] if is_count else ["SUM", "AVG"],
                key="int_agg_type",
                disabled=is_count
            )
            
        try:
            if is_count:
                df_chart = frame_from_rows(pipeline.grouped(group_col, metric="count"))
                df_chart.columns = [group_col, "Count"]
                st.bar_chart(df_chart, x=group_col, y="Count", use_container_width=True)
            else:
                agg_func = "AVG" if agg_type == "AVG" else "SUM"
                rows = pipeline.connection.execute(
                    f"SELECT {group_col}, {agg_func}({val_col}) AS val_field "
                    f"FROM {pipeline.table_name} "
                    f"GROUP BY {group_col} "
                    f"ORDER BY val_field DESC "
                    f"LIMIT 15"
                ).fetchall()
                df_chart = pd.DataFrame([dict(r) for r in rows])
                if not df_chart.empty:
                    y_label = f"{agg_type} of {val_col.replace('_', ' ').title()}"
                    df_chart.columns = [group_col, y_label]
                    st.bar_chart(df_chart, x=group_col, y=y_label, use_container_width=True)
                else:
                    st.info("No data returned for selected groupings.")
        except Exception as e:
            st.error(f"Failed to generate interactive chart: {e}")
            
    with chart_col2:
        st.subheader("📈 Category Overview")
        if pipeline.categorical_columns:
            overview_group = pipeline.categorical_columns[0]
            if pipeline.numeric_columns:
                overview_num = pipeline.default_numeric_col or pipeline.numeric_columns[0]
                
                st.markdown(f"**Average {overview_num.replace('_', ' ').title()} by {overview_group.replace('_', ' ').title()}**")
                try:
                    rows = pipeline.connection.execute(
                        f"SELECT {overview_group}, AVG({overview_num}) AS avg_val "
                        f"FROM {pipeline.table_name} "
                        f"GROUP BY {overview_group} "
                        f"ORDER BY avg_val DESC "
                        f"LIMIT 15"
                    ).fetchall()
                    df_over = pd.DataFrame([dict(r) for r in rows])
                    if not df_over.empty:
                        y_label = f"Avg {overview_num.replace('_', ' ').title()}"
                        df_over.columns = [overview_group, y_label]
                        st.bar_chart(df_over, x=overview_group, y=y_label, use_container_width=True)
                    else:
                        st.info("No data available.")
                except Exception as e:
                    st.error(f"Failed to render overview chart: {e}")
            else:
                st.markdown(f"**Record Count by {overview_group.replace('_', ' ').title()}**")
                try:
                    df_over = frame_from_rows(pipeline.grouped(overview_group, metric="count"))
                    df_over.columns = [overview_group, "Count"]
                    st.bar_chart(df_over, x=overview_group, y="Count", use_container_width=True)
                except Exception as e:
                    st.error(f"Failed to render overview count chart: {e}")
        else:
            st.info("Overview chart unavailable: No categorical columns detected.")

# ----------------- NL QUERY RUNNER -----------------
st.markdown("---")
st.subheader("💬 Natural Language Query Runner")
# Optionally show NLP details alongside the runner
with st.expander("Show NLP Methods & Concepts"):
    st.markdown(
        """
**How the query is processed**
- The raw question is **cleaned** (lower‑cased, punctuation stripped).
- It is **tokenized** into individual words.
- **Stop‑words** are filtered out.
- Tokens are **lemmatized** to their root forms.
- An **intent** is inferred (e.g., `SELECT`, `COUNT`, `AGGREGATE`).
- **Entities** such as column names and known values are extracted.
- These pieces are fed to the **SQL generator** to produce the final query.
"""
    )

default_question = st.session_state.get("question", selected_question)
if selected_question != st.session_state.get("prev_selected_question"):
    default_question = selected_question
    st.session_state["prev_selected_question"] = selected_question

question = st.text_input("Ask your question about the active dataset", value=default_question)

if st.button("Run Analytics", type="primary") or question:
    st.session_state["question"] = question
    try:
        result = pipeline.run(question)
    except ValueError as error:
        st.warning(str(error))
    except Exception as error:
        st.error(f"Pipeline error: {error}")
    else:
        sql_col, nlp_col = st.columns([1.15, 1])

        with sql_col:
            st.write("🔧 Generated SQL Query")
            st.code(result.sql.display_sql, language="sql")

            st.write("📊 Query Results")
            if result.rows:
                st.dataframe(frame_from_rows(result.rows), use_container_width=True)
                st.caption(f"{len(result.rows)} record(s) returned")
            else:
                st.info("No matching records found.")

        with nlp_col:
            st.write("🔬 NLP Tokenizer & Intent Analysis")
            st.json(
                {
                    "cleaned_query": result.analysis.cleaned_text,
                    "tokens": result.analysis.tokens,
                    "filtered_tokens": result.analysis.filtered_tokens,
                    "lemmas": result.analysis.lemmas,
                    "intent": result.analysis.intent,
                    "entities": result.analysis.entities,
                }
            )

# ----------------- DATA EXPLORER -----------------
try:
    dataset_df = frame_from_rows(pipeline.dataset())
except Exception:
    dataset_df = pd.DataFrame()

with st.expander("🔍 View Raw Dataset (First 100 Rows)"):
    if not dataset_df.empty:
        st.dataframe(dataset_df.head(100), use_container_width=True)
    else:
        st.info("Dataset is empty or file not uploaded yet.")