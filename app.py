import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# DO NOT import page modules here - causes circular import
# from pages import data_upload, distribution, relationship, bar_plot, heatmap

# Initialize the Dash app
# Use suppress_callback_exceptions=True because callbacks are defined in separate files
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server # Expose server variable for deployment

# Define the navigation bar
navbar = html.Nav([
    dcc.Link('Data Upload', href='/data_upload'),
    html.Span(" | ", style={'padding': '0 10px'}),
    dcc.Link('Distribution Plot', href='/distribution'),
    html.Span(" | ", style={'padding': '0 10px'}),
    dcc.Link('Relationship Plot', href='/relationship'),
    html.Span(" | ", style={'padding': '0 10px'}),
    dcc.Link('Bar Plot', href='/bar'),
    html.Span(" | ", style={'padding': '0 10px'}),
    dcc.Link('Heatmap', href='/heatmap'),
], style={'marginBottom': '20px', 'padding': '10px', 'borderBottom': '1px solid #ccc'})

# Main application layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False), # Component to track URL changes
    dcc.Store(id='stored-data'), # Store component to hold data across pages
    html.H1("Multi-Page Data Visualization Tool"),
    navbar,
    html.Div(id='page-content') # Content will be loaded here based on URL
])

# Assign the layout components to a variable first
main_layout_components = html.Div([
    dcc.Location(id='url', refresh=False), # Component to track URL changes
    dcc.Store(id='stored-data'), # Store component to hold data across pages
    html.H1("Multi-Page Data Visualization Tool"),
    navbar,
    html.Div(id='page-content') # Content will be loaded here based on URL
])

# Callback to render page content based on URL
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    # Import layouts dynamically INSIDE the callback
    if pathname == '/distribution':
        from pages import distribution
        return distribution.layout
    elif pathname == '/relationship':
        from pages import relationship
        return relationship.layout
    elif pathname == '/bar':
        from pages import bar_plot
        return bar_plot.layout
    elif pathname == '/heatmap':
        from pages import heatmap
        return heatmap.layout
    elif pathname == '/data_upload':
        from pages import data_upload
        page_layout = data_upload.layout # Get layout directly
        print(f"Data Upload page_layout type: {type(page_layout)}") # Add this print statement to check layout type
        data_upload.register_callbacks(app) # Register callbacks for data_upload page here
        return page_layout
    else: # Default to data upload page - now needs explicit path
        return html.Div("Page not found") # Or redirect to data_upload page

# Set the layout AFTER defining the display_page callback
app.layout = main_layout_components

if __name__ == '__main__':
    # Note: debug=True should be False in production
    app.run(debug=True)
