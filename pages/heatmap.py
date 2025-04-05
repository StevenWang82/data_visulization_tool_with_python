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
    html.H2("熱力圖"),
    html.P("選擇變數以視覺化相關性。"),
    html.Div([
        html.Label("選擇要顯示的變數："),
        dcc.Dropdown(
            id='heatmap-columns-dropdown',
            multi=True,
            placeholder="選擇要包含的變數..."
        ),
    ]),
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
    html.Div([
        dcc.Graph(id='heatmap-plotly-graph', style={'display': 'block'}),
        html.Img(id='heatmap-static-img', style={'display': 'none', 'maxWidth': '100%'})
    ])
])

def register_callbacks(app):
    @app.callback(
        [Output('heatmap-plotly-graph', 'style'),
         Output('heatmap-static-img', 'style')],
        [Input('heatmap-plot-type-radio', 'value')]
    )
    def toggle_heatmap_view(view_mode):
        if view_mode == 'dynamic':
            return {'display': 'block'}, {'display': 'none'}
        else:
            return {'display': 'none'}, {'display': 'block', 'maxWidth': '100%'}

    @app.callback(
        Output('heatmap-plotly-graph', 'figure'),
        [Input('stored-data', 'data'),
         Input('heatmap-columns-dropdown', 'value'),
         Input('heatmap-plot-type-radio', 'value')]
    )
    def update_plotly_heatmap(stored_data_json, selected_columns, view_mode):
        if view_mode != 'dynamic' or stored_data_json is None or not selected_columns:
            return px.scatter(title="請選擇動態檢視和至少兩個變數")

        try:
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')
            
            # 計算相關係數
            corr_df = df[selected_columns].corr()
            
            # 創建熱力圖
            fig = px.imshow(
                corr_df,
                title="變數間的相關性熱力圖",
                labels=dict(color="相關係數"),
                color_continuous_scale="RdBu",
                aspect="auto"
            )
            
            fig.update_layout(
                transition_duration=300,
                xaxis_title="變數",
                yaxis_title="變數"
            )
            
            return fig

        except Exception as e:
            print(f"生成圖表時發生錯誤：{e}")
            return px.scatter(title=f"錯誤：{e}")

    @app.callback(
        Output('heatmap-static-img', 'src'),
        [Input('stored-data', 'data'),
         Input('heatmap-columns-dropdown', 'value'),
         Input('heatmap-plot-type-radio', 'value')]
    )
    def update_static_heatmap(stored_data_json, selected_columns, view_mode):
        if view_mode != 'static' or stored_data_json is None or not selected_columns:
            return "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

        try:
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')
            
            plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 計算相關係數
            corr_df = df[selected_columns].corr()
            
            # 創建熱力圖
            fig_static, ax = plt.subplots(figsize=(10, 8), tight_layout=True)
            sns.heatmap(corr_df, annot=True, cmap='RdBu', center=0, ax=ax)
            
            ax.set_title("變數間的相關性熱力圖")
            
            # 調整標籤方向以確保可讀性
            plt.xticks(rotation=45, ha='right')
            plt.yticks(rotation=0)

            buf = BytesIO()
            fig_static.savefig(buf, format="png", bbox_inches='tight')
            buf.seek(0)
            data = base64.b64encode(buf.getvalue()).decode("utf8")

            print("Static heatmap updated.")
            # Return the base64 encoded image string
            return f"data:image/png;base64,{data}"

        except Exception as e:
            print(f"Error generating static heatmap: {e}")
            error_message = f"Error: {e}"
            # Return an SVG error placeholder
            return f"data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='100'%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='10px' fill='red'%3E{error_message}%3C/text%3E%3C/svg%3E"
        finally:
            # Ensure Matplotlib figure is closed
            if fig_static:
                plt.close(fig_static)

# --- End of Callback Registration ---

# NOTE: No 'if __name__ == "__main__":' block here
