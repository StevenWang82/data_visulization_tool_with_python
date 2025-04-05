import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
import io
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

# Configure Matplotlib to use 'Agg' backend
import matplotlib
matplotlib.use('Agg')

# Import the main app instance
from app import app

# --- Layout for Relationship Plot Page ---
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
        html.Label("Select Grouping Variable (Optional, Categorical, <20 unique values):"),
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

# --- Callbacks for Relationship Plot Page ---

# Callback to toggle visibility
@app.callback(
    [Output('relationship-plotly-graph', 'style'),
     Output('relationship-static-img', 'style')],
    [Input('rel-plot-type-radio', 'value')]
)
def toggle_relationship_view(view_mode):
    if view_mode == 'dynamic':
        return {'display': 'block'}, {'display': 'none'}
    else: # static
        return {'display': 'none'}, {'display': 'block', 'maxWidth': '100%'}

# Callback to populate dropdowns
@app.callback(
    [Output('rel-xaxis-dropdown', 'options'),
     Output('rel-yaxis-dropdown', 'options'),
     Output('rel-grouping-dropdown', 'options'),
     Output('rel-xaxis-dropdown', 'value'),
     Output('rel-yaxis-dropdown', 'value'),
     Output('rel-grouping-dropdown', 'value')],
    [Input('stored-data', 'data'),
     Input('rel-plot-type-radio', 'value')] # Trigger update on view mode change
)
def update_relationship_dropdowns(stored_data_json, plot_type):
    if stored_data_json is None:
        return [], [], [], None, None, None

    df = pd.read_json(io.StringIO(stored_data_json), orient='split')
    numeric_cols = df.select_dtypes(include=['number']).columns
    # Filter categorical columns for grouping based on unique value count
    potential_grouping_cols = df.select_dtypes(include=['object', 'category']).columns
    valid_grouping_cols = [col for col in potential_grouping_cols if df[col].nunique() < 20]

    numerical_options = [{'label': col, 'value': col} for col in numeric_cols]
    grouping_options = [{'label': col, 'value': col} for col in valid_grouping_cols]

    # Default selections
    default_x = numeric_cols[0] if len(numeric_cols) > 0 else None
    default_y = numeric_cols[1] if len(numeric_cols) > 1 else None

    return numerical_options, numerical_options, grouping_options, default_x, default_y, None

# Callback to update the Plotly plot
@app.callback(
    Output('relationship-plotly-graph', 'figure'),
    [Input('stored-data', 'data'),
     Input('rel-xaxis-dropdown', 'value'),
     Input('rel-yaxis-dropdown', 'value'),
     Input('rel-grouping-dropdown', 'value'),
     Input('rel-plot-type-radio', 'value')] # Trigger on type change too
)
def update_plotly_relationship_plot(stored_data_json, x_col, y_col, group_col, plot_type):
    # Only update if dynamic mode is selected and data/axes are present
    if plot_type != 'dynamic' or stored_data_json is None or x_col is None or y_col is None:
        return px.scatter(title="Select Dynamic View and X/Y Axes")

    df = pd.read_json(io.StringIO(stored_data_json), orient='split')
    title = f"Relationship between {x_col} and {y_col}" + (f" grouped by {group_col}" if group_col else "")

    try:
        # Use Plotly Express scatter plot
        fig = px.scatter(df, x=x_col, y=y_col, color=group_col, title=title, hover_data=df.columns)
    except Exception as e:
        print(f"Error generating Plotly relationship plot: {e}")
        return px.scatter(title=f"Error generating plot: {e}")

    fig.update_layout(transition_duration=300)
    return fig


# Callback to update the Static plot image
@app.callback(
    Output('relationship-static-img', 'src'),
    [Input('stored-data', 'data'),
     Input('rel-xaxis-dropdown', 'value'),
     Input('rel-yaxis-dropdown', 'value'),
     Input('rel-grouping-dropdown', 'value'),
     Input('rel-plot-type-radio', 'value')] # Trigger on type change too
)
def update_static_relationship_plot(stored_data_json, x_col, y_col, group_col, plot_type):
    # Only update if static mode is selected and data/axes are present
    if plot_type != 'static' or stored_data_json is None or x_col is None or y_col is None:
        return "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" # Transparent pixel

    df = pd.read_json(io.StringIO(stored_data_json), orient='split')
    fig_static = None # Initialize

    try:
        # Create Matplotlib figure and axes
        fig_static, ax = plt.subplots(figsize=(8, 6), tight_layout=True) # Adjust size if needed

        # Use Seaborn scatterplot
        sns.scatterplot(data=df, x=x_col, y=y_col, hue=group_col, ax=ax, s=50, alpha=0.7) # Adjust size/alpha

        # Set title
        title = f"Static Relationship: {x_col} vs {y_col}" + (f" by {group_col}" if group_col else "")
        ax.set_title(title)
        ax.grid(True, linestyle='--', alpha=0.6) # Add grid

        # Save plot to buffer
        buf = BytesIO()
        fig_static.savefig(buf, format="png")
        buf.seek(0)
        data = base64.b64encode(buf.getvalue()).decode("utf8")
        plt.close(fig_static) # Close plot

        return f"data:image/png;base64,{data}"

    except Exception as e:
        print(f"Error generating static relationship plot: {e}")
        if fig_static:
             plt.close(fig_static)
        error_message = f"Error: {e}"
        return f"data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='100'%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='10px' fill='red'%3E{error_message}%3C/text%3E%3C/svg%3E"
