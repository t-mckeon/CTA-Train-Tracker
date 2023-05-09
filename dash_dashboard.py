
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import google.auth
from google.cloud import bigquery
import plotly.graph_objs as go
import plotly.express as px
import dash_table
from google.oauth2 import service_account
import geopandas as gpd
import json
import re
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/Thomas/Desktop/future-sonar-331521-1d79baf510a6.json'


external_stylesheets = ['https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, assets_folder='assets')
server = app.server


# Set up authentication for BigQuery
credentials = service_account.Credentials.from_service_account_file(
    '/Users/Thomas/Desktop/future-sonar-331521-1d79baf510a6.json',
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)
project_id = "future-sonar-331521"

client = bigquery.Client(credentials=credentials, project=project_id)

def hex_to_rgb(hex_color, lighten = 0):
    hex_color = re.search(r'^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$', hex_color, re.I)
    r, g, b = [(int(hex_color.group(i), 16) + (255 - int(hex_color.group(i), 16))*lighten) for i in (1, 2, 3)]
    return f"rgb({r}, {g}, {b})"

# Define the layout of the app
app.layout = html.Div([
    dcc.Interval(
        id='interval-component',
        interval=15 * 1000,  # in milliseconds
        n_intervals=0
    ),
    html.Div([
        html.Div([
            dcc.Graph(id='cta-map', style={'height': '800px'}),
        ], style={'flex': '3'}),
        html.Div([
            html.Label('Select Route:'),
            dcc.Dropdown(
                id='route-dropdown',
                options=[
                        {'label': 'Red Line', 'value': 'Red Line', 'style': {'backgroundColor': hex_to_rgb('#fb003d')}},
                        {'label': 'Blue Line', 'value': 'Blue Line', 'style': {'backgroundColor': hex_to_rgb('#00a8df')}},
                        {'label': 'Green Line', 'value': 'Green Line', 'style': {'backgroundColor': hex_to_rgb('#00a447')}},
                        {'label': 'Brown Line', 'value': 'Brown Line', 'style': {'backgroundColor': hex_to_rgb('#7b4213')}},
                        {'label': 'Orange Line', 'value': 'Orange Line', 'style': {'backgroundColor': hex_to_rgb('#fe9307')}},
                        {'label': 'Pink Line', 'value': 'Pink Line', 'style': {'backgroundColor': hex_to_rgb('#f68eb9')}},
                        {'label': 'Purple Line', 'value': 'Purple Line', 'style': {'backgroundColor': hex_to_rgb('#492f8a')}},
                        {'label': 'Yellow Line', 'value': 'Yellow Line', 'style': {'backgroundColor': hex_to_rgb('#f9ef00')}},
                    ],
                value='Red Line'),
            html.Div(id='table-div', style={'marginTop': 50}),
        ], style={'flex': '2', 'padding': '20px'}),
    ], style={'display': 'flex', 'padding': '0px'}),
])

# Set the title and icon of the web app
app.title = 'CTA Train Tracker'
app.icon = 'assets/favicon.ico'


# Define a function to get the train location data from BigQuery
def get_bq_data():
    client = bigquery.Client()
    query = """
        SELECT route, run_number, destination_station_name, latitude, longitude, next_station_name, timestamp, arrival_time, heading
        FROM `future-sonar-331521.cta_tracker.train_data`
    """
    query_job = client.query(query)
    results = query_job.result()
    train_data = []
    for row in results:
        train_data.append({
            'route': row['route'],
            'train_id': row['run_number'],
            'destination': row['destination_station_name'],
            'latitude': row['latitude'],
            'longitude': row['longitude'],
            'next_station_name': row['next_station_name'],
            'timestamp': row['timestamp'],
            'arrival_time': row['arrival_time'],
            'heading': row['heading']
        })
    return pd.DataFrame(train_data)


# Define a function to plot the train locations on the map
def plot_train_locations(zoom, lat, lon):
    train_df = get_bq_data()

    # Read in the CTA train lines GeoJSON file
    with open('CTA_RailLines.geojson', 'r') as f:
        cta_lines = json.load(f)

    # Create a mapbox plot of the CTA train lines
    line_color_map = {'Yellow Line': '#f9ef00',
     'Orange Line': '#fe9307',
     'Pink Line': '#f68eb9',
     'Brown Line': '#7b4213',
     'Green Line': '#00a447',
     'Red Line': '#fb003d',
     "Blue Line (O'Hare)": '#00a8df',
     "Blue Line (Forest Park)": '#00a8df',
     'Purple Line': '#492f8a',
     'Blue Line' : '#00a8df',
     'Brown, Orange, Pink, Purple (Express)': ['#7b4213', '#fe9307', '#ff85bc', '#492f8a'],
     'Brown, Purple': ['#7b4213', '#492f8a'],
     'Green, Orange': ['#00a447', '#fe9307'],
     'Brown, Green, Orange, Pink, Purple (Exp)': ['#7b4213', '#00a447', '#fe9307', '#f68eb9', '#492f8a'],
     'Red, Purple Line': ['#fb003d', '#492f8a'],
     'Brown, Purple (Express), Red':['#7b4213', '#492f8a', '#fa0034'], 
     'Green, Pink': ['#00a447', '#f68eb9']
    }

    line_color_scales = {}

    for line, color in line_color_map.items():
        if isinstance(color, list):
            line_color_scales[line] = color
        else:
            line_color_scales[line] = [color]

    line_traces = []

    for feature in cta_lines['features']:
        line = feature['properties']['Name']
        geo = feature['geometry']
        coords = geo['coordinates']
        line_colors = line_color_map[line]
        if isinstance(line_colors, str):
            # If line color is a string, create a single trace with the given color
            trace = go.Scattermapbox(
                lat=[c[1] for c in coords],
                lon=[c[0] for c in coords],
                mode='lines',
                line=dict(color=line_colors, width=3),
                hoverinfo='none'
            )
            line_traces.append(trace)
        elif isinstance(line_colors, list):
            # If line color is a list, create multiple traces with different colors
            n_colors = len(line_colors)
            for i in range(n_colors):
                trace = go.Scattermapbox(
                    lat=[c[1] + i*.00007 for c in coords],
                    lon=[c[0] + i*.00005 for c in coords],
                    mode= 'lines',
                    line=dict(color=line_colors[i], width=3),
                    hoverinfo='none'
                )
                line_traces.append(trace)

    
    train_df['min_to_arrival'] = ((train_df['arrival_time'] - train_df['timestamp']).dt.total_seconds() / 60).astype('int')
    train_df['hover_info'] = train_df['train_id'].astype('str') + ' Towards: ' + train_df['destination'].str.replace(' ', '-').astype('str') + '\n' + 'Arriving at ' + train_df['next_station_name'].str.replace(' ', '-').astype('str') + ' in ' + train_df['min_to_arrival'].astype('str') + ' min'
    train_df['route_color'] = train_df['route'].apply(lambda x: line_color_map[x])
    
    # Create a scatter mapbox plot of the train locations

    hover_template = '<b>{}</b><br>{}'.format(
        '%{text[0]} %{text[1]} %{text[2]}',
        '%{text[3]} %{text[4]} %{text[5]} %{text[6]} %{text[7]} %{text[8]}'
    )
    
    scatter_trace_outline = go.Scattermapbox(
        lat=train_df['latitude'],
        lon=train_df['longitude'],
        mode='markers',
        marker=dict(
        symbol='circle', 
        size = 11, 
        color = 'white'
)

    )
    scatter_trace = go.Scattermapbox(
        lat=train_df['latitude'],
        lon=train_df['longitude'],
        mode='markers',
        marker=dict(
        symbol='circle', 
        size = 10, 
        color = train_df['route_color']),
        text=train_df['hover_info'].apply(lambda x: x.split()),
        hovertemplate= hover_template,
        name=''

    )
    

        
    # Add the line and scatter traces to the figure
    fig = go.Figure(line_traces + [scatter_trace_outline] + [scatter_trace])
    
    fig.update_layout(
        mapbox=dict(
            style='carto-darkmatter',
            zoom=zoom,
            center=dict(lat=lat, lon= lon),
        ),
        height = 800, 
        width = 720,
        showlegend=False )
        
    return fig

def display_table(route):
    
    line_color_map = {'Yellow Line': '#f9ef00',
     'Orange Line': '#fe9307',
     'Pink Line': '#f68eb9',
     'Brown Line': '#7b4213',
     'Green Line': '#00a447',
     'Red Line': '#fb003d',
     "Blue Line (O'Hare)": '#00a8df',
     "Blue Line (Forest Park)": '#00a8df',
     'Purple Line': '#492f8a',
     'Blue Line' : '#00a8df',
     'Brown, Orange, Pink, Purple (Express)': ['#7b4213', '#fe9307', '#ff85bc', '#492f8a'],
     'Brown, Purple': ['#7b4213', '#492f8a'],
     'Green, Orange': ['#00a447', '#fe9307'],
     'Brown, Green, Orange, Pink, Purple (Exp)': ['#7b4213', '#00a447', '#fe9307', '#f68eb9', '#492f8a'],
     'Red, Purple Line': ['#fb003d', '#492f8a'],
     'Brown, Purple (Express), Red':['#7b4213', '#492f8a', '#fa0034'], 
     'Green, Pink': ['#00a447', '#f68eb9']
    }
    
    train_df = get_bq_data()
    
    train_df['min_to_arrival'] = ((train_df['arrival_time'] -train_df['timestamp']).dt.total_seconds() / 60).astype('int')
    train_df['hover_info'] = train_df['train_id'].astype('str') + ' Towards: ' + train_df['destination'].str.replace(' ', '-').astype('str') + '\n' + 'Arriving at ' + train_df['next_station_name'].str.replace(' ', '-').astype('str') + ' in ' + train_df['min_to_arrival'].astype('str') + ' min'
    train_df['route_color'] = train_df['route'].apply(lambda x: line_color_map[x])
    # Filter the train location data for the selected route
    route_df = train_df[train_df['route'] == route]
    
    table_color = hex_to_rgb(route_df.route_color.unique()[0])
    lighten_table_color = hex_to_rgb(route_df.route_color.unique()[0], lighten = .8)
    
    route_df = route_df[['train_id', 'destination', 'next_station_name', 'min_to_arrival']]
    route_df.columns = ['Train #', 'Destination', 'Nest Station', 'Arriving in:']
    # Create a Dash table component to display the data
    table = dash_table.DataTable(
        id='train-table',
        columns=[{"name": i, "id": i} for i in route_df.columns],
        data=route_df.to_dict('records'),
        page_size=20,
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(255, 255, 255)'
            },
            {
                'if': {'row_index': 'even'},
                'backgroundColor': lighten_table_color
            }
        ],
        style_header={
            'backgroundColor': table_color,
            'fontWeight': 'bold'
        },
        style_cell={
        'width': '200px',
        'textAlign': 'center',
        'whiteSpace': 'normal',
        'height': 'auto',
        'padding': '5px'
    }
    )
    return table

# Define a callback function to update the map and table when the page is loaded
@app.callback(
    [dash.dependencies.Output('cta-map', 'figure'),
     dash.dependencies.Output('table-div', 'children')],
    [dash.dependencies.Input('interval-component', 'n_intervals'),
     dash.dependencies.Input('cta-map', 'figure'),
     dash.dependencies.Input('route-dropdown', 'value')],
    [dash.dependencies.State('cta-map', 'figure')])



def update_on_load(interval, fig, route, table_div):
    # If the figure argument is None, then the page is being loaded for the first time
    if fig is None:
        init_zoom = 9.85
        init_lat = 41.894
        init_lon = -87.72
        # Plot the train locations on the map
        fig = plot_train_locations(init_zoom, init_lat, init_lon)
        # Display the table of train location data
        table = display_table(route)
    else:
        upd_zoom = fig['layout']['mapbox']['zoom']
        upd_lat = fig['layout']['mapbox']['center']['lat']
        upd_lon = fig['layout']['mapbox']['center']['lon']
        # If the figure argument is not None, then the page is being reloaded due to an update
        # so we only need to update the train locations on the map
        fig = plot_train_locations(upd_zoom, upd_lat, upd_lon)
        table = display_table(route)
    return fig, table


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)




