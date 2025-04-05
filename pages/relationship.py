import dash
from dash import dcc, html, Input, Output, State # Ensure State is imported if used
import plotly.express as px
import pandas as pd
import numpy as np # Import numpy for numeric selection
import io
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

# Configure Matplotlib to use 'Agg' backend
import matplotlib
matplotlib.use('Agg')

# --- Layout for Relationship Plot Page (Stays at top level) ---
layout = html.Div([
    html.H2("Relationship Plot"),
    html.P("Select variables to visualize their relationship."),

    html.Div([
        html.Label("Select X-axis Variable (Numerical):"),
        dcc.Dropdown(id='rel-xaxis-dropdown', placeholder="Select X-axis..."),
    ]),
    html.Div([
        html.Label("Select Y-axis Variable (Numerical):"),
        dcc.Dropdown(id='rel-yaxis-dropdown', placeholder="Select Y-axis..."),
    ]),
    html.Div([
        # Clarified the label regarding unique value limit for performance/readability
        html.Label("Select Grouping Variable (Optional, Categorical, <20 unique vals recommended):"),
        dcc.Dropdown(id='rel-grouping-dropdown', placeholder="Select grouping variable..."),
    ]),
    html.Div([
        html.Label("Select Plot Type:"),
        dcc.RadioItems(
            id='rel-plot-type-radio',
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
        dcc.Graph(id='relationship-plotly-graph', style={'display': 'block'}),
        html.Img(id='relationship-static-img', style={'display': 'none', 'maxWidth': '100%'})
    ])
])

# --- Callback Registration Function ---
# ALL callbacks defined INSIDE this function
def register_callbacks(app):

    # Callback to toggle visibility based on plot type selection
    @app.callback(
        [Output('relationship-plotly-graph', 'style'),
         Output('relationship-static-img', 'style')],
        [Input('rel-plot-type-radio', 'value')]
    )
    def toggle_relationship_view(view_mode):
        if view_mode == 'dynamic':
            # Show Plotly graph, hide static image
            return {'display': 'block'}, {'display': 'none'}
        else: # static
            # Hide Plotly graph, show static image
            return {'display': 'none'}, {'display': 'block', 'maxWidth': '100%'}

    # Callback to populate dropdowns based on stored data
    @app.callback(
        [Output('rel-xaxis-dropdown', 'options'),
         Output('rel-yaxis-dropdown', 'options'),
         Output('rel-grouping-dropdown', 'options'),
         Output('rel-xaxis-dropdown', 'value'),
         Output('rel-yaxis-dropdown', 'value'),
         Output('rel-grouping-dropdown', 'value')],
        [Input('stored-data', 'data')] # Removed plot_type trigger - dropdowns only depend on data
    )
    def update_relationship_dropdowns(stored_data_json):
        # Define default return values (important for error handling and initial state)
        default_return = ([], [], [], None, None, None)

        if not stored_data_json:
            print("update_relationship_dropdowns: No stored data found.")
            return default_return

        try:
            print("update_relationship_dropdowns: Reading stored data.")
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')

            if df.empty:
                print("update_relationship_dropdowns: DataFrame is empty.")
                return default_return

            # Select columns using robust methods
            numeric_cols = df.select_dtypes(include=np.number).columns
            potential_grouping_cols = df.select_dtypes(include=['object', 'category']).columns

            # Filter grouping columns based on unique value count (performance suggestion)
            valid_grouping_cols = [col for col in potential_grouping_cols if df[col].nunique() < 20]

            # Format options
            numerical_options = [{'label': f"{col} (numeric)", 'value': col} for col in numeric_cols]
            grouping_options = []
            for col in valid_grouping_cols:
                dtype_str = 'category' if pd.api.types.is_categorical_dtype(df[col]) else 'object'
                grouping_options.append({'label': f"{col} ({dtype_str})", 'value': col})

            # Set default selections safely
            default_x = numeric_cols[0] if not numeric_cols.empty else None
            default_y = numeric_cols[1] if len(numeric_cols) > 1 else None # Check length >= 2

            print("update_relationship_dropdowns: Success.")
            # Return the calculated options and default values
            return numerical_options, numerical_options, grouping_options, default_x, default_y, None

        except Exception as e:
            print(f"Error reading/processing data for relationship dropdowns: {e}")
            # Return the default empty structure on error
            return default_return

    # Callback to update the Plotly relationship plot
    # *** THIS CALLBACK IS NOW CORRECTLY INDENTED INSIDE register_callbacks ***
    @app.callback(
        Output('relationship-plotly-graph', 'figure'),
        [Input('stored-data', 'data'),
         Input('rel-xaxis-dropdown', 'value'),
         Input('rel-yaxis-dropdown', 'value'),
         Input('rel-grouping-dropdown', 'value'),
         Input('rel-plot-type-radio', 'value')] # Need to know if dynamic is selected
    )
    def update_plotly_relationship_plot(stored_data_json, x_col, y_col, group_col, plot_type):
        # Guard clause: Only proceed if dynamic mode, data exists, and axes are selected
        if plot_type != 'dynamic' or not stored_data_json or not x_col or not y_col:
            # Return a blank figure matching the Output type
            return px.scatter(title="Select Dynamic View and X/Y Axes")

        try:
            print("Updating Plotly relationship plot...")
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')
            title = f"Relationship between {x_col} and {y_col}" + (f" grouped by {group_col}" if group_col else "")

            # Generate Plotly scatter plot
            fig = px.scatter(df, x=x_col, y=y_col, color=group_col, title=title,
                             hover_data=df.columns, # Show all columns on hover
                             trendline="ols" if group_col is None else None, # Add trendline if no grouping
                             trendline_scope="overall" if group_col is None else None
                            )
            fig.update_layout(transition_duration=300) # Smooth transitions
            print("Plotly relationship plot updated.")
            return fig

        except Exception as e:
            print(f"Error generating Plotly relationship plot: {e}")
            # Return a figure indicating the error
            return px.scatter(title=f"Error: {e}")


    # Callback to update the Static (Seaborn) relationship plot image
    # *** THIS CALLBACK IS NOW CORRECTLY INDENTED INSIDE register_callbacks ***
    @app.callback(
        Output('relationship-static-img', 'src'),
        [Input('stored-data', 'data'),
         Input('rel-xaxis-dropdown', 'value'),
         Input('rel-yaxis-dropdown', 'value'),
         Input('rel-grouping-dropdown', 'value'),
         Input('rel-plot-type-radio', 'value')] # Need to know if static is selected
    )
    def update_static_relationship_plot(stored_data_json, x_col, y_col, group_col, plot_type):
        # Guard clause: Only proceed if static mode, data exists, and axes are selected
        if plot_type != 'static' or not stored_data_json or not x_col or not y_col:
            # Return transparent pixel placeholder
            return "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

        fig_static = None # Initialize fig_static
        try:
            print("Updating Static relationship plot...")
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')

            # Create Matplotlib figure and axes
            fig_static, ax = plt.subplots(figsize=(8, 6), tight_layout=True)

            # Generate Seaborn scatter plot
            sns.scatterplot(data=df, x=x_col, y=y_col, hue=group_col, ax=ax, s=50, alpha=0.7)

            # Add title and grid
            title = f"Static Relationship: {x_col} vs {y_col}" + (f" by {group_col}" if group_col else "")
            ax.set_title(title)
            ax.grid(True, linestyle='--', alpha=0.6)

            # Save plot to buffer
            buf = BytesIO()
            fig_static.savefig(buf, format="png")
            buf.seek(0) # Rewind buffer
            data = base64.b64encode(buf.getvalue()).decode("utf8")

            print("Static relationship plot updated.")
            # Return the base64 encoded image string
            return f"data:image/png;base64,{data}"

        except Exception as e:
            print(f"Error generating static relationship plot: {e}")
            error_message = f"Error: {e}"
            # Return an SVG error placeholder
            return f"data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='100'%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='10px' fill='red'%3E{error_message}%3C/text%3E%3C/svg%3E"
        finally:
             # Ensure Matplotlib figure is closed to prevent memory leaks
            if fig_static:
                plt.close(fig_static)

# --- End of Callback Registration ---

# NOTE: No 'if __name__ == "__main__":' block here