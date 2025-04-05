import dash
from dash import dcc, html, Input, Output, State # Ensure State is imported if used
import plotly.express as px
import pandas as pd
import numpy as np # Import numpy
import io
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

# Configure Matplotlib to use 'Agg' backend
import matplotlib
matplotlib.use('Agg')

# --- Layout for Bar Plot Page (Stays at top level) ---
layout = html.Div([
    html.H2("Bar Plot"),
    html.P("Select variables to visualize counts or aggregated values."),

    html.Div([
        html.Label("Select Categorical Variable (X-axis):"),
        dcc.Dropdown(id='bar-categorical-dropdown', placeholder="Select X-axis..."),
    ]),
    html.Div([
        # Clarified Y-axis purpose (aggregation or optional if counting)
        html.Label("Select Numerical Variable (Y-axis, for aggregation):"),
        dcc.Dropdown(id='bar-numerical-dropdown', placeholder="Select Y-axis (optional for counts)..."),
    ]),
    html.Div([
        html.Label("Select Grouping Variable (Optional, for color/hue):"),
        dcc.Dropdown(id='bar-grouping-dropdown', placeholder="Select grouping variable..."),
    ]),
    # Group Plotly-specific controls together
    html.Div(id='plotly-bar-controls', children=[
        html.Label("Select Bar Mode (Plotly):"),
        dcc.RadioItems(
            id='bar-mode-radio',
            options=[
                {'label': 'Grouped', 'value': 'group'},
                {'label': 'Stacked', 'value': 'stack'},
                # Removed 'basic' as it's implied when no grouping is used or Plotly handles it
            ],
            value='group', # Default to group if grouping is chosen
            labelStyle={'display': 'inline-block', 'margin-right': '10px'}
        ),
    ], style={'display': 'block'}), # Initially visible, linked to dynamic view

    html.Div([
        html.Label("Select Plot Type:"),
        dcc.RadioItems(
            id='bar-plot-type-radio',
            options=[
                {'label': 'Dynamic (Plotly)', 'value': 'dynamic'},
                {'label': 'Static (Seaborn)', 'value': 'static'},
            ],
            value='dynamic',
            labelStyle={'display': 'inline-block', 'margin-right': '10px'}
        ),
    ]),

    # Div to hold the plots
    html.Div([
        dcc.Graph(id='bar-plotly-graph', style={'display': 'block'}),
        html.Img(id='bar-static-img', style={'display': 'none', 'maxWidth': '100%'})
    ])
])

