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

# --- Layout for Heatmap Page ---
layout = html.Div([
    html.H2("Heatmap"),
    html.P("Visualize data matrix as a heatmap."),

    # Add controls for selecting data/columns for the heatmap later
    html.Div([
        html.Label("Select Numerical Columns for Heatmap:"),
        dcc.Dropdown(id='heatmap-columns-dropdown', placeholder="Select columns...", multi=True),
    ]),
     html.Div([
        html.Label("Select Plot Type:"),
        dcc.RadioItems(
            id='heatmap-plot-type-radio',
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
        dcc.Graph(id='heatmap-plotly-graph', style={'display': 'block'}),
        html.Img(id='heatmap-static-img', style={'display': 'none', 'maxWidth': '100%'})
    ])
])

# --- Callbacks for Heatmap Page ---

# Callback to toggle visibility
@app.callback(
    [Output('heatmap-plotly-graph', 'style'),
     Output('heatmap-static-img', 'style')],
    [Input('heatmap-plot-type-radio', 'value')]
)
def toggle_heatmap_view(view_mode):
    if view_mode == 'dynamic':
        return {'display': 'block'}, {'display': 'none'}
    else: # static
        return {'display': 'none'}, {'display': 'block', 'maxWidth': '100%'}

# Callback to populate dropdown
@app.callback(
    [Output('heatmap-columns-dropdown', 'options'),
     Output('heatmap-columns-dropdown', 'value')],
    [Input('stored-data', 'data'),
     Input('heatmap-plot-type-radio', 'value')] # Trigger update on view mode change
)
def update_heatmap_dropdown(stored_data_json, plot_type):
    if stored_data_json is None:
        return [], None

    df = pd.read_json(io.StringIO(stored_data_json), orient='split')
    numeric_cols = df.select_dtypes(include=['number']).columns
    options = [{'label': col, 'value': col} for col in numeric_cols]

    # Default to selecting all numeric columns initially, or a subset if too many
    default_value = numeric_cols.tolist()
    # Limit default selection if needed, e.g., max 10 columns
    # if len(default_value) > 10:
    #     default_value = default_value[:10]

    return options, default_value

# Callback to update the Plotly plot
@app.callback(
    Output('heatmap-plotly-graph', 'figure'),
    [Input('stored-data', 'data'),
     Input('heatmap-columns-dropdown', 'value'),
     Input('heatmap-plot-type-radio', 'value')] # Trigger on type change
)
def update_plotly_heatmap(stored_data_json, selected_columns, plot_type):
    # Only update if dynamic mode is selected and data/columns are present
    if plot_type != 'dynamic' or stored_data_json is None or not selected_columns:
        return px.imshow([[]], title="Select Dynamic View and Numerical Columns")

    df = pd.read_json(io.StringIO(stored_data_json), orient='split')

    try:
        numeric_df = df[selected_columns].select_dtypes(include=['number'])
        if numeric_df.empty or len(numeric_df.columns) < 2: # Need at least 2 columns for correlation
             return px.imshow([[]], title="Select at least 2 valid numerical columns.")

        corr_matrix = numeric_df.corr()

        # Use Plotly's imshow for heatmaps
        fig = px.imshow(corr_matrix, text_auto='.2f', aspect="auto", # Format text to 2 decimal places
                        title=f"Correlation Heatmap", color_continuous_scale='viridis') # Use a specific colorscale
        fig.update_xaxes(side="bottom")
        fig.update_layout(transition_duration=300)

    except Exception as e:
        print(f"Error generating Plotly heatmap: {e}")
        return px.imshow([[]], title=f"Error generating plot: {e}")

    return fig


# Callback to update the Static plot image
@app.callback(
    Output('heatmap-static-img', 'src'),
    [Input('stored-data', 'data'),
     Input('heatmap-columns-dropdown', 'value'),
     Input('heatmap-plot-type-radio', 'value')] # Trigger on type change
)
def update_static_heatmap(stored_data_json, selected_columns, plot_type):
    # Only update if static mode is selected and data/columns are present
    if plot_type != 'static' or stored_data_json is None or not selected_columns:
        return "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" # Transparent pixel

    df = pd.read_json(io.StringIO(stored_data_json), orient='split')
    fig_static = None # Initialize

    try:
        numeric_df = df[selected_columns].select_dtypes(include=['number'])
        if numeric_df.empty or len(numeric_df.columns) < 2:
            # Return placeholder if not enough columns
            return f"data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='100'%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='10px' fill='orange'%3ESelect at least 2 numerical columns%3C/text%3E%3C/svg%3E"

        corr_matrix = numeric_df.corr()

        # Create Matplotlib figure and axes
        fig_static, ax = plt.subplots(figsize=(8, 7), tight_layout=True) # Adjust size

        # Use Seaborn heatmap
        sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap='viridis', linewidths=.5, ax=ax) # Add annotations, formatting, cmap

        # Set title
        ax.set_title("Static Correlation Heatmap")
        plt.xticks(rotation=45, ha='right') # Rotate x-axis labels for better readability
        plt.yticks(rotation=0)

        # Save plot to buffer
        buf = BytesIO()
        fig_static.savefig(buf, format="png")
        buf.seek(0)
        data = base64.b64encode(buf.getvalue()).decode("utf8")
        plt.close(fig_static) # Close plot

        return f"data:image/png;base64,{data}"

    except Exception as e:
        print(f"Error generating static heatmap: {e}")
        if fig_static:
             plt.close(fig_static)
        error_message = f"Error: {e}"
        return f"data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='100'%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='10px' fill='red'%3E{error_message}%3C/text%3E%3C/svg%3E"
