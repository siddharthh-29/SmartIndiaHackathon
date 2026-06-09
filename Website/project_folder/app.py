import os
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from flask import Flask, render_template, request, jsonify
import requests
from geopy.distance import geodesic
from hmmlearn.hmm import GaussianHMM
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, recall_score, f1_score, precision_score
import numpy as np
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
from collections import deque
# Initialize Flask app
app = Flask(__name__)

# Define path for saving uploaded CSV files and generated map HTML
UPLOAD_FOLDER = 'uploads'
MAP_FOLDER = 'static/maps'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(MAP_FOLDER, exist_ok=True)

# Function to snap coordinates to the nearest road using OSRM's Nearest API
def snap_to_road(lat, lon):
    osrm_url = f'http://router.project-osrm.org/nearest/v1/driving/{lon},{lat}'
    response = requests.get(osrm_url)
    if response.status_code == 200:
        data = response.json()
        # Extract the snapped point's coordinates (lat, lon) and the road name
        snapped_point = data['waypoints'][0]['location']
        snapped_lat = snapped_point[1]
        snapped_lon = snapped_point[0]
        road_name = data['waypoints'][0].get('name', 'Unknown')  # Get road name if available
        return snapped_lat, snapped_lon, road_name
    else:
        print(f"Error with request: {response.status_code}")
        return None, None, 'Unknown'
#NEW

def classify_road_type(road_name):
    road_type_mapping = {
        "Bengaluru-Mysuru Expressway": "highway",
        "Bengaluru - Mysuru Road": "service",
        "Kumbalagodu Flyover": "highway",
        "Bangalore-Mysore Road": "service"
    }
    
    if isinstance(road_name, str):
        for known_road, road_type in road_type_mapping.items():
            if known_road in road_name:
                return road_type
    return "unknown"

def process_and_classify_roads(input_file):
    data = pd.read_csv(input_file)
    road_types = []
    
    for _, row in data.iterrows():
        road_name = row['road_name']
        if pd.isna(road_name):
            road_name = "unknown"
        road_type = classify_road_type(road_name)
        road_types.append(road_type)
    
    data['road_type'] = road_types
    return data

def plot_roads_on_map(data):
    map_center = [data['snapped_latitude'].mean(), data['snapped_longitude'].mean()]
    m = folium.Map(location=map_center, zoom_start=15)
    marker_cluster = MarkerCluster().add_to(m)
    
    for _, row in data.iterrows():
        lat = row['snapped_latitude']
        lon = row['snapped_longitude']
        road_type = row['road_type']
        
        if road_type == 'service':
            color = 'green'
            label = 'Service Road'
        elif road_type == 'highway':
            color = 'blue'
            label = 'Highway'
        else:
            color = 'grey'
            label = 'Unknown'
        
        folium.Marker([lat, lon], popup=label, icon=folium.Icon(color=color)).add_to(marker_cluster)
    
    return m

#NEW2
def create_features_complex(df):
    df['prev_lat'] = df['snapped_latitude'].shift(1)
    df['prev_lon'] = df['snapped_longitude'].shift(1)
    df['next_lat'] = df['snapped_latitude'].shift(-1)
    df['next_lon'] = df['snapped_longitude'].shift(-1)
    df = df.fillna(method='ffill').fillna(method='bfill')
    features = ['speed', 'altitude', 'bearing']
    scaler = StandardScaler()
    df[features] = scaler.fit_transform(df[features])
    return df

def create_features_simple(df):
    return df[['snapped_latitude', 'snapped_longitude']]

def train_hmm(features, n_components=2, random_state=None):
    hmm = GaussianHMM(n_components=n_components, covariance_type="full", n_iter=1000, random_state=random_state)
    hmm.fit(features)
    return hmm

def evaluate_model(hmm_model, features, labels):
    predicted_labels = hmm_model.predict(features)
    accuracy = accuracy_score(labels, predicted_labels)
    recall = recall_score(labels, predicted_labels, average='binary')
    precision = precision_score(labels, predicted_labels, average='binary')
    f1 = f1_score(labels, predicted_labels, average='binary')
    return accuracy, recall, precision, f1

#NEW3
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in kilometers
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    return distance

