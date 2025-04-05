import dash
from dash import dcc, html, dash_table, Input, Output, State, callback_context
import pandas as pd
import numpy as np
import base64
import io

# --- Layout for Data Upload ---
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

    # --- Tabs for Preview and Overview ---
    dcc.Tabs(id="data-tabs", value='tab-preview', children=[
        # --- Tab 1: Data Category Overview ---
        dcc.Tab(label='資料類別檢視 (Data Category Overview)', value='tab-overview', children=[
            html.Div([
                html.H4("資料類別檢視:", style={'marginTop': '20px'}),
                html.Div([ # Wrap dropdown in a div
                    html.Label("每頁顯示行數: ", style={'marginRight': '10px'}),
                    dcc.Dropdown(
                        id='category-rows-per-page-dropdown', # New ID for category view dropdown
                        options=[{'label': str(i), 'value': i} for i in [10, 25, 50]], # Options for category view
                        value=10, # Default page size
                        clearable=False,
                        style={'width': '150px', 'display': 'inline-block', 'verticalAlign': 'middle'}
                    )
                ], style={'marginBottom': '10px'}),
                dash_table.DataTable(
                    id='category-overview-table', # New ID for category table
                    columns=[],
                    data=[],
                    page_current=0,
                    page_size=10, # Initial page size
                    page_action='native',
                    sort_action='native',
                    filter_action='native', # Allow filtering if needed, though less common here
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left', 'padding': '5px', 'minWidth': '80px', 'whiteSpace': 'normal', 'height': 'auto'},
                    style_header={
                        'backgroundColor': 'rgb(220, 220, 220)',
                        'fontWeight': 'bold'
                    },
                    style_data_conditional=[
                        {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(245, 245, 245)'}
                    ]
                )
            ], style={'padding': '10px'})
        ]),

        # --- Tab 2: Data Table Preview ---
        dcc.Tab(label='資料表預覽 (Data Preview)', value='tab-preview', children=[
            html.Div([
                html.H4("資料表預覽:", style={'marginTop': '20px'}),
                html.Div([ # Wrap dropdown in a div
                    html.Label("每頁顯示行數: ", style={'marginRight': '10px'}),
                    dcc.Dropdown(
                        id='rows-per-page-dropdown', # Original ID for preview dropdown
                        options=[{'label': str(i), 'value': i} for i in [10, 25, 50, 100]],
                        value=10, # Default page size
                        clearable=False,
                        style={'width': '150px', 'display': 'inline-block', 'verticalAlign': 'middle'}
                    )
                ], style={'marginBottom': '10px'}),
                dash_table.DataTable(
                    id='data-table', # Original ID for preview table
                    columns=[],
                    data=[],
                    page_current=0,
                    page_size=10,
                    page_action='native',
                    sort_action='native',
                    filter_action='native',
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
    ]),
    # Removed the old separate sections for overview and preview
])

# --- Parsing Function (Keep original) ---
def parse_csv_simple(contents, filename):
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
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            print("成功使用 UTF-8 讀取 CSV。")
        except UnicodeDecodeError:
            print("UTF-8 解碼失敗，嘗試 GBK...")
            try:
                df = pd.read_csv(io.StringIO(decoded.decode('gbk')))
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

        return df, f"成功載入 '{filename}'。"

    except Exception as e:
        error_msg = f"處理檔案 '{filename}' 時發生錯誤: {str(e)}"
        print(error_msg)
        return None, error_msg

# --- Modified Helper Function to Generate Category Overview Data ---
def generate_category_overview_data(df):
    """根據 DataFrame 生成資料類別概覽的數據和欄位定義"""
    if df is None or df.empty:
        return [], [] # Return empty data and columns

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
        {'name': '平均值', 'id': '平均值'},
        {'name': '標準差', 'id': '標準差'},
        {'name': '最小值', 'id': '最小值'},
        {'name': '最大值', 'id': '最大值'},
        {'name': '唯一值數量', 'id': '唯一值數量'},
        {'name': '缺失值數量', 'id': '缺失值數量'},
        {'name': '缺失比例', 'id': '缺失比例'},
    ]

    return overview_data, columns_definition # Return data and columns separately

# --- Callback registration function ---
def register_callbacks(app):
    print("register_callbacks function called in pages/data_upload.py")

    @app.callback(
        [Output('output-status', 'children'),
         Output('data-table', 'columns'),
         Output('data-table', 'data'),
         Output('data-table', 'page_size'),
         Output('category-overview-table', 'columns'), # Output for category table columns
         Output('category-overview-table', 'data'),    # Output for category table data
         Output('category-overview-table', 'page_size'),# Output for category table page size
         Output('stored-data', 'data')],
        [Input('upload-data', 'contents'),
         Input('rows-per-page-dropdown', 'value'),      # Input for preview page size
         Input('category-rows-per-page-dropdown', 'value')], # Input for category page size
        [State('upload-data', 'filename'),
         State('stored-data', 'data')] # Get existing stored data if only page size changes
    )
    def update_outputs(contents, preview_page_size, category_page_size, filename, stored_data_json):
        ctx = callback_context
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
        print(f"--- update_outputs triggered by: {triggered_id} ---")
        print(f"Filename: {filename}, Preview Page Size: {preview_page_size}, Category Page Size: {category_page_size}")

        # Initialize outputs
        status_msg = "請上傳一個 CSV 檔案。"
        preview_cols = []
        preview_data = []
        category_cols = []
        category_data = []
        new_stored_data = dash.no_update # Avoid overwriting stored data unless new upload

        # Determine current page sizes (use defaults if None initially)
        current_preview_page_size = preview_page_size if preview_page_size is not None else 10
        current_category_page_size = category_page_size if category_page_size is not None else 10

        # --- Case 1: New File Upload ---
        if triggered_id == 'upload-data' and contents is not None:
            print("處理新上傳的檔案...")
            df, message = parse_csv_simple(contents, filename)
            if df is not None:
                print("檔案解析成功。")
                status_msg = html.Div(message, style={'color': 'green'})
                # Prepare Preview Table
                preview_cols = [{"name": i, "id": i} for i in df.columns]
                preview_data = df.to_dict('records')
                # Prepare Category Overview Table
                category_data, category_cols = generate_category_overview_data(df)
                # Store the new data
                new_stored_data = df.to_json(orient='split')
                print("新資料已儲存。")
            else:
                print(f"檔案解析失敗: {message}")
                status_msg = html.Div(f"錯誤: {message}", style={'color': 'red'})
                # Clear tables and stored data on error
                preview_cols, preview_data = [], []
                category_cols, category_data = [], []
                new_stored_data = None
        # --- Case 2: Page Size Change (or initial load without upload) ---
        else:
            print("處理頁面大小變更或初始載入。")
            if stored_data_json: # Check if data exists in the store
                print("從 store 載入現有資料...")
                try:
                    df = pd.read_json(io.StringIO(stored_data_json), orient='split')
                    # Update tables with existing data
                    preview_cols = [{"name": i, "id": i} for i in df.columns]
                    preview_data = df.to_dict('records')
                    category_data, category_cols = generate_category_overview_data(df)
                    status_msg = "使用已儲存的資料更新檢視。" # Update status
                    print("使用已儲存的資料更新表格。")
                except Exception as e:
                    print(f"從 store 載入資料時發生錯誤: {e}")
                    status_msg = html.Div(f"從 store 載入資料時發生錯誤: {e}", style={'color': 'red'})
                    preview_cols, preview_data = [], []
                    category_cols, category_data = [], []
                    new_stored_data = None # Clear stored data if loading fails
            else:
                # No upload and no stored data (initial load)
                print("無上傳內容且 store 中無資料。")
                status_msg = "請上傳一個 CSV 檔案。"
                # Keep tables empty

        # Always return all outputs
        print("--- Callback 完成 ---")
        return (status_msg,
                preview_cols, preview_data, current_preview_page_size,
                category_cols, category_data, current_category_page_size,
                new_stored_data)

# --- Ensure this function is called in your main app.py ---
# Example in app.py:
# from pages import data_upload
# app = dash.Dash(__name__, suppress_callback_exceptions=True)
# server = app.server
# app.layout = ... # Your main layout including page content div and dcc.Store(id='stored-data')
# data_upload.register_callbacks(app)
# ... (rest of your app.py)
