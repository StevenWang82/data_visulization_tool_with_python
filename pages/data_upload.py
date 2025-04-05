import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table, Input, Output, State, callback_context, no_update
import pandas as pd
import numpy as np
import base64
import io

# --- Layout ---
layout = html.Div([
    html.H2("載入 CSV 資料"),
    dcc.Upload(
        id='upload-data',
        children=html.Div(['拖放或 ', html.A('選擇 CSV 檔案')]),
        style={
            'width': '95%', 'height': '60px', 'lineHeight': '60px',
            'borderWidth': '1px', 'borderStyle': 'dashed',
            'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px auto'
        },
        multiple=False
    ),
    html.Div(id='output-status', style={'marginTop': '10px'}),
    html.Hr(),

    # --- Date Conversion Button and Modal ---
    dbc.Button('日期格式轉換', id='open-date-modal-button', n_clicks=0, className="mb-3"), # Use dbc Button and Bootstrap margin
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("日期格式轉換")),
            dbc.ModalBody([
                html.Label("選擇要轉換的欄位:"),
                dcc.Dropdown(
                    id='modal-date-column-dropdown',
                    options=[],
                    placeholder="選擇欄位...",
                    className="mb-3" # Bootstrap margin
                ),
                html.Label("輸入日期格式 (Python strptime):"),
                dbc.Input( # Use dbc Input
                    id='modal-date-format-input',
                    type='text',
                    placeholder="例如: %Y-%m-%d 或 %m/%d/%Y",
                    className="mb-3" # Bootstrap margin
                ),
                html.P("常見格式範例:", style={'fontWeight': 'bold', 'marginBottom': '2px'}),
                html.Ul([
                    html.Li("%Y-%m-%d (例如: 2023-10-26)"),
                    html.Li("%Y/%m/%d (例如: 2023/10/26)"),
                    html.Li("%m/%d/%Y (例如: 10/26/2023)"),
                    html.Li("%Y%m%d (例如: 20231026)"),
                    html.Li("%Y-%m-%d %H:%M:%S (例如: 2023-10-26 14:30:00)"),
                ], style={'fontSize': 'small', 'color': 'grey', 'marginTop': '0px', 'marginBottom': '15px'}),
                html.Div(id='modal-conversion-status', className="text-danger mt-2") # Use Bootstrap text color and margin
            ]),
            dbc.ModalFooter(
                dbc.Button('轉換', id='modal-convert-date-button', n_clicks=0, className="ml-auto")
            ),
        ],
        id='date-conversion-modal',
        is_open=False,
    ),

    # --- Tabs for Preview and Overview ---
    dcc.Tabs(id="data-tabs", value='tab-preview', children=[
        # --- Tab 1: Data Table Preview ---
        dcc.Tab(label='資料表預覽 (Data Preview)', value='tab-preview', children=[
            html.Div([
                html.H4("資料表預覽:", style={'marginTop': '20px'}),
                html.Div([
                    html.Label("每頁顯示行數: ", style={'marginRight': '10px'}),
                    dcc.Dropdown(
                        id='rows-per-page-dropdown',
                        options=[{'label': str(i), 'value': i} for i in [10, 25, 50, 100]],
                        value=10,
                        clearable=False,
                        style={'width': '150px', 'display': 'inline-block', 'verticalAlign': 'middle'}
                    )
                ], style={'marginBottom': '10px'}),
                dash_table.DataTable(
                    id='data-table',
                    columns=[],
                    data=[],
                    page_current=0,
                    page_size=10,
                    page_action='native',
                    sort_action='native',
                    filter_action='none',
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'height': 'auto',
                        'minWidth': '100px', 'width': '100px', 'maxWidth': '180px',
                        'whiteSpace': 'normal',
                        'textAlign': 'left',
                        'padding': '5px'
                    },
                    style_header={
                        'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold'
                    },
                    style_data_conditional=[
                        {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}
                    ]
                )
            ], style={'padding': '10px'})
        ]),

        # --- Tab 2: Data Category Overview ---
        dcc.Tab(label='資料類別檢視 (Data Category Overview)', value='tab-overview', children=[
            html.Div([
                html.H4("資料類別檢視:", style={'marginTop': '20px'}),
                html.Div([
                    html.Label("每頁顯示行數: ", style={'marginRight': '10px'}),
                    dcc.Dropdown(
                        id='category-rows-per-page-dropdown',
                        options=[{'label': str(i), 'value': i} for i in [10, 25, 50]],
                        value=25,
                        clearable=False,
                        style={'width': '150px', 'display': 'inline-block', 'verticalAlign': 'middle'}
                    )
                ], style={'marginBottom': '10px'}),
                dash_table.DataTable(
                    id='category-overview-table',
                    columns=[],
                    data=[],
                    page_current=0,
                    page_size=10,
                    page_action='native',
                    sort_action='native',
                    filter_action='none',
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left', 'padding': '5px', 'minWidth': '80px', 'whiteSpace': 'normal', 'height': 'auto'},
                    style_header={
                        'backgroundColor': 'rgb(220, 220, 220)',
                        'fontWeight': 'bold'
                    },
                    style_data_conditional=[
                        {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(245, 245, 245)'}
                    ]
                ),
                # Removed old date conversion section here
            ], style={'padding': '10px'})
        ]),
    ]),
])

