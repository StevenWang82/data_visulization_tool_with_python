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

# --- Layout for Heatmap Page (Stays at top level) ---
layout = html.Div([
    html.H2("Correlation Heatmap"), # Title clarifies it's a correlation heatmap
    html.P("Visualize the correlation matrix of selected numerical columns."),

    html.Div([
        html.Label("Select Numerical Columns for Heatmap (at least 2):"),
        # Enable multi-select for columns
        dcc.Dropdown(id='heatmap-columns-dropdown',
                     placeholder="Select numerical columns...",
                     multi=True),
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
        # Plotly graph for dynamic view
        dcc.Graph(id='heatmap-plotly-graph', style={'display': 'block'}),
        # Image placeholder for static view
        html.Img(id='heatmap-static-img', style={'display': 'none', 'maxWidth': '100%'})
    ])
])

# --- Callback Registration Function ---
# ALL callbacks defined INSIDE this function
def register_callbacks(app):

    # Callback to toggle visibility based on selected plot type
    @app.callback(
        [Output('heatmap-plotly-graph', 'style'),
         Output('heatmap-static-img', 'style')],
        [Input('heatmap-plot-type-radio', 'value')]
    )
    def toggle_heatmap_view(view_mode):
        if view_mode == 'dynamic':
            # Show Plotly, hide Static
            return {'display': 'block'}, {'display': 'none'}
        else: # static
            # Hide Plotly, show Static
            return {'display': 'none'}, {'display': 'block', 'maxWidth': '100%'}

    # Callback to populate the column selection dropdown
    @app.callback(
        [Output('heatmap-columns-dropdown', 'options'),
         Output('heatmap-columns-dropdown', 'value')],
        [Input('stored-data', 'data')] # Trigger only when data changes
    )
    def update_heatmap_dropdown(stored_data_json):
        # Define default return values
        default_return = ([], []) # Empty options, empty value list

        if not stored_data_json:
            print("update_heatmap_dropdown: No stored data.")
            return default_return

        try:
            print("update_heatmap_dropdown: Reading stored data.")
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')

            if df.empty:
                print("update_heatmap_dropdown: DataFrame empty.")
                return default_return

            # Select only numerical columns
            numeric_cols = df.select_dtypes(include=np.number).columns

            if numeric_cols.empty:
                 print("update_heatmap_dropdown: No numeric columns found.")
                 return default_return

            # Create options for dropdown
            options = [{'label': f"{col} (numeric)", 'value': col} for col in numeric_cols]

            # Default value: select all numeric columns initially
            default_value = numeric_cols.tolist()
            # Optional: Limit the number of initially selected columns for performance/readability
            # max_default_cols = 10
            # if len(default_value) > max_default_cols:
            #     print(f"Limiting default selection to first {max_default_cols} numeric columns.")
            #     default_value = default_value[:max_default_cols]

            print("update_heatmap_dropdown: Success.")
            return options, default_value

        except Exception as e:
            print(f"Error updating heatmap dropdown: {e}")
            return default_return # Return default structure on error

    # Callback to update the Plotly heatmap
    # *** CORRECTLY INDENTED INSIDE register_callbacks ***
    @app.callback(
        Output('heatmap-plotly-graph', 'figure'),
        [Input('stored-data', 'data'),
         Input('heatmap-columns-dropdown', 'value'), # Selected columns
         Input('heatmap-plot-type-radio', 'value')]  # Is dynamic view selected?
    )
    def update_plotly_heatmap(stored_data_json, selected_columns, plot_type):
        # Guard Clause: Check prerequisites
        # Need dynamic mode, data, and at least 2 selected columns
        if plot_type != 'dynamic' or not stored_data_json or not selected_columns or len(selected_columns) < 2:
            print("Plotly Heatmap: Prerequisites not met.")
            # Return an empty figure matching Output type
            return px.imshow([[]], title="Select Dynamic View & at least 2 numerical columns")

        try:
            print("Updating Plotly heatmap...")
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')

            # Ensure selected columns actually exist and are numeric (robustness)
            valid_numeric_cols = [col for col in selected_columns if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
            if len(valid_numeric_cols) < 2:
                 print("Plotly Heatmap: Not enough valid numeric columns selected.")
                 return px.imshow([[]], title="Select at least 2 valid numerical columns")

            numeric_df = df[valid_numeric_cols]
            corr_matrix = numeric_df.corr() # Calculate correlation matrix

            # Generate Plotly heatmap using imshow
            fig = px.imshow(corr_matrix,
                            text_auto='.2f', # Display correlation values formatted to 2 decimals
                            aspect="auto",   # Adjust aspect ratio automatically
                            labels=dict(color="Correlation"), # Label for the color bar
                            title=f"Correlation Heatmap",
                            color_continuous_scale=px.colors.sequential.Viridis) # Use a nice colorscale

            fig.update_xaxes(side="bottom") # Move x-axis labels to bottom for clarity
            fig.update_layout(transition_duration=300)
            print("Plotly heatmap updated.")
            return fig

        except Exception as e:
            print(f"Error generating Plotly heatmap: {e}")
            # Return a figure indicating the error
            return px.imshow([[]], title=f"Error: {e}")

    # Callback to update the Static (Seaborn) heatmap image
    # *** CORRECTLY INDENTED INSIDE register_callbacks ***
    @app.callback(
        Output('heatmap-static-img', 'src'),
        [Input('stored-data', 'data'),
         Input('heatmap-columns-dropdown', 'value'), # Selected columns
         Input('heatmap-plot-type-radio', 'value')]  # Is static view selected?
    )
    def update_static_heatmap(stored_data_json, selected_columns, plot_type):
        # Guard Clause: Check prerequisites
        # Need static mode, data, and at least 2 selected columns
        if plot_type != 'static' or not stored_data_json or not selected_columns or len(selected_columns) < 2:
            print("Static Heatmap: Prerequisites not met.")
            # Return transparent pixel placeholder
            return "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

        fig_static = None # Initialize fig_static
        try:
            print("Updating Static heatmap...")
            df = pd.read_json(io.StringIO(stored_data_json), orient='split')

            # Ensure selected columns actually exist and are numeric
            valid_numeric_cols = [col for col in selected_columns if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
            if len(valid_numeric_cols) < 2:
                 print("Static Heatmap: Not enough valid numeric columns selected.")
                 # Return an SVG indicating the requirement
                 return f"data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='100'%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='10px' fill='orange'%3ESelect at least 2 valid numerical columns%3C/text%3E%3C/svg%3E"

            numeric_df = df[valid_numeric_cols]
            corr_matrix = numeric_df.corr() # Calculate correlation matrix

            # Create Matplotlib figure and axes
            # Adjust figsize based on number of columns for better readability
            num_cols = len(valid_numeric_cols)
            fig_width = max(8, num_cols * 0.8)
            fig_height = max(6, num_cols * 0.6)
            fig_static, ax = plt.subplots(figsize=(fig_width, fig_height), tight_layout=True)

            # Generate Seaborn heatmap
            sns.heatmap(corr_matrix,
                        annot=True,      # Show correlation values on the map
                        fmt=".2f",       # Format annotations to 2 decimal places
                        cmap='viridis',  # Use a perceptually uniform colormap
                        linewidths=.5,   # Add lines between cells
                        ax=ax)

            # Adjust plot aesthetics
            ax.set_title("Static Correlation Heatmap")
            plt.xticks(rotation=45, ha='right') # Rotate x-labels for readability
            plt.yticks(rotation=0)           # Keep y-labels horizontal

            # Save plot to buffer
            buf = BytesIO()
            fig_static.savefig(buf, format="png")
            buf.seek(0) # Rewind buffer
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