def calculate_statistics(data):
    highway_distance = 0
    service_distance = 0
    total_distance = 0

    for i in range(len(data)-1):
        lat1 = data.iloc[i]['snapped_latitude']
        lon1 = data.iloc[i]['snapped_longitude']
        lat2 = data.iloc[i+1]['snapped_latitude']
        lon2 = data.iloc[i+1]['snapped_longitude']

        segment_distance = calculate_distance(lat1, lon1, lat2, lon2)
        total_distance += segment_distance

        if data.iloc[i]['road_type'] == 'highway':
            highway_distance += segment_distance
        elif data.iloc[i]['road_type'] == 'service':
            service_distance += segment_distance

    total_time_hours = len(data) / 3600  # Assuming data points are 1 second apart

    avg_speed = data['speed'].mean()
    avg_acceleration = data['acceleration'].mean()

    stats = [
        {'metric': 'Highway Distance', 'value': f"{highway_distance:.2f} km"},
        {'metric': 'Service Road Distance', 'value': f"{service_distance:.2f} km"},
        {'metric': 'Total Distance', 'value': f"{total_distance:.2f} km"},
        {'metric': 'Total Time', 'value': f"{total_time_hours:.2f} hours"},
        {'metric': 'Average Speed', 'value': f"{avg_speed:.2f} km/h"},
        {'metric': 'Average Acceleration', 'value': f"{avg_acceleration:.2f} m/s²"}
    ]

    return stats

#NEW MAP FUNCTION 

def plot_roads_on_map(data):
    # Create a folium map centered at the mean coordinates
    map_center = [data['snapped_latitude'].mean(), data['snapped_longitude'].mean()]
    m = folium.Map(location=map_center, zoom_start=15)

    # Initialize sliding windows for road type verification
    window_size = 6
    road_types_window = deque(maxlen=window_size)

    # Lists to store coordinates by road type
    highway_coords = []
    service_coords = []
    current_segment = []
    current_type = None

    def add_path_with_arrows(coordinates, color, map_obj):
        """Add a path with arrow markers showing direction of movement"""
        if len(coordinates) >= 2:
            # Create the main path
            folium.PolyLine(
                coordinates,
                weight=3,
                color=color,
                opacity=0.8
            ).add_to(map_obj)

            # Add arrow markers at intervals
            for i in range(0, len(coordinates)-1, 3):  # Add arrow every 3 points
                point1 = coordinates[i]
                point2 = coordinates[i+1]

                # Calculate bearing for arrow rotation
                y = np.sin(point2[1] - point1[1]) * np.cos(point2[0])
                x = np.cos(point1[0]) * np.sin(point2[0]) - np.sin(point1[0]) * np.cos(point2[0]) * np.cos(point2[1] - point1[1])
                bearing = np.degrees(np.arctan2(y, x))

                # Add arrow marker
                folium.RegularPolygonMarker(
                    location=[(point1[0] + point2[0])/2, (point1[1] + point2[1])/2],
                    number_of_sides=3,
                    rotation=bearing,
                    radius=6,
                    color=color,
                    fill=True,
                    fill_color=color
                ).add_to(map_obj)

    # Add start point marker (first point in CSV)
    first_row = data.iloc[0]
    folium.Marker(
        [first_row['snapped_latitude'], first_row['snapped_longitude']],
        popup='Starting Point<br>' + f"""
            Speed: {first_row['speed']:.2f} km/h<br>
            Acceleration: {first_row['acceleration']:.2f} m/s²<br>
            Bearing: {first_row['bearing']:.2f}°
        """,
        icon=folium.Icon(color='yellow', icon='info-sign', prefix='fa')
    ).add_to(m)

    # Process points and detect transitions
    for i, row in data.iterrows():
        lat = row['snapped_latitude']
        lon = row['snapped_longitude']
        current_road_type = row['road_type']

        # Create popup content with vehicle metrics
        popup_content = f"""
            Road Type: {current_road_type}<br>
            Speed: {row['speed']:.2f} km/h<br>
            Acceleration: {row['acceleration']:.2f} m/s²<br>
            Bearing: {row['bearing']:.2f}°
        """

        # Check for road type transition
        if i >= window_size:
            prev_window = data.iloc[i-window_size:i]['road_type'].tolist()
            next_window = data.iloc[i:i+window_size]['road_type'].tolist() if i+window_size <= len(data) else []

            # Detect stable transitions
            if len(next_window) == window_size and len(prev_window) == window_size:
                if (all(rt == prev_window[0] for rt in prev_window) and
                    all(rt == next_window[0] for rt in next_window) and
                    prev_window[0] != next_window[0]):

                    # Add transition marker
                    transition_type = f"Transition: {prev_window[0]} → {next_window[0]}"
                    folium.Marker(
                        [lat, lon],
                        popup=transition_type + "<br>" + popup_content,
                        icon=folium.Icon(color='red', icon='info-sign')
                    ).add_to(m)

                    # Handle path segmentation at transition points
                    if current_segment:
                        if current_type == 'highway':
                            highway_coords.append(current_segment)
                        elif current_type == 'service':
                            service_coords.append(current_segment)
                        current_segment = []
                    continue

        # Add point to current segment
        current_segment.append([lat, lon])
        current_type = current_road_type

        # Regular point markers with color coding
        if current_road_type == 'service':
            color = 'green'
        elif current_road_type == 'highway':
            color = 'blue'
        else:
            color = 'grey'

        # Add circle markers for regular points (skip for first and last points)
        if i != 0 and i != len(data) - 1:
            folium.CircleMarker(
                location=[lat, lon],
                radius=6,
                popup=popup_content,
                color=color,
                fill=True,
                fill_color=color
            ).add_to(m)

    # Add end point marker (last point in CSV)
    last_row = data.iloc[-1]
    folium.Marker(
        [last_row['snapped_latitude'], last_row['snapped_longitude']],
        popup='Ending Point<br>' + f"""
            Speed: {last_row['speed']:.2f} km/h<br>
            Acceleration: {last_row['acceleration']:.2f} m/s²<br>
            Bearing: {last_row['bearing']:.2f}°
        """,
        icon=folium.Icon(color='yellow', icon='info-sign', prefix='fa')
    ).add_to(m)

    # Add final segment
    if current_segment:
        if current_type == 'highway':
            highway_coords.append(current_segment)
        elif current_type == 'service':
            service_coords.append(current_segment)

    # Add paths with arrows for each segment
    for segment in highway_coords:
        add_path_with_arrows(segment, 'darkblue', m)
    for segment in service_coords:
        add_path_with_arrows(segment, 'darkgreen', m)

    # Add a legend
    legend_html = """
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: white; padding: 10px; border: 2px solid grey; border-radius: 5px">
        <p><i class="fa fa-circle" style="color:blue"></i> Highway</p>
        <p><i class="fa fa-circle" style="color:green"></i> Service Road</p>
        <p><i class="fa fa-circle" style="color:grey"></i> Unknown</p>
        <p><i class="fa fa-info-sign" style="color:red"></i> Transition Point</p>
        <p><i class="fa fa-info-sign" style="color:yellow"></i> Start/End Points</p>
        <p><span style="color:darkblue">▶</span> Highway Direction</p>
        <p><span style="color:darkgreen">▶</span> Service Road Direction</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m
def plot_colour_on_map(input_file, output_map_path):
    """
    Reads the CSV, extracts snapped coordinates, and plots them on a map with
    color-coded markers for road types (Green for service, Blue for highway, Grey for unknown).
    """
    # Load the CSV data
    data = pd.read_csv(input_file)

    # Create a folium map centered at the mean coordinates of the snapped points
    map_center = [data['snapped_latitude'].mean(), data['snapped_longitude'].mean()]
    m = folium.Map(location=map_center, zoom_start=15)

    # Add markers with color coding based on road type
    for _, row in data.iterrows():
        lat = row['snapped_latitude']
        lon = row['snapped_longitude']
        road_type = row['road_type']

        # Determine the color and label based on the road type
        if road_type == 'service':
            color = 'green'
            label = 'Service Road'
        elif road_type == 'highway':
            color = 'blue'
            label = 'Highway'
        else:
            color = 'grey'  # For unknown roads
            label = 'Unknown'

        # Add the marker to the map with the appropriate label and color
        folium.Marker([lat, lon], popup=label, icon=folium.Icon(color=color)).add_to(m)

    # Save the map to an HTML file
    m.save(output_map_path)


# Route to render the index page
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle CSV file upload
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"})
    
    # Save the uploaded CSV file
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    
    # Process the CSV file and generate map
    df = pd.read_csv(filepath)
    initial_location = [df['latitude'][0], df['longitude'][0]]
    osm_map = folium.Map(location=initial_location, zoom_start=12)
   
    
  # Function to add normal markers to the map
    def add_marker(lat, lon, map_object):
        marker = folium.Marker(location=[lat, lon])
        marker.add_to(map_object)
    
    # Add normal markers for each location
    for i, row in df.iterrows():
        add_marker(row['latitude'], row['longitude'], osm_map)
    
    # Create a polyline to plot the route (GNSS data path)
    route_coords = list(zip(df['latitude'], df['longitude']))

    # Add the polyline for the route, adjust color and thickness
    folium.PolyLine(route_coords, color="blue", weight=3, opacity=0.6).add_to(osm_map)
    
    # Save the map as an HTML file
    map_filename = os.path.join(MAP_FOLDER, 'osm_route_map.html')
    osm_map.save(map_filename)
    
    return jsonify({"map_url": f"/static/maps/osm_route_map.html", "status": "Map generated successfully"})

# Route to generate snapped coordinates and display the snapped map
@app.route('/generate_snapped', methods=['POST'])
def generate_snapped_coordinates():
    file = request.files['file']
    
    # Save the uploaded file
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # Now process the uploaded CSV file
    df = pd.read_csv(filepath)
    
    snapped_latitudes = []
    snapped_longitudes = []
    road_names = []
    
    for _, row in df.iterrows():
        result = snap_to_road(row['latitude'], row['longitude'])
        if result[0] and result[1]:
            snapped_latitudes.append(result[0])
            snapped_longitudes.append(result[1])
            road_names.append(result[2])
        else:
            snapped_latitudes.append(row['latitude'])
            snapped_longitudes.append(row['longitude'])
            road_names.append('Unknown')
    
    # Add snapped coordinates and road names to the dataframe
    df['snapped_latitude'] = snapped_latitudes
    df['snapped_longitude'] = snapped_longitudes
    df['road_name'] = road_names
    
    snapped_file = os.path.join(UPLOAD_FOLDER, 'snapped_coordinates.csv')
    df.to_csv(snapped_file, index=False)
    
    # Apply same map plotting style as the '/upload' route
    snapped_map = folium.Map(location=[snapped_latitudes[0], snapped_longitudes[0]], zoom_start=12)
    
    # Function to add normal markers to the snapped map
    def add_marker(lat, lon, map_object):
        marker = folium.Marker(location=[lat, lon], popup=f"Road: {road_names}")
        marker.add_to(map_object)
    
    # Add normal markers for snapped coordinates
    for lat, lon in zip(snapped_latitudes, snapped_longitudes):
        add_marker(lat, lon, snapped_map)
    
    # Create a polyline to plot the snapped route (GNSS data path)
    snapped_route_coords = list(zip(snapped_latitudes, snapped_longitudes))

    # Add the polyline for the snapped route, adjust color and thickness
    folium.PolyLine(snapped_route_coords, color="blue", weight=3, opacity=0.6).add_to(snapped_map)
    
    # Save the snapped map as an HTML file
    snapped_map_filename = os.path.join(MAP_FOLDER, 'snapped_route_map.html')
    snapped_map.save(snapped_map_filename)
    
    return jsonify({"map_url": f"/static/maps/snapped_route_map.html", "status": "Snapped map generated successfully"})
#NEW

@app.route('/classify_and_map', methods=['POST'])
def classify_and_map():
    input_file = os.path.join(UPLOAD_FOLDER, 'snapped_coordinates.csv')
    
    if not os.path.exists(input_file):
        return jsonify({"error": "Snapped coordinates file not found. Please generate snapped coordinates first."})
    
    data = process_and_classify_roads(input_file)
    
    # Save the updated data with road types
    output_file = os.path.join(UPLOAD_FOLDER, 'classified_coordinates.csv')
    data.to_csv(output_file, index=False)
    
    # Generate the map using the new plot_roads_on_map function
    output_map_path = os.path.join(MAP_FOLDER, 'classified_road_map.html')
    plot_colour_on_map(output_file, output_map_path)
    
    # Save the map
    map_filename = os.path.join(MAP_FOLDER, 'classified_road_map.html')
    
    
    return jsonify({
        "map_url": f"/static/maps/classified_road_map.html",
        "status": "Road classification and map generated successfully"
    })

#NEW2

@app.route('/predict_road_types', methods=['POST'])
def predict_road_types():
    input_file = os.path.join(UPLOAD_FOLDER, 'classified_coordinates.csv')
    
    if not os.path.exists(input_file):
        return jsonify({"error": "Classified coordinates file not found. Please classify roads first."})
    
    # Set the random seed for reproducibility
    seed_value = 42
    np.random.seed(seed_value)
    
    # Load the CSV file
    df = pd.read_csv(input_file)
    
    # Preprocess the data
    train_data = df[df['road_type'].isin(['highway', 'service'])]
    test_data = df[df['road_type'] == 'unknown']
    
    # Apply feature engineering for both models
    train_data_complex = create_features_complex(train_data)
    train_data_simple = create_features_simple(train_data)
    test_data_complex = create_features_complex(test_data)
    test_data_simple = create_features_simple(test_data)
    
    # Train the models
    train_features_complex = train_data_complex[['prev_lat', 'prev_lon', 'snapped_latitude', 'snapped_longitude', 'next_lat', 'next_lon', 'speed', 'altitude', 'bearing']].values
    hmm_model_complex = train_hmm(train_features_complex, random_state=seed_value)
    
    train_features_simple = train_data_simple[['snapped_latitude', 'snapped_longitude']].values
    hmm_model_simple = train_hmm(train_features_simple, random_state=seed_value)
    
    # Evaluate the models
    road_type_mapping = {'highway': 0, 'service': 1}
    train_data['road_type_label'] = train_data['road_type'].map(road_type_mapping)
    train_labels = train_data['road_type_label'].values
    
    accuracy_complex, recall_complex, precision_complex, f1_complex = evaluate_model(hmm_model_complex, train_features_complex, train_labels)
    accuracy_simple, recall_simple, precision_simple, f1_simple = evaluate_model(hmm_model_simple, train_features_simple, train_labels)
    
    # Select the best model
    if f1_complex > f1_simple:
        selected_model = hmm_model_complex
        selected_features = test_data_complex[['prev_lat', 'prev_lon', 'snapped_latitude', 'snapped_longitude', 'next_lat', 'next_lon', 'speed', 'altitude', 'bearing']].values
    else:
        selected_model = hmm_model_simple
        selected_features = test_data_simple[['snapped_latitude', 'snapped_longitude']].values
    
    # Handle NaN values before prediction
    selected_features = np.nan_to_num(selected_features)
    
    # Predict the road types for unknown rows
    predicted_labels = selected_model.predict(selected_features)
    
    # Map the predicted numeric labels back to 'highway' or 'service'
    predicted_road_types = {0: 'highway', 1: 'service'}
    test_data['predicted_road_type'] = [predicted_road_types[label] for label in predicted_labels]
    
    # Update the original dataframe with the predictions
    df.loc[df['road_type'] == 'unknown', 'road_type'] = test_data['predicted_road_type'].values
    
    # Save the updated dataframe to a new CSV file
    output_file = os.path.join(UPLOAD_FOLDER, 'updated_road_type_predictions.csv')
    df.to_csv(output_file, index=False)
    
   # Generate the map with updated road types
    m = plot_roads_on_map(df)
    
    # Save the map
    map_filename = os.path.join(MAP_FOLDER, 'predicted_road_map.html')
    m.save(map_filename)
    
    return jsonify({
        "map_url": f"/static/maps/predicted_road_map.html",
        "status": "Road type prediction and map generation completed successfully"
    })

#NEW3

@app.route('/calculate_statistics', methods=['POST'])
def get_journey_statistics():
    input_file = os.path.join(UPLOAD_FOLDER, 'updated_road_type_predictions.csv')
    
    if not os.path.exists(input_file):
        return jsonify({"error": "Updated road type predictions file not found. Please predict road types first."})
    
    df = pd.read_csv(input_file)
    stats = calculate_statistics(df)
    
    return jsonify({
        "statistics": stats,
        "status": "Journey statistics calculated successfully"
    })


# Start Flask app
if __name__ == '__main__':
    app.run(debug=True)