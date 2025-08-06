[README.md](https://github.com/user-attachments/files/21621060/README.md)
# LREE-Orders Application

A Streamlit application for filtering product data from a CSV file, building an order, and managing order history.

## How to Use

1.  **Launch the Application**: Run the app from your terminal using the command:
    ```bash
    streamlit run app.py
    ```

2.  **Upload Data**: Use the sidebar to upload your product data in CSV format. The application will load the data and enable the filtering controls.

3.  **Filter Data**: In the "Filtered View" tab, use the sequential filters at the top of the page to narrow down the product list. Filters are activated from left to right as you make selections.

4.  **Build Your Order**:
    *   Select the checkboxes next to the items you wish to order from the filtered list.
    *   Click the "Add Selected to Order" button.

5.  **Manage the Current Order**:
    *   Navigate to the "Current Order" tab.
    *   Here you can edit the `Quantity`, `Price per unit`, `Location`, and other details for each item.
    *   Use the checkboxes to mark items as `Approved`, `Delivered`, or `Transferred`.
    *   Click "Update Order" to save any changes.
    *   To remove items, select the "Remove" checkbox and click "Remove Selected from Order".

6.  **Archive Your Order**:
    *   Once your order is finalized, enter a unique name for it in the "Archive Order" section.
    *   Click "Archive this Order". This will save the current order to your history and clear the "Current Order" tab.

7.  **View Past Orders**:
    *   Go to the "Past Orders" tab to see a list of all your archived orders.
    *   Expand any order to view its details, update its status, or delete it permanently.

## Upcoming Adjustments

Here is a list of planned features and improvements for future versions:

1.  **Enhanced Past Order View**: Add a total price summary (with a breakdown by location) to each archived order in the "Past Orders" tab.
2.  **Asset Tracking**: In the "Past Orders" tab, implement functionality to expand an item row to create a number of sub-rows matching its "ATC" (Available to Customer) count. These new rows will include fields for "S/N" (Serial Number), "Received" status, and "Current Owner" to enable detailed asset tracking.
3.  **Live Data Integration**: Implement an API connection with Box to automatically fetch the latest product data, transforming the tool into a live application and removing the need for manual CSV uploads.
4.  **Standalone Application**: Package the application into a standalone executable for macOS, allowing it to be run without needing a terminal or a Python environment.
