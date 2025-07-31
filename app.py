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
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        if any(col.startswith('Unnamed:') for col in df.columns):
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        st.session_state.df = df
        # Initialize session state for filters when a new file is uploaded
        st.session_state.filters = {col: {"mode": "All", "values": []} for col in df.columns}
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
    df_to_display = st.session_state.df.copy()

    st.header("Column Filters")

    # --- Robust Stateful Cascading Filter Logic ---
    
    # Automatically find a description column
    description_col = None
    possible_desc_cols = ['Description', 'Item with specs', 'Item with Specs', 'Item Name', 'Product']
    for col_name in possible_desc_cols:
        if col_name in df_to_display.columns:
            description_col = col_name
            break

    columns_for_grid = [col for col in df_to_display.columns if col != 'ATC']
    if 'ATC' in df_to_display.columns:
        columns_for_grid.append('ATC')
        
    filter_cols = st.columns(len(columns_for_grid))

    # First pass: Display widgets and collect user input into session state
    for i, column in enumerate(columns_for_grid):
        with filter_cols[i]:
            if column == 'ATC':
                st.selectbox("ATC", options=["--", "⬆️", "⬇️"], index=0, key=f"sort_{column}")
                continue

            if df_to_display[column].dtype == 'object':
                label = "By Country/Region" if column == "Customer Country/Region" else f"By {column}"
                st.selectbox(label, ["All", "None", "Custom"], key=f"mode_{column}")
                
                if st.session_state[f"mode_{column}"] == "Custom":
                    # Options for this multiselect are based on the data filtered by *all previous* selections
                    temp_df = st.session_state.df.copy()
                    for prev_col in columns_for_grid[:i]:
                        if st.session_state[f"mode_{prev_col}"] == "None":
                            temp_df = temp_df[temp_df[prev_col].isnull()]
                        elif st.session_state[f"mode_{prev_col}"] == "Custom":
                            if st.session_state[f"values_{prev_col}"]:
                                temp_df = temp_df[temp_df[prev_col].isin(st.session_state[f"values_{prev_col}"])]
                    
                    cascading_unique_values = temp_df[column].dropna().unique()
                    
                    if column == description_col:
                        keyword_patterns = [r'\d+\s*TB', r'\d+\s*GB', r'\d+T', r'\d+G', 'MBP', 'MBA', 'STUDIO', 'MINI']
                        all_matches = []
                        descriptions = temp_df[description_col].astype(str)
                        for pattern in keyword_patterns:
                            try:
                                matches = descriptions.str.findall(pattern, flags=re.IGNORECASE).explode().dropna()
                                all_matches.extend(matches)
                            except Exception:
                                continue
                        cascading_unique_values = sorted(list(set(all_matches)), key=str.casefold)
                        st.multiselect("Select Keywords", list(cascading_unique_values), key=f"values_{column}")
                    else:
                        st.multiselect("Select Values", list(cascading_unique_values), key=f"values_{column}")

            elif pd.api.types.is_numeric_dtype(df_to_display[column]):
                min_val, max_val = float(df_to_display[column].min()), float(df_to_display[column].max())
                if min_val < max_val:
                    st.slider(f"Filter by {column}", min_val, max_val, (min_val, max_val), key=f"values_{column}")

    # Second pass: Apply all collected filters from session state
    for column in columns_for_grid:
        if column == 'ATC': continue
        
        mode = st.session_state.get(f"mode_{column}", "All")
        if mode == "None":
            df_to_display = df_to_display[df_to_display[column].isnull()]
        elif mode == "Custom":
            values = st.session_state.get(f"values_{column}", [])
            if values:
                if column == description_col:
                    pattern = '|'.join([re.escape(val) for val in values])
                    df_to_display = df_to_display[df_to_display[column].str.contains(pattern, case=False, na=False)]
                else:
                    df_to_display = df_to_display[df_to_display[column].isin(values)]
        
        if pd.api.types.is_numeric_dtype(st.session_state.df[column]):
             if f"values_{column}" in st.session_state:
                slider_values = st.session_state[f"values_{column}"]
                df_to_display = df_to_display[(df_to_display[column] >= slider_values[0]) & (df_to_display[column] <= slider_values[1])]

    # Apply ATC sorter last
    if 'ATC' in st.session_state.df.columns:
        sort_direction = st.session_state.get("sort_ATC", "--")
        if sort_direction != "--":
            ascending = sort_direction == "⬆️"
            df_to_display = df_to_display.sort_values(by="ATC", ascending=ascending)

    # --- Display Filtered Data ---
    st.header("Filtered Data")
    st.dataframe(df_to_display)

with tab2:
    # --- Display Original Data ---
    st.header("Original Data")
    st.dataframe(st.session_state.df)
