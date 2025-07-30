import streamlit as st
import pandas as pd
import re

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
        # Remove unnamed index columns that can be added by spreadsheet software
        if any(col.startswith('Unnamed:') for col in df.columns):
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        st.session_state.df = df
        st.sidebar.success("File uploaded and processed successfully!")
    except Exception as e:
        st.error(f"Error reading the CSV file: {e}")
        st.stop()
else:
    st.info("Please upload a CSV file using the sidebar to get started.")
    st.stop()

# Create tabs
tab1, tab2 = st.tabs(["Filtered View", "Data Sheet"])

with tab1:
    # --- Filtering ---
    df_filtered = st.session_state.df.copy()
    
    st.header("Column Filters")
    
    # Create columns for the filters
    filter_cols = st.columns(len(df_filtered.columns))

    for i, column in enumerate(df_filtered.columns):
        with filter_cols[i]:
            # For object/string columns, create a multiselect filter
            if df_filtered[column].dtype == 'object':
                unique_values = df_filtered[column].unique()
                # Use a text input for filtering large numbers of unique values
                if len(unique_values) > 50:
                     search_term = st.text_input(f"Search {column}")
                     if search_term:
                         df_filtered = df_filtered[df_filtered[column].str.contains(search_term, case=False, na=False)]
                else:
                    selected_values = st.multiselect(f"Filter by {column}", unique_values, default=unique_values)
                    df_filtered = df_filtered[df_filtered[column].isin(selected_values)]

            # For numerical columns, create a range slider
            elif pd.api.types.is_numeric_dtype(df_filtered[column]):
                min_val = float(df_filtered[column].min())
                max_val = float(df_filtered[column].max())
                # Add a check to ensure min_val is not greater than max_val
                if min_val < max_val:
                    selected_range = st.slider(f"Filter by {column}", min_val, max_val, (min_val, max_val))
                    df_filtered = df_filtered[(df_filtered[column] >= selected_range[0]) & (df_filtered[column] <= selected_range[1])]

    # --- Display Filtered Data ---
    st.header("Filtered Data")
    st.dataframe(df_filtered)

with tab2:
    # --- Display Original Data ---
    st.header("Original Data")
    st.dataframe(st.session_state.df)
