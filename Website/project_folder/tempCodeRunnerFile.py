import os
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from flask import Flask, render_template, request, jsonify
import requests

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
        # Extract the snapped point's coordinates (lat, lon)
        snapped_point = data['waypoints'][0]['location']
        snapped_lat = snapped_point[1]
        snapped_lon = snapped_point[0]
        return snapped_lat, snapped_lon
    else:
        print(f"Error with request: {response.status_code}")
        return None, None

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
    marker_cluster = MarkerCluster().add_to(osm_map)
    
    # Add markers to the map
    for i, row in df.iterrows():
        folium.Marker([row['latitude'], row['longitude']]).add_to(marker_cluster)
    
    # Save the map as an HTML file
    map_filename = os.path.join(MAP_FOLDER, 'osm_route_map.html')
    osm_map.save(map_filename)

    return jsonify({"map_url": f"static/maps/osm_route_map.html", "status": "Map generated successfully"})

# Route to generate snapped coordinates and display the snapped map
@app.route('/generate_snapped', methods=['POST'])
def generate_snapped_coordinates():
    filepath = request.form['file']
    df = pd.read_csv(filepath)

    snapped_latitudes = []
    snapped_longitudes = []

    # Snap all coordinates to the nearest road
    for _, row in df.iterrows():
        snapped_lat, snapped_lon = snap_to_road(row['latitude'], row['longitude'])
        if snapped_lat and snapped_lon:
            snapped_latitudes.append(snapped_lat)
            snapped_longitudes.append(snapped_lon)
        else:
            snapped_latitudes.append(row['latitude'])
            snapped_longitudes.append(row['longitude'])
    
    # Add snapped coordinates to the dataframe
    df['snapped_latitude'] = snapped_latitudes
    df['snapped_longitude'] = snapped_longitudes
    
    # Save the updated dataframe to a new CSV
    snapped_file = os.path.join(UPLOAD_FOLDER, 'snapped_coordinates.csv')
    df.to_csv(snapped_file, index=False)
    
    # Generate a new map with the snapped coordinates
    snapped_map = folium.Map(location=[snapped_latitudes[0], snapped_longitudes[0]], zoom_start=12)
    snapped_marker_cluster = MarkerCluster().add_to(snapped_map)
    
    # Add markers for snapped coordinates to the map
    for lat, lon in zip(snapped_latitudes, snapped_longitudes):
        folium.Marker([lat, lon]).add_to(snapped_marker_cluster)
    
    # Save the snapped map as an HTML file
    snapped_map_filename = os.path.join(MAP_FOLDER, 'snapped_route_map.html')
    snapped_map.save(snapped_map_filename)

    return jsonify({"map_url": f"static/maps/snapped_route_map.html", "status": "Snapped map generated successfully"})

# Start Flask app
if __name__ == '__main__':
    app.run(debug=True)
