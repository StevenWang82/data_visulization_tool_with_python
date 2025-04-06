import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

# Configure Matplotlib to use 'Agg' backend
import matplotlib
matplotlib.use('Agg')

# --- Layout Definition ---
layout = html.Div([
    html.H2("長條圖"),
    html.P("選擇變數以視覺化類別資料。"),
    html.Div([
        html.Label("選擇類別變數："),
        dcc.Dropdown(id='bar-category-dropdown', placeholder="選擇類別變數..."),
    ]),
    html.Div([
        html.Label("選擇數值變數（選填）："),
        dcc.Dropdown(id='bar-value-dropdown', placeholder="選擇數值變數..."),
    ]),
    html.Div([
        html.Label("選擇分組變數（選填）："),
        dcc.Dropdown(id='bar-group-dropdown', placeholder="選擇分組變數..."),
    ]),
    html.Div([
        html.Label("長條圖模式："),
        dcc.Dropdown(
            id='bar-mode-dropdown',
            options=[
                {'label': '群組', 'value': 'group'},
                {'label': '堆疊', 'value': 'stack'},
            ],
            value='group',
            clearable=False
        ),
    ], id='plotly-bar-controls'),
    html.Div([
        html.Label("選擇檢視模式："),
        dcc.RadioItems(
            id='bar-plot-type-radio',
            options=[
                {'label': '動態圖表', 'value': 'dynamic'},
                {'label': '靜態圖表', 'value': 'static'},
            ],
            value='dynamic',
            labelStyle={'display': 'inline-block', 'margin-right': '10px'}
        ),
    ]),
    html.Div([
        dcc.Graph(id='bar-plotly-graph', style={'display': 'block'}),
        html.Img(id='bar-static-img', style={'display': 'none', 'maxWidth': '100%'})
    ])
])

