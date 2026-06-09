# Switching Hidden Markov Model for Vehicle Movement Tracking

This repository contains the implementation of a **vehicle movement tracking system** using **Switching Hidden Markov Models (HMM)**. The project integrates **OpenStreetMap**, **OSRM**, and advanced AI/ML techniques to distinguish vehicular movement on **highways**, **service roads**, and **flyovers** from coarse GNSS data.The detailed content of the project is avaiable in this Drive (https://drive.google.com/drive/folders/1_oNnTAJcahV3ncNSAKwsDxIfSOmAFOma).

## Problem Statement
The challenge was to develop a **map-matching algorithm** using **AI-ML techniques** to:
1. Distinguish vehicular movement on highways, service roads, and flyovers, even with coarse GNSS data.
2. Overcome issues with intermittent GNSS signals and biases in position data.
3. Automate tolling systems and aid applications like GNSS-based tolling and insurance pattern analysis.

## Developed Solution
1. **Data Preprocessing**:
   - **Feature Engineering**: Refined dataset using **Kalman Filters** and **Z-Score**-based outlier detection.
   - Input data includes coarse GNSS positions, road names, and vehicle features (latitude, longitude, speed, height, etc.).

2. **Map-Matching Algorithm**:
   - **Snap to Road**: Snaps GNSS coordinates to the nearest road using **OSRM API**.
   - **Road Classification**: Classifies roads as highway, service, or unknown based on snapped coordinates.

3. **AI/ML Modeling**:
   - Implemented a **Switching Hidden Markov Model**:
     - **Simple Model**: Uses latitude, longitude, and speed as features.
     - **Complex Model**: Adds acceleration and height for better accuracy in complex scenarios.
   - Predicts hidden states (highway/service road/flyover) based on observed states.
   - Provides journey statistics such as total distance/time on highways, service roads, and flyovers.

4. **Dynamic Website Deployment**:
   - Developed a user-friendly web interface using **Flask**, **HTML**, **CSS**, and **JavaScript**.
   - Allows users to upload `.pos` and `.kml` files to:
     - Visualize trajectory on OpenStreetMap.
     - Display journey statistics and a GNSS-based toll calculator.

5. **Applications**:
   - GNSS-based tolling automation.
   - Insurance companies for analyzing driving patterns.

---

## File and Folder Functions

### **static/maps**
- Contains HTML visualizations:
  - **osm_route_map.html**: Displays raw OpenStreetMap routes.
  - **classified_road_map.html**: Highlights road classifications.
  - **predicted_route_map.html**: Visualizes predicted trajectories.
  - **snapped_route_map.html**: Shows snapped coordinates on the map.

### **static/uploads**
- Stores user-uploaded files like `.pos` and `.kml` during runtime.

### **templates/index.html**
- Web app frontend for file uploads and displaying results.

### **app.py**
- Flask application handling:
  - User uploads.
  - Backend processing.
  - Map visualizations.

### **2_Smart_India_Hackathon_maincode.ipynb**
- Notebook with:
  - Data preprocessing.
  - Implementation of Switching Hidden Markov Model.
  - Visualization of trajectories.

### **3_smart_india_hackathon.py**
- Automates:
  - Dataset preprocessing.
  - Running the map-matching model.
  - Generating journey statistics and maps.

---

## Prerequisites

- Python 3.9+
- Install required libraries:
  ```bash
  pip install -r requirements.txt

## How to Run

1. **Run the Flask App**:
   - Start the backend:
     ```bash
     python app.py
     ```
   - Access the web app at: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

2. **Upload Files**:
   - Upload `.pos` and `.kml` datasets on the web app.

3. **View Results**:
   - Predicted trajectories are displayed as maps.
   - Journey statistics are calculated and shown on the web app.

---

## Outputs

### Predicted Trajectories:
- Visualized as maps showing transitions between highways, service roads, and flyovers.

### Journey Statistics:
- **Total Distance**: The total distance traveled.
- **Total Time**: The total time spent on the journey.
- **Average Speed**: The vehicle's average speed throughout the journey.
- **Average Acceleration**: The vehicle's average acceleration.
- **GNSS-based Toll Calculation**: Automatic toll calculation based on highway distance.

---

## Applications

1. **Automated Tolling**:
   - Automatically calculates tolls based on distance traveled on highways.

2. **Insurance Analysis**:
   - Provides insights into driving behavior for insurance companies to personalize policies.

3. **Route Analytics**:
   - Improves transportation planning and monitoring by analyzing route usage and driving patterns.
