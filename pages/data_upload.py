import dash
from dash import dcc, html, dash_table, Input, Output, State
import pandas as pd
import numpy as np # Import numpy for numeric type checking and potential NaN handling
import base64
import io
# math is not explicitly used here after adding numpy/pandas stats, can be removed if not needed elsewhere
# import math

# --- Layout for Data Upload ---
layout = html.Div([
    html.H2("載入 CSV 資料"), # Changed title slightly for consistency
    dcc.Upload(
        id='upload-data',
        children=html.Div(['拖放或 ', html.A('選擇 CSV 檔案')]), # Adjusted text
        style={
            'width': '95%', 'height': '60px', 'lineHeight': '60px',
            'borderWidth': '1px', 'borderStyle': 'dashed',
            'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px auto' # Centered margin
        },
        multiple=False
    ),
    html.Div(id='output-status', style={'marginTop': '10px'}), # Status message area
    html.Hr(),

    # --- 新增：資料類別檢視區塊 ---
    html.H4("資料類別檢視 (Data Category Overview):"),
    html.Div(id='category-overview-output', children=[
        html.P("上傳檔案後將在此顯示資料類別概覽。") # Initial placeholder
    ]),
    html.Hr(), # Separator

    # --- 維持：資料表預覽區塊 ---
    html.H4("資料表預覽 (Data Preview):"),
    html.Div([ # Wrap dropdown in a div for better spacing control if needed
        html.Label("每頁顯示行數: ", style={'marginRight': '10px'}),
        dcc.Dropdown(
            id='rows-per-page-dropdown',
            options=[{'label': str(i), 'value': i} for i in [10, 25, 50, 100]], # Added 100
            value=10, # Default page size
            clearable=False,
            style={'width': '150px', 'display': 'inline-block', 'verticalAlign': 'middle'}
        )
    ], style={'marginBottom': '10px'}),

    # --- DataTable Container for Preview ---
    dash_table.DataTable(
        id='data-table',
        columns=[], # Initially empty
        data=[],    # Initially empty
        page_current=0,
        page_size=10, # Initial page size matches dropdown default
        page_action='native', # Enable native pagination
        sort_action='native',
        filter_action='native',
        style_table={'overflowX': 'auto'},
        style_cell={
            'height': 'auto',
            'minWidth': '100px', 'width': '100px', 'maxWidth': '180px',
            'whiteSpace': 'normal',
            'textAlign': 'left', # Align text left for readability
             'padding': '5px'
        },
         style_header={ # Added header style
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        },
        style_data_conditional=[ # Added striped rows
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            }
        ]
    ),
    # Removed duplicate dcc.Store, assuming 'stored-data' defined in main app layout or elsewhere if needed globally
    # If you specifically need another store here, uncomment and give unique ID
    # dcc.Store(id='data-upload-stored-data')
    # Using the global 'stored-data' defined in app.py if persistence across pages is needed.
    # If data is only needed WITHIN this page's callbacks, a store here might be less critical
    # but still useful if multiple callbacks on this page need the df without re-parsing.
    # Let's assume the main 'stored-data' from app.py is used.
])

# --- Parsing Function (保持您的原始函數) ---
def parse_csv_simple(contents, filename):
    print(f"parse_csv_simple called for: {filename}")
    if contents is None:
         return None, "未上傳檔案。" # Modified message
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        # Ensure filename is a string before checking 'csv'
        if not isinstance(filename, str) or not filename.lower().endswith('.csv'):
             return None, "檔案類型無效。請上傳 CSV 檔案。" # Modified message

        print("嘗試使用 UTF-8 解碼讀取 CSV...")
        try:
            # Use StringIO for text data
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

        # Optional: Sanitize column names (replace spaces, special chars)
        # df.columns = df.columns.str.replace('[^A-Za-z0-9_]+', '', regex=True)

        return df, f"成功載入 '{filename}'。"

    except Exception as e:
        error_msg = f"處理檔案 '{filename}' 時發生錯誤: {str(e)}"
        print(error_msg)
        return None, error_msg

