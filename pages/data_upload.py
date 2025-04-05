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
        # --- Tab 1: Data Table Preview ---
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
                    filter_action='none', # Allow filtering if needed, though less common here
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
                html.Hr(style={'marginTop': '20px', 'marginBottom': '20px'}), # Separator

                # --- Date Conversion Section ---
                html.H4("日期欄位轉換:", style={'marginTop': '20px'}),
                html.Div(id='auto-date-detection-results', style={'marginBottom': '10px'}), # Area for auto-detection results

                html.Div([
                    html.Label("選擇要轉換的欄位:", style={'marginRight': '10px'}),
                    dcc.Dropdown(
                        id='manual-date-column-dropdown',
                        options=[], # Populated by callback
                        placeholder="選擇欄位...",
                        style={'width': '250px', 'display': 'inline-block', 'verticalAlign': 'middle', 'marginRight': '20px'}
                    ),
                    html.Label("輸入日期格式:", style={'marginRight': '10px'}),
                    dcc.Input(
                        id='manual-date-format-input',
                        type='text',
                        placeholder="例如: %Y-%m-%d 或 %m/%d/%Y",
                        style={'width': '200px', 'display': 'inline-block', 'verticalAlign': 'middle', 'marginRight': '20px'}
                    ),
                    html.Button('手動轉換日期', id='manual-convert-date-button', n_clicks=0, style={'verticalAlign': 'middle'}),
                ], style={'marginBottom': '10px'}),
                html.Div([
                    html.P("常見格式範例:", style={'fontWeight': 'bold', 'marginBottom': '2px'}),
                    html.Ul([
                        html.Li("%Y-%m-%d (例如: 2023-10-26)"),
                        html.Li("%Y/%m/%d (例如: 2023/10/26)"),
                        html.Li("%m/%d/%Y (例如: 10/26/2023)"),
                        html.Li("%Y%m%d (例如: 20231026)"),
                        html.Li("%Y-%m-%d %H:%M:%S (例如: 2023-10-26 14:30:00)"),
                    ], style={'fontSize': 'small', 'color': 'grey', 'marginTop': '0px'})
                ]),
                html.Div(id='manual-date-conversion-status', style={'marginTop': '10px'}), # Area for manual conversion status

            ], style={'padding': '10px'})
        ]),
    ]),
])

# --- Parsing Function (Modified for Auto Date Detection) ---
def parse_csv_simple(contents, filename):
    """Parses CSV, attempts auto date conversion, returns df, message, and list of auto-converted date columns."""
    print(f"parse_csv_simple called for: {filename}")
    if contents is None:
         return None, "未上傳檔案。", []
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    auto_converted_cols = [] # Keep track of automatically converted columns
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
            return None, "CSV 檔案是空的。", []

        # --- Auto Date Detection ---
        print("開始自動偵測日期欄位...")
        for col in df.select_dtypes(include=['object']).columns:
            try:
                # Attempt to parse the first few non-null values to infer if it's a date column
                sample_size = min(5, df[col].dropna().nunique()) # Sample up to 5 unique non-null values
                if sample_size == 0:
                    continue

                sample_values = df[col].dropna().unique()[:sample_size]
                parsed_count = 0
                for val in sample_values:
                    try:
                        pd.to_datetime(val) # Use pandas' default inference
                        parsed_count += 1
                    except (ValueError, TypeError):
                        pass # Ignore values that don't parse

                # If a high percentage parses, convert the whole column
                # Adjust threshold (e.g., 0.8) as needed
                if parsed_count / sample_size >= 0.8:
                    print(f"偵測到欄位 '{col}' 可能為日期，嘗試轉換...")
                    original_dtype = df[col].dtype
                    # Use errors='coerce' to handle potential non-date values gracefully
                    converted_col = pd.to_datetime(df[col], errors='coerce')
                    # Check if conversion actually changed the dtype and didn't just create NaTs
                    if pd.api.types.is_datetime64_any_dtype(converted_col) and converted_col.notna().any():
                        df[col] = converted_col
                        auto_converted_cols.append(col)
                        print(f"成功將欄位 '{col}' 轉換為日期格式。")
                    else:
                         print(f"欄位 '{col}' 轉換失敗或結果為空，保持原樣。")


            except Exception as date_err:
                print(f"自動偵測欄位 '{col}' 日期時發生錯誤: {date_err}")
        print(f"自動日期轉換完成。轉換的欄位: {auto_converted_cols}")
        # --- End Auto Date Detection ---

        return df, f"成功載入 '{filename}'。", auto_converted_cols

    except Exception as e:
        error_msg = f"處理檔案 '{filename}' 時發生錯誤: {str(e)}"
        print(error_msg)
        return None, error_msg, []

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
        {'name': '缺失值數量', 'id': '缺失值數量'},
        {'name': '缺失比例', 'id': '缺失比例'},
        {'name': '平均值', 'id': '平均值'},
        {'name': '標準差', 'id': '標準差'},
        {'name': '最小值', 'id': '最小值'},
        {'name': '最大值', 'id': '最大值'},
        {'name': '唯一值數量', 'id': '唯一值數量'},
    ]

    return overview_data, columns_definition # Return data and columns separately


