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

    # --- Display Filtered Data with Add to Order Buttons ---
    st.header("Filtered Data")
    
    # Create header row
    header_cols = st.columns(len(df_filtered.columns) + 1)
    for i, col_name in enumerate(df_filtered.columns):
        header_cols[i].write(f"**{col_name}**")
    header_cols[-1].write("**Add to Order**")

    # Create rows with buttons
    for index, row in df_filtered.iterrows():
        row_cols = st.columns(len(df_filtered.columns) + 1)
        for i, col_name in enumerate(df_filtered.columns):
            row_cols[i].write(row[col_name])
        
        if row_cols[-1].button("Add", key=f"add_{index}", type="primary"):
            row_dict = row.to_dict()
            row_dict['Quantity'] = 1
            row_dict['Price per unit'] = 0.0
            row_dict['Hardware DRI'] = ""
            row_dict['Location'] = "Cork"
            row_dict['1-line Justification'] = ""
            st.session_state.current_order.append(row_dict)
            st.success(f"Added '{row.get('Description', 'Item')}' to current order.")
            # No rerun needed, order updates in the background

with tab2:
    st.header("Original Data")
    st.dataframe(st.session_state.df)

with tab3:
    st.header("Current Order")
    if st.session_state.current_order:
        order_df = pd.DataFrame(st.session_state.current_order)
        
        order_df['Total Unit Cost'] = order_df['Quantity'] * order_df['Price per unit']

        # --- Real-time Stock Validation ---
        stock_errors = []
        # Group by Part number and sum the quantities
        order_summary = order_df.groupby('Part').agg({
            'Quantity': 'sum',
            'ATC': 'first', # Assuming ATC is the same for the same part number
            'Description': 'first'
        }).reset_index()

        for index, row in order_summary.iterrows():
            if row['Quantity'] > row['ATC']:
                stock_errors.append(f"<li>{row['Description']} (Part: {row['Part']}): Total Quantity ({row['Quantity']}) exceeds stock ({row['ATC']})</li>")
        
        if stock_errors:
            error_message = "<b>Stock Errors:</b><ul>" + "".join(stock_errors) + "</ul>"
            st.warning(error_message, icon="⚠️")

        # Define the columns to display and their order
        display_cols = [
            "Description", "Part", "ATC", "Quantity", "Price per unit", 
            "Total Unit Cost", "Hardware DRI", "Location", "1-line Justification"
        ]
        # Filter out any columns that might not exist in the dataframe yet
        display_cols = [col for col in display_cols if col in order_df.columns]
        
        # Reorder and filter the DataFrame
        order_df = order_df[display_cols]

        edited_order_df = st.data_editor(
            order_df,
            column_config={
                "Price per unit": st.column_config.NumberColumn("$ per unit"),
                "Total Unit Cost": st.column_config.NumberColumn("Total Cost"),
                "Location": st.column_config.SelectboxColumn(
                    "Location",
                    help="Select the location for the item",
                    options=["Cork", "Hyderabad", "Hong Kong", "Tokyo"],
                    required=False,
                ),
                "1-line Justification": st.column_config.Column(width="large")
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
