import streamlit as st
import pandas as pd
import re

st.set_page_config(layout="wide")
st.title("CSV Data Viewer and Filter")

# --- File Uploader ---
st.sidebar.title("Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload your CSV file", type="csv")

# --- Main App Logic ---
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()
if 'filters' not in st.session_state:
    st.session_state.filters = {}

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        if any(col.startswith('Unnamed:') for col in df.columns):
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        st.session_state.df = df
        # Initialize session state for filters when a new file is uploaded
        st.session_state.filters = {col: "All" for col in df.columns}
        st.sidebar.success("File uploaded and processed successfully!")
    except Exception as e:
        st.error(f"Error reading the CSV file: {e}")
        st.stop()

if st.session_state.df.empty:
    st.info("Please upload a CSV file using the sidebar to get started.")
    st.stop()

# Create tabs
tab1, tab2 = st.tabs(["Filtered View", "Data Sheet"])

with tab1:
    st.header("Column Filters")

    # --- Bi-directional Cascading Filter Logic ---
    
    columns_for_grid = [col for col in st.session_state.df.columns if col != 'ATC']
    if 'ATC' in st.session_state.df.columns:
        columns_for_grid.append('ATC')
        
    filter_cols = st.columns(len(columns_for_grid))

    # Create a copy of the dataframe to be filtered
    df_filtered = st.session_state.df.copy()

    for i, column in enumerate(columns_for_grid):
        with filter_cols[i]:
            # Create a temporary dataframe that is filtered by all *other* columns
            temp_df = st.session_state.df.copy()
            for other_col in columns_for_grid:
                if i != columns_for_grid.index(other_col) and st.session_state.filters[other_col] != "All":
                    temp_df = temp_df[temp_df[other_col] == st.session_state.filters[other_col]]
            
            unique_values = ["All"] + temp_df[column].dropna().unique().tolist()
            
            if column == 'ATC':
                st.selectbox("ATC", options=["--", "⬆️", "⬇️"], index=0, key=f"filters", args=(column,))
                continue

            label = "By Country/Region" if column == "Customer Country/Region" else f"By {column}"
            st.selectbox(label, unique_values, key=f"filters", args=(column,))

    # Apply all filters from session state
    for column, value in st.session_state.filters.items():
        if value != "All":
            df_filtered = df_filtered[df_filtered[column] == value]

    # Apply ATC sorter last
    if 'ATC' in st.session_state.df.columns:
        sort_direction = st.session_state.filters.get("ATC", "--")
        if sort_direction != "--":
            ascending = sort_direction == "⬆️"
            df_filtered = df_filtered.sort_values(by="ATC", ascending=ascending)

    # --- Display Filtered Data ---
    st.header("Filtered Data")
    st.dataframe(df_filtered)

with tab2:
    # --- Display Original Data ---
    st.header("Original Data")
    st.dataframe(st.session_state.df)