# --- 新增：Helper Function to Generate Category Overview ---
def generate_category_overview(df):
    """根據 DataFrame 生成資料類別概覽的表格元件"""
    if df is None or df.empty:
        return html.P("無資料可供分析。")

    overview_data = []
    for col in df.columns:
        col_data = df[col]
        # Basic Info
        dtype = str(col_data.dtype)
        missing_count = int(col_data.isnull().sum())
        unique_count = int(col_data.nunique())
        total_count = len(col_data) # Total non-null count might also be useful
        missing_percentage = f"{(missing_count / total_count * 100):.1f}%" if total_count > 0 else "N/A"

        # Initialize stats
        stats = {'mean': 'N/A', 'std': 'N/A', 'min': 'N/A', 'max': 'N/A'}

        # Calculate stats only for numeric types (excluding boolean)
        if pd.api.types.is_numeric_dtype(col_data) and not pd.api.types.is_bool_dtype(col_data):
            # Drop NA for calculations
            numeric_data = col_data.dropna()
            if not numeric_data.empty:
                try:
                    stats['mean'] = f"{numeric_data.mean():.2f}" if pd.notna(numeric_data.mean()) else 'N/A'
                    stats['std'] = f"{numeric_data.std():.2f}" if pd.notna(numeric_data.std()) else 'N/A' # Std might be NaN if only 1 value
                    stats['min'] = f"{numeric_data.min():.2f}" if pd.notna(numeric_data.min()) else 'N/A'
                    stats['max'] = f"{numeric_data.max():.2f}" if pd.notna(numeric_data.max()) else 'N/A'
                except Exception as stat_err:
                     print(f"Error calculating stats for column {col}: {stat_err}")
                     # Keep stats as N/A

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

    overview_table = dash_table.DataTable(
        data=overview_data,
        columns=[
            {'name': '欄位名稱', 'id': '欄位名稱'},
            {'name': '資料類型', 'id': '資料類型'},
            {'name': '平均值', 'id': '平均值'},
            {'name': '標準差', 'id': '標準差'},
            {'name': '最小值', 'id': '最小值'},
            {'name': '最大值', 'id': '最大值'},
            {'name': '唯一值數量', 'id': '唯一值數量'},
            {'name': '缺失值數量', 'id': '缺失值數量'},
            {'name': '缺失比例', 'id': '缺失比例'}, # Added missing percentage column
        ],
        page_size=10, # Adjust as needed
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '5px', 'minWidth': '80px'},
        style_header={
            'backgroundColor': 'rgb(220, 220, 220)', # Slightly different header color
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(245, 245, 245)'} # Slightly different stripe color
        ]
    )
    # No need for H3 title here as it's already in the main layout
    return overview_table


# --- Callback registration function ---
def register_callbacks(app):
    print("register_callbacks function called in pages/data_upload.py")

    @app.callback(
        [Output('output-status', 'children'),
         Output('data-table', 'columns'),        # Output for preview table columns
         Output('data-table', 'data'),           # Output for preview table data
         Output('data-table', 'page_size'),      # Output to set preview table page size
         Output('category-overview-output', 'children'), # *** NEW: Output for category overview table ***
         Output('stored-data', 'data')],         # Output to store the full data in global store
        [Input('upload-data', 'contents'),
         Input('rows-per-page-dropdown', 'value')], # Input for page size changes
        [State('upload-data', 'filename')]
    )
    def update_outputs_on_upload_or_pagesize(contents, page_size, filename):
        # Determine what triggered the callback (for potential future optimization)
        # ctx = dash.callback_context
        # triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
        # print(f"Callback triggered by: {triggered_id}")

        print(f"--- update_outputs_on_upload_or_pagesize triggered ---")
        print(f"Filename: {filename}, Page size: {page_size}")

        # Initialize outputs to default/empty states
        status_msg = "請上傳一個 CSV 檔案。"
        preview_cols = []
        preview_data = []
        overview_output = html.P("上傳檔案後將在此顯示資料類別概覽。") # Default overview message
        stored_data_json = None

        if contents is not None:
            print("內容存在，嘗試解析檔案...")
            df, message = parse_csv_simple(contents, filename)

            if df is not None:
                print("DataFrame 建立成功，準備輸出。")
                status_msg = html.Div(message, style={'color': 'green'})
                # Prepare Preview Table data
                preview_cols = [{"name": i, "id": i} for i in df.columns]
                preview_data = df.to_dict('records') # Full data for native pagination

                # --- Generate Category Overview ---
                print("正在生成資料類別概覽...")
                overview_output = generate_category_overview(df)
                print("資料類別概覽生成完畢。")

                # Store the full data
                stored_data_json = df.to_json(orient='split')
                print("資料已儲存至 dcc.Store。")

            else:
                # Parsing failed
                print(f"DataFrame 為空。錯誤訊息: {message}")
                status_msg = html.Div(f"錯誤: {message}", style={'color': 'red'})
                # Keep other outputs as empty/default
                overview_output = html.P("因檔案處理錯誤，無法產生類別概覽。")

        else:
            # No content uploaded (initial load or potentially just page size change)
            print("無上傳內容。")
            # We still need to return the correct number of values, including the page_size
            # If you wanted to preserve the table on page size change *without* re-upload,
            # you'd need more complex logic possibly involving reading from 'stored-data'.
            # For now, it clears the table if no content.
            status_msg = "請上傳一個 CSV 檔案。" # Keep initial message

        # Always return all outputs in the correct order
        print("--- Callback 完成 ---")
        return status_msg, preview_cols, preview_data, page_size, overview_output, stored_data_json

# --- Ensure this function is called in your main app.py ---
# (The example comment in your original code is correct)
# Example in app.py:
# from pages import data_upload # Assuming 'pages' is a package or directory
# app = dash.Dash(__name__, suppress_callback_exceptions=True)
# server = app.server
# app.layout = ... # Your main layout including page content div and dcc.Store(id='stored-data')
# data_upload.register_callbacks(app) # Call the registration function
# ... (rest of your app.py)