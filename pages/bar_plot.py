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

# --- Layout for Bar Plot Page ---
layout = html.Div([
    html.H2("Bar Plot"),
    html.P("Select variables to visualize their relationship using bars."),

    html.Div([
        html.Label("Select Categorical Variable (X-axis):"),
        dcc.Dropdown(id='bar-categorical-dropdown', placeholder="Select X-axis..."),
    ]),
    html.Div([
        html.Label("Select Numerical Variable (Y-axis):"),
        dcc.Dropdown(id='bar-numerical-dropdown', placeholder="Select Y-axis..."),
    ]),
    html.Div([
        html.Label("Select Grouping Variable (Optional, for Stacked/Grouped):"),
        dcc.Dropdown(id='bar-grouping-dropdown', placeholder="Select grouping variable..."),
    ]),
    html.Div([
        html.Label("Select Bar Mode:"),
        dcc.RadioItems(
            id='bar-mode-radio',
            options=[
                {'label': 'Grouped', 'value': 'group'},
                {'label': 'Stacked', 'value': 'stack'},
                {'label': 'Basic (No Grouping)', 'value': 'basic'},
            ],
            value='basic',
            labelStyle={'display': 'inline-block', 'margin-right': '10px'}
        ),
    ]),
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

# --- Callbacks for Bar Plot Page ---

# Callback to toggle visibility
@app.callback(
    [Output('bar-plotly-graph', 'style'),
     Output('bar-static-img', 'style'),
     Output('bar-mode-radio', 'style')], # Also control visibility of bar mode options
    [Input('bar-plot-type-radio', 'value')]
)
def toggle_bar_view(view_mode):
    # Hide bar mode options for static plot as Seaborn handles grouping differently
    bar_mode_style = {'display': 'block'} if view_mode == 'dynamic' else {'display': 'none'}
    if view_mode == 'dynamic':
        return {'display': 'block'}, {'display': 'none'}, bar_mode_style
    else: # static
        return {'display': 'none'}, {'display': 'block', 'maxWidth': '100%'}, bar_mode_style

# Callback to populate dropdowns
@app.callback(
    [Output('bar-categorical-dropdown', 'options'),
     Output('bar-numerical-dropdown', 'options'),
     Output('bar-grouping-dropdown', 'options'),
     Output('bar-categorical-dropdown', 'value'),
     Output('bar-numerical-dropdown', 'value'),
     Output('bar-grouping-dropdown', 'value')],
    [Input('stored-data', 'data'), # Input from store
     Input('bar-plot-type-radio', 'value')] # Added to trigger on view mode change
)
def update_bar_dropdowns(stored_data_json, plot_type): # Added plot_type argument
    if stored_data_json is None:
        return [], [], [], None, None, None

    df = pd.read_json(io.StringIO(stored_data_json), orient='split')
    numeric_cols = df.select_dtypes(include=['number']).columns
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns

    numerical_options = [{'label': col, 'value': col} for col in numeric_cols]
    categorical_options = [{'label': col, 'value': col} for col in categorical_cols]

    # Default selections
    default_cat = categorical_cols[0] if len(categorical_cols) > 0 else None
    default_num = numeric_cols[0] if len(numeric_cols) > 0 else None

    return categorical_options, numerical_options, categorical_options, default_cat, default_num, None

# Callback to update the Plotly plot
@app.callback(
    Output('bar-plotly-graph', 'figure'),
    [Input('stored-data', 'data'),
     Input('bar-categorical-dropdown', 'value'),
     Input('bar-numerical-dropdown', 'value'),
     Input('bar-grouping-dropdown', 'value'),
     Input('bar-mode-radio', 'value'),
     Input('bar-plot-type-radio', 'value')] # Trigger on type change
)
def update_plotly_bar_plot(stored_data_json, x_col, y_col, group_col, bar_mode, plot_type):
    # Only update if dynamic mode is selected and data/axes are present
    if plot_type != 'dynamic' or stored_data_json is None or x_col is None or y_col is None:
        return px.bar(title="Select Dynamic View and X/Y Axes")

    df = pd.read_json(io.StringIO(stored_data_json), orient='split')

    # Determine barmode for Plotly based on radio selection and grouping
    plotly_barmode = None
    actual_group_col = None # Grouping only applies if selected and mode is not basic
    if bar_mode != 'basic' and group_col:
        actual_group_col = group_col
        if bar_mode == 'group':
            plotly_barmode = 'group'
        elif bar_mode == 'stack':
            plotly_barmode = 'stack'

    title = f"Bar plot of {y_col} by {x_col}" + (f" grouped by {actual_group_col}" if actual_group_col else "")

    try:
        fig = px.bar(df, x=x_col, y=y_col, color=actual_group_col, barmode=plotly_barmode,
                     title=title, hover_data=df.columns)
    except Exception as e:
        print(f"Error generating Plotly bar plot: {e}")
        return px.bar(title=f"Error generating plot: {e}")

    fig.update_layout(transition_duration=300)
    return fig


# Callback to update the Static plot image
@app.callback(
    Output('bar-static-img', 'src'),
    [Input('stored-data', 'data'),
     Input('bar-categorical-dropdown', 'value'),
     Input('bar-numerical-dropdown', 'value'),
     Input('bar-grouping-dropdown', 'value'),
     # Note: bar_mode is not directly used by Seaborn barplot's basic call,
     # grouping/stacking is handled by the 'hue' parameter.
     Input('bar-plot-type-radio', 'value')] # Trigger on type change
)
def update_static_bar_plot(stored_data_json, x_col, y_col, group_col, plot_type):
     # Only update if static mode is selected and data/axes are present
    if plot_type != 'static' or stored_data_json is None or x_col is None or y_col is None:
        return "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" # Transparent pixel

    df = pd.read_json(io.StringIO(stored_data_json), orient='split')
    fig_static = None # Initialize

    try:
        # Create Matplotlib figure and axes
        fig_static, ax = plt.subplots(figsize=(10, 6), tight_layout=True) # Adjust size

        # Use Seaborn barplot
        # Seaborn's barplot typically shows mean for numerical data per category,
        # might need aggregation beforehand if you want sums or counts.
        # Assuming you want the mean (default behavior of sns.barplot)
        sns.barplot(data=df, x=x_col, y=y_col, hue=group_col, ax=ax, errorbar=None) # Use errorbar=None to hide confidence intervals if desired

        # Set title and labels
        title = f"Static Bar plot of {y_col} by {x_col}" + (f" grouped by {group_col}" if group_col else "")
        ax.set_title(title)
        ax.tick_params(axis='x', rotation=45) # Rotate x-axis labels if they overlap
        ax.grid(axis='y', linestyle='--', alpha=0.7) # Add horizontal grid lines

        # Save plot to buffer
        buf = BytesIO()
        fig_static.savefig(buf, format="png")
        buf.seek(0)
        data = base64.b64encode(buf.getvalue()).decode("utf8")
        plt.close(fig_static) # Close plot

        return f"data:image/png;base64,{data}"

    except Exception as e:
        print(f"Error generating static bar plot: {e}")
        if fig_static:
             plt.close(fig_static)
        error_message = f"Error: {e}"
        return f"data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='100'%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='10px' fill='red'%3E{error_message}%3C/text%3E%3C/svg%3E"