def register_callbacks(app):
    @app.callback(
        [Output('bar-plotly-graph', 'style'),
         Output('bar-static-img', 'style'),
         Output('plotly-bar-controls', 'style')],
        [Input('bar-plot-type-radio', 'value')]
    )
    def toggle_bar_view(view_mode):
        plotly_controls_style = {'display': 'block'} if view_mode == 'dynamic' else {'display': 'none'}
        if view_mode == 'dynamic':
            return {'display': 'block'}, {'display': 'none'}, plotly_controls_style
        else:
            return {'display': 'none'}, {'display': 'block', 'maxWidth': '100%'}, plotly_controls_style

    @app.callback(
        Output('bar-plotly-graph', 'figure'),
        [Input('stored-data', 'data'),
         Input('bar-category-dropdown', 'value'),
         Input('bar-value-dropdown', 'value'),
         Input('bar-group-dropdown', 'value'),
         Input('bar-mode-dropdown', 'value'),
         Input('bar-plot-type-radio', 'value')]
    )
    def update_plotly_bar_plot(stored_data_json, category_col, value_col, group_col, bar_mode, view_mode):
        if view_mode != 'dynamic' or stored_data_json is None or category_col is None:
            return px.scatter(title="請選擇動態檢視和類別變數")

        try:
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')
            
            title = f"{category_col} 的分布"
            if value_col:
                title = f"{value_col} 依據 {category_col} 的分布"
            if group_col:
                title += f"\n依據 {group_col} 分組"

            if value_col:
                fig = px.bar(df, x=category_col, y=value_col, color=group_col,
                           title=title, barmode=bar_mode)
            else:
                value_counts = df[category_col].value_counts().reset_index()
                value_counts.columns = [category_col, '計數']
                fig = px.bar(value_counts, x=category_col, y='計數',
                           title=title)

            fig.update_layout(
                transition_duration=300,
                xaxis_title=category_col,
                yaxis_title=value_col if value_col else "計數"
            )
            return fig

        except Exception as e:
            print(f"生成圖表時發生錯誤：{e}")
            return px.scatter(title=f"錯誤：{e}")

    @app.callback(
        Output('bar-static-img', 'src'),
        [Input('stored-data', 'data'),
         Input('bar-category-dropdown', 'value'),
         Input('bar-value-dropdown', 'value'),
         Input('bar-group-dropdown', 'value'),
         Input('bar-plot-type-radio', 'value')]
    )
    def update_static_bar_plot(stored_data_json, category_col, value_col, group_col, view_mode):
        if view_mode != 'static' or stored_data_json is None or category_col is None:
            return "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

        try:
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')
            
            plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
            plt.rcParams['axes.unicode_minus'] = False
            
            fig_static, ax = plt.subplots(figsize=(10, 6), tight_layout=True)
            
            if value_col:
                if group_col:
                    sns.barplot(data=df, x=category_col, y=value_col, hue=group_col, ax=ax)
                else:
                    sns.barplot(data=df, x=category_col, y=value_col, ax=ax)
            else:
                sns.countplot(data=df, x=category_col, hue=group_col, ax=ax)
            
            title = f"{category_col} 的分布"
            if value_col:
                title = f"{value_col} 依據 {category_col} 的分布"
            if group_col:
                title += f"\n依據 {group_col} 分組"
            
            ax.set_title(title)
            ax.set_xlabel(category_col)
            ax.set_ylabel(value_col if value_col else "計數")
            
            # 如果類別標籤太長，旋轉它們
            plt.xticks(rotation=45, ha='right')

            buf = BytesIO()
            fig_static.savefig(buf, format="png", bbox_inches='tight')
            buf.seek(0)
            data = base64.b64encode(buf.getvalue()).decode("utf8")
            plt.close(fig_static)
            return f"data:image/png;base64,{data}"

        except Exception as e:
            print(f"生成靜態圖表時發生錯誤：{e}")
            error_message = f"錯誤：{e}"
            # Return an SVG error placeholder
            return f"data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='100'%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='10px' fill='red'%3E{error_message}%3C/text%3E%3C/svg%3E"
        finally:
            # Ensure Matplotlib figure is closed
            if 'fig_static' in locals() and fig_static:
                 plt.close(fig_static)

    # Callback to populate dropdowns based on stored data
    @app.callback(
        [Output('bar-category-dropdown', 'options'),
         Output('bar-value-dropdown', 'options'),
         Output('bar-group-dropdown', 'options'),
         Output('bar-category-dropdown', 'value'),
         Output('bar-value-dropdown', 'value'),
         Output('bar-group-dropdown', 'value')],
        [Input('stored-data', 'data')]
    )
    def update_bar_dropdowns(stored_data_json):
        default_return = ([], [], [], None, None, None) # Define default return tuple

        if not stored_data_json:
            print("update_bar_dropdowns: No stored data.")
            return default_return

        try:
            print("update_bar_dropdowns: Reading stored data.")
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')

            if df.empty:
                 print("update_bar_dropdowns: DataFrame is empty.")
                 return default_return

            # Identify column types
            numeric_cols = df.select_dtypes(include=np.number).columns
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns

            # Create options
            categorical_options = [{'label': f"{col} (categorical)", 'value': col} for col in categorical_cols]
            numerical_options = [{'label': f"{col} (numeric)", 'value': col} for col in numeric_cols]
            grouping_options = categorical_options # Grouping is typically categorical

            # Set default values (e.g., first categorical for category, first numeric for value)
            default_category = categorical_cols[0] if not categorical_cols.empty else None
            # Value and group are optional, so default to None
            default_value = None
            default_group = None

            print("update_bar_dropdowns: Success.")
            return categorical_options, numerical_options, grouping_options, default_category, default_value, default_group

        except Exception as e:
            print(f"Error updating bar dropdowns: {e}")
            return default_return # Return default tuple on error

# --- End of Callback Registration ---

# NOTE: No 'if __name__ == "__main__":' block here
