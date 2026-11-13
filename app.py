import io
import sqlite3
from datetime import datetime, timezone

import matplotlib.pyplot as plt  # type: ignore[reportMissingModuleSource]
import pandas as pd  # type: ignore[reportMissingModuleSource]
import streamlit as st  # type: ignore[reportMissingImports]

DB_PATH = "analysis_history.db"
MAX_FILE_MB = 20

st.set_page_config(page_title="Smart CSV Analyzer", page_icon="📊", layout="wide")

def init_db():
    """Create a small metadata-only history table. Uploaded data is not stored."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                row_count INTEGER NOT NULL,
                column_count INTEGER NOT NULL,
                missing_cells INTEGER NOT NULL,
                duplicate_rows INTEGER NOT NULL,
                analyzed_at TEXT NOT NULL
            )
        """)

def save_history(file_name, df):
    missing_cells = int(df.isna().sum().sum())
    duplicate_rows = int(df.duplicated().sum())
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """INSERT INTO analysis_history
               (file_name, row_count, column_count, missing_cells, duplicate_rows, analyzed_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                file_name,
                int(df.shape[0]),
                int(df.shape[1]),
                missing_cells,
                duplicate_rows,
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            ),
        )

def read_csv_safely(uploaded_file):
    """Read CSV with a small encoding fallback and clear errors."""
    raw = uploaded_file.getvalue()
    try:
        return pd.read_csv(io.BytesIO(raw))
    except UnicodeDecodeError:
        return pd.read_csv(io.BytesIO(raw), encoding="latin-1")

def main():
    init_db()
    st.title("📊 Smart CSV Analyzer")
    st.caption("Upload a CSV, inspect data quality, explore columns and download a cleaned copy.")

    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

    if uploaded_file is None:
        st.info("Upload a CSV file to begin. Try the sample file in the project's data folder.")
        with st.expander("What this app does"):
            st.write("- Previews rows and columns")
            st.write("- Summarizes data types and missing values")
            st.write("- Detects duplicate rows")
            st.write("- Creates simple charts")
            st.write("- Lets you clean and download a CSV")
            st.write("- Stores analysis metadata in SQLite, not the uploaded file")
        show_history()
        return

    if uploaded_file.size > MAX_FILE_MB * 1024 * 1024:
        st.error(f"File is larger than {MAX_FILE_MB} MB. Please upload a smaller CSV.")
        return

    try:
        original_df = read_csv_safely(uploaded_file)
    except Exception as exc:
        st.error(f"Could not read this CSV: {exc}")
        return

    if original_df.empty or len(original_df.columns) == 0:
        st.warning("The CSV has no rows or columns to analyze.")
        return

    st.success(f"Loaded {uploaded_file.name}")
    save_history(uploaded_file.name, original_df)

    rows, cols = original_df.shape
    missing_cells = int(original_df.isna().sum().sum())
    duplicate_rows = int(original_df.duplicated().sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{rows:,}")
    c2.metric("Columns", f"{cols:,}")
    c3.metric("Missing cells", f"{missing_cells:,}")
    c4.metric("Duplicate rows", f"{duplicate_rows:,}")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Preview", "Data quality", "Charts", "Clean & download"]
    )

    with tab1:
        st.subheader("Dataset preview")
        st.dataframe(original_df.head(100), use_container_width=True)
        st.subheader("Column information")
        info_df = pd.DataFrame({
            "column": original_df.columns.astype(str),
            "data_type": [str(dtype) for dtype in original_df.dtypes],
            "non_null_count": original_df.notna().sum().values,
            "missing_count": original_df.isna().sum().values,
        })
        st.dataframe(info_df, use_container_width=True)
        st.subheader("Descriptive statistics")
        st.dataframe(original_df.describe(include="all").transpose(), use_container_width=True)

    with tab2:
        st.subheader("Missing values by column")
        missing_df = original_df.isna().sum().rename("missing_count").to_frame()
        missing_df["missing_percent"] = (
            original_df.isna().mean().mul(100).round(2)
        )
        st.dataframe(missing_df, use_container_width=True)
        st.subheader("Duplicate rows")
        st.write(f"Found **{duplicate_rows}** duplicate rows.")
        if duplicate_rows:
            st.dataframe(original_df[original_df.duplicated(keep=False)].head(50),
                         use_container_width=True)

    with tab3:
        st.subheader("Explore a column")
        numeric_cols = original_df.select_dtypes(include="number").columns.tolist()
        all_cols = original_df.columns.astype(str).tolist()
        selected_col = st.selectbox("Choose a column", all_cols)
        if selected_col in numeric_cols:
            fig, ax = plt.subplots()
            original_df[selected_col].dropna().plot(kind="hist", bins=20, ax=ax)
            ax.set_title(f"Distribution of {selected_col}")
            ax.set_xlabel(selected_col)
            st.pyplot(fig)
            plt.close(fig)
        else:
            counts = original_df[selected_col].astype(str).value_counts().head(15)
            st.bar_chart(counts)

    with tab4:
        st.subheader("Clean the dataset")
        cleaned_df = original_df.copy()
        drop_duplicates = st.checkbox("Remove duplicate rows")
        fill_missing = st.checkbox("Fill missing values")
        if drop_duplicates:
            cleaned_df = cleaned_df.drop_duplicates()
        if fill_missing:
            for col in cleaned_df.columns:
                if pd.api.types.is_numeric_dtype(cleaned_df[col]):
                    if cleaned_df[col].isna().any():
                        cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].median())
                else:
                    if cleaned_df[col].isna().any():
                        mode = cleaned_df[col].mode(dropna=True)
                        replacement = mode.iloc[0] if not mode.empty else "Unknown"
                        cleaned_df[col] = cleaned_df[col].fillna(replacement)

        st.write(f"Original rows: **{len(original_df)}** | Cleaned rows: **{len(cleaned_df)}**")
        st.dataframe(cleaned_df.head(100), use_container_width=True)
        csv_bytes = cleaned_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download cleaned CSV",
            data=csv_bytes,
            file_name=f"cleaned_{uploaded_file.name}",
            mime="text/csv",
        )

    show_history()

def show_history():
    st.subheader("Recent analysis history")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            history = pd.read_sql_query(
                """SELECT file_name, row_count, column_count, missing_cells,
                          duplicate_rows, analyzed_at
                   FROM analysis_history ORDER BY id DESC LIMIT 10""",
                conn,
            )
        if history.empty:
            st.caption("No analyses recorded yet.")
        else:
            st.dataframe(history, use_container_width=True)
    except sqlite3.Error:
        st.caption("History is not available yet.")

if __name__ == "__main__":
    main()
