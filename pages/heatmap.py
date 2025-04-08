import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
import dash_bootstrap_components as dbc

# Configure Matplotlib to use 'Agg' backend
import matplotlib
matplotlib.use('Agg')

# --- Layout Definition ---
layout = html.Div([

    html.H2("熱力圖"),
    html.P("選擇變數以視覺化相關性或交叉分布。"),

    html.Div([
        html.Label("選擇檢視類型："),
        dcc.RadioItems(
            id='heatmap-mode-radio',
            options=[
                {'label': '數值相關性', 'value': 'numeric'},
                {'label': '類別交叉表', 'value': 'categorical'}
            ],
            value='numeric',
            labelStyle={'display': 'inline-block', 'margin-right': '10px'}
        ),
    ]),

    html.Div([
        html.Label("選擇數值變數："),
        dcc.Dropdown(
            id='heatmap-numeric-dropdown',
            multi=True,
            placeholder="選擇數值變數..."
        ),
    ], id='numeric-dropdown-div'),

    html.Div([
        html.Label("選擇第一個類別變數："),
        dcc.Dropdown(
            id='heatmap-cat1-dropdown',
            placeholder="選擇第一個類別變數..."
        ),
    ], id='cat1-dropdown-div', style={'display': 'none'}),

    html.Div([
        html.Label("選擇第二個類別變數："),
        dcc.Dropdown(
            id='heatmap-cat2-dropdown',
            placeholder="選擇第二個類別變數..."
        ),
    ], id='cat2-dropdown-div', style={'display': 'none'}),

    html.Div([
        html.Label("選擇檢視模式："),
        dcc.RadioItems(
            id='heatmap-plot-type-radio',
            options=[
                {'label': '動態圖表', 'value': 'dynamic'},
                {'label': '靜態圖表', 'value': 'static'},
            ],
            value='dynamic',
            labelStyle={'display': 'inline-block', 'margin-right': '10px'}
        ),
    ]),

    html.Div(id='heatmap-filter-status-display',
             style={'marginBottom': '15px', 'padding': '10px', 'border': '1px solid #ddd', 'borderRadius': '5px', 'backgroundColor': '#f9f9f9'}),

    html.Div([
        dcc.Graph(id='heatmap-plotly-graph', style={'display': 'block'}),
        html.Img(id='heatmap-static-img', style={'display': 'none', 'maxWidth': '100%'})
    ]),

    # Section for Dynamic Code Snippet
    html.Div(id='heatmap-dynamic-code-section', children=[
        html.H4("動態圖表範例程式碼"),
        dcc.Markdown(
            id='heatmap-dynamic-code-block',
            style={
                'whiteSpace': 'pre-wrap',
                'backgroundColor': '#f8f8f8',
                'padding': '10px',
                'border': '1px solid #ccc'
            }
        )
    ]),

    # Section for Static Code Snippet
    html.Div(id='heatmap-static-code-section', children=[
        html.H4("靜態圖表範例程式碼"),
        dcc.Markdown(
            id='heatmap-static-code-block',
            style={
                'whiteSpace': 'pre-wrap',
                'backgroundColor': '#f8f8f8',
                'padding': '10px',
                'border': '1px solid #ccc'
            }
        )
    ])
])

def register_callbacks(app):
    @app.callback(
        [Output('numeric-dropdown-div', 'style'),
         Output('cat1-dropdown-div', 'style'),
         Output('cat2-dropdown-div', 'style')],
        Input('heatmap-mode-radio', 'value')
    )
    def toggle_dropdowns(mode):
        if mode == 'numeric':
            return {'display': 'block'}, {'display': 'none'}, {'display': 'none'}
        else:
            return {'display': 'none'}, {'display': 'block'}, {'display': 'block'}

    @app.callback(
        [Output('heatmap-plotly-graph', 'style'),
         Output('heatmap-static-img', 'style')],
        Input('heatmap-plot-type-radio', 'value')
    )
    def toggle_heatmap_view(view_mode):
        if view_mode == 'dynamic':
            return {'display': 'block'}, {'display': 'none'}
        else:
            return {'display': 'none'}, {'display': 'block', 'maxWidth': '100%'}

    @app.callback(
        [Output('heatmap-numeric-dropdown', 'options'),
         Output('heatmap-numeric-dropdown', 'value'),
         Output('heatmap-cat1-dropdown', 'options'),
         Output('heatmap-cat2-dropdown', 'options')],
        Input('filtered-data-store', 'data')
    )
    def update_dropdown_options(stored_data_json):
        default_return = ([], None, [], [])
        if not stored_data_json:
            return default_return

        try:
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')
            if df.empty:
                return default_return

            numeric_cols = df.select_dtypes(include=np.number).columns
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns

            numeric_options = [{'label': f"{col} (numeric)", 'value': col} for col in numeric_cols]
            cat_options = []
            for col in categorical_cols:
                dtype_str = 'category' if pd.api.types.is_categorical_dtype(df[col]) else 'object'
                cat_options.append({'label': f"{col} ({dtype_str})", 'value': col})

            default_numeric = numeric_cols.tolist() if not numeric_cols.empty else None

            return numeric_options, default_numeric, cat_options, cat_options

        except Exception as e:
            print(f"Error updating dropdowns: {e}")
            return default_return

    @app.callback(
        Output('heatmap-plotly-graph', 'figure'),
        [Input('filtered-data-store', 'data'),
         Input('heatmap-mode-radio', 'value'),
         Input('heatmap-numeric-dropdown', 'value'),
         Input('heatmap-cat1-dropdown', 'value'),
         Input('heatmap-cat2-dropdown', 'value'),
         Input('heatmap-plot-type-radio', 'value')]
    )
    def update_plotly_heatmap(stored_data_json, mode, numeric_cols, cat1, cat2, view_mode):
        if view_mode != 'dynamic' or stored_data_json is None:
            return px.scatter(title="請選擇動態檢視")

        try:
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')

            if mode == 'numeric':
                if not numeric_cols or len(numeric_cols) < 2:
                    return px.scatter(title="請選擇至少兩個數值變數")
                corr_df = df[numeric_cols].corr()
                fig = px.imshow(
                    corr_df,
                    title="變數間的相關性熱力圖",
                    labels=dict(color="相關係數"),
                    color_continuous_scale="Blues",
                    aspect="auto"
                )
                fig.update_layout(
                    transition_duration=300,
                    xaxis_title="變數",
                    yaxis_title="變數"
                )
                return fig

            else:  # categorical mode
                if not cat1 or not cat2:
                    return px.scatter(title="請選擇兩個類別變數")
                nunique1 = df[cat1].nunique()
                nunique2 = df[cat2].nunique()
                if nunique1 > 20 or nunique2 > 20:
                    warning_message = f"類別變數 '{cat1}' 或 '{cat2}' 的唯一值超過 20 個，不適合繪製交叉表。"
                    fig = go.Figure()
                    fig.add_annotation(
                        text=warning_message, xref="paper", yref="paper",
                        x=0.5, y=0.5, showarrow=False, font=dict(size=14)
                    )
                    fig.update_layout(title="警告", xaxis={'visible': False}, yaxis={'visible': False}, plot_bgcolor='white')
                    return fig

                ct = pd.crosstab(df[cat1], df[cat2])
                fig = px.imshow(
                    ct,
                    text_auto=True,
                    labels=dict(color="計數"),
                    title=f"{cat1} 與 {cat2} 的交叉表熱力圖",
                    aspect="auto",
                    color_continuous_scale="Blues"
                )
                fig.update_layout(
                    transition_duration=300,
                    xaxis_title=cat2,
                    yaxis_title=cat1
                )
                return fig

        except Exception as e:
            print(f"生成圖表時發生錯誤：{e}")
            return px.scatter(title=f"錯誤：{e}")

    @app.callback(
        Output('heatmap-static-img', 'src'),
        [Input('filtered-data-store', 'data'),
         Input('heatmap-mode-radio', 'value'),
         Input('heatmap-numeric-dropdown', 'value'),
         Input('heatmap-cat1-dropdown', 'value'),
         Input('heatmap-cat2-dropdown', 'value'),
         Input('heatmap-plot-type-radio', 'value')]
    )
    def update_static_heatmap(stored_data_json, mode, numeric_cols, cat1, cat2, view_mode):
        if view_mode != 'static' or stored_data_json is None:
            return "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

        try:
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')

            plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
            plt.rcParams['axes.unicode_minus'] = False

            if mode == 'numeric':
                if not numeric_cols or len(numeric_cols) < 2:
                    fig_warn, ax_warn = plt.subplots(figsize=(6, 2))
                    ax_warn.text(0.5, 0.5, "請選擇至少兩個數值變數", ha='center', va='center', fontsize=12, color='red')
                    ax_warn.axis('off')
                    buf = BytesIO()
                    fig_warn.savefig(buf, format="png")
                    buf.seek(0)
                    data = base64.b64encode(buf.getvalue()).decode("utf8")
                    plt.close(fig_warn)
                    return f"data:image/png;base64,{data}"

                corr_df = df[numeric_cols].corr()
                fig_static, ax = plt.subplots(figsize=(10, 8), tight_layout=True)
                sns.heatmap(corr_df, annot=True, cmap='Blues', ax=ax)
                ax.set_title("變數間的相關性熱力圖")
                plt.xticks(rotation=45, ha='right')
                plt.yticks(rotation=0)

            else:
                if not cat1 or not cat2:
                    fig_warn, ax_warn = plt.subplots(figsize=(6, 2))
                    ax_warn.text(0.5, 0.5, "請選擇兩個類別變數", ha='center', va='center', fontsize=12, color='red')
                    ax_warn.axis('off')
                    buf = BytesIO()
                    fig_warn.savefig(buf, format="png")
                    buf.seek(0)
                    data = base64.b64encode(buf.getvalue()).decode("utf8")
                    plt.close(fig_warn)
                    return f"data:image/png;base64,{data}"

                nunique1 = df[cat1].nunique()
                nunique2 = df[cat2].nunique()
                if nunique1 > 20 or nunique2 > 20:
                    warning_message = f"類別變數 '{cat1}' 或 '{cat2}' 的唯一值超過 20 個，\n不適合繪製交叉表。"
                    fig_warn, ax_warn = plt.subplots(figsize=(8, 2), tight_layout=True)
                    ax_warn.text(0.5, 0.5, warning_message, ha='center', va='center', fontsize=12, color='red')
                    ax_warn.axis('off')
                    buf = BytesIO()
                    fig_warn.savefig(buf, format="png")
                    buf.seek(0)
                    data = base64.b64encode(buf.getvalue()).decode("utf8")
                    plt.close(fig_warn)
                    return f"data:image/png;base64,{data}"

                ct = pd.crosstab(df[cat1], df[cat2])
                fig_static, ax = plt.subplots(figsize=(10, 8), tight_layout=True)
                sns.heatmap(ct, annot=True, fmt='d', cmap='Blues', ax=ax)
                ax.set_title(f"{cat1} 與 {cat2} 的交叉表熱力圖")
                plt.xticks(rotation=45, ha='right')
                plt.yticks(rotation=0)

            buf = BytesIO()
            fig_static.savefig(buf, format="png", bbox_inches='tight')
            buf.seek(0)
            data = base64.b64encode(buf.getvalue()).decode("utf8")
            plt.close(fig_static)
            return f"data:image/png;base64,{data}"

        except Exception as e:
            print(f"Error generating static heatmap: {e}")
            error_message = f"Error: {e}"
            return f"data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='100'%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='10px' fill='red'%3E{error_message}%3C/text%3E%3C/svg%3E"

    @app.callback(
        Output('heatmap-filter-status-display', 'children'),
        Input('filter-status-message-store', 'data')
    )
    def update_heatmap_filter_status(status_message):
        if status_message:
            return status_message
        return "目前未套用篩選條件。"

    @app.callback(
        [Output('heatmap-dynamic-code-section', 'style'),
         Output('heatmap-static-code-section', 'style')],
        [Input('heatmap-plot-type-radio', 'value')]
    )
    def toggle_heatmap_code_section_visibility(view_mode):
        if view_mode == 'dynamic':
            return {'display': 'block'}, {'display': 'none'}
        elif view_mode == 'static':
            return {'display': 'none'}, {'display': 'block'}
        return {'display': 'block'}, {'display': 'none'} # Default to showing dynamic

    @app.callback(
        [Output('heatmap-dynamic-code-block', 'children'),
         Output('heatmap-static-code-block', 'children')],
        [Input('filtered-data-store', 'data'),
         Input('heatmap-mode-radio', 'value'),
         Input('heatmap-numeric-dropdown', 'value'),
         Input('heatmap-cat1-dropdown', 'value'),
         Input('heatmap-cat2-dropdown', 'value'),
         Input('heatmap-plot-type-radio', 'value')]
    )
    def update_heatmap_code_snippets(stored_data_json, mode, numeric_cols, cat1, cat2, view_mode):
        if stored_data_json is None:
            msg = "請先上傳資料"
            return msg, msg

        dynamic_code = "```python\n# 動態圖表程式碼生成失敗\n```"
        static_code = "```python\n# 靜態圖表程式碼生成失敗\n```"

        try:
            if mode == 'numeric':
                if not numeric_cols or len(numeric_cols) < 2:
                    msg = "請選擇至少兩個數值變數"
                    return msg, msg

                numeric_cols_str = str(numeric_cols) # Convert list to string representation

                # Dynamic Plotly Code (Numeric)
                dynamic_code = f"""```python
import plotly.express as px
import pandas as pd

# 假設 df 是您的 DataFrame
# df = pd.read_csv('your_data.csv') # 或其他載入方式

numeric_cols = {numeric_cols_str}
if len(numeric_cols) >= 2:
    corr_df = df[numeric_cols].corr()
    fig = px.imshow(
        corr_df,
        title="變數間的相關性熱力圖",
        labels=dict(color="相關係數"),
        color_continuous_scale="Blues",
        aspect="auto"
    )
    fig.update_layout(
        xaxis_title="變數",
        yaxis_title="變數"
    )
    fig.show()
else:
    print("請選擇至少兩個數值變數")
```"""

                # Static Seaborn Code (Numeric)
                static_code = f"""```python
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

# 假設 df 是您的 DataFrame
# df = pd.read_csv('your_data.csv') # 或其他載入方式
# plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] # 設定中文字體 (如果需要)
# plt.rcParams['axes.unicode_minus'] = False # 解決負號顯示問題

numeric_cols = {numeric_cols_str}
if len(numeric_cols) >= 2:
    corr_df = df[numeric_cols].corr()
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_df, annot=True, cmap='Blues')
    plt.title("變數間的相關性熱力圖")
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.show()
else:
    print("請選擇至少兩個數值變數")
```"""

            elif mode == 'categorical':
                if not cat1 or not cat2:
                    msg = "請選擇兩個類別變數"
                    return msg, msg

                # Dynamic Plotly Code (Categorical)
                dynamic_code = f"""```python
import plotly.express as px
import pandas as pd

# 假設 df 是您的 DataFrame
# df = pd.read_csv('your_data.csv') # 或其他載入方式

cat1 = '{cat1}'
cat2 = '{cat2}'

# 檢查唯一值數量 (可選)
# if df[cat1].nunique() > 20 or df[cat2].nunique() > 20:
#     print(f"警告: 類別變數 '{cat1}' 或 '{cat2}' 的唯一值可能過多")
# else:

ct = pd.crosstab(df[cat1], df[cat2])
fig = px.imshow(
    ct,
    text_auto=True,
    labels=dict(color="計數"),
    title=f"{{cat1}} 與 {{cat2}} 的交叉表熱力圖",
    aspect="auto",
    color_continuous_scale="Blues"
)
fig.update_layout(
    xaxis_title=cat2,
    yaxis_title=cat1
)
fig.show()
```"""

                # Static Seaborn Code (Categorical)
                static_code = f"""```python
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

# 假設 df 是您的 DataFrame
# df = pd.read_csv('your_data.csv') # 或其他載入方式
# plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] # 設定中文字體 (如果需要)
# plt.rcParams['axes.unicode_minus'] = False # 解決負號顯示問題

cat1 = '{cat1}'
cat2 = '{cat2}'

# 檢查唯一值數量 (可選)
# if df[cat1].nunique() > 20 or df[cat2].nunique() > 20:
#     print(f"警告: 類別變數 '{cat1}' 或 '{cat2}' 的唯一值可能過多")
# else:

ct = pd.crosstab(df[cat1], df[cat2])
plt.figure(figsize=(10, 8))
sns.heatmap(ct, annot=True, fmt='d', cmap='Blues')
plt.title(f"{{cat1}} 與 {{cat2}} 的交叉表熱力圖")
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)
plt.tight_layout()
plt.show()
```"""
            else:
                 msg = "未知的檢視類型"
                 return msg, msg

        except Exception as e:
            print(f"Error generating code snippets: {e}")
            error_msg = f"生成程式碼時發生錯誤: {e}"
            return error_msg, error_msg

        if view_mode == 'dynamic':
            return dynamic_code, static_code # Return both, visibility handled by CSS
        elif view_mode == 'static':
            return dynamic_code, static_code # Return both, visibility handled by CSS
        else:
            return dynamic_code, static_code # Default case

# --- End of Callback Registration ---

# NOTE: No 'if __name__ == "__main__":' block here
