import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table, Input, Output, State, callback_context, no_update
import pandas as pd
import numpy as np
import base64 # 用於處理檔案上傳
import io # 用於處理檔案上傳
import json # 用於處理篩選狀態

# --- 頁面佈局 ---
layout = html.Div([
    # Data Stores
    dcc.Store(id='stored-data'), # Stores the original uploaded/converted DataFrame JSON
    dcc.Store(id='filtered-data-store'), # Stores the currently displayed (potentially filtered) DataFrame JSON
    dcc.Store(id='filter-state-store'), # Stores the state of the filter controls

    html.H3("載入 CSV 資料"),
    dcc.Upload(
        id='upload-data',
        children=html.Div(['拖放或 ', html.A('選擇 CSV 檔案')]),
        style={
            'width': '95%', 'height': '60px', 'lineHeight': '60px',
            'borderWidth': '1px', 'borderStyle': 'dashed',
            'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px auto'
        },
        multiple=False # 僅允許上傳單一檔案
    ),
    html.Div(id='output-status', style={'marginTop': '10px'}),
    html.Hr(),

    # --- 按鈕區域 ---
    html.Div([
        dbc.Button('日期格式轉換', id='open-date-modal-button', n_clicks=0, className="me-2 mb-3"), # me-2 for margin-end
        dbc.Button('資料篩選', id='open-filter-modal-button', n_clicks=0, className="mb-3"), # 新增篩選按鈕
    ]),

    # --- 日期轉換彈出視窗 ---
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("日期格式轉換")),
            dbc.ModalBody([
                html.Label("選擇要轉換的欄位:"),
                dcc.Dropdown(
                    id='modal-date-column-dropdown',
                    options=[],
                    placeholder="選擇欄位...",
                    className="mb-3" # Bootstrap 邊距
                ),
                html.Label("輸入日期格式 (Python strptime):"),
                dbc.Input( # 使用 dbc 輸入框
                    id='modal-date-format-input',
                    type='text',
                    placeholder="例如: %Y-%m-%d ",
                    className="mb-3" # Bootstrap 邊距
                ),
                html.P("常見格式範例:", style={'fontWeight': 'bold', 'marginBottom': '2px'}),
                html.Ul([
                    html.Li("%Y-%m-%d (例如: 2023-10-26)"),
                    html.Li("%Y/%m/%d (例如: 2023/10/26)"),
                    html.Li("%m/%d/%Y (例如: 10/26/2023)"),
                    html.Li("%Y%m%d (例如: 20231026)"),
                    html.Li("%Y-%m-%d %H:%M:%S (例如: 2023-10-26 14:30:00)"),
                ], style={'fontSize': 'small', 'color': 'grey', 'marginTop': '0px', 'marginBottom': '15px'}),
                html.Div(id='modal-conversion-status', className="text-danger mt-2") # 使用 Bootstrap 文字顏色和邊距
            ]),
            dbc.ModalFooter(
                dbc.Button('轉換', id='modal-convert-date-button', n_clicks=0, className="ml-auto")
            ),
        ],
        id='date-conversion-modal',
        is_open=False,
    ),

    # --- 資料篩選彈出視窗 ---
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("資料篩選")),
            dbc.ModalBody([
                html.Label("選擇要篩選的欄位:"),
                dcc.Dropdown(
                    id='filter-column-dropdown',
                    options=[],
                    placeholder="選擇欄位...",
                    multi=True, # 允許多選
                    className="mb-3"
                ),
                html.Div(id='filter-controls-container', children=[]), # 動態生成篩選控制項
                html.Div(id='filter-status', className="text-danger mt-2")
            ]),
            dbc.ModalFooter([
                dbc.Button('重設', id='reset-filter-button', n_clicks=0, color="secondary", className="me-auto"), # 重設按鈕
                dbc.Button('套用篩選', id='apply-filter-button', n_clicks=0, className="ml-auto")
            ]),
        ],
        id='filter-modal',
        is_open=False,
        size="lg", # 可以調整大小 large
    ),

    # --- 資料預覽與總覽分頁 ---
    dcc.Tabs(id="data-tabs", value='tab-preview', children=[
        # --- 分頁 1：資料表預覽 ---
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

        # --- 分頁 2：資料類別總覽 ---
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
                # 已移除舊的日期轉換區塊
            ], style={'padding': '10px'})
        ]),
    ]),
])

# --- 解析函式 ---
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
            # 初始保留物件類型為字串，以便手動轉換
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

        # --- 已移除自動日期偵測 ---
        print("自動日期偵測已移除。")

        return df, f"成功載入 '{filename}'。"

    except Exception as e:
        error_msg = f"處理檔案 '{filename}' 時發生錯誤: {str(e)}"
        print(error_msg)
        return None, error_msg

# --- 輔助函式：產生資料類別總覽 ---
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
            # Ensure data is numeric before calculating stats
            numeric_data = pd.to_numeric(col_data, errors='coerce').dropna()
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

