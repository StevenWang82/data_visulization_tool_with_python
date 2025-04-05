import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
import base64
import io
import math # Import math for ceil

# Import the main app instance from parent directory (ensure this works in your structure)
# from app import app # Assuming app.py is in the parent directory

# --- Layout for Data Upload ---
layout = html.Div([
    html.H2("Load CSV Data"),
    dcc.Upload(
        id='upload-data',
        children=html.Div(['Drag and Drop or ', html.A('Select CSV File')]),
        style={
            'width': '95%', 'height': '60px', 'lineHeight': '60px',
            'borderWidth': '1px', 'borderStyle': 'dashed',
            'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
        },
        multiple=False
    ),
    html.Div(id='output-status'),
    html.Hr(),
    html.H4("Data Table Preview:"),
    dcc.Dropdown(
        id='rows-per-page-dropdown',
        options=[{'label': str(i), 'value': i} for i in [10, 25, 50]],
        value=10, # Default page size
        clearable=False,
        style={'width': '200px', 'marginBottom': '10px'} # Adjust style as needed
    ),
    # --- DataTable Container ---
    # The DataTable itself will now handle pagination
    dash_table.DataTable(
        id='data-table',
        columns=[], # Initially empty
        data=[],    # Initially empty
        page_current=0,
        page_size=10, # Initial page size matches dropdown default
        page_action='native', # Enable native pagination
        sort_action='native', # Optional: Enable native sorting
        filter_action='native', # Optional: Enable native filtering
        style_table={'overflowX': 'auto'}, # Ensure horizontal scrolling if needed
        style_cell={
            'height': 'auto',
            # all three widths are needed
            'minWidth': '100px', 'width': '100px', 'maxWidth': '180px',
            'whiteSpace': 'normal'
        },
    ),
    dcc.Store(id='stored-data') # Hidden storage for the full dataset (optional but good practice)
])

# --- Minimal Parsing Function (Keep your existing function) ---
def parse_csv_simple(contents, filename):
    # ... (your existing parse_csv_simple function remains the same) ...
    print(f"parse_csv_simple called for: {filename}")
    if contents is None:
         return None, "No file uploaded."
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if not isinstance(filename, str) or 'csv' not in filename.lower():
            return None, "Invalid file type. Please upload a CSV file."

        print("Attempting to read CSV with UTF-8...")
        try:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            print("CSV read successfully with UTF-8.")
        except UnicodeDecodeError:
            print("UTF-8 decode failed, trying GBK...")
            try:
                df = pd.read_csv(io.StringIO(decoded.decode('gbk')))
                print("CSV read successfully with GBK.")
            except Exception as decode_err:
                error_msg_decode = f"Error decoding file: {str(decode_err)}"
                print(error_msg_decode)
                return None, error_msg_decode

        if df.empty:
            return None, "CSV file is empty."

        return df, f"Successfully loaded '{filename}'."

    except Exception as e:
        error_msg = f"Error processing file '{filename}': {str(e)}"
        print(error_msg)
        return None, error_msg


# --- Callback registration (Simplified) ---
# Define a function to register callbacks, taking app as argument
def register_callbacks(app):
    print("register_callbacks function called in pages/data_upload.py")

    @app.callback(
        [Output('output-status', 'children'),
         Output('data-table', 'columns'),
         Output('data-table', 'data'),
         Output('data-table', 'page_size'),
         Output('stored-data', 'data')], # Output to store the full data
        [Input('upload-data', 'contents'),
         Input('rows-per-page-dropdown', 'value')], # Input for page size
        [State('upload-data', 'filename')]
    )
    def update_table_on_upload_or_pagesize(contents, page_size, filename):
        print(f"--- update_table_on_upload_or_pagesize triggered ---")
        print(f"Filename: {filename}, Page size: {page_size}")

        if contents is None:
            print("No contents, initial state or page size change without data.")
            # Keep existing data if only page size changed, otherwise clear
            # This logic needs refinement if you want to preserve data on page size change
            # For simplicity now, we clear if no content, might need stored-data interaction
            return "Please upload a CSV file.", [], [], page_size, None # Return empty table, updated page size

        df, message = parse_csv_simple(contents, filename)

        if df is not None:
            print("DataFrame created, preparing data table output.")
            status_div = html.Div(message, style={'color': 'green', 'marginTop': '10px'})
            columns = [{"name": i, "id": i} for i in df.columns]
            data = df.to_dict('records') # Provide the FULL data to DataTable
            stored_data_json = df.to_json(orient='split') # Store the full data

            # Reset page_current to 0 when new data is loaded? Usually good UX.
            # DataTable's page_current is handled internally, but you might
            # want to reset it visually. We don't directly control it here.

            return status_div, columns, data, page_size, stored_data_json
        else:
            print(f"DataFrame is None. Error: {message}")
            status_div = html.Div(f"Error: {message}", style={'color': 'red', 'marginTop': '10px'})
            # Return empty table state on error
            return status_div, [], [], page_size, None