# --- Callback Registration Function ---
# ALL callbacks defined INSIDE this function
def register_callbacks(app):

    # Callback to toggle visibility of plot areas and Plotly controls
    @app.callback(
        [Output('bar-plotly-graph', 'style'),
         Output('bar-static-img', 'style'),
         Output('plotly-bar-controls', 'style')], # Toggle Plotly bar mode visibility
        [Input('bar-plot-type-radio', 'value')]
    )
    def toggle_bar_view(view_mode):
        plotly_controls_style = {'display': 'block'} if view_mode == 'dynamic' else {'display': 'none'}
        if view_mode == 'dynamic':
            return {'display': 'block'}, {'display': 'none'}, plotly_controls_style
        else: # static
            return {'display': 'none'}, {'display': 'block', 'maxWidth': '100%'}, plotly_controls_style

    # Callback to populate dropdowns based on stored data
    @app.callback(
        [Output('bar-categorical-dropdown', 'options'),
         Output('bar-numerical-dropdown', 'options'),
         Output('bar-grouping-dropdown', 'options'),
         Output('bar-categorical-dropdown', 'value'),
         Output('bar-numerical-dropdown', 'value'),
         Output('bar-grouping-dropdown', 'value')],
        [Input('stored-data', 'data')] # Only trigger on data change
    )
    def update_bar_dropdowns(stored_data_json):
        # Define default return structure
        default_return = ([], [], [], None, None, None)

        if not stored_data_json:
            print("update_bar_dropdowns: No stored data.")
            return default_return

        try:
            print("update_bar_dropdowns: Reading stored data.")
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')

            if df.empty:
                print("update_bar_dropdowns: DataFrame empty.")
                return default_return

            # Get column types
            numeric_cols = df.select_dtypes(include=np.number).columns
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns

            # Format options
            numerical_options = [{'label': f"{col} (numeric)", 'value': col} for col in numeric_cols]
            categorical_options = []
            for col in categorical_cols:
                dtype_str = 'category' if pd.api.types.is_categorical_dtype(df[col]) else 'object'
                categorical_options.append({'label': f"{col} ({dtype_str})", 'value': col})

            # Set default values safely
            default_cat = categorical_cols[0] if not categorical_cols.empty else None
            default_num = numeric_cols[0] if not numeric_cols.empty else None
            # Grouping is optional, default to None

            print("update_bar_dropdowns: Success.")
            # Provide categorical options for both X and Grouping dropdowns
            return categorical_options, numerical_options, categorical_options, default_cat, default_num, None

        except Exception as e:
            print(f"Error updating bar dropdowns: {e}")
            return default_return # Return default structure on error

    # Callback to update the Plotly bar plot
    # *** CORRECTLY INDENTED INSIDE register_callbacks ***
    @app.callback(
        Output('bar-plotly-graph', 'figure'),
        [Input('stored-data', 'data'),
         Input('bar-categorical-dropdown', 'value'),
         Input('bar-numerical-dropdown', 'value'), # Optional Y-axis
         Input('bar-grouping-dropdown', 'value'), # Optional grouping/color
         Input('bar-mode-radio', 'value'),       # Plotly barmode
         Input('bar-plot-type-radio', 'value')]  # Is dynamic view selected?
    )
    def update_plotly_bar_plot(stored_data_json, x_col, y_col, group_col, bar_mode, plot_type):
        # Guard Clause: Check prerequisites
        # Need dynamic mode, data, and at least an X-axis column
        if plot_type != 'dynamic' or not stored_data_json or not x_col:
            return px.bar(title="Select Dynamic View and X-axis") # Return empty bar fig

        try:
            print("Updating Plotly bar plot...")
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')

            # Determine actual parameters for px.bar
            # If no y_col, Plotly counts occurrences of x_col categories
            # If y_col is provided, it aggregates y_col for each x_col category
            # Barmode ('group' or 'stack') only applies if group_col is also selected
            plotly_barmode = bar_mode if group_col else None # Use selected mode only if grouping

            title = f"Bar plot: {x_col}" + (f" vs {y_col}" if y_col else " Counts")
            if group_col:
                title += f" grouped by {group_col}"

            fig = px.bar(df, x=x_col, y=y_col, # y_col can be None for counts
                         color=group_col,       # group_col used for color
                         barmode=plotly_barmode,  # 'group' or 'stack' if group_col present
                         title=title,
                         hover_data=df.columns)

            fig.update_layout(transition_duration=300)
            print("Plotly bar plot updated.")
            return fig

        except Exception as e:
            print(f"Error generating Plotly bar plot: {e}")
            # Return a bar figure indicating the error
            return px.bar(title=f"Error: {e}")


    # Callback to update the Static (Seaborn) bar plot image
    # *** CORRECTLY INDENTED INSIDE register_callbacks ***
    @app.callback(
        Output('bar-static-img', 'src'),
        [Input('stored-data', 'data'),
         Input('bar-categorical-dropdown', 'value'),
         Input('bar-numerical-dropdown', 'value'), # Optional Y-axis
         Input('bar-grouping-dropdown', 'value'), # Optional grouping/hue
         Input('bar-plot-type-radio', 'value')]  # Is static view selected?
    )
    def update_static_bar_plot(stored_data_json, x_col, y_col, group_col, plot_type):
        # Guard Clause: Check prerequisites
        # Need static mode, data, and at least an X-axis column
        if plot_type != 'static' or not stored_data_json or not x_col:
            return "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

        fig_static = None # Initialize fig_static
        try:
            print("Updating Static bar plot...")
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')

            # Create Matplotlib figure and axes
            fig_static, ax = plt.subplots(figsize=(10, 6), tight_layout=True)

            # Determine plot type: countplot if no y_col, barplot if y_col
            if y_col:
                # Barplot aggregates numerical y_col (default: mean)
                print(f"Generating Seaborn barplot (aggregating {y_col})")
                sns.barplot(data=df, x=x_col, y=y_col, hue=group_col, ax=ax, errorbar=('ci', 95)) # Show confidence interval
                title = f"Static Bar plot: Mean of {y_col} by {x_col}"
            else:
                # Countplot shows counts of categories in x_col
                print("Generating Seaborn countplot")
                sns.countplot(data=df, x=x_col, hue=group_col, ax=ax)
                title = f"Static Count plot: {x_col}"

            if group_col:
                title += f" grouped by {group_col}"

            # Common plot adjustments
            ax.set_title(title)
            ax.tick_params(axis='x', rotation=45) # Rotate labels if needed
            ax.grid(axis='y', linestyle='--', alpha=0.7)

            # Save plot to buffer
            buf = BytesIO()
            fig_static.savefig(buf, format="png")
            buf.seek(0) # Rewind buffer
            data = base64.b64encode(buf.getvalue()).decode("utf8")

            print("Static bar plot updated.")
            # Return the base64 encoded image string
            return f"data:image/png;base64,{data}"

        except Exception as e:
            print(f"Error generating static bar plot: {e}")
            error_message = f"Error: {e}"
            # Return an SVG error placeholder
            return f"data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='100'%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='10px' fill='red'%3E{error_message}%3C/text%3E%3C/svg%3E"
        finally:
            # Ensure Matplotlib figure is closed
            if fig_static:
                plt.close(fig_static)

# --- End of Callback Registration ---

# NOTE: No 'if __name__ == "__main__":' block here