# --- Parsing Function (Simplified - No Auto Date Detection) ---
def parse_csv_simple(contents, filename):
    """Parses CSV, returns df and message."""
    print(f"parse_csv_simple called for: {filename}")
    if contents is None:
         return None, "未上傳檔案。"
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if not isinstance(filename, str) or not filename.lower().endswith('.csv'):
             return None, "檔案類型無效。請上傳 CSV 檔案。"

        print("嘗試使用 UTF-8 解碼讀取 CSV...")
        try:
            # Keep object types as strings initially for manual conversion
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), keep_default_na=False, na_values=[''])
            print("成功使用 UTF-8 讀取 CSV。")
        except UnicodeDecodeError:
            print("UTF-8 解碼失敗，嘗試 GBK...")
            try:
                df = pd.read_csv(io.StringIO(decoded.decode('gbk')), keep_default_na=False, na_values=[''])
                print("成功使用 GBK 讀取 CSV。")
            except Exception as decode_err:
                error_msg_decode = f"解碼檔案時發生錯誤: {str(decode_err)}"
                print(error_msg_decode)
                return None, error_msg_decode
        except pd.errors.ParserError as pe:
             error_msg_parse = f"解析 CSV 時發生錯誤: {str(pe)}. 請檢查檔案格式。"
             print(error_msg_parse)
             return None, error_msg_parse

        if df.empty:
            return None, "CSV 檔案是空的。"

        # --- Removed Auto Date Detection ---
        print("自動日期偵測已移除。")

        return df, f"成功載入 '{filename}'。"

    except Exception as e:
        error_msg = f"處理檔案 '{filename}' 時發生錯誤: {str(e)}"
        print(error_msg)
        return None, error_msg

# --- Helper Function to Generate Category Overview Data ---
def generate_category_overview_data(df):
    """根據 DataFrame 生成資料類別概覽的數據和欄位定義"""
    if df is None or df.empty:
        return [], []

    overview_data = []
    for col in df.columns:
        col_data = df[col]
        dtype = str(col_data.dtype)
        missing_count = int(col_data.isnull().sum())
        unique_count = int(col_data.nunique())
        total_count = len(col_data)
        missing_percentage = f"{(missing_count / total_count * 100):.1f}%" if total_count > 0 else "N/A"

        stats = {'mean': 'N/A', 'std': 'N/A', 'min': 'N/A', 'max': 'N/A'}
        if pd.api.types.is_numeric_dtype(col_data) and not pd.api.types.is_bool_dtype(col_data):
            numeric_data = col_data.dropna()
            if not numeric_data.empty:
                try:
                    stats['mean'] = f"{numeric_data.mean():.2f}" if pd.notna(numeric_data.mean()) else 'N/A'
                    stats['std'] = f"{numeric_data.std():.2f}" if pd.notna(numeric_data.std()) else 'N/A'
                    stats['min'] = f"{numeric_data.min():.2f}" if pd.notna(numeric_data.min()) else 'N/A'
                    stats['max'] = f"{numeric_data.max():.2f}" if pd.notna(numeric_data.max()) else 'N/A'
                except Exception as stat_err:
                     print(f"Error calculating stats for column {col}: {stat_err}")

        overview_data.append({
            '欄位名稱': col,
            '資料類型': dtype,
            '平均值': stats['mean'],
            '標準差': stats['std'],
            '最小值': stats['min'],
            '最大值': stats['max'],
            '唯一值數量': unique_count,
            '缺失值數量': missing_count,
            '缺失比例': missing_percentage,
        })

    columns_definition = [
        {'name': '欄位名稱', 'id': '欄位名稱'},
        {'name': '資料類型', 'id': '資料類型'},
        {'name': '缺失值數量', 'id': '缺失值數量'},
        {'name': '缺失比例', 'id': '缺失比例'},
        {'name': '平均值', 'id': '平均值'},
        {'name': '標準差', 'id': '標準差'},
        {'name': '最小值', 'id': '最小值'},
        {'name': '最大值', 'id': '最大值'},
        {'name': '唯一值數量', 'id': '唯一值數量'},
    ]

    return overview_data, columns_definition

