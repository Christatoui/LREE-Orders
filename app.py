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

    # --- Simplified, Correct Cascading Filter Logic ---
    
    columns_for_grid = [col for col in df_filtered.columns if col != 'ATC']
    if 'ATC' in df_filtered.columns:
        columns_for_grid.append('ATC')
        
    filter_cols = st.columns(len(columns_for_grid))

    for i, column in enumerate(columns_for_grid):
        with filter_cols[i]:
            if column == 'ATC':
                # --- ATC Sorter ---
                sort_direction = st.selectbox("ATC", options=["--", "⬆️", "⬇️"], index=0, key=f"sort_{column}")
                if sort_direction != "--":
                    ascending = sort_direction == "⬆️"
                    df_filtered = df_filtered.sort_values(by="ATC", ascending=ascending)
                continue

            # Get unique values from the *currently* filtered dataframe
            unique_values = df_filtered[column].dropna().unique()
            
            # The selectbox will be populated with options relevant to previous selections
            label = "By Country/Region" if column == "Customer Country/Region" else f"By {column}"
            
            # Use a simple selectbox for cascading logic
            selected_value = st.selectbox(label, ["All"] + list(unique_values), key=f"filter_{column}")
            
            # Immediately apply the filter to the dataframe for the next iteration
            if selected_value != "All":
                df_filtered = df_filtered[df_filtered[column] == selected_value]

    # --- Display Filtered Data ---
    st.header("Filtered Data")
    st.dataframe(df_filtered)

with tab2:
    # --- Display Original Data ---
    st.header("Original Data")
    st.dataframe(st.session_state.df)
