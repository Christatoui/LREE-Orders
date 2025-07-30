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

    # --- Hybrid Cascading Filter Logic ---
    
    # Automatically find a description column
    description_col = None
    possible_desc_cols = ['Description', 'Item with specs', 'Item with Specs', 'Item Name', 'Product']
    for col_name in possible_desc_cols:
        if col_name in df_filtered.columns:
            description_col = col_name
            break

    columns_to_filter = [col for col in df_filtered.columns if col != 'ATC']
    filter_cols = st.columns(len(columns_to_filter))

    # This dataframe will be updated sequentially by the custom filters
    df_for_custom_options = st.session_state.df.copy()

    for i, column in enumerate(columns_to_filter):
        with filter_cols[i]:
            # Primary filters are always based on the original full dataset
            primary_unique_values = st.session_state.df[column].dropna().unique()
            
            label = "By Country/Region" if column == "Customer Country/Region" else f"By {column}"
            filter_mode = st.selectbox(label, ["All", "None", "Custom"], key=f"mode_{column}")

            if filter_mode == "None":
                df_filtered = df_filtered[df_filtered[column].isnull()]
            
            elif filter_mode == "Custom":
                # --- Secondary Cascading Filter ---
                # Options for this multiselect are based on the data filtered by *previous* custom selections
                cascading_unique_values = df_for_custom_options[column].dropna().unique()

                if column == description_col:
                    # Special keyword filter for the description column
                    keyword_patterns = [r'\d+\s*TB', r'\d+\s*GB', r'\d+T', r'\d+G', 'MBP', 'MBA', 'STUDIO', 'MINI']
                    all_matches = []
                    descriptions = df_for_custom_options[description_col].astype(str)
                    for pattern in keyword_patterns:
                        try:
                            matches = descriptions.str.findall(pattern, flags=re.IGNORECASE).explode().dropna()
                            all_matches.extend(matches)
                        except Exception:
                            continue
                    
                    cascading_unique_values = sorted(list(set(all_matches)), key=str.casefold)
                    
                    selected_values = st.multiselect("Select Keywords", list(cascading_unique_values), key=f"multiselect_{column}")
                    if selected_values:
                        # Build a regex pattern to find any of the selected keywords
                        pattern = '|'.join([re.escape(val) for val in selected_values])
                        df_filtered = df_filtered[df_filtered[column].str.contains(pattern, case=False, na=False)]
                        # Update the dataframe for the next custom filter in the sequence
                        df_for_custom_options = df_for_custom_options[df_for_custom_options[column].str.contains(pattern, case=False, na=False)]

                else: # Standard multiselect for other columns
                    selected_values = st.multiselect("Select Values", list(cascading_unique_values), key=f"multiselect_{column}")
                    if selected_values:
                        df_filtered = df_filtered[df_filtered[column].isin(selected_values)]
                        # Update the dataframe for the next custom filter in the sequence
                        df_for_custom_options = df_for_custom_options[df_for_custom_options[column].isin(selected_values)]

    # --- ATC Sorter (applied after all filters) ---
    if 'ATC' in df_filtered.columns:
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
