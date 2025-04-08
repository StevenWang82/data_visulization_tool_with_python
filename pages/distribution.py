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
import dash_bootstrap_components as dbc # Import dbc for Alert

# Configure Matplotlib to use 'Agg' backend
import matplotlib
matplotlib.use('Agg')

# --- Layout Definition ---
layout = html.Div([
    # --- Filter Status Display Area (NEW) ---

    html.H2("分布圖"),
    html.P("選擇變數以視覺化其分布。"),
    html.Div([
        html.Label("選擇數值變數："),
        dcc.Dropdown(id='dist-numerical-dropdown', placeholder="選擇一個數值欄位..."),
    ]),
    html.Div([
        html.Label("選擇分組變數（選填）："),
        dcc.Dropdown(id='dist-grouping-dropdown', placeholder="選擇一個分類欄位..."),
    ]),
    html.Div([
        html.Label("選擇圖表類型："),
        dcc.Dropdown(
            id='dist-plotly-type-dropdown',
            options=[
                {'label': '直方圖', 'value': 'histogram'},
                {'label': '箱型圖', 'value': 'box'},
                {'label': '小提琴圖', 'value': 'violin'},
            ],
            value='histogram',
            clearable=False
        ),
    ], id='plotly-type-div'),
    html.Div([
        html.Label("選擇檢視模式："),
        dcc.RadioItems(
            id='dist-view-mode-radio',
            options=[
                {'label': '動態圖表', 'value': 'dynamic'},
                {'label': '靜態圖表', 'value': 'static'},
            ],
            value='dynamic',
            labelStyle={'display': 'inline-block', 'margin-right': '10px'}
        ),
    ]),
    html.Div(id='distribution-filter-status-display', 
            style={'marginBottom': '15px', 'padding': '10px', 'border': '1px solid #ddd', 'borderRadius': '5px', 'backgroundColor': '#f9f9f9'}),

    html.Div([
        dcc.Graph(id='distribution-plotly-graph', style={'display': 'block'}),
        html.Img(id='distribution-static-img', style={'display': 'none', 'maxWidth': '100%'})
    ])
])

