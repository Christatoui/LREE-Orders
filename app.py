import streamlit as st
import pandas as pd
import re

st.set_page_config(layout="wide")

# --- Custom CSS for button colors ---
st.markdown("""
<style>
    /* Add button */
    div[data-testid*="stButton"] > button[kind="primary"] {
        background-color: #4CAF50; /* Green */
        color: white;
        border-color: #4CAF50;
    }
    /* Remove button */
    div[data-testid*="stButton"] > button:not([kind="primary"]) {
        background-color: #f44336; /* Red */
        color: white;
    }
</style>
""", unsafe_allow_html=True)

st.title("CSV Data Viewer and Filter")

# --- File Uploader ---
st.sidebar.title("Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload your CSV file", type="csv")

# --- Main App Logic ---
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()
if 'current_order' not in st.session_state:
    st.session_state.current_order = []

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
tab1, tab2, tab3, tab4 = st.tabs(["Filtered View", "Data Sheet", "Current Order", "Past Orders"])

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
            is_active = i == 0
            
            if i > 0:
                prev_col = filter_order[i-1]
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

    # --- Display Filtered Data with "Add to Order" buttons ---
    st.header("Filtered Data")
    
    # Create a header row
    cols = st.columns(len(df_filtered.columns) + 1)
    cols[0].write("**Add to Order**")
    for i, col_name in enumerate(df_filtered.columns):
        cols[i+1].write(f"**{col_name}**")

    # Display data rows with buttons
    for index, row in df_filtered.iterrows():
        cols = st.columns(len(row) + 1)
        
        row_dict = row.to_dict()
        is_in_order = any(item['Part'] == row_dict['Part'] for item in st.session_state.current_order)

        if is_in_order:
            if cols[0].button("Remove", key=f"remove_{index}"):
                st.session_state.current_order = [item for item in st.session_state.current_order if item['Part'] != row_dict['Part']]
                st.success(f"Removed {row['Product Description']} from current order.")
                st.rerun()
        else:
            if cols[0].button("Add", key=f"add_{index}", type="primary"):
                row_dict['Quantity'] = 1
                row_dict['Price per unit'] = 0.0
                row_dict['Hardware DRI'] = ""
                row_dict['Location'] = "Cork"
                row_dict['1-line Justification'] = ""
                st.session_state.current_order.append(row_dict)
                st.success(f"Added {row['Product Description']} to current order.")
                st.rerun()
        
        for i, value in enumerate(row):
            cols[i+1].write(value)

with tab2:
    st.header("Original Data")
    st.dataframe(st.session_state.df)

with tab3:
    st.header("Current Order")
    if st.session_state.current_order:
        order_df = pd.DataFrame(st.session_state.current_order)
        
        order_df['Total Unit Cost'] = order_df['Quantity'] * order_df['Price per unit']

        if 'Description' in order_df.columns and 'Part' in order_df.columns:
            cols = order_df.columns.tolist()
            cols.insert(0, cols.pop(cols.index('Description')))
            cols.insert(1, cols.pop(cols.index('Part')))
            if 'Quantity' in cols:
                cols.insert(2, cols.pop(cols.index('Quantity')))
            if 'Price per unit' in cols:
                cols.insert(3, cols.pop(cols.index('Price per unit')))
            if 'Total Unit Cost' in cols:
                cols.insert(4, cols.pop(cols.index('Total Unit Cost')))
            if 'Hardware DRI' in cols:
                cols.insert(5, cols.pop(cols.index('Hardware DRI')))
            if 'Location' in cols:
                cols.insert(6, cols.pop(cols.index('Location')))
            if '1-line Justification' in cols:
                cols.insert(7, cols.pop(cols.index('1-line Justification')))
            order_df = order_df[cols]
        
        # Define the columns to display and hide the rest
        display_cols = [
            "Description", "Part", "Quantity", "Price per unit",
            "Total Unit Cost", "Hardware DRI", "Location", "1-line Justification"
        ]
        # Filter out any columns that might not exist in the dataframe yet
        display_cols = [col for col in display_cols if col in order_df.columns]
        
        edited_order_df = st.data_editor(
            order_df[display_cols],
            column_config={
                "Location": st.column_config.SelectboxColumn(
                    "Location",
                    help="Select the location for the item",
                    options=["Cork", "Hyderabad", "Hong Kong", "Tokyo"],
                    required=False,
                )
            },
            hide_index=True,
            key="order_editor"
        )
        st.session_state.current_order = edited_order_df.to_dict('records')

    else:
        st.info("Your current order is empty. Add items from the 'Filtered View' tab.")

with tab4:
    st.header("Past Orders")
    st.info("This feature is not yet implemented.")
