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
    df_filtered = st.session_state.df.copy()

    # --- ATC Sorter ---
    if 'ATC' in df_filtered.columns:
        st.header("Sort by ATC")
        sort_direction = st.selectbox("ATC", options=["--", "⬆️", "⬇️"], index=0)
        if sort_direction != "--":
            ascending = sort_direction == "⬆️"
            df_filtered = df_filtered.sort_values(by="ATC", ascending=ascending)

    # --- Keyword Filter ---
    st.header("Keyword Filter")
    # Automatically find a description column to search
    description_col = None
    possible_desc_cols = ['Description', 'Item with specs', 'Item with Specs', 'Item Name', 'Product']
    for col_name in possible_desc_cols:
        if col_name in df_filtered.columns:
            description_col = col_name
            break
    
    if description_col:
        # Define keyword patterns, correctly handling any number of digits
        keyword_patterns = [
            r'\d+\s*TB',  # e.g., "1TB", "16 TB"
            r'\d+\s*GB',  # e.g., "8GB", "256 GB"
            r'\d+T',      # e.g., "1T"
            r'\d+G',      # e.g., "8G"
            'MBP', 
            'MBA', 
            'STUDIO', 
            'MINI'
        ]
        
        # Extract all matching keywords from the identified description column
        all_matches = []
        descriptions = df_filtered[description_col].astype(str)
        for pattern in keyword_patterns:
            try:
                matches = descriptions.str.findall(pattern, flags=re.IGNORECASE).explode().dropna()
                all_matches.extend(matches)
            except Exception:
                # Ignore columns that may not be compatible with string operations
                continue
        
        unique_matches = sorted(list(set(all_matches)), key=str.casefold)

        if unique_matches:
            selected_match = st.selectbox(
                f"Filter by Keyword in '{description_col}'",
                options=["All"] + unique_matches
            )
            if selected_match != "All":
                # Use re.escape to safely handle special characters in the search term
                df_filtered = df_filtered[descriptions.str.contains(re.escape(selected_match), case=False, na=False)]

    # --- Column Filters ---
    st.header("Column Filters")
    
    # Create columns for the filters
    filter_cols = st.columns(len(df_filtered.columns))

    for i, column in enumerate(df_filtered.columns):
        # Skip creating a filter for the 'ATC' column as it has a dedicated sorter
        if column == 'ATC':
            continue
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
