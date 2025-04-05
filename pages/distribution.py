import dash
from dash import dcc, html, Input, Output, State # Ensure State is imported if used
import plotly.express as px
import pandas as pd
import numpy as np # Ensure numpy is imported if used (e.g., for np.number)
import io
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

# Configure Matplotlib to use 'Agg' backend
import matplotlib
matplotlib.use('Agg')

# --- Layout Definition (Stays at the top level) ---
layout = html.Div([
    html.H2("Distribution Plot"),
    html.P("Select variables to visualize their distribution."),
    html.Div([
        html.Label("Select Numerical Variable:"),
        dcc.Dropdown(id='dist-numerical-dropdown', placeholder="Select a numerical column..."),
    ]),
    html.Div([
        html.Label("Select Grouping Variable (Optional):"),
        dcc.Dropdown(id='dist-grouping-dropdown', placeholder="Select a categorical column..."),
    ]),
     html.Div([
        html.Label("Select Plotly Chart Type (if Dynamic):"),
        dcc.Dropdown(
            id='dist-plotly-type-dropdown',
            options=[
                {'label': 'Histogram', 'value': 'histogram'},
                {'label': 'Box Plot', 'value': 'box'},
                {'label': 'Violin Plot', 'value': 'violin'},
            ],
            value='histogram',
            clearable=False
        ),
    ], id='plotly-type-div'),
    html.Div([
        html.Label("Select View Mode:"),
        dcc.RadioItems(
            id='dist-view-mode-radio',
            options=[
                {'label': 'Dynamic (Plotly)', 'value': 'dynamic'},
                {'label': 'Static (Seaborn)', 'value': 'static'},
            ],
            value='dynamic',
            labelStyle={'display': 'inline-block', 'margin-right': '10px'}
        ),
    ]),
    html.Div([
        dcc.Graph(id='distribution-plotly-graph', style={'display': 'block'}),
        html.Img(id='distribution-static-img', style={'display': 'none', 'maxWidth': '100%'})
    ])
])

# --- Callback Registration Function ---
# ALL callbacks are defined INSIDE this function
def register_callbacks(app):

    # Callback to control visibility of Plotly graph vs Static image
    @app.callback(
        [Output('distribution-plotly-graph', 'style'),
         Output('distribution-static-img', 'style'),
         Output('plotly-type-div', 'style')],
        [Input('dist-view-mode-radio', 'value')]
    )
    def toggle_distribution_view(view_mode):
        if view_mode == 'dynamic':
            return {'display': 'block'}, {'display': 'none'}, {'display': 'block'}
        else: # static
            return {'display': 'none'}, {'display': 'block', 'maxWidth': '100%'}, {'display': 'none'}

    # Callback to update the Plotly graph
    @app.callback(
        Output('distribution-plotly-graph', 'figure'),
        [Input('stored-data', 'data'),
         Input('dist-numerical-dropdown', 'value'),
         Input('dist-grouping-dropdown', 'value'),
         Input('dist-plotly-type-dropdown', 'value'),
         Input('dist-view-mode-radio', 'value')]
    )
    def update_plotly_distribution_plot(stored_data_json, numerical_col, grouping_col, plotly_type, view_mode):
        if view_mode != 'dynamic' or stored_data_json is None or numerical_col is None:
            return px.scatter(title="Select Dynamic View and Numerical Variable") # Return empty fig

        try:
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')
            title = f"{plotly_type.capitalize()} plot of {numerical_col}" + (f" grouped by {grouping_col}" if grouping_col else "")

            if plotly_type == 'histogram':
                fig = px.histogram(df, x=numerical_col, color=grouping_col, title=title, marginal="rug", hover_data=df.columns)
            elif plotly_type == 'box':
                # For box plot, x is usually the grouping, y is numerical
                fig = px.box(df, x=grouping_col, y=numerical_col, color=grouping_col, title=title, points="all")
            elif plotly_type == 'violin':
                 # For violin plot, x is usually the grouping, y is numerical
                fig = px.violin(df, x=grouping_col, y=numerical_col, color=grouping_col, title=title, box=True, points="all")
            else:
                fig = px.histogram(df, x=numerical_col, color=grouping_col, title=f"Unknown type: {plotly_type}, showing Histogram")

            fig.update_layout(transition_duration=300)
            return fig

        except Exception as e:
            print(f"Error generating Plotly distribution plot: {e}")
            # Return a figure indicating error, ensure it matches Output type (figure)
            return px.scatter(title=f"Error: {e}")


    # Callback to update the Static plot image
    @app.callback(
        Output('distribution-static-img', 'src'),
        [Input('stored-data', 'data'),
         Input('dist-numerical-dropdown', 'value'),
         Input('dist-grouping-dropdown', 'value'),
         Input('dist-view-mode-radio', 'value')]
    )
    def update_static_distribution_plot(stored_data_json, numerical_col, grouping_col, view_mode):
        if view_mode != 'static' or stored_data_json is None or numerical_col is None:
            return "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

        fig_static = None # Initialize for finally block
        try:
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')

            fig_static, ax = plt.subplots(figsize=(8, 5), tight_layout=True)
            sns.histplot(data=df, x=numerical_col, hue=grouping_col, kde=True, ax=ax)
            title = f"Static Distribution of {numerical_col}" + (f" by {grouping_col}" if grouping_col else "")
            ax.set_title(title)

            buf = BytesIO()
            fig_static.savefig(buf, format="png")
            buf.seek(0)
            data = base64.b64encode(buf.getvalue()).decode("utf8")
            plt.close(fig_static) # Close figure AFTER getting data
            return f"data:image/png;base64,{data}"

        except Exception as e:
            print(f"Error generating static distribution plot: {e}")
            error_message = f"Error: {e}"
            # Simple SVG placeholder for error
            return f"data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='100'%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='10px' fill='red'%3E{error_message}%3C/text%3E%3C/svg%3E"
        # finally: # Ensure plot is closed even if errors occur before saving
        #     if fig_static:
        #         plt.close(fig_static) # This might be redundant if closed in try, but safe

    # Callback to populate dropdowns based on stored data
    @app.callback(
        [Output('dist-numerical-dropdown', 'options'),
         Output('dist-grouping-dropdown', 'options'),
         Output('dist-numerical-dropdown', 'value'),
         Output('dist-grouping-dropdown', 'value')],
        [Input('stored-data', 'data')] # Removed view_mode trigger, dropdowns depend only on data
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

# --- End of Callback Registration ---

# NOTE: No 'if __name__ == "__main__":' block here