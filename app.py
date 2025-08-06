import streamlit as st
import pandas as pd
import re
import os
import json

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

# --- Constants ---
CURRENT_ORDER_FILE = "current_order.csv"
PAST_ORDERS_FILE = "past_orders.json"

# --- Functions to Save and Load Order ---
def save_current_order():
    if st.session_state.current_order:
        pd.DataFrame(st.session_state.current_order).to_csv(CURRENT_ORDER_FILE, index=False)

def load_current_order():
    if os.path.exists(CURRENT_ORDER_FILE):
        return pd.read_csv(CURRENT_ORDER_FILE).to_dict('records')
    return []

def save_past_orders():
    with open(PAST_ORDERS_FILE, 'w') as f:
        json.dump(st.session_state.past_orders, f)

def load_past_orders():
    if os.path.exists(PAST_ORDERS_FILE):
        with open(PAST_ORDERS_FILE, 'r') as f:
            return json.load(f)
    return []

# --- Main App Logic ---
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()
if 'current_order' not in st.session_state:
    st.session_state.current_order = load_current_order()
if 'past_orders' not in st.session_state:
    st.session_state.past_orders = load_past_orders()
if 'editor_key_version' not in st.session_state:
    st.session_state.editor_key_version = 0

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        if any(col.startswith('Unnamed:') for col in df.columns):
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        st.session_state.df = df
        st.sidebar.success("File uploaded and processed successfully!")

        # --- Re-validate ATC in Current Order ---
        if st.session_state.current_order:
            atc_map = df.set_index('Part')['ATC'].to_dict()
            for item in st.session_state.current_order:
                item['ATC'] = atc_map.get(item['Part'], 0) # Default to 0 if part no longer exists
            save_current_order()
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

    # --- Display Filtered Data with Row Selection ---
    st.header("Filtered Data")
    
    # Add a "Select" column to the dataframe
    df_filtered.insert(0, "Select", False)

    # Use data_editor to display the dataframe with checkboxes
    edited_df = st.data_editor(
        df_filtered,
        hide_index=True,
        column_config={"Select": st.column_config.CheckboxColumn(required=True)},
        disabled=df_filtered.columns.drop("Select"),
        key=f"data_editor_{st.session_state.editor_key_version}"
    )

    selected_rows = edited_df[edited_df.Select]

    if not selected_rows.empty:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Add Selected to Order", type="primary"):
                # Get the selected rows without the "Select" column
                rows_to_add = selected_rows.drop(columns=["Select"])
                for index, row in rows_to_add.iterrows():
                    row_dict = row.to_dict()
                    row_dict['Quantity'] = 1
                    row_dict['Price per unit'] = 0.0
                    row_dict['Hardware DRI'] = ""
                    row_dict['Location'] = "Cork"
                    row_dict['1-line Justification'] = ""
                    row_dict['Approved'] = False
                    row_dict['Delivered'] = False
                    row_dict['Transferred'] = False
                    st.session_state.current_order.append(row_dict)
                save_current_order()
                st.success(f"Added {len(rows_to_add)} item(s) to current order.")
                # Increment the key version to force a reset of the data_editor
                st.session_state.editor_key_version += 1
                st.rerun()
        with col2:
            if st.button("Clear Selection"):
                # Increment the key version to force a reset of the data_editor
                st.session_state.editor_key_version += 1
                st.rerun()

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

        problematic_parts = []
        for index, row in order_summary.iterrows():
            if row['Quantity'] > row['ATC']:
                stock_errors.append(f"<li>{row['Description']} (Part: {row['Part']}): Total Quantity ({row['Quantity']}) exceeds stock ({row['ATC']})</li>")
                problematic_parts.append(row['Part'])
        
        # Add a "Status" column
        order_df['Status'] = order_df.apply(lambda row: "⚠️ Exceeds Stock" if row['Part'] in problematic_parts else "✅ OK", axis=1)
        
        if stock_errors:
            error_message = "<b>Stock Errors:</b><ul>" + "".join(stock_errors) + "</ul>"
            st.markdown(f":warning: {error_message}", unsafe_allow_html=True)

        # Define the columns to display and their order
        display_cols = [
            "Status", "Description", "Part", "ATC", "Quantity", "Price per unit",
            "Total Unit Cost", "Hardware DRI", "Location", "1-line Justification",
            "Approved", "Delivered", "Transferred"
        ]
        # Filter out any columns that might not exist in the dataframe yet
        display_cols = [col for col in display_cols if col in order_df.columns]
        
        # Reorder and filter the DataFrame
        order_df = order_df[display_cols]

        # Add a "Remove" column to the order dataframe
        order_df.insert(0, "Remove", False)

        edited_order_df = st.data_editor(
            order_df,
            column_config={
                "Remove": st.column_config.CheckboxColumn(required=True),
                "Price per unit": st.column_config.NumberColumn("$ per unit"),
                "Total Unit Cost": st.column_config.NumberColumn("Total Cost"),
                "Location": st.column_config.SelectboxColumn(
                    "Location",
                    help="Select the location for the item",
                    options=["Cork", "Hyderabad", "Hong Kong", "Tokyo"],
                    required=False,
                ),
                "1-line Justification": st.column_config.TextColumn(width="large"),
                "Hardware DRI": st.column_config.TextColumn(),
                "Approved": st.column_config.CheckboxColumn(required=True),
                "Delivered": st.column_config.CheckboxColumn(required=True),
                "Transferred": st.column_config.CheckboxColumn(required=True)
            },
            hide_index=True,
            key="order_editor"
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Remove Selected from Order"):
                rows_to_keep = edited_order_df[~edited_order_df.Remove]
                st.session_state.current_order = rows_to_keep.drop(columns=["Remove"]).to_dict('records')
                save_current_order()
                st.rerun()
        with col2:
            if st.button("Update Order", type="primary"):
                st.session_state.current_order = edited_order_df.drop(columns=["Remove"]).to_dict('records')
                save_current_order()
                st.success("Order updated!")

        st.header("Order Summary")
        total_price = order_df['Total Unit Cost'].sum()
        with st.expander(f"Total Price: ${total_price:,.2f}"):
            location_summary = order_df.groupby('Location')['Total Unit Cost'].sum().reset_index()
            st.dataframe(location_summary, hide_index=True)

        st.header("Archive Order")
        archive_name = st.text_input("Enter a name for this order:")
        if st.button("Archive this Order", type="primary"):
            if archive_name:
                st.session_state.past_orders.append({"name": archive_name, "order": st.session_state.current_order})
                save_past_orders()
                st.session_state.current_order = []
                if os.path.exists(CURRENT_ORDER_FILE):
                    os.remove(CURRENT_ORDER_FILE)
                st.success(f"Order '{archive_name}' archived successfully!")
                st.rerun()
            else:
                st.warning("Please enter a name for the order before archiving.")

    else:
        st.info("Your current order is empty. Add items from the 'Filtered View' tab.")

with tab4:
    st.header("Past Orders")
    if st.session_state.past_orders:
        for i, order_data in enumerate(st.session_state.past_orders):
            with st.expander(order_data["name"]):
                past_order_df = pd.DataFrame(order_data["order"])
                edited_past_order_df = st.data_editor(
                    past_order_df,
                    column_config={
                        "Approved": st.column_config.CheckboxColumn(required=True),
                        "Delivered": st.column_config.CheckboxColumn(required=True),
                        "Transferred": st.column_config.CheckboxColumn(required=True)
                    },
                    hide_index=True,
                    key=f"past_order_editor_{i}"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Update this Order", key=f"update_{i}", type="primary"):
                        st.session_state.past_orders[i]["order"] = edited_past_order_df.to_dict('records')
                        save_past_orders()
                        st.success(f"Order '{order_data['name']}' updated.")
                with col2:
                    if st.button("Delete this Order", key=f"delete_{i}"):
                        st.session_state.past_orders.pop(i)
                        save_past_orders()
                        st.rerun()
    else:
        st.info("You have no past orders.")
