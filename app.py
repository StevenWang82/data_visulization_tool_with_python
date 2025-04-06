import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output

from pages import data_upload, distribution, relationship, bar_plot, heatmap # Import all page modules

# Initialize the Dash app with Bootstrap theme
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server # Expose server variable for deployment

# Define the navigation bar using Bootstrap components for better styling potential
# Using dbc.Nav for better Bootstrap integration
navbar = dbc.Nav(
    [
        dbc.NavItem(dbc.NavLink('資料上傳 (data loading)', href='/', active="exact")),
        dbc.NavItem(dbc.NavLink('分布圖 (distribution plot)', href='/distribution', active="exact")),
        dbc.NavItem(dbc.NavLink('關聯分析 (relationships)', href='/relationship', active="exact")),
        dbc.NavItem(dbc.NavLink('長條圖 (bar plot)', href='/bar', active="exact")),
        dbc.NavItem(dbc.NavLink('熱力圖 (Heatmap)', href='/heatmap', active="exact")),
    ],
    pills=True, # Use pills style for navigation
    className="mb-3", # Add margin bottom
)

# Main application layout using a function and Bootstrap container
def serve_layout():
    return dbc.Container([ # Use Bootstrap container for layout
        dcc.Location(id='url', refresh=False), # Component to track URL changes
        dcc.Store(id='stored-data'), # Store component to hold data across pages
        html.H1("資料視覺化工具(Data Visualization Tool)", className="my-4"), # Add margin with Bootstrap class
        navbar,
        html.Div(id='page-content') # Content will be loaded here based on URL
    ], fluid=True) # Use fluid container to take full width

app.layout = serve_layout # Assign the layout function

# Register callbacks from data_upload page ONCE after app initialization
# This assumes data_upload.py has a function register_callbacks(app)
# Make sure data_upload.py doesn't import 'app' directly at the top level
# causing circular imports. If it does, you might need a different pattern
# Register callbacks from imported page modules
# This pattern assumes each page module has a 'register_callbacks(app)' function
# if it defines callbacks that need the app instance.
# If a page only has layout and no callbacks needing 'app', it doesn't need this.
for page_module in [data_upload, distribution, relationship, bar_plot, heatmap]: # Register all imported modules
    try:
        page_module.register_callbacks(app)
        print(f"Successfully registered callbacks from {page_module.__name__}.")
    except AttributeError:
        print(f"Warning: 'register_callbacks' function not found in {page_module.__name__}.")
    except Exception as e:
        print(f"Error registering callbacks for {page_module.__name__}: {e}")


# Callback to render page content based on URL
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    # Return layout based on pathname from pre-imported modules
    if pathname == '/distribution':
        return distribution.layout
    elif pathname == '/relationship':
        return relationship.layout
    elif pathname == '/bar':
        return bar_plot.layout
    elif pathname == '/heatmap':
        return heatmap.layout
    elif pathname == '/' or pathname == '/data_upload': # Handle root and explicit path
        return data_upload.layout
    else:
        return html.Div("404 Page not found")
    # Removed dynamic imports from display_page


if __name__ == '__main__':
    # Note: debug=True should be False in production
    app.run(debug=True)