# --- 輔助函式：提取日期部分 ---
def extract_date_parts(df, column_name):
    """Extracts year, month, dayofweek from a datetime column and adds them as new columns."""
    if column_name in df.columns and pd.api.types.is_datetime64_any_dtype(df[column_name]):
        print(f"正在為欄位 '{column_name}' 提取日期部分...")
        base_name = column_name.replace(' ', '_') # 清理基底名稱
        # 確保新欄位名稱不存在或處理衝突
        year_col = f'{base_name}_年'
        month_col = f'{base_name}_月'
        dow_col = f'{base_name}_星期幾'
        dname_col = f'{base_name}_星期名稱'

        if year_col not in df.columns: df[year_col] = df[column_name].dt.year
        if month_col not in df.columns: df[month_col] = df[column_name].dt.month
        if dow_col not in df.columns: df[dow_col] = df[column_name].dt.dayofweek # 週一=0, 週日=6
        if dname_col not in df.columns:
            day_map = {0: '星期一', 1: '星期二', 2: '星期三', 3: '星期四', 4: '星期五', 5: '星期六', 6: '星期日'}
            df[dname_col] = df[dow_col].map(day_map)
        print(f"成功提取日期部分: {year_col}, {month_col}, {dow_col}, {dname_col}")
    else:
        print(f"欄位 '{column_name}' 不存在或不是日期類型，無法提取日期部分。")
    return df

# --- 回調函式註冊 ---
def register_callbacks(app):
    print("register_callbacks function called in pages/data_upload.py")

    # --- 主要回調：處理檔案上傳與頁面大小變更 ---
    @app.callback(
        [Output('output-status', 'children'),
         Output('data-table', 'columns'),
         Output('data-table', 'data'),
         Output('data-table', 'page_size'),
         Output('category-overview-table', 'columns'),
         Output('category-overview-table', 'data'),
         Output('category-overview-table', 'page_size'),
         Output('stored-data', 'data'), # Output for original data
         Output('filtered-data-store', 'data'), # Output for displayed data
         Output('filter-column-dropdown', 'options'), # Output for filter dropdown
         Output('filter-state-store', 'data')], # Output to clear filter state on new upload
        [Input('upload-data', 'contents'),
         Input('rows-per-page-dropdown', 'value'),
         Input('category-rows-per-page-dropdown', 'value'),
         Input('filtered-data-store', 'data')], # Use filtered data to update tables on page change
        [State('upload-data', 'filename'),
         State('stored-data', 'data')] # Add state for original data to get columns
    )
    def update_outputs_on_upload_or_pagesize(contents, preview_page_size, category_page_size, filtered_data_json, filename, original_data_json):
        ctx = callback_context
        triggered_input = ctx.triggered[0]['prop_id'] if ctx.triggered else 'initial load'
        print(f"--- update_outputs_on_upload_or_pagesize triggered by: {triggered_input} ---")
        print(f"Filename: {filename}, Preview Page Size: {preview_page_size}, Category Page Size: {category_page_size}")

        # Initialize outputs
        status_msg = "請上傳一個 CSV 檔案。"
        preview_cols, preview_data = [], []
        category_cols, category_data = [], []
        original_data_out = no_update
        filtered_data_out = no_update
        filter_options_out = no_update
        filter_state_out = no_update

        current_preview_page_size = preview_page_size if preview_page_size is not None else 10
        current_category_page_size = category_page_size if category_page_size is not None else 10

        # --- Case 1: New file upload ---
        if triggered_input.startswith('upload-data'):
            print("處理新上傳的檔案...")
            df, message = parse_csv_simple(contents, filename)

            if df is not None:
                print("檔案解析成功。")
                status_msg = html.Div(message, style={'color': 'green'})
                df_json = df.to_json(orient='split')
                original_data_out = df_json # Store original data
                filtered_data_out = df_json # Initially, filtered data is the same as original
                filter_options_out = [{'label': col, 'value': col} for col in df.columns]
                filter_state_out = {} # Clear any previous filter state
                # Update tables immediately with the new data
                preview_cols = [{"name": i, "id": i} for i in df.columns]
                preview_data = df.to_dict('records')
                category_data, category_cols = generate_category_overview_data(df)
                print("新資料已儲存至 stored-data 和 filtered-data-store。篩選下拉選單已更新。篩選狀態已清除。")
            else: # Parse failed
                print(f"檔案解析失敗: {message}")
                status_msg = html.Div(f"錯誤: {message}", style={'color': 'red'})
                original_data_out = None
                filtered_data_out = None
                filter_options_out = []
                filter_state_out = {} # Clear filter state on error too
                preview_cols, preview_data = [], []
                category_cols, category_data = [], []

        # --- Case 2: Page size change or initial load using stored (filtered) data ---
        # Use filtered_data_json which comes from Input('filtered-data-store', 'data')
        elif triggered_input.startswith(('rows-per-page-dropdown', 'category-rows-per-page-dropdown', 'filtered-data-store')) or \
             (triggered_input == 'initial load' and filtered_data_json):
            print(f"處理事件: {triggered_input} 或從 filtered-data-store 載入。")
            if filtered_data_json:
                print("從 filtered-data-store 載入現有資料...")
                try:
                    # Read the *filtered* data for display
                    df_filtered = pd.read_json(io.StringIO(filtered_data_json), orient='split')
                    preview_cols = [{"name": i, "id": i} for i in df_filtered.columns]
                    preview_data = df_filtered.to_dict('records')
                    category_data, category_cols = generate_category_overview_data(df_filtered)
                    # Only update status if triggered by store load, not page size change
                    if triggered_input.startswith('filtered-data-store') or triggered_input == 'initial load':
                        status_msg = "使用已儲存的資料更新檢視。"
                        print("使用 filtered-data-store 的資料更新表格。")
                    else:
                         print("使用 filtered-data-store 的資料更新表格 (頁面大小變更)。")
                         status_msg = no_update # Don't change status on page size change

                    # Filter options should always reflect original columns. Update them if original data exists.
                    if original_data_json:
                        try:
                            df_original = pd.read_json(io.StringIO(original_data_json), orient='split')
                            filter_options_out = [{'label': col, 'value': col} for col in df_original.columns]
                            print("篩選下拉選單選項已根據原始資料更新。")
                        except Exception as e_orig:
                            print(f"從 stored-data 讀取欄位以更新篩選選項時發生錯誤: {e_orig}")
                            filter_options_out = [] # Clear on error
                    else:
                         # If original data isn't available for some reason, try using filtered columns
                         filter_options_out = [{'label': col, 'value': col} for col in df_filtered.columns]
                         print("警告：無法讀取原始資料，篩選下拉選單選項基於過濾後的資料。")


                except Exception as e:
                    print(f"從 filtered-data-store 載入資料時發生錯誤: {e}")
                    status_msg = html.Div(f"從 filtered-data-store 載入資料時發生錯誤: {e}", style={'color': 'red'})
                    preview_cols, preview_data = [], []
                    category_cols, category_data = [], []
                    # Don't clear original_data_out here
                    filtered_data_out = None # Clear filtered data on error
                    filter_options_out = []
            else:
                print("無上傳內容且 filtered-data-store 中無資料。")
                status_msg = "請上傳一個 CSV 檔案。"
                filter_options_out = []

        # --- Case 3: Initial load and no stored data ---
        elif triggered_input == 'initial load' and not filtered_data_json:
             print("初始載入，無資料。")
             status_msg = "請上傳一個 CSV 檔案。"
             filter_options_out = []


        print("--- Main Callback 完成 ---")
        return (status_msg,
                preview_cols, preview_data, current_preview_page_size,
                category_cols, category_data, current_category_page_size,
                original_data_out, filtered_data_out, filter_options_out, filter_state_out)

    # --- 回調：開啟/關閉日期轉換彈出視窗 ---
    @app.callback(
        Output('date-conversion-modal', 'is_open'),
        [Input('open-date-modal-button', 'n_clicks'),
         Input('modal-convert-date-button', 'n_clicks')], # 轉換成功時關閉
        [State('date-conversion-modal', 'is_open'),
         State('modal-conversion-status', 'children')], # 檢查轉換是否成功
        prevent_initial_call=True
    )
    def toggle_date_modal(n_open, n_convert, is_open, conversion_status):
        ctx = callback_context
        button_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
        print(f"toggle_date_modal triggered by: {button_id}")

        # 僅在轉換成功時關閉彈出視窗 (狀態訊息非紅色)
        if button_id == 'modal-convert-date-button':
             # 檢查狀態訊息是否表示成功 (例如，不是錯誤的 Div)
             # 簡單檢查：如果是 Div，暫時假設為錯誤。如有需要再改進。
             is_error = isinstance(conversion_status, html.Div) and 'red' in str(conversion_status.style.get('color', ''))
             if not is_error:
                 print("Conversion successful or no error, closing modal.")
                 return False
             else:
                 print("Conversion error, keeping modal open.")
                 return True # 發生錯誤時保持開啟

        if button_id == 'open-date-modal-button' and n_open > 0:
            print("Opening date modal.")
            return not is_open

        return is_open # 其他情況下保持目前狀態

    # --- 回調：填入彈出視窗下拉選單 ---
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
            # 填入適合日期轉換的物件/字串類型欄位
            potential_date_cols = df.select_dtypes(include=['object']).columns.tolist()
            options = [{'label': col, 'value': col} for col in potential_date_cols]
            print(f"Updating modal dropdown options: {options}")
            return options
        except Exception as e:
            print(f"Error updating modal dropdown: {e}")
            return []

    # --- 回調：從彈出視窗進行日期轉換 ---
    @app.callback(
        [Output('stored-data', 'data', allow_duplicate=True),
         Output('modal-conversion-status', 'children'),
         Output('data-table', 'columns', allow_duplicate=True),
         Output('data-table', 'data', allow_duplicate=True),
         Output('category-overview-table', 'columns', allow_duplicate=True),
         Output('category-overview-table', 'data', allow_duplicate=True),
         Output('modal-date-column-dropdown', 'options', allow_duplicate=True),
         Output('filtered-data-store', 'data', allow_duplicate=True)], # Update filtered data as well
        Input('modal-convert-date-button', 'n_clicks'),
        [State('modal-date-column-dropdown', 'value'),
         State('modal-date-format-input', 'value'),
         State('stored-data', 'data')], # Read from original data
        prevent_initial_call=True
    )
    def handle_modal_date_conversion(n_clicks, column_to_convert, date_format, stored_data_json):
        print(f"--- handle_modal_date_conversion triggered ---")
        print(f"n_clicks: {n_clicks}, Column: {column_to_convert}, Format: {date_format}")

        if not n_clicks or not column_to_convert or not stored_data_json:
            print("Modal conversion conditions not met.")
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

        if not date_format:
            print("Error: Date format is missing.")
            return no_update, html.Div("錯誤：請輸入日期格式。", style={'color': 'red'}), no_update, no_update, no_update, no_update, no_update, no_update

        try:
            # Operate on the original data
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')

            if column_to_convert not in df.columns:
                 print(f"Error: Column '{column_to_convert}' not found.")
                 return no_update, html.Div(f"錯誤：欄位 '{column_to_convert}' 不存在。", style={'color': 'red'}), no_update, no_update, no_update, no_update, no_update, no_update

            print(f"Attempting conversion for column '{column_to_convert}' with format '{date_format}'...")
            original_dtype = df[column_to_convert].dtype
            converted_col = pd.to_datetime(df[column_to_convert], format=date_format, errors='coerce')

            if converted_col.isnull().all() and df[column_to_convert].notna().any():
                print("Conversion failed: All values became NaT.")
                error_msg = f"錯誤：無法使用格式 '{date_format}' 解析欄位 '{column_to_convert}' 中的任何值。請檢查格式或欄位內容。"
                return no_update, html.Div(error_msg, style={'color': 'red'}), no_update, no_update, no_update, no_update, no_update, no_update

            successful_conversions = converted_col.notna().sum()
            print(f"Successfully converted {successful_conversions} values.")

            # Update DataFrame column in the original data copy
            df[column_to_convert] = converted_col

            # Extract date parts if conversion was successful
            if successful_conversions > 0 and pd.api.types.is_datetime64_any_dtype(df[column_to_convert]):
                 df = extract_date_parts(df, column_to_convert)

            # Prepare outputs
            new_stored_data = df.to_json(orient='split') # Save updated original data
            new_filtered_data = new_stored_data # Update filtered data to reflect conversion
            status_msg = html.Div(f"成功將欄位 '{column_to_convert}' 使用格式 '{date_format}' 轉換為日期，並提取了年/月/星期。", style={'color': 'green'})
            preview_cols = [{"name": i, "id": i} for i in df.columns]
            preview_data = df.to_dict('records')
            category_data, category_cols = generate_category_overview_data(df)

            # Update modal dropdown options (remove column if no longer object/string)
            potential_date_cols = df.select_dtypes(include=['object']).columns.tolist()
            modal_dropdown_options = [{'label': col, 'value': col} for col in potential_date_cols]

            print("Modal conversion successful, updating stored-data, filtered-data-store, tables, and modal dropdown.")
            return (new_stored_data, status_msg,
                    preview_cols, preview_data,
                    category_cols, category_data,
                    modal_dropdown_options,
                    new_filtered_data) # Return updated filtered data

        except ValueError as ve:
             print(f"Conversion error (ValueError): {ve}")
             error_msg = f"轉換欄位 '{column_to_convert}' 時發生錯誤：無效的日期格式 '{date_format}' 或欄位包含無法解析的值。錯誤: {ve}"
             return no_update, html.Div(error_msg, style={'color': 'red'}), no_update, no_update, no_update, no_update, no_update, no_update
        except Exception as e:
            print(f"Unexpected error during conversion: {e}")
            error_msg = f"轉換欄位 '{column_to_convert}' 時發生未預期錯誤: {e}"
            return no_update, html.Div(error_msg, style={'color': 'red'}), no_update, no_update, no_update, no_update, no_update, no_update


    # --- 回調：開啟/關閉篩選彈出視窗 ---
    @app.callback(
        Output('filter-modal', 'is_open'),
        [Input('open-filter-modal-button', 'n_clicks'),
         Input('apply-filter-button', 'n_clicks'),
         Input('reset-filter-button', 'n_clicks')], # Add reset button as trigger to close
        [State('filter-modal', 'is_open')],
        prevent_initial_call=True
    )
    def toggle_filter_modal(n_open, n_apply, n_reset, is_open):
        ctx = callback_context
        button_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
        print(f"toggle_filter_modal triggered by: {button_id}")

        if button_id == 'open-filter-modal-button':
            print("Opening filter modal.")
            return not is_open
        elif button_id in ['apply-filter-button', 'reset-filter-button']:
             print(f"Closing filter modal due to {button_id}.")
             return False # Close modal on apply or reset for now

        return is_open # Keep current state otherwise


    # --- 回調：動態生成篩選控制項 ---
    @app.callback(
        Output('filter-controls-container', 'children'),
        [Input('filter-column-dropdown', 'value'),
         Input('stored-data', 'data')], # Need original data to determine types and values
        [State('filter-state-store', 'data')], # To potentially restore previous filter values
        prevent_initial_call=True
    )
    def update_filter_controls(selected_columns, stored_data_json, filter_state):
        print(f"--- update_filter_controls triggered. Selected: {selected_columns} ---")
        if not selected_columns or not stored_data_json:
            print("No columns selected or no data, clearing filter controls.")
            return []

        try:
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')
            filter_state = filter_state or {} # Ensure filter_state is a dict
            controls = []

            for col in selected_columns:
                if col not in df.columns:
                    print(f"Warning: Column '{col}' selected for filtering not found in DataFrame.")
                    continue

                col_series = df[col]
                col_filter_state = filter_state.get(col, {}) # Get saved state for this column

                control_card_content = [dbc.Label(f"篩選欄位: {col} ({col_series.dtype})", className="fw-bold")]

                # --- 類別變數 (Object/String/Category) ---
                if pd.api.types.is_object_dtype(col_series) or pd.api.types.is_string_dtype(col_series) or pd.api.types.is_categorical_dtype(col_series):
                    unique_values = col_series.unique()
                    # Limit checklist options for performance and usability
                    if len(unique_values) < 50: # Increased limit slightly
                        options = [{'label': str(val), 'value': str(val)} for val in unique_values if pd.notna(val)]
                        # Restore checked values from state if available
                        value = col_filter_state.get('values', [opt['value'] for opt in options]) # Default to all selected
                        control_card_content.append(
                            dbc.Checklist(
                                id={'type': 'filter-control', 'index': col, 'control': 'checklist'},
                                options=options,
                                value=value,
                                inline=True,
                                className="mb-2"
                            )
                        )
                    else:
                        control_card_content.append(html.P(f"欄位 '{col}' 的唯一值過多 ({len(unique_values)})，暫不提供類別篩選。", className="text-muted small"))

                # --- 數值變數 (Integer/Float) ---
                elif pd.api.types.is_numeric_dtype(col_series) and not pd.api.types.is_bool_dtype(col_series):
                    numeric_col = pd.to_numeric(col_series, errors='coerce').dropna()
                    if not numeric_col.empty:
                        # Round min/max and determine step for 2 decimal places
                        is_integer = pd.api.types.is_integer_dtype(numeric_col)
                        if is_integer:
                            min_val = np.floor(numeric_col.min())
                            max_val = np.ceil(numeric_col.max())
                            step = 1
                            mark_format = '{:.0f}' # Format for integers
                        else: # Float
                            min_val = np.round(numeric_col.min(), 2)
                            max_val = np.round(numeric_col.max(), 2)
                            step = 0.01
                            mark_format = '{:.2f}' # Format for floats

                        # Ensure min_val is strictly less than max_val for linspace/slider
                        if min_val >= max_val:
                             if is_integer: max_val = min_val + 1
                             else: max_val = min_val + 0.01 # Add minimal step if equal after rounding

                        # Restore slider range from state if available, ensuring it respects rounded min/max
                        saved_range = col_filter_state.get('range', [min_val, max_val])
                        # Clamp saved range to the actual min/max
                        slider_value = [max(min_val, saved_range[0]), min(max_val, saved_range[1])]


                        # Generate marks using the rounded values and appropriate format
                        marks_dict = {}
                        try:
                            # Generate 5 marks including endpoints
                            mark_values = np.linspace(min_val, max_val, 5)
                            marks_dict = {num: mark_format.format(num) for num in mark_values}
                        except Exception as mark_err:
                             print(f"Could not generate marks for {col}: {mark_err}. Using min/max only.")
                             marks_dict = {min_val: mark_format.format(min_val), max_val: mark_format.format(max_val)}


                        control_card_content.extend([ # Use extend with a list
                            dcc.RangeSlider(
                                id={'type': 'filter-control', 'index': col, 'control': 'range-slider'},
                                min=min_val,
                                max=max_val,
                                step=step,
                                value=slider_value,
                                marks=marks_dict, # Use the generated marks
                                tooltip={"placement": "bottom", "always_visible": False},
                            ),
                            dbc.Row([
                                dbc.Col(dbc.Input(
                                    id={'type': 'filter-control', 'index': col, 'control': 'min-input'},
                                    type='number',
                                    value=slider_value[0], # Initial min value
                                    min=min_val,
                                    max=max_val,
                                    step=step,
                                    placeholder="最小值",
                                    debounce=True, # Update only after user stops typing for a bit
                                    size="sm"
                                ), width=6),
                                dbc.Col(dbc.Input(
                                    id={'type': 'filter-control', 'index': col, 'control': 'max-input'},
                                    type='number',
                                    value=slider_value[1], # Initial max value
                                    min=min_val,
                                    max=max_val,
                                    step=step,
                                    placeholder="最大值",
                                    debounce=True,
                                    size="sm"
                                ), width=6),
                            ], className="mt-2 mb-3"),
                            html.Div(
                                id={'type': 'filter-control', 'index': col, 'control': 'range-display'},
                                children=f"目前範圍: {mark_format.format(slider_value[0])} - {mark_format.format(slider_value[1])}",
                                className="text-muted small"
                            )
                        ]) # Close the list for extend
                    else:
                         control_card_content.append(html.P(f"欄位 '{col}' 不包含有效的數值資料。", className="text-muted small"))

                # --- 日期時間變數 ---
                elif pd.api.types.is_datetime64_any_dtype(col_series):
                    datetime_col = pd.to_datetime(col_series, errors='coerce').dropna()
                    if not datetime_col.empty:
                        min_date = datetime_col.min().date()
                        max_date = datetime_col.max().date()
                        # Restore start/end dates from state if available
                        start_date = col_filter_state.get('start_date', min_date)
                        end_date = col_filter_state.get('end_date', max_date)
                        control_card_content.append(
                            dcc.DatePickerRange(
                                id={'type': 'filter-control', 'index': col, 'control': 'date-range'},
                                min_date_allowed=min_date,
                                max_date_allowed=max_date,
                                initial_visible_month=start_date or min_date,
                                start_date=start_date,
                                end_date=end_date,
                                display_format='YYYY-MM-DD',
                                className="mb-2"
                            )
                        )
                    else:
                        control_card_content.append(html.P(f"欄位 '{col}' 不包含有效的日期資料。", className="text-muted small"))

                # --- 其他類型 (Boolean, etc.) ---
                else:
                    control_card_content.append(html.P(f"欄位 '{col}' 的類型 ({col_series.dtype}) 目前不支援篩選。", className="text-muted small"))

                controls.append(dbc.Card(dbc.CardBody(control_card_content), className="mb-3"))

            print(f"Generated {len(controls)} filter control cards.")
            return controls

        except Exception as e:
            print(f"Error generating filter controls: {e}")
            import traceback
            traceback.print_exc()
            return [html.Div(f"生成篩選控制項時發生錯誤: {e}", style={'color': 'red'})]


    # --- 回調：套用篩選 ---
    @app.callback(
        [Output('filtered-data-store', 'data', allow_duplicate=True),
         Output('filter-state-store', 'data', allow_duplicate=True),
         Output('filter-status', 'children'),
         Output('data-table', 'columns', allow_duplicate=True),
         Output('data-table', 'data', allow_duplicate=True),
         Output('category-overview-table', 'columns', allow_duplicate=True),
         Output('category-overview-table', 'data', allow_duplicate=True)],
        [Input('apply-filter-button', 'n_clicks')],
        [State('stored-data', 'data'),
         State({'type': 'filter-control', 'index': dash.ALL, 'control': dash.ALL}, 'id'), # Get IDs of all controls
         # Get specific properties for different control types
         State({'type': 'filter-control', 'index': dash.ALL, 'control': 'checklist'}, 'value'),
         State({'type': 'filter-control', 'index': dash.ALL, 'control': 'range-slider'}, 'value'), # Get RangeSlider value
         State({'type': 'filter-control', 'index': dash.ALL, 'control': 'date-range'}, 'start_date'),
         State({'type': 'filter-control', 'index': dash.ALL, 'control': 'date-range'}, 'end_date'),
         State('filter-column-dropdown', 'value')], # Get the list of columns selected for filtering
        prevent_initial_call=True
    )
    def apply_filters(n_clicks, stored_data_json,
                      filter_control_ids, # All control IDs
                      checklist_values, # Values from checklists
                      range_slider_values, # Values from range sliders
                      start_dates, # Start dates from date pickers
                      end_dates, # End dates from date pickers
                      selected_filter_columns):
        print(f"--- apply_filters triggered ---")
        # Print received values for debugging
        print(f"Received checklist_values: {checklist_values}")
        print(f"Received range_slider_values: {range_slider_values}")
        print(f"Received start_dates: {start_dates}")
        print(f"Received end_dates: {end_dates}")
        print(f"Received filter_control_ids: {filter_control_ids}")

        if not n_clicks or not stored_data_json or not selected_filter_columns:
            print("Apply filter conditions not met (no click, data, or selected columns).")
            return no_update, no_update, "請先選擇欄位並設定篩選條件。", no_update, no_update, no_update, no_update

        try:
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')
            current_filter_state = {} # To store the applied filter values for saving state
            status_messages = []      # To build the status message
            combined_mask = pd.Series([True] * len(df)) # Start with a mask that includes all rows

            # --- Helper function to find the index of a control in the ALL list ---
            def find_control_index(col_name, control_type_str, all_id_dicts):
                target_id_dict = {'type': 'filter-control', 'index': col_name, 'control': control_type_str}
                for i, current_id_dict in enumerate(all_id_dicts):
                    if current_id_dict == target_id_dict:
                        return i
                return -1 # Not found

            print(f"Selected columns for filtering: {selected_filter_columns}")

            # --- Apply filters by iterating through selected columns ---
            for col in selected_filter_columns:
                print(f"--- Processing Column: {col} ---")
                if col not in df.columns:
                    print(f"Warning: Column '{col}' selected for filtering not found in DataFrame.")
                    continue

                col_series = df[col]
                col_filter_state_for_col = {}
                col_mask = pd.Series([True] * len(df)) # Start with True for this column's mask

                # --- Apply Categorical Filter ---
                checklist_idx = find_control_index(col, 'checklist', filter_control_ids)
                if checklist_idx != -1 and checklist_idx < len(checklist_values):
                    selected_values = checklist_values[checklist_idx]
                    if selected_values is not None:
                        # Check if the filter is actually active (not all values selected)
                        all_unique_values = [str(v) for v in col_series.unique() if pd.notna(v)]
                        if set(selected_values) != set(all_unique_values):
                            print(f"Applying categorical filter on '{col}': Keep values {selected_values}")
                            try:
                                typed_selected_values = pd.Series(selected_values).astype(col_series.dtype).tolist()
                                col_mask &= col_series.isin(typed_selected_values)
                            except Exception as e:
                                print(f"Warning: Could not convert selected values for column '{col}' to original dtype ({col_series.dtype}). Filtering with strings. Error: {e}")
                                col_mask &= col_series.astype(str).isin(selected_values)
                            col_filter_state_for_col['values'] = selected_values
                            status_messages.append(f"'{col}' in [{', '.join(map(str, selected_values))}]")


                # --- Apply Numerical Filter (RangeSlider) ---
                slider_idx = find_control_index(col, 'range-slider', filter_control_ids)
                print(f"[Index Check - Slider] slider_idx: {slider_idx}")
                if slider_idx != -1 and slider_idx < len(range_slider_values):
                    slider_range = range_slider_values[slider_idx]
                    print(f"[Value Check - Slider] Raw slider_range: {slider_range}")
                    if slider_range: # Ensure it's not None or empty
                        min_val, max_val = slider_range
                        # Check if the slider range is different from the column's full range
                        numeric_col_full = pd.to_numeric(col_series, errors='coerce').dropna()
                        full_min = numeric_col_full.min()
                        full_max = numeric_col_full.max()

                        if min_val > full_min or max_val < full_max:
                            print(f"Applying numerical range filter on '{col}': between {min_val} and {max_val}")
                            numeric_col = pd.to_numeric(col_series, errors='coerce')
                            # Use between (inclusive by default)
                            col_mask &= numeric_col.between(min_val, max_val, inclusive='both')
                            col_filter_state_for_col['range'] = [min_val, max_val]
                            status_messages.append(f"'{col}' between {min_val:.2f} and {max_val:.2f}")
                        else:
                             print(f"Skipping numerical filter for '{col}': Slider range covers full data range.")
                    else:
                        print(f"Skipping numerical filter for '{col}': Slider value is None or empty.")


                # --- Apply Date Filter ---
                date_range_idx = find_control_index(col, 'date-range', filter_control_ids)
                if date_range_idx != -1:
                    start_date_val = start_dates[date_range_idx] if date_range_idx < len(start_dates) else None
                    end_date_val = end_dates[date_range_idx] if date_range_idx < len(end_dates) else None
                    print(f"[Value Check - Date] Raw start: '{start_date_val}', Raw end: '{end_date_val}'")

                    if start_date_val is not None or end_date_val is not None:
                        datetime_col = pd.to_datetime(col_series, errors='coerce')
                        valid_dates_mask = datetime_col.notna()
                        applied_date_filter = False

                        # Check if filter is active (dates differ from full range)
                        full_min_date = datetime_col.min().date() if valid_dates_mask.any() else None
                        full_max_date = datetime_col.max().date() if valid_dates_mask.any() else None
                        start_date_dt = pd.to_datetime(start_date_val).date() if start_date_val else None
                        end_date_dt = pd.to_datetime(end_date_val).date() if end_date_val else None

                        is_filter_active = (start_date_dt != full_min_date) or (end_date_dt != full_max_date)

                        if is_filter_active:
                            print(f"Applying date range filter on '{col}': {start_date_val} to {end_date_val}")
                            if start_date_val:
                                try:
                                    start_dt = pd.to_datetime(start_date_val)
                                    col_mask &= (datetime_col >= start_dt) & valid_dates_mask
                                    col_filter_state_for_col['start_date'] = start_date_val
                                    applied_date_filter = True
                                except Exception as date_err:
                                    print(f"Error converting start_date '{start_date_val}' for column '{col}': {date_err}")
                            if end_date_val:
                                try:
                                    end_dt = pd.to_datetime(end_date_val)
                                    # Include the end date fully by setting time to end of day
                                    end_dt = end_dt.replace(hour=23, minute=59, second=59)
                                    col_mask &= (datetime_col <= end_dt) & valid_dates_mask
                                    col_filter_state_for_col['end_date'] = end_date_val
                                    applied_date_filter = True
                                except Exception as date_err:
                                    print(f"Error converting end_date '{end_date_val}' for column '{col}': {date_err}")

                            if applied_date_filter:
                                status_messages.append(f"'{col}' between {start_date_val or 'any'} and {end_date_val or 'any'}")
                        else:
                            print(f"Skipping date filter for '{col}': Range covers full data range.")


                # Combine this column's mask with the overall mask
                combined_mask &= col_mask

                # Store the state for this column if any filters were applied
                if col_filter_state_for_col:
                    current_filter_state[col] = col_filter_state_for_col

                print(f"--- Finished Processing Column: {col}. Current combined mask sum: {combined_mask.sum()} ---")

            # --- Apply the combined mask to the original DataFrame ---
            df_filtered = df[combined_mask].copy()

            # --- Prepare Outputs ---
            filtered_df_json = df_filtered.to_json(orient='split')
            filter_status_msg = f"篩選已套用 ({len(df_filtered)} / {len(df)} 行). 條件: {'; '.join(status_messages)}" if status_messages else "篩選條件未變更或無效。"
            filter_status_msg_display = html.Div(filter_status_msg, style={'color': 'green' if status_messages and len(df_filtered) < len(df) else ('darkgray' if not status_messages else 'black')}) # Green if filtered, gray if no filters, black if filters applied but no change

            preview_cols_out = [{"name": i, "id": i} for i in df_filtered.columns]
            preview_data_out = df_filtered.to_dict('records')
            category_data_out, category_cols_out = generate_category_overview_data(df_filtered)

            print(f"Filtering complete. Filtered rows: {len(df_filtered)}. Saving filter state: {current_filter_state}")

            return (filtered_df_json, current_filter_state, filter_status_msg_display,
                    preview_cols_out, preview_data_out,
                    category_cols_out, category_data_out)

        except Exception as e:
            print(f"Error applying filters: {e}")
            import traceback
            traceback.print_exc()
            return no_update, no_update, html.Div(f"套用篩選時發生錯誤: {e}", style={'color': 'red'}), no_update, no_update, no_update, no_update


    # --- 回調：重設篩選 ---
    @app.callback(
        [Output('filtered-data-store', 'data', allow_duplicate=True),
         Output('filter-state-store', 'data', allow_duplicate=True),
         Output('filter-status', 'children', allow_duplicate=True),
         Output('data-table', 'columns', allow_duplicate=True),
         Output('data-table', 'data', allow_duplicate=True),
         Output('category-overview-table', 'columns', allow_duplicate=True),
         Output('category-overview-table', 'data', allow_duplicate=True),
         Output('filter-column-dropdown', 'value', allow_duplicate=True)], # Clear selected columns
        [Input('reset-filter-button', 'n_clicks')],
        [State('stored-data', 'data')], # Get original data
        prevent_initial_call=True
    )
    def reset_filters(n_clicks, stored_data_json):
        print(f"--- reset_filters triggered (n_clicks={n_clicks}) ---")
        if not n_clicks or not stored_data_json:
            print("Reset filter conditions not met (no click or no original data).")
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

        try:
            # Reset filtered data to original data
            df_original = pd.read_json(io.StringIO(stored_data_json), orient='split')
            preview_cols_out = [{"name": i, "id": i} for i in df_original.columns]
            preview_data_out = df_original.to_dict('records')
            category_data_out, category_cols_out = generate_category_overview_data(df_original)

            print("Filters reset. Updating filtered store to original data and clearing state.")

            return (stored_data_json, # Reset filtered store to original
                    {}, # Clear filter state
                    None, # Clear filter status message
                    preview_cols_out, preview_data_out,
                    category_cols_out, category_data_out,
                    None) # Clear selected columns in dropdown

        except Exception as e:
            print(f"Error resetting filters: {e}")
            return no_update, no_update, html.Div(f"重設篩選時發生錯誤: {e}", style={'color': 'red'}), no_update, no_update, no_update, no_update, no_update


    # --- 回調：同步 RangeSlider -> Min/Max Inputs ---
    @app.callback(
        [Output({'type': 'filter-control', 'index': dash.MATCH, 'control': 'min-input'}, 'value'),
         Output({'type': 'filter-control', 'index': dash.MATCH, 'control': 'max-input'}, 'value'),
         Output({'type': 'filter-control', 'index': dash.MATCH, 'control': 'range-display'}, 'children')],
        [Input({'type': 'filter-control', 'index': dash.MATCH, 'control': 'range-slider'}, 'value')],
        [State({'type': 'filter-control', 'index': dash.MATCH, 'control': 'range-slider'}, 'step'),
         State({'type': 'filter-control', 'index': dash.MATCH, 'control': 'min-input'}, 'value'), # Get current min input value
         State({'type': 'filter-control', 'index': dash.MATCH, 'control': 'max-input'}, 'value')], # Get current max input value
        prevent_initial_call=True
    )
    def sync_slider_to_inputs(slider_value, step, current_input_min, current_input_max):
        if slider_value is None:
            return no_update, no_update, no_update

        min_val, max_val = slider_value
        is_integer = step == 1
        mark_format = '{:.0f}' if is_integer else '{:.2f}'
        range_text = f"目前範圍: {mark_format.format(min_val)} - {mark_format.format(max_val)}"

        # Check if inputs need updating to prevent unnecessary triggers
        min_output = min_val if min_val != current_input_min else no_update
        max_output = max_val if max_val != current_input_max else no_update

        # Always update the display text
        return min_output, max_output, range_text

    # --- 回調：同步 Min/Max Inputs -> RangeSlider ---
    @app.callback(
        [Output({'type': 'filter-control', 'index': dash.MATCH, 'control': 'range-slider'}, 'value'),
         Output({'type': 'filter-control', 'index': dash.MATCH, 'control': 'range-display'}, 'children', allow_duplicate=True)],
        [Input({'type': 'filter-control', 'index': dash.MATCH, 'control': 'min-input'}, 'value'),
         Input({'type': 'filter-control', 'index': dash.MATCH, 'control': 'max-input'}, 'value')],
        [State({'type': 'filter-control', 'index': dash.MATCH, 'control': 'range-slider'}, 'value'), # Current slider value
         State({'type': 'filter-control', 'index': dash.MATCH, 'control': 'range-slider'}, 'min'),   # Slider min limit
         State({'type': 'filter-control', 'index': dash.MATCH, 'control': 'range-slider'}, 'max'),   # Slider max limit
         State({'type': 'filter-control', 'index': dash.MATCH, 'control': 'range-slider'}, 'step')], # Slider step
        prevent_initial_call=True
    )
    def sync_inputs_to_slider(input_min, input_max, current_slider_value, slider_min_limit, slider_max_limit, step):
        ctx = callback_context
        triggered_id_dict = ctx.triggered[0]['prop_id'].split('.')[0]
        try:
            # ID might be a string representation of a dict
            triggered_id = json.loads(triggered_id_dict.replace("'", "\"")) # Basic handling for dict string
        except json.JSONDecodeError:
             print(f"Error decoding triggered ID: {triggered_id_dict}")
             return no_update, no_update # Cannot determine trigger

        print(f"sync_inputs_to_slider triggered by: {triggered_id.get('control', 'unknown')}")


        # Use current slider values as fallback if inputs are None or invalid
        current_min, current_max = current_slider_value if current_slider_value else [slider_min_limit, slider_max_limit]

        # Helper to safely convert input to float/int or return fallback
        def safe_convert(val, fallback):
            if val is None: return fallback
            try: return float(val) # Use float for broader compatibility initially
            except (ValueError, TypeError): return fallback

        new_min = safe_convert(input_min, current_min)
        new_max = safe_convert(input_max, current_max)


        # --- Input Validation and Clamping ---
        # 1. Clamp to slider limits
        new_min = max(slider_min_limit, new_min)
        new_max = min(slider_max_limit, new_max)

        # 2. Ensure min <= max
        if new_min > new_max:
            # If min input triggered, set max to min
            if triggered_id.get('control') == 'min-input':
                new_max = new_min
            # If max input triggered, set min to max
            elif triggered_id.get('control') == 'max-input':
                new_min = new_max
            # If triggered by something else (unlikely here), default to clamping min
            else:
                 new_min = new_max


        # 3. (Optional but good) Snap to step? RangeSlider might do this automatically.
        # Let's assume RangeSlider handles snapping based on its value property update.

        new_slider_value = [new_min, new_max]

        # Update range display text
        is_integer = step == 1
        mark_format = '{:.0f}' if is_integer else '{:.2f}'
        range_text = f"目前範圍: {mark_format.format(new_min)} - {mark_format.format(new_max)}"

        # Only update slider if the value actually changed
        if new_slider_value != current_slider_value:
            print(f"Updating slider value from inputs: {new_slider_value}")
            return new_slider_value, range_text
        else:
            print("Input change didn't result in slider value change, updating display only.")
            # Still update display text even if slider value doesn't change (e.g., input clamped)
            return no_update, range_text


# 在 app.py 中的範例用法 (確保此函式被呼叫):
# from pages import data_upload
# app = dash.Dash(__name__, suppress_callback_exceptions=True)
# server = app.server
# app.layout = html.Div([
#     dcc.Store(id='stored-data'), # 確保主佈局中存在 dcc.Store
#     # ... 其他佈局元件
#     html.Div(id='page-content')
# ])
# data_upload.register_callbacks(app)
# # ... app.py 的其餘部分
