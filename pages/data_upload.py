import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import base64
import io
from dash import dash_table # Updated import

# Import the main app instance from parent directory
from app import app

# --- Layout for Data Upload ---
layout = html.Div([
    html.H2("Load CSV Data"),
    dcc.Upload(
        id='upload-data', # More general ID
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select CSV File')
        ]),
        style={
            'width': '95%', 'height': '60px', 'lineHeight': '60px',
            'borderWidth': '1px', 'borderStyle': 'dashed',
            'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
        },
        multiple=False
    ),
    html.Div(id='output-status'), # More general ID
    html.Hr(),
    html.H4("Data Table Preview:"),
    dcc.Dropdown(
        id='rows-per-page-dropdown',
        options=[{'label': str(i), 'value': i} for i in [10, 25, 50]],
        value=10,
        clearable=False,
        style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}
    ),
    dcc.Store(id='stored-data') # Hidden storage
])

# --- Minimal Parsing Function ---
def parse_csv_simple(contents, filename):
    print(f"parse_csv_simple called for: {filename}")  # 確認函數被呼叫
    content_type, content_string = contents.split(',')
    print(f"content_type: {content_type}") # 印出 content_type
    # print(f"content_string: {content_string[:100]}...") # 印出 content_string 前 100 字元 (避免過長)
    decoded = base64.b64decode(content_string)
    print("base64 decoded successfully") # 確認 base64 解碼成功
    try:
        if not isinstance(filename, str) or 'csv' not in filename.lower(): # Add check for filename type
             return None, "Invalid file type. Please upload a CSV file." # More specific error

        # Try reading with UTF-8
        print("Attempting to read CSV with UTF-8...")
        try:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            print("CSV read successfully with UTF-8.")
        except UnicodeDecodeError:
            print("UTF-8 decode failed, trying GBK...")
            try:
                df = pd.read_csv(io.StringIO(decoded.decode('gbk'))) # Try GBK encoding
                print("CSV read successfully with GBK.")
            except Exception as decode_err:
                error_msg_decode = f"Error decoding file: {str(decode_err)}"
                print(error_msg_decode)
                return None, error_msg_decode # Return decode error

        if df.empty:
            return None, "CSV file is empty."

        return df, f"Successfully loaded '{filename}'."

    except Exception as e:
        error_msg = f"Error processing file '{filename}': {str(e)}"
        print(error_msg) # Log error to terminal
        return None, error_msg

# --- Callback to update output and store data ---
def update_output(contents, filename, rows_per_page): # More general name
    print(f"--- update_output triggered --- Filename: {filename}, Rows per page: {rows_per_page}")
    print(f"--- Filename type: {type(filename)}, Rows per page type: {type(rows_per_page)}") # Add these print statements
    if contents is None:
        print("No contents, initial state.")
        return html.Div("Please upload a CSV file."), None # Initial state, also return None for stored data

    df, message = parse_csv_simple(contents, filename)

    if df is not None:
        print("DataFrame created, preparing data table output.")
        status_div = html.Div(message, style={'color': 'green', 'marginTop': '10px'}) # Success message in green
        raw_head_str = df.head().to_string()

        # --- DataTable and Pagination ---
        page_current = 1
        page_size = rows_per_page
        page_count = (len(df) + page_size - 1) // page_size # Calculate total pages

        def generate_pagination_controls(page_current, page_count):
            # Basic pagination controls
            return html.Div([
                html.Button("<<", id="page-back-to-first", disabled=page_current <= 1),
                html.Button("<", id="page-previous", disabled=page_current <= 1),
                html.Span(f"Page {page_current} of {page_count}", style={'margin': '0 10px'}),
                html.Button(">", id="page-next", disabled=page_current >= page_count),
                html.Button(">>", id="page-forward-to-last", disabled=page_current >= page_count),
            ])


        pagination_controls = generate_pagination_controls(page_current, page_count)

        # Format data for DataTable
        data = df.iloc[0:page_size].to_dict('records') # Display first page
        columns = [{"name": i, "id": i} for i in df.columns]

        data_table = dash_table.DataTable(
            data=data,
            columns=columns,
            page_current=page_current,
            page_size=page_size,
            page_count=page_count,
            id='data-table' # Important: Keep DataTable id for future callbacks
        )
        
        stored_data_json = df.to_json(orient='split') # Convert DataFrame to JSON

        return status_div, stored_data_json # Return status and stored data
    else:
        print(f"DataFrame is None. Error: {message}")
        status_div = html.Div(message, style={'color': 'red', 'marginTop': '10px'}) # Error message in red
        return status_div, None # Return None for stored data in case of error

# --- Callback registration ---
# Note: The @app.callback decorator needs the 'app' instance imported from app.py
def register_callbacks(app): # Define a function to register callbacks, taking app as argument
    print("register_callbacks function called in pages/data_upload.py") # Add this print statement
    update_output_callback =  app.callback( # Use app instance passed to layout function
        [
     Output('output-status', 'children'), # More general Output ID
     Output('stored-data', 'data') # Output to store
          ],
        [Input('upload-data', 'contents')], # More general Input ID
        [State('upload-data', 'filename'), # More general State ID
         Input('rows-per-page-dropdown', 'value')], # rows_per-page as Input, after filename
    )(update_output) # Register the updated callback function name
    return update_output_callback
