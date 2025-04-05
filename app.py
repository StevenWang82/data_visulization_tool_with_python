import dash
from dash import dcc, html, Input, Output
# DO NOT import page modules here directly if they import 'app' - causes circular import
# Instead, import them when needed or structure differently if possible.
# However, for registering callbacks, we might need to import the registration function.
from pages import data_upload # Assuming register_callbacks is in data_upload

# Initialize the Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server # Expose server variable for deployment

# Define the navigation bar
navbar = html.Nav([
    # Add '/' as the base path for Data Upload if it's the default landing page
    dcc.Link('Data Upload', href='/'),
    html.Span(" | ", style={'padding': '0 10px'}),
    dcc.Link('Distribution Plot', href='/distribution'),
    html.Span(" | ", style={'padding': '0 10px'}),
    dcc.Link('Relationship Plot', href='/relationship'),
    html.Span(" | ", style={'padding': '0 10px'}),
    dcc.Link('Bar Plot', href='/bar'),
    html.Span(" | ", style={'padding': '0 10px'}),
    dcc.Link('Heatmap', href='/heatmap'),
], style={'marginBottom': '20px', 'padding': '10px', 'borderBottom': '1px solid #ccc'})

# Main application layout using a function to avoid potential direct layout assignment issues
def serve_layout():
    return html.Div([
        dcc.Location(id='url', refresh=False), # Component to track URL changes
        dcc.Store(id='stored-data'), # Store component to hold data across pages
        html.H1("Multi-Page Data Visualization Tool"),
        navbar,
        html.Div(id='page-content') # Content will be loaded here based on URL
    ])

app.layout = serve_layout # Assign the layout function

# Register callbacks from data_upload page ONCE after app initialization
# This assumes data_upload.py has a function register_callbacks(app)
# Make sure data_upload.py doesn't import 'app' directly at the top level
# causing circular imports. If it does, you might need a different pattern
# (like explicitly importing callbacks or using a central callback manager).
try:
    # Assuming the register_callbacks function exists in pages.data_upload
    data_upload.register_callbacks(app)
    print("Successfully registered callbacks from data_upload.")
except AttributeError:
    print("Warning: 'register_callbacks' function not found in pages.data_upload.")
except ImportError:
    print("Warning: Could not import pages.data_upload to register callbacks.")


# Callback to render page content based on URL
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    # Import layouts dynamically INSIDE the callback
    # Ensure these page modules DO NOT try to import the 'app' instance directly
    # at the top level, pass 'app' to them if needed via functions.
    try:
        if pathname == '/distribution':
            from pages import distribution
            # Assuming distribution page also has callbacks, register them similarly
            # distribution.register_callbacks(app) # Add if needed
            return distribution.layout
        elif pathname == '/relationship':
            from pages import relationship
            # relationship.register_callbacks(app) # Add if needed
            return relationship.layout
        elif pathname == '/bar':
            from pages import bar_plot
            # bar_plot.register_callbacks(app) # Add if needed
            return bar_plot.layout
        elif pathname == '/heatmap':
            from pages import heatmap
            # heatmap.register_callbacks(app) # Add if needed
            return heatmap.layout
        elif pathname == '/' or pathname == '/data_upload': # Handle root and explicit path
            # No need to register callbacks here, done outside
            # We just need the layout from data_upload
            from pages import data_upload
            return data_upload.layout
        else:
            return html.Div("404 Page not found")
    except ImportError as e:
        print(f"Error importing page module for {pathname}: {e}")
        return html.Div(f"Error loading page {pathname}. Check imports.")
    except Exception as e:
        print(f"An unexpected error occurred rendering page {pathname}: {e}")
        return html.Div(f"An error occurred while loading the page.")


if __name__ == '__main__':
    # Note: debug=True should be False in production
    app.run(debug=True)