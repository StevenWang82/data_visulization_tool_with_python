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

# Configure Matplotlib to use 'Agg' backend for non-interactive plotting in server environment
import matplotlib
matplotlib.use('Agg')

# Import the main app instance
from app import app

# --- Layout for Distribution Plot Page ---
layout = html.Div([
    html.H2("Distribution Plot"),
    html.P("Select variables to visualize their distribution."),

    # Add controls for selecting variables and plot type (dynamic/static) later
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
            value='histogram', # Default Plotly type
            clearable=False
        ),
    ], id='plotly-type-div'), # Add ID to control visibility later if needed
    html.Div([
        html.Label("Select View Mode:"), # Renamed Label
        dcc.RadioItems(
            id='dist-view-mode-radio', # Renamed ID
            options=[
                {'label': 'Dynamic (Plotly)', 'value': 'dynamic'},
                {'label': 'Static (Seaborn)', 'value': 'static'},
            ],
            value='dynamic', # Default to dynamic view
            labelStyle={'display': 'inline-block', 'margin-right': '10px'}
        ),
    ]),

    # Div to hold the plots - visibility controlled by callback
    html.Div([
        # Plotly Graph (initially visible)
        dcc.Graph(id='distribution-plotly-graph', style={'display': 'block'}),
        # Static Image Placeholder (initially hidden)
        html.Img(id='distribution-static-img', style={'display': 'none', 'maxWidth': '100%'})
    ])
])

# --- Callbacks for Distribution Plot Page ---

# Callback to control visibility of Plotly graph vs Static image
@app.callback(
    [Output('distribution-plotly-graph', 'style'),
     Output('distribution-static-img', 'style'),
     Output('plotly-type-div', 'style')], # Control visibility of Plotly type dropdown
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
     Input('dist-plotly-type-dropdown', 'value'), # Use selected Plotly type
     Input('dist-view-mode-radio', 'value')] # Trigger only if dynamic is selected
)
def update_plotly_distribution_plot(stored_data_json, numerical_col, grouping_col, plotly_type, view_mode):
    # Only update Plotly fig if dynamic mode is active
    if view_mode != 'dynamic' or stored_data_json is None or numerical_col is None:
        # Return an empty figure or prevent update if not dynamic or data missing
        return px.scatter(title="Select Dynamic View and Numerical Variable")

    df = pd.read_json(io.StringIO(stored_data_json), orient='split')
    title = f"{plotly_type.capitalize()} plot of {numerical_col}" + (f" grouped by {grouping_col}" if grouping_col else "")

    try:
        if plotly_type == 'histogram':
            # Use marginal='rug' to show individual data points along the axis
            fig = px.histogram(df, x=numerical_col, color=grouping_col, title=title, marginal="rug", hover_data=df.columns)
        elif plotly_type == 'box':
            # Use points='all' to show underlying data points
            fig = px.box(df, x=grouping_col, y=numerical_col, color=grouping_col, title=title, points="all")
        elif plotly_type == 'violin':
            # Use box=True and points='all' for more detail
            fig = px.violin(df, x=grouping_col, y=numerical_col, color=grouping_col, title=title, box=True, points="all")
        else:
            # Default case or handle unknown type
            fig = px.histogram(df, x=numerical_col, color=grouping_col, title=f"Unknown type: {plotly_type}, showing Histogram")
    except Exception as e:
        print(f"Error generating Plotly distribution plot: {e}")
        return px.scatter(title=f"Error generating plot: {e}")

    fig.update_layout(transition_duration=300) # Smooth transition
    return fig


# Callback to update the Static plot image (Placeholder for now)
@app.callback(
    Output('distribution-static-img', 'src'),
    [Input('stored-data', 'data'),
     Input('dist-numerical-dropdown', 'value'),
     Input('dist-grouping-dropdown', 'value'),
     Input('dist-view-mode-radio', 'value')] # Trigger only if static is selected
)
def update_static_distribution_plot(stored_data_json, numerical_col, grouping_col, view_mode):
     # Only update static fig if static mode is active
    if view_mode != 'static' or stored_data_json is None or numerical_col is None:
        # Return a transparent pixel as a placeholder or prevent update
        return "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" # Return transparent pixel if not static mode or no data

    # --- Static Plot Generation (Seaborn/Matplotlib) ---
    df = pd.read_json(io.StringIO(stored_data_json), orient='split')
    fig_static = None # Initialize fig_static to ensure it's defined for plt.close()

    try:
        # Create Matplotlib figure and axes
        # Use tight_layout=True for better spacing
        fig_static, ax = plt.subplots(figsize=(8, 5), tight_layout=True)

        # Use Seaborn histplot (can also use displot with kind='hist')
        sns.histplot(data=df, x=numerical_col, hue=grouping_col, kde=True, ax=ax) # Add KDE curve

        # Set title
        title = f"Static Distribution of {numerical_col}" + (f" by {grouping_col}" if grouping_col else "")
        ax.set_title(title)

        # Save plot to a BytesIO buffer
        buf = BytesIO()
        fig_static.savefig(buf, format="png") # Save as PNG
        buf.seek(0) # Rewind buffer to the beginning

        # Encode buffer to base64
        data = base64.b64encode(buf.getvalue()).decode("utf8")

        # Close the Matplotlib figure to free memory
        plt.close(fig_static)

        # Return the base64 encoded image as a data URI
        return f"data:image/png;base64,{data}"

    except Exception as e:
        print(f"Error generating static distribution plot: {e}")
        if fig_static: # Ensure figure exists before trying to close
             plt.close(fig_static)
        # Return placeholder or error image data URI
        error_message = f"Error: {e}"
        # Simple SVG placeholder for error
        return f"data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='100'%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='10px' fill='red'%3E{error_message}%3C/text%3E%3C/svg%3E"


# Callback to populate dropdowns based on stored data (remains the same)
@app.callback(
    [Output('dist-numerical-dropdown', 'options'),
     Output('dist-grouping-dropdown', 'options'),
     Output('dist-numerical-dropdown', 'value'), # Reset value on new data
     Output('dist-grouping-dropdown', 'value')], # Reset value on new data
    [Input('stored-data', 'data'),
     Input('dist-view-mode-radio', 'value')] # Trigger update on view mode change
)
def update_distribution_dropdowns(stored_data_json, view_mode):
    if stored_data_json is None:
        return [], [], None, None

    df = pd.read_json(io.StringIO(stored_data_json), orient='split')
    numeric_cols = df.select_dtypes(include=['number']).columns
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns # Include category type

    numerical_options = [{'label': col, 'value': col} for col in numeric_cols]
    grouping_options = [{'label': col, 'value': col} for col in categorical_cols]

    # Try to set a default numerical value if available
    default_numerical = numeric_cols[0] if len(numeric_cols) > 0 else None

    return numerical_options, grouping_options, default_numerical, None