# --- Helper Function to Extract Date Parts ---
def extract_date_parts(df, column_name):
    """Extracts year, month, dayofweek from a datetime column and adds them as new columns."""
    if column_name in df.columns and pd.api.types.is_datetime64_any_dtype(df[column_name]):
        print(f"正在為欄位 '{column_name}' 提取日期部分...")
        base_name = column_name.replace(' ', '_') # Sanitize base name
        # Ensure new column names don't already exist or handle collision
        year_col = f'{base_name}_年'
        month_col = f'{base_name}_月'
        dow_col = f'{base_name}_星期幾'
        dname_col = f'{base_name}_星期名稱'

        if year_col not in df.columns: df[year_col] = df[column_name].dt.year
        if month_col not in df.columns: df[month_col] = df[column_name].dt.month
        if dow_col not in df.columns: df[dow_col] = df[column_name].dt.dayofweek # Monday=0, Sunday=6
        if dname_col not in df.columns:
            day_map = {0: '星期一', 1: '星期二', 2: '星期三', 3: '星期四', 4: '星期五', 5: '星期六', 6: '星期日'}
            df[dname_col] = df[dow_col].map(day_map)
        print(f"成功提取日期部分: {year_col}, {month_col}, {dow_col}, {dname_col}")
    else:
        print(f"欄位 '{column_name}' 不存在或不是日期類型，無法提取日期部分。")
    return df

# --- Callback registration function ---
def register_callbacks(app):
    print("register_callbacks function called in pages/data_upload.py")

    # --- Main Callback for Upload and Page Size Changes ---
    @app.callback(
        [Output('output-status', 'children'),
         Output('data-table', 'columns'),
         Output('data-table', 'data'),
         Output('data-table', 'page_size'),
         Output('category-overview-table', 'columns'),
         Output('category-overview-table', 'data'),
         Output('category-overview-table', 'page_size'),
         Output('stored-data', 'data')],
        [Input('upload-data', 'contents'),
         Input('rows-per-page-dropdown', 'value'),
         Input('category-rows-per-page-dropdown', 'value')],
        [State('upload-data', 'filename'),
         State('stored-data', 'data')]
        # Removed prevent_initial_call to allow updates from stored data on load
    )
    def update_outputs_on_upload_or_pagesize(contents, preview_page_size, category_page_size, filename, stored_data_json):
        ctx = callback_context
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
        print(f"--- update_outputs_on_upload_or_pagesize triggered by: {triggered_id} ---")
        print(f"Filename: {filename}, Preview Page Size: {preview_page_size}, Category Page Size: {category_page_size}")

        # Initialize outputs
        status_msg = "請上傳一個 CSV 檔案。"
        preview_cols, preview_data = [], []
        category_cols, category_data = [], []
        new_stored_data = no_update

        current_preview_page_size = preview_page_size if preview_page_size is not None else 10
        current_category_page_size = category_page_size if category_page_size is not None else 10

        # --- Case 1: New File Upload ---
        if triggered_id == 'upload-data' and contents is not None:
            print("處理新上傳的檔案...")
            df, message = parse_csv_simple(contents, filename) # Simplified parse function

            if df is not None:
                print("檔案解析成功。")
                status_msg = html.Div(message, style={'color': 'green'})
                preview_cols = [{"name": i, "id": i} for i in df.columns]
                preview_data = df.to_dict('records')
                category_data, category_cols = generate_category_overview_data(df)
                new_stored_data = df.to_json(orient='split')
                print("新資料已儲存。")
            else: # Parsing failed
                print(f"檔案解析失敗: {message}")
                status_msg = html.Div(f"錯誤: {message}", style={'color': 'red'})
                preview_cols, preview_data = [], []
                category_cols, category_data = [], []
                new_stored_data = None # Clear stored data on failure

        # --- Case 2: Page Size Change or Initial Load with Stored Data ---
        elif triggered_id in ['rows-per-page-dropdown', 'category-rows-per-page-dropdown'] or (triggered_id is None and stored_data_json):
            print("處理頁面大小變更或從 store 載入。")
            if stored_data_json:
                print("從 store 載入現有資料...")
                try:
                    df = pd.read_json(io.StringIO(stored_data_json), orient='split')
                    preview_cols = [{"name": i, "id": i} for i in df.columns]
                    preview_data = df.to_dict('records')
                    category_data, category_cols = generate_category_overview_data(df)
                    status_msg = "使用已儲存的資料更新檢視。"
                    print("使用已儲存的資料更新表格。")
                except Exception as e:
                    print(f"從 store 載入資料時發生錯誤: {e}")
                    status_msg = html.Div(f"從 store 載入資料時發生錯誤: {e}", style={'color': 'red'})
                    preview_cols, preview_data = [], []
                    category_cols, category_data = [], []
                    new_stored_data = None # Clear stored data on error
            else:
                print("無上傳內容且 store 中無資料。")
                status_msg = "請上傳一個 CSV 檔案。"
        # --- Case 3: Initial load without stored data ---
        elif triggered_id is None and not stored_data_json:
             print("初始載入，無資料。")
             status_msg = "請上傳一個 CSV 檔案。"


        print("--- Main Callback 完成 ---")
        return (status_msg,
                preview_cols, preview_data, current_preview_page_size,
                category_cols, category_data, current_category_page_size,
                new_stored_data)

    # --- Callback to Open/Close Date Conversion Modal ---
    @app.callback(
        Output('date-conversion-modal', 'is_open'),
        [Input('open-date-modal-button', 'n_clicks'),
         Input('modal-convert-date-button', 'n_clicks')], # Close on successful conversion
        [State('date-conversion-modal', 'is_open'),
         State('modal-conversion-status', 'children')], # Check if conversion was successful
        prevent_initial_call=True
    )
    def toggle_date_modal(n_open, n_convert, is_open, conversion_status):
        ctx = callback_context
        button_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
        print(f"toggle_date_modal triggered by: {button_id}")

        # Close modal only if conversion was successful (status message is not red)
        if button_id == 'modal-convert-date-button':
             # Check if the status message indicates success (e.g., not an error Div)
             # A simple check: if it's a Div, assume error for now. Improve if needed.
             is_error = isinstance(conversion_status, html.Div) and 'red' in str(conversion_status.style.get('color', ''))
             if not is_error:
                 print("Conversion successful or no error, closing modal.")
                 return False
             else:
                 print("Conversion error, keeping modal open.")
                 return True # Keep open on error

        if button_id == 'open-date-modal-button' and n_open > 0:
            print("Opening date modal.")
            return not is_open

        return is_open # Keep current state otherwise

    # --- Callback to Populate Modal Dropdown ---
    @app.callback(
        Output('modal-date-column-dropdown', 'options'),
        Input('stored-data', 'data'),
        prevent_initial_call=True
    )
    def update_modal_dropdown(stored_data_json):
        if not stored_data_json:
            return []
        try:
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')
            # Populate with object/string columns suitable for date conversion
            potential_date_cols = df.select_dtypes(include=['object']).columns.tolist()
            options = [{'label': col, 'value': col} for col in potential_date_cols]
            print(f"Updating modal dropdown options: {options}")
            return options
        except Exception as e:
            print(f"Error updating modal dropdown: {e}")
            return []

    # --- Callback for Date Conversion from Modal ---
    @app.callback(
        [Output('stored-data', 'data', allow_duplicate=True),
         Output('modal-conversion-status', 'children'),
         Output('data-table', 'columns', allow_duplicate=True),
         Output('data-table', 'data', allow_duplicate=True),
         Output('category-overview-table', 'columns', allow_duplicate=True),
         Output('category-overview-table', 'data', allow_duplicate=True),
         Output('modal-date-column-dropdown', 'options', allow_duplicate=True)], # Update dropdown after conversion
        Input('modal-convert-date-button', 'n_clicks'),
        [State('modal-date-column-dropdown', 'value'),
         State('modal-date-format-input', 'value'),
         State('stored-data', 'data')],
        prevent_initial_call=True
    )
    def handle_modal_date_conversion(n_clicks, column_to_convert, date_format, stored_data_json):
        print(f"--- handle_modal_date_conversion triggered ---")
        print(f"n_clicks: {n_clicks}, Column: {column_to_convert}, Format: {date_format}")

        if not n_clicks or not column_to_convert or not stored_data_json:
            print("Modal conversion conditions not met.")
            # Return no_update for all outputs if conditions aren't met
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update

        if not date_format:
            print("Error: Date format is missing.")
            return no_update, html.Div("錯誤：請輸入日期格式。", style={'color': 'red'}), no_update, no_update, no_update, no_update, no_update

        try:
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')

            if column_to_convert not in df.columns:
                 print(f"Error: Column '{column_to_convert}' not found.")
                 return no_update, html.Div(f"錯誤：欄位 '{column_to_convert}' 不存在。", style={'color': 'red'}), no_update, no_update, no_update, no_update, no_update

            print(f"Attempting conversion for column '{column_to_convert}' with format '{date_format}'...")
            # Use errors='coerce' to turn unparseable values into NaT
            converted_col = pd.to_datetime(df[column_to_convert], format=date_format, errors='coerce')

            # Check if conversion resulted in all NaT
            if converted_col.isnull().all() and df[column_to_convert].notna().any():
                print("Conversion failed: All values became NaT.")
                error_msg = f"錯誤：無法使用格式 '{date_format}' 解析欄位 '{column_to_convert}' 中的任何值。請檢查格式或欄位內容。"
                return no_update, html.Div(error_msg, style={'color': 'red'}), no_update, no_update, no_update, no_update, no_update

            successful_conversions = converted_col.notna().sum()
            print(f"Successfully converted {successful_conversions} values.")

            # Update the DataFrame column
            df[column_to_convert] = converted_col

            # Extract date parts for the newly converted column
            df = extract_date_parts(df, column_to_convert)

            # Prepare outputs
            new_stored_data = df.to_json(orient='split')
            status_msg = html.Div(f"成功將欄位 '{column_to_convert}' 使用格式 '{date_format}' 轉換為日期，並提取了年/月/星期。", style={'color': 'green'}) # Success message for modal status
            preview_cols = [{"name": i, "id": i} for i in df.columns]
            preview_data = df.to_dict('records')
            category_data, category_cols = generate_category_overview_data(df)

            # Update modal dropdown options (remove converted column if no longer object)
            potential_date_cols = df.select_dtypes(include=['object']).columns.tolist()
            modal_dropdown_options = [{'label': col, 'value': col} for col in potential_date_cols]

            print("Modal conversion successful, updating store, tables, and modal dropdown.")
            return (new_stored_data, status_msg,
                    preview_cols, preview_data,
                    category_cols, category_data,
                    modal_dropdown_options)

        except ValueError as ve:
             print(f"Conversion error (ValueError): {ve}")
             error_msg = f"轉換欄位 '{column_to_convert}' 時發生錯誤：無效的日期格式 '{date_format}' 或欄位包含無法解析的值。錯誤: {ve}"
             return no_update, html.Div(error_msg, style={'color': 'red'}), no_update, no_update, no_update, no_update, no_update
        except Exception as e:
            print(f"Unexpected error during conversion: {e}")
            error_msg = f"轉換欄位 '{column_to_convert}' 時發生未預期錯誤: {e}"
            return no_update, html.Div(error_msg, style={'color': 'red'}), no_update, no_update, no_update, no_update, no_update

# --- Removed old handle_manual_date_conversion callback ---

# Example usage in app.py (ensure this is called):
# from pages import data_upload
# app = dash.Dash(__name__, suppress_callback_exceptions=True)
# server = app.server
# app.layout = html.Div([
#     dcc.Store(id='stored-data'), # Make sure dcc.Store exists in the main layout
#     # ... other layout components
#     html.Div(id='page-content')
# ])
# data_upload.register_callbacks(app)
# # ... rest of app.py
