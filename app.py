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

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        if any(col.startswith('Unnamed:') for col in df.columns):
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        st.session_state.df = df
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
    df_filtered = st.session_state.df.copy()

    st.header("Column Filters")

    # --- Guided, Sequential, Multi-Select Filtering ---
    
    filter_order = [
        "Product Family Code",
        "Product Description",
        "Description",
        "Subclass Desc",
        "Subfamily Desc",
        "Country/Region",
        "Part"
    ]

    # Filter out columns that are not in the dataframe
    filter_order = [col for col in filter_order if col in df_filtered.columns]
    
    filter_cols = st.columns(len(filter_order))

    for i, column in enumerate(filter_order):
        with filter_cols[i]:
            # The first filter is always active
            is_active = i == 0
            
            # A filter becomes active if the one before it has a selection
            if i > 0:
                prev_col = filter_order[i-1]
                # A filter becomes active if the one before it has any kind of selection
                if (st.session_state.get(f"filter_{prev_col}") or
                    st.session_state.get(f"search_{prev_col}") or
                    st.session_state.get(f"multiselect_{prev_col}")):
                    is_active = True

            unique_values = df_filtered[column].dropna().unique()
            
            if is_active:
                if column in ["Product Description", "Description"]:
                    filter_mode = st.selectbox(f"Filter {column} by:", ["Search by Text", "Select from List"], key=f"mode_{column}")
                    if filter_mode == "Search by Text":
                        search_term = st.text_input(f"Search {column}", key=f"search_{column}")
                        if search_term:
                            df_filtered = df_filtered[df_filtered[column].str.contains(search_term, case=False, na=False)]
                    else:
                        selected_values = st.multiselect(f"Select {column} values", list(unique_values), key=f"multiselect_{column}")
                        if selected_values:
                            df_filtered = df_filtered[df_filtered[column].isin(selected_values)]
                else:
                    selected_values = st.multiselect(f"By {column}", list(unique_values), key=f"filter_{column}")
                    if selected_values:
                        df_filtered = df_filtered[df_filtered[column].isin(selected_values)]
            else:
                if column in ["Product Description", "Description"]:
                    st.selectbox(f"Filter {column} by:", ["Search by Text", "Select from List"], disabled=True, key=f"mode_{column}")
                else:
                    st.multiselect(f"By {column}", [], disabled=True, key=f"filter_{column}")

    # --- Display Filtered Data ---
    st.header("Filtered Data")
    st.dataframe(df_filtered)

with tab2:
    # --- Display Original Data ---
    st.header("Original Data")
    st.dataframe(st.session_state.df)