# --- Helper Function to Extract Date Parts ---
def extract_date_parts(df, column_name):
    """Extracts year, month, dayofweek from a datetime column and adds them as new columns."""
    if column_name in df.columns and pd.api.types.is_datetime64_any_dtype(df[column_name]):
        print(f"正在為欄位 '{column_name}' 提取日期部分...")
        base_name = column_name.replace(' ', '_') # Sanitize base name
        df[f'{base_name}_年'] = df[column_name].dt.year
        df[f'{base_name}_月'] = df[column_name].dt.month
        # Monday=0, Sunday=6
        df[f'{base_name}_星期幾'] = df[column_name].dt.dayofweek
        # Optional: Map to names
        day_map = {0: '星期一', 1: '星期二', 2: '星期三', 3: '星期四', 4: '星期五', 5: '星期六', 6: '星期日'}
        df[f'{base_name}_星期名稱'] = df[f'{base_name}_星期幾'].map(day_map)
        print(f"成功提取日期部分: 年, 月, 星期幾, 星期名稱")
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
         Output('stored-data', 'data'),
         Output('auto-date-detection-results', 'children'),
         Output('manual-date-column-dropdown', 'options'),
         Output('manual-date-column-dropdown', 'value'),
         Output('manual-date-conversion-status', 'children', allow_duplicate=True)], # <<< ADDED allow_duplicate=True
        [Input('upload-data', 'contents'),
         Input('rows-per-page-dropdown', 'value'),
         Input('category-rows-per-page-dropdown', 'value')],
        [State('upload-data', 'filename'),
         State('stored-data', 'data')],
        prevent_initial_call='initial_duplicate' # <<< ADDED to allow initial call with duplicate output
    )
    def update_outputs_on_upload_or_pagesize(contents, preview_page_size, category_page_size, filename, stored_data_json):
        ctx = callback_context
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
        print(f"--- update_outputs triggered by: {triggered_id} ---")
        print(f"Filename: {filename}, Preview Page Size: {preview_page_size}, Category Page Size: {category_page_size}")

        print(f"--- update_outputs_on_upload_or_pagesize triggered by: {triggered_id} ---")
        print(f"Filename: {filename}, Preview Page Size: {preview_page_size}, Category Page Size: {category_page_size}")

        # Initialize outputs
        status_msg = "請上傳一個 CSV 檔案。"
        preview_cols, preview_data = [], []
        category_cols, category_data = [], []
        new_stored_data = dash.no_update
        auto_detect_msg = ""
        manual_dropdown_options = []
        manual_dropdown_value = None
        manual_status_msg = "" # Clear manual status

        current_preview_page_size = preview_page_size if preview_page_size is not None else 10
        current_category_page_size = category_page_size if category_page_size is not None else 10

        # --- Case 1: New File Upload ---
        if triggered_id == 'upload-data' and contents is not None:
            print("處理新上傳的檔案...")
            # parse_csv_simple now returns df, message, auto_converted_cols
            df, message, auto_converted_cols = parse_csv_simple(contents, filename)

            if df is not None:
                print("檔案解析成功。")
                status_msg = html.Div(message, style={'color': 'green'})

                # --- Handle Auto Date Conversion Results ---
                if auto_converted_cols:
                    auto_detect_msg = html.Div([
                        html.P("自動偵測並轉換以下欄位為日期格式:", style={'fontWeight': 'bold'}),
                        html.Ul([html.Li(col) for col in auto_converted_cols])
                    ], style={'color': 'blue'})
                    # Extract date parts for auto-converted columns
                    for col in auto_converted_cols:
                        df = extract_date_parts(df, col)
                else:
                    auto_detect_msg = html.P("未自動偵測到可轉換的日期欄位。", style={'color': 'orange'})

                # --- Prepare Outputs ---
                preview_cols = [{"name": i, "id": i} for i in df.columns]
                preview_data = df.to_dict('records')
                category_data, category_cols = generate_category_overview_data(df)
                new_stored_data = df.to_json(orient='split')
                # Populate manual dropdown with object/string columns
                potential_date_cols = df.select_dtypes(include=['object']).columns.tolist()
                manual_dropdown_options = [{'label': col, 'value': col} for col in potential_date_cols]
                print("新資料已儲存，手動轉換下拉選單已更新。")

            else: # Parsing failed
                print(f"檔案解析失敗: {message}")
                status_msg = html.Div(f"錯誤: {message}", style={'color': 'red'})
                preview_cols, preview_data = [], []
                category_cols, category_data = [], []
                new_stored_data = None
                auto_detect_msg = ""
                manual_dropdown_options = []

        # --- Case 2: Page Size Change or Initial Load ---
        else:
            print("處理頁面大小變更或初始載入。")
            if stored_data_json:
                print("從 store 載入現有資料...")
                try:
                    df = pd.read_json(io.StringIO(stored_data_json), orient='split')
                    preview_cols = [{"name": i, "id": i} for i in df.columns]
                    preview_data = df.to_dict('records')
                    category_data, category_cols = generate_category_overview_data(df)
                    status_msg = "使用已儲存的資料更新檢視。"
                    # Populate manual dropdown based on stored data
                    potential_date_cols = df.select_dtypes(include=['object']).columns.tolist()
                    manual_dropdown_options = [{'label': col, 'value': col} for col in potential_date_cols]
                    print("使用已儲存的資料更新表格和下拉選單。")
                except Exception as e:
                    print(f"從 store 載入資料時發生錯誤: {e}")
                    status_msg = html.Div(f"從 store 載入資料時發生錯誤: {e}", style={'color': 'red'})
                    preview_cols, preview_data = [], []
                    category_cols, category_data = [], []
                    new_stored_data = None
                    manual_dropdown_options = []
            else:
                print("無上傳內容且 store 中無資料。")
                status_msg = "請上傳一個 CSV 檔案。"

        print("--- Main Callback 完成 ---")
        return (status_msg,
                preview_cols, preview_data, current_preview_page_size,
                category_cols, category_data, current_category_page_size,
                new_stored_data,
                auto_detect_msg, # Auto detect message
                manual_dropdown_options, # Manual dropdown options
                manual_dropdown_value, # Reset manual dropdown value
                manual_status_msg) # Clear manual status

    # --- Callback for Manual Date Conversion ---
    @app.callback(
        [Output('stored-data', 'data', allow_duplicate=True), # Update stored data
         Output('manual-date-conversion-status', 'children'), # Show status message
         Output('data-table', 'columns', allow_duplicate=True), # Update preview table
         Output('data-table', 'data', allow_duplicate=True),
         Output('category-overview-table', 'columns', allow_duplicate=True),
         Output('category-overview-table', 'data', allow_duplicate=True),
         Output('manual-date-column-dropdown', 'options', allow_duplicate=True)],
        [Input('manual-convert-date-button', 'n_clicks')],
        [State('manual-date-column-dropdown', 'value'),
         State('manual-date-format-input', 'value'),
         State('stored-data', 'data')],
         prevent_initial_call=True # Prevent running on initial load
    )
    def handle_manual_date_conversion(n_clicks, column_to_convert, date_format, stored_data_json):
        print(f"--- handle_manual_date_conversion triggered ---")
        print(f"n_clicks: {n_clicks}, Column: {column_to_convert}, Format: {date_format}")

        if not n_clicks or not column_to_convert or not stored_data_json:
            print("條件不滿足，不執行轉換。")
            return dash.no_update # Or return defaults if needed

        if not date_format:
            return (dash.no_update,
                    html.Div("錯誤：請輸入日期格式。", style={'color': 'red'}),
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update)

        try:
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')

            if column_to_convert not in df.columns:
                 return (dash.no_update,
                        html.Div(f"錯誤：欄位 '{column_to_convert}' 不存在。", style={'color': 'red'}),
                        dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update)

            print(f"嘗試使用格式 '{date_format}' 轉換欄位 '{column_to_convert}'...")
            original_dtype = df[column_to_convert].dtype
            # Use errors='coerce' to turn unparseable values into NaT
            converted_col = pd.to_datetime(df[column_to_convert], format=date_format, errors='coerce')

            # Check if conversion resulted in all NaT (which means format was likely wrong)
            if converted_col.isnull().all():
                print("轉換失敗：所有值都無法使用指定格式解析。")
                return (dash.no_update,
                        html.Div(f"錯誤：無法使用格式 '{date_format}' 解析欄位 '{column_to_convert}' 中的任何值。請檢查格式或欄位內容。", style={'color': 'red'}),
                        dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update)

            # Check if at least some values were converted successfully
            successful_conversions = converted_col.notna().sum()
            total_non_null_original = df[column_to_convert].notna().sum()
            print(f"成功轉換 {successful_conversions} 個值 (原始非空值: {total_non_null_original})。")

            # Update the DataFrame column
            df[column_to_convert] = converted_col

            # Extract date parts for the newly converted column
            df = extract_date_parts(df, column_to_convert)

            # Prepare outputs
            new_stored_data = df.to_json(orient='split')
            status_msg = html.Div(f"成功將欄位 '{column_to_convert}' 使用格式 '{date_format}' 轉換為日期，並提取了年/月/星期。", style={'color': 'green'})
            preview_cols = [{"name": i, "id": i} for i in df.columns]
            preview_data = df.to_dict('records')
            category_data, category_cols = generate_category_overview_data(df)
            # Update dropdown options (remove the converted column if it's no longer object)
            potential_date_cols = df.select_dtypes(include=['object']).columns.tolist()
            manual_dropdown_options = [{'label': col, 'value': col} for col in potential_date_cols]

            print("手動轉換成功，更新 store 和表格。")
            return (new_stored_data, status_msg,
                    preview_cols, preview_data,
                    category_cols, category_data,
                    manual_dropdown_options)

        except ValueError as ve:
             # This might catch format string issues, though errors='coerce' handles data issues
             print(f"轉換錯誤 (ValueError): {ve}")
             error_msg = f"轉換欄位 '{column_to_convert}' 時發生錯誤：無效的日期格式 '{date_format}' 或欄位包含無法解析的值。錯誤: {ve}"
             return (dash.no_update, html.Div(error_msg, style={'color': 'red'}),
                     dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update)
        except Exception as e:
            print(f"轉換時發生未預期錯誤: {e}")
            error_msg = f"轉換欄位 '{column_to_convert}' 時發生未預期錯誤: {e}"
            return (dash.no_update, html.Div(error_msg, style={'color': 'red'}),
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update)


# --- Ensure this function is called in your main app.py ---
# Example in app.py:

# --- Ensure this function is called in your main app.py ---
# Example in app.py:
# from pages import data_upload
# app = dash.Dash(__name__, suppress_callback_exceptions=True)
# server = app.server
# app.layout = ... # Your main layout including page content div and dcc.Store(id='stored-data')
# data_upload.register_callbacks(app)
# ... (rest of your app.py)
