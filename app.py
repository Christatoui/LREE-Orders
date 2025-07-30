import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("CSV Data Viewer and Filter")

# --- File Uploader ---
st.sidebar.title("Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload your CSV file", type="csv")

# --- Main App Logic ---
if uploaded_file is not None:
    # Read the uploaded CSV into a pandas DataFrame
    try:
        df = pd.read_csv(uploaded_file)
        st.session_state.df = df
        st.sidebar.success("File uploaded and processed successfully!")
    except Exception as e:
        st.error(f"Error reading the CSV file: {e}")
        st.stop()
else:
    st.info("Please upload a CSV file using the sidebar to get started.")
    st.stop()

# --- Filtering ---
st.sidebar.title("Filters")
df_filtered = st.session_state.df.copy()

# Create filters for each column
for column in df_filtered.columns:
    # For object/string columns, create a multiselect filter
    if df_filtered[column].dtype == 'object':
        unique_values = df_filtered[column].unique()
        selected_values = st.sidebar.multiselect(f"Filter by {column}", unique_values, default=unique_values)
        df_filtered = df_filtered[df_filtered[column].isin(selected_values)]

    # For numerical columns, create a range slider
    elif pd.api.types.is_numeric_dtype(df_filtered[column]):
        min_val = float(df_filtered[column].min())
        max_val = float(df_filtered[column].max())
        # Add a check to ensure min_val is not greater than max_val
        if min_val < max_val:
            selected_range = st.sidebar.slider(f"Filter by {column}", min_val, max_val, (min_val, max_val))
            df_filtered = df_filtered[(df_filtered[column] >= selected_range[0]) & (df_filtered[column] <= selected_range[1])]

# --- Display Data ---
st.header("Filtered Data")
st.dataframe(df_filtered)

st.header("Original Data")
st.dataframe(st.session_state.df)
