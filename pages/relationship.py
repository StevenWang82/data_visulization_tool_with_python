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

# 設定分組變數唯一值最大門檻
MAX_UNIQUE_GROUP_CATEGORIES = 50

# --- Layout Definition ---
layout = html.Div([

    html.H2("關係圖"),
    html.P("選擇變數以視覺化其關係。"),
    html.Div([
        html.Label("選擇第一個變數："),
        dcc.Dropdown(id='rel-var1-dropdown', placeholder="選擇第一個變數..."),
    ]),
    html.Div([
        html.Label("選擇第二個變數："),
        dcc.Dropdown(id='rel-var2-dropdown', placeholder="選擇第二個變數..."),
    ]),
    html.Div([
        html.Label("選擇分組變數（選填）："),
        dcc.Dropdown(id='rel-group-dropdown', placeholder="選擇分組變數..."),
    ]),
    html.Div([
        html.Label("選擇檢視模式："),
        dcc.RadioItems(
            id='rel-plot-type-radio',
            options=[
                {'label': '動態圖表', 'value': 'dynamic'},
                {'label': '靜態圖表', 'value': 'static'},
            ],
            value='dynamic',
            labelStyle={'display': 'inline-block', 'margin-right': '10px'}
        ),
    ]),

    html.Div(id='relationship-filter-status-display', 
             style={'marginBottom': '15px', 'padding': '10px', 'border': '1px solid #ddd', 'borderRadius': '5px', 'backgroundColor': '#f9f9f9'}),

    html.Div([
        dcc.Graph(id='relationship-plotly-graph', style={'display': 'block'}),
        html.Img(id='relationship-static-img', style={'display': 'none', 'maxWidth': '100%'})
    ]),

    # Section for Dynamic Code Snippet
    html.Div(id='rel-dynamic-code-section', children=[
        html.H4("動態圖表範例程式碼"),
        dcc.Markdown(
            id='rel-dynamic-code-block',
            style={
                'whiteSpace': 'pre-wrap',
                'backgroundColor': '#f8f8f8',
                'padding': '10px',
                'border': '1px solid #ccc'
            }
        )
    ]),

    # Section for Static Code Snippet
    html.Div(id='rel-static-code-section', children=[
        html.H4("靜態圖表範例程式碼"),
        dcc.Markdown(
            id='rel-static-code-block',
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
        [Output('relationship-plotly-graph', 'style'),
         Output('relationship-static-img', 'style')],
        [Input('rel-plot-type-radio', 'value')]
    )
    def toggle_relationship_view(view_mode):
        if view_mode == 'dynamic':
            return {'display': 'block'}, {'display': 'none'}
        else:
            return {'display': 'none'}, {'display': 'block', 'maxWidth': '100%'}

    @app.callback(
        Output('relationship-plotly-graph', 'figure'),
        [Input('filtered-data-store', 'data'), # Changed from stored-data
         Input('rel-var1-dropdown', 'value'),
         Input('rel-var2-dropdown', 'value'),
         Input('rel-group-dropdown', 'value'),
         Input('rel-plot-type-radio', 'value')]
    )
    def update_plotly_relationship_plot(stored_data_json, var1, var2, group_var, view_mode):
        if view_mode != 'dynamic' or stored_data_json is None or var1 is None or var2 is None:
            return px.scatter(title="請選擇動態檢視和兩個變數")

        try:
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')

            # Check for grouping variable unique value count
            if group_var and df[group_var].dtype in ['object', 'category'] and df[group_var].nunique() > MAX_UNIQUE_GROUP_CATEGORIES:
                warning_message = f"分組變數 '{group_var}' 的唯一值超過 {MAX_UNIQUE_GROUP_CATEGORIES} 個，不適合分組繪圖。"
                fig = go.Figure()
                fig.add_annotation(
                    text=warning_message,
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=14)
                )
                fig.update_layout(
                    title="警告",
                    xaxis={'visible': False},
                    yaxis={'visible': False},
                    plot_bgcolor='white' # Optional: set background color
                )
                return fig

            title = f"{var1} 和 {var2} 的關係"
            if group_var:
                title += f"\n依據 {group_var} 分組"

            fig = px.scatter(df, x=var1, y=var2, color=group_var,
                           title=title, trendline="ols")

            fig.update_layout(
                transition_duration=300,
                xaxis_title=var1,
                yaxis_title=var2
            )
            return fig

        except Exception as e:
            print(f"生成圖表時發生錯誤：{e}")
            return px.scatter(title=f"錯誤：{e}")

    @app.callback(
        Output('relationship-static-img', 'src'),
        [Input('filtered-data-store', 'data'), # Changed from stored-data
         Input('rel-var1-dropdown', 'value'),
         Input('rel-var2-dropdown', 'value'),
         Input('rel-group-dropdown', 'value'),
         Input('rel-plot-type-radio', 'value')]
    )
    def update_static_relationship_plot(stored_data_json, var1, var2, group_var, view_mode):
        if view_mode != 'static' or stored_data_json is None or var1 is None or var2 is None:
            return "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

        try:
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')

            plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
            plt.rcParams['axes.unicode_minus'] = False

            # Check for grouping variable unique value count
            if group_var and df[group_var].dtype in ['object', 'category'] and df[group_var].nunique() > MAX_UNIQUE_GROUP_CATEGORIES:
                warning_message = f"分組變數 '{group_var}' 的唯一值超過 {MAX_UNIQUE_GROUP_CATEGORIES} 個，\n不適合分組繪圖。"
                fig_warn, ax_warn = plt.subplots(figsize=(8, 2), tight_layout=True)
                ax_warn.text(0.5, 0.5, warning_message, ha='center', va='center', fontsize=12, color='red')
                ax_warn.axis('off') # Hide axes

                buf = BytesIO()
                fig_warn.savefig(buf, format="png")
                buf.seek(0)
                data = base64.b64encode(buf.getvalue()).decode("utf8")
                plt.close(fig_warn) # Close the warning figure
                return f"data:image/png;base64,{data}"

            fig_static, ax = plt.subplots(figsize=(8, 5), tight_layout=True)

            if group_var:
                sns.scatterplot(data=df, x=var1, y=var2, hue=group_var, ax=ax)
            else:
                sns.scatterplot(data=df, x=var1, y=var2, ax=ax)
                sns.regplot(data=df, x=var1, y=var2, scatter=False, ax=ax)
            
            title = f"{var1} 和 {var2} 的關係"
            if group_var:
                title += f"\n依據 {group_var} 分組"
            
            ax.set_title(title)
            ax.set_xlabel(var1)
            ax.set_ylabel(var2)

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
        [Output('rel-var1-dropdown', 'options'),
         Output('rel-var2-dropdown', 'options'),
         Output('rel-group-dropdown', 'options'),
         Output('rel-var1-dropdown', 'value'),
         Output('rel-var2-dropdown', 'value'),
         Output('rel-group-dropdown', 'value')],
        [Input('filtered-data-store', 'data')] # Changed from stored-data
    )
    def update_relationship_dropdowns(stored_data_json):
        default_return = ([], [], [], None, None, None) # Define default return tuple

        if not stored_data_json:
            print("update_relationship_dropdowns: No stored data.")
            return default_return

        try:
            print("update_relationship_dropdowns: Reading stored data.")
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')

            if df.empty:
                 print("update_relationship_dropdowns: DataFrame is empty.")
                 return default_return

            # Identify column types
            numeric_cols = df.select_dtypes(include=np.number).columns
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns
            datetime_cols = df.select_dtypes(include=['datetime', 'datetimetz']).columns
            bool_cols = df.select_dtypes(include=['bool']).columns
            all_cols = df.columns

            # 過濾唯一值超過門檻的類別變數
            categorical_cols = [
                col for col in categorical_cols
                if df[col].nunique() <= MAX_UNIQUE_GROUP_CATEGORIES
            ]

            # Create options with data type labels for var1 and var2 dropdowns
            all_options = []
            for col in all_cols:
                if col in numeric_cols:
                    dtype_label = "numeric"
                elif col in categorical_cols:
                    dtype_label = "categorical"
                elif col in datetime_cols:
                    dtype_label = "datetime"
                elif col in bool_cols:
                    dtype_label = "boolean"
                else:
                    dtype_label = "other"
                all_options.append({'label': f"{col} ({dtype_label})", 'value': col})

            grouping_options = [{'label': f"{col} (categorical)", 'value': col} for col in categorical_cols]

            # Set default values (e.g., first two numeric columns if available)
            default_var1 = numeric_cols[0] if len(numeric_cols) > 0 else None
            default_var2 = numeric_cols[1] if len(numeric_cols) > 1 else None

            print("update_relationship_dropdowns: Success.")
            return all_options, all_options, grouping_options, default_var1, default_var2, None

        except Exception as e:
            print(f"Error updating relationship dropdowns: {e}")
            return default_return # Return default tuple on error

    # --- Callback to update filter status display on this page ---
    @app.callback(
        Output('relationship-filter-status-display', 'children'),
        Input('filter-status-message-store', 'data')
    )
    def update_relationship_filter_status(status_message):
        if status_message:
            return status_message
        return "目前未套用篩選條件。"

    @app.callback(
        [Output('rel-dynamic-code-section', 'style'),
         Output('rel-static-code-section', 'style')],
        [Input('rel-plot-type-radio', 'value')]
    )
    def toggle_rel_code_section_visibility(view_mode):
        if view_mode == 'dynamic':
            return {'display': 'block'}, {'display': 'none'}
        elif view_mode == 'static':
            return {'display': 'none'}, {'display': 'block'}
        return {'display': 'block'}, {'display': 'none'} # Default to showing dynamic

    @app.callback(
        [Output('rel-dynamic-code-block', 'children'),
         Output('rel-static-code-block', 'children')],
        [Input('filtered-data-store', 'data'),
         Input('rel-var1-dropdown', 'value'),
         Input('rel-var2-dropdown', 'value'),
         Input('rel-group-dropdown', 'value'),
         Input('rel-plot-type-radio', 'value')]
    )
    def update_rel_code_snippets(stored_data_json, var1, var2, group_var, view_mode):
        if stored_data_json is None or var1 is None or var2 is None:
            msg = "請先選擇兩個變數"
            return msg, msg

        # Dynamic (Plotly) code generation
        plotly_params = f"df, x='{var1}', y='{var2}'"
        if group_var:
            plotly_params += f", color='{group_var}'"
        plotly_params += ", title='', trendline='ols'" # Match plot generation

        plotly_code = f"""```python
import plotly.express as px

# Assuming 'df' is your pandas DataFrame
fig = px.scatter({plotly_params})
fig.show()
```"""

        # Static (Seaborn) code generation
        static_code = f"""```python
import seaborn as sns
import matplotlib.pyplot as plt

# Assuming 'df' is your pandas DataFrame
plt.figure(figsize=(8, 5))
"""
        if group_var:
            static_code += f"sns.scatterplot(data=df, x='{var1}', y='{var2}', hue='{group_var}')\n"
        else:
            static_code += f"sns.scatterplot(data=df, x='{var1}', y='{var2}')\n"
            static_code += f"sns.regplot(data=df, x='{var1}', y='{var2}', scatter=False)\n" # Add regplot if no grouping

        static_code += f"""plt.title('')
plt.xlabel('{var1}')
plt.ylabel('{var2}')
plt.tight_layout() # Added for better spacing
plt.show()
```"""

        if view_mode == 'dynamic':
            return plotly_code, ""
        elif view_mode == 'static':
            return "", static_code
        else:
            # Should not happen with RadioItems, but return dynamic as default
            return plotly_code, ""

# --- End of Callback Registration ---

# NOTE: No 'if __name__ == "__main__":' block here