def register_callbacks(app):
    @app.callback(
        [Output('distribution-plotly-graph', 'style'),
         Output('distribution-static-img', 'style'),
         Output('plotly-type-div', 'style')],
        [Input('dist-view-mode-radio', 'value')]
    )
    def toggle_distribution_view(view_mode):
        if view_mode == 'dynamic':
            return {'display': 'block'}, {'display': 'none'}, {'display': 'block'}
        else:
            return {'display': 'none'}, {'display': 'block', 'maxWidth': '100%'}, {'display': 'none'}

    @app.callback(
        Output('distribution-plotly-graph', 'figure'),
        [Input('filtered-data-store', 'data'), # Changed from stored-data to use filtered/latest data
         Input('dist-numerical-dropdown', 'value'),
         Input('dist-grouping-dropdown', 'value'),
         Input('dist-plotly-type-dropdown', 'value'),
         Input('dist-view-mode-radio', 'value')]
    )
    def update_plotly_distribution_plot(stored_data_json, numerical_col, grouping_col, plotly_type, view_mode):
        if view_mode != 'dynamic' or stored_data_json is None or numerical_col is None:
            return px.scatter(title="請選擇動態檢視和數值變數")

        try:
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')

            # Check unique values for grouping variable
            if grouping_col and df[grouping_col].dtype in ['object', 'category'] and df[grouping_col].nunique() > 20:
                warning_message = f"分組變數 '{grouping_col}' 的唯一值超過 20 個，不適合分組繪圖。"
                fig = go.Figure()
                fig.add_annotation(
                    text=warning_message, xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False, font=dict(size=14)
                )
                fig.update_layout(title="警告", xaxis={'visible': False}, yaxis={'visible': False}, plot_bgcolor='white')
                return fig

            plot_type_names = {
                'histogram': '直方圖',
                'box': '箱型圖',
                'violin': '小提琴圖'
            }
            
            title = f"{plot_type_names[plotly_type]}：{numerical_col}"
            if grouping_col:
                title += f" (依據 {grouping_col} 分組)"

            if plotly_type == 'histogram':
                fig = px.histogram(df, x=numerical_col, color=grouping_col, 
                                 title=title, marginal="rug", hover_data=df.columns)
            elif plotly_type == 'box':
                fig = px.box(df, x=grouping_col, y=numerical_col, 
                           color=grouping_col, title=title, points="all")
            elif plotly_type == 'violin':
                fig = px.violin(df, x=grouping_col, y=numerical_col, 
                              color=grouping_col, title=title, box=True, points="all")

            fig.update_layout(
                transition_duration=300,
                xaxis_title="數值",
                yaxis_title="頻率" if plotly_type == 'histogram' else "數值分布"
            )
            return fig

        except Exception as e:
            print(f"生成圖表時發生錯誤：{e}")
            return px.scatter(title=f"錯誤：{e}")

    @app.callback(
        Output('distribution-static-img', 'src'),
        [Input('filtered-data-store', 'data'), # Changed from stored-data to use filtered/latest data
         Input('dist-numerical-dropdown', 'value'),
         Input('dist-grouping-dropdown', 'value'),
         Input('dist-view-mode-radio', 'value')]
    )
    def update_static_distribution_plot(stored_data_json, numerical_col, grouping_col, view_mode):
        if view_mode != 'static' or stored_data_json is None or numerical_col is None:
            return "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

        try:
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')

            # Check unique values for grouping variable
            if grouping_col and df[grouping_col].dtype in ['object', 'category'] and df[grouping_col].nunique() > 20:
                warning_message = f"分組變數 '{grouping_col}' 的唯一值超過 20 個，\n不適合分組繪圖。"
                fig_warn, ax_warn = plt.subplots(figsize=(8, 2), tight_layout=True)
                ax_warn.text(0.5, 0.5, warning_message, ha='center', va='center', fontsize=12, color='red')
                ax_warn.axis('off')
                buf = BytesIO()
                fig_warn.savefig(buf, format="png")
                buf.seek(0)
                data = base64.b64encode(buf.getvalue()).decode("utf8")
                plt.close(fig_warn)
                return f"data:image/png;base64,{data}"

            plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']  # 設置中文字體
            plt.rcParams['axes.unicode_minus'] = False  # 解決負號顯示問題
            
            fig_static, ax = plt.subplots(figsize=(8, 5), tight_layout=True)
            sns.histplot(data=df, x=numerical_col, hue=grouping_col, kde=True, ax=ax)
            
            title = f"{numerical_col} 的分布"
            if grouping_col:
                title += f"\n依據 {grouping_col} 分組"
            
            ax.set_title(title)
            ax.set_xlabel("數值")
            ax.set_ylabel("頻率")

            buf = BytesIO()
            fig_static.savefig(buf, format="png")
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
        [Output('dist-numerical-dropdown', 'options'),
         Output('dist-grouping-dropdown', 'options'),
         Output('dist-numerical-dropdown', 'value'),
         Output('dist-grouping-dropdown', 'value')],
        [Input('filtered-data-store', 'data')] # Changed from stored-data to use filtered/latest data for dropdown population
        # If you *really* want dropdowns to clear/reset on mode change, keep it,
        # but usually dropdowns should just reflect the available data columns.
    )
    def update_distribution_dropdowns(stored_data_json):
        default_return = ([], [], None, None) # Define default return tuple

        if not stored_data_json:
            print("update_distribution_dropdowns: No stored data.")
            return default_return

        try:
            print("update_distribution_dropdowns: Reading stored data.")
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')

            if df.empty:
                 print("update_distribution_dropdowns: DataFrame is empty.")
                 return default_return

            # Use numpy for robust numeric check
            numeric_cols = df.select_dtypes(include=np.number).columns
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns

            numerical_options = [{'label': f"{col} (numeric)", 'value': col} for col in numeric_cols]
            grouping_options = []
            for col in categorical_cols:
                 # Check dtype more robustly
                dtype_str = 'category' if pd.api.types.is_categorical_dtype(df[col]) else 'object'
                grouping_options.append({'label': f"{col} ({dtype_str})", 'value': col})

            # Set default safely
            default_numerical = numeric_cols[0] if not numeric_cols.empty else None

            print("update_distribution_dropdowns: Success.")
            return numerical_options, grouping_options, default_numerical, None

        except Exception as e:
            print(f"Error updating distribution dropdowns: {e}")
            return default_return # Return default tuple on error

    # --- Callback to update filter status display on this page ---
    @app.callback(
        Output('distribution-filter-status-display', 'children'),
        Input('filter-status-message-store', 'data')
    )
    def update_distribution_filter_status(status_message):
        if status_message:
            return status_message
        
        return "目前未套用篩選條件。"

# --- End of Callback Registration ---

# NOTE: No 'if __name__ == "__main__":' block here
