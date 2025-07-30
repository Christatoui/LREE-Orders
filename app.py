import streamlit as st
import pandas as pd
import re

st.set_page_config(layout="wide")
st.title("CSV Data Viewer and Filter")

# Inject custom CSS to set the font size
st.markdown("""
<style>
    .stMultiSelect [data-baseweb="select"] > div > div > div {
        font-size: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- File Uploader ---
st.sidebar.title("Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload your CSV file", type="csv")

# --- Main App Logic ---
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
else:
    st.info("Please upload a CSV file using the sidebar to get started.")
    st.stop()

# Create tabs
tab1, tab2 = st.tabs(["Filtered View", "Data Sheet"])

with tab1:
    df_filtered = st.session_state.df.copy()

    # --- Column Filters ---
    st.header("Column Filters")

    # Automatically find a description column to search
    description_col = None
    possible_desc_cols = ['Description', 'Item with specs', 'Item with Specs', 'Item Name', 'Product']
    for col_name in possible_desc_cols:
        if col_name in df_filtered.columns:
            description_col = col_name
            break

    columns_to_filter = [col for col in df_filtered.columns if col != 'ATC']
    filter_cols = st.columns(len(df_filtered.columns))

    for i, column in enumerate(columns_to_filter):
        with filter_cols[i]:
            # Get unique values from the *currently filtered* dataframe
            unique_values = df_filtered[column].dropna().unique()

            if column == description_col:
                # Special handling for the description column
                label = "By Country/Region" if column == "Customer Country/Region" else f"By {column}"
                filter_mode = st.selectbox(label, ["All", "None", "Custom"], key=f"mode_{column}")

                if filter_mode == "None":
                    df_filtered = df_filtered[df_filtered[column].isnull()]
                elif filter_mode == "Custom":
                    keyword_patterns = [
                        r'\d+\s*TB', r'\d+\s*GB', r'\d+T', r'\d+G',
                        'MBP', 'MBA', 'STUDIO', 'MINI'
                    ]
                    all_matches = []
                    descriptions = df_filtered[description_col].astype(str)
                    for pattern in keyword_patterns:
                        try:
                            matches = descriptions.str.findall(pattern, flags=re.IGNORECASE).explode().dropna()
                            all_matches.extend(matches)
                        except Exception:
                            continue
                    
                    unique_matches = sorted(list(set(all_matches)), key=str.casefold)

                    if unique_matches:
                        selected_match = st.selectbox(
                            "Filter by Keyword",
                            options=["All"] + unique_matches,
                            key=f"keyword_multiselect_{column}"
                        )
                        if selected_match != "All":
                            df_filtered = df_filtered[descriptions.str.contains(re.escape(selected_match), case=False, na=False)]
            
            elif df_filtered[column].dtype == 'object':
                # Standard filter for other object columns
                label = "By Country/Region" if column == "Customer Country/Region" else f"By {column}"
                filter_mode = st.selectbox(label, ["All", "None", "Custom"], key=f"mode_{column}")

                if filter_mode == "None":
                    df_filtered = df_filtered[df_filtered[column].isnull()]
                elif filter_mode == "Custom":
                    selected_values = st.multiselect("Select Values", list(unique_values), key=f"multiselect_{column}")
                    if selected_values:
                        df_filtered = df_filtered[df_filtered[column].isin(selected_values)]
            
            elif pd.api.types.is_numeric_dtype(df_filtered[column]):
                # Filter for numerical columns
                min_val, max_val = float(df_filtered[column].min()), float(df_filtered[column].max())
                if min_val < max_val:
                    selected_range = st.slider(f"Filter by {column}", min_val, max_val, (min_val, max_val))
                    df_filtered = df_filtered[(df_filtered[column] >= selected_range[0]) & (df_filtered[column] <= selected_range[1])]

    # Add the ATC sorter as the last filter
    if 'ATC' in df_filtered.columns:
        with filter_cols[len(columns_to_filter)]:
            sort_direction = st.selectbox("ATC", options=["--", "⬆️", "⬇️"], index=0)
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
