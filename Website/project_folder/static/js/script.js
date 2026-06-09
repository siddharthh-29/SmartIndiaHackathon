let globalHighwayDistance = 0;

document.getElementById('uploadForm').onsubmit = async function(event) {
    event.preventDefault();
    const formData = new FormData();
    const csvFile = document.getElementById("csvFile").files[0];

    if (!csvFile) {
        document.getElementById('statusMessage').innerText = 'Please upload a CSV file.';
        return;
    }

    formData.append("file", csvFile);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.status === 'Map generated successfully') {
            document.getElementById('statusMessage').innerText = 'Map generated!';
            document.getElementById('mapContainer').style.display = 'flex';
            const iframe = document.createElement('iframe');
            iframe.src = result.map_url;
            iframe.width = "100%";
            iframe.height = "500";

            const openMapButton = document.createElement('button');
            openMapButton.innerText = 'Open Map in New Tab';
            openMapButton.onclick = function() {
                window.open(result.map_url, '_blank');
            };

            document.getElementById('map').innerHTML = '';
            document.getElementById('map').appendChild(iframe);
            document.getElementById('map').appendChild(openMapButton);
        } else {
            document.getElementById('statusMessage').innerText = 'Error: ' + result.error;
        }
    } catch (error) {
        document.getElementById('statusMessage').innerText = 'Error: ' + error.message;
    }
};

document.getElementById('generateSnappedMapBtn').onclick = async function() {
    const fileInput = document.getElementById('fileInput');
    
    if (!fileInput.files[0]) {
        document.getElementById('statusMessage').innerText = 'Please select a file first.';
        return;
    }

    document.getElementById('statusMessage').innerText = 'Snapping and generating map...';

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const response = await fetch('/generate_snapped', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.status === 'Snapped map generated successfully') {
            document.getElementById('statusMessage').innerText = 'Snapped map generated!';
            document.getElementById('snappedMapContainer').style.display = 'flex';
            const iframe = document.createElement('iframe');
            iframe.src = result.map_url;
            iframe.width = "100%";
            iframe.height = "500";

            const openMapButton = document.createElement('button');
            openMapButton.innerText = 'Open Map in New Tab';
            openMapButton.onclick = function() {
                window.open(result.map_url, '_blank');
            };

            document.getElementById('snappedMap').innerHTML = '';
            document.getElementById('snappedMap').appendChild(iframe);
            document.getElementById('snappedMap').appendChild(openMapButton);
        } else {
            document.getElementById('statusMessage').innerText = 'Error: ' + result.error;
        }
    } catch (error) {
        document.getElementById('statusMessage').innerText = 'Error: ' + error.message;
    }
};

document.getElementById('generateClassifiedMapBtn').onclick = async function() {
    document.getElementById('statusMessage').innerText = 'Classifying roads and generating map...';

    try {
        const response = await fetch('/classify_and_map', {
            method: 'POST'
        });

        const result = await response.json();

        if (result.status === 'Road classification and map generated successfully') {
            document.getElementById('statusMessage').innerText = 'Classified road map generated!';
            document.getElementById('classifiedMapContainer').style.display = 'flex';
            const iframe = document.createElement('iframe');
            iframe.src = result.map_url;
            iframe.width = "100%";
            iframe.height = "500";

            const openMapButton = document.createElement('button');
            openMapButton.innerText = 'Open Map in New Tab';
            openMapButton.onclick = function() {
                window.open(result.map_url, '_blank');
            };

            document.getElementById('classifiedMap').innerHTML = '';
            document.getElementById('classifiedMap').appendChild(iframe);
            document.getElementById('classifiedMap').appendChild(openMapButton);
        } else {
            document.getElementById('statusMessage').innerText = 'Error: ' + result.error;
        }
    } catch (error) {
        document.getElementById('statusMessage').innerText = 'Error: ' + error.message;
    }
};

document.getElementById('predictRoadTypesBtn').onclick = async function() {
    document.getElementById('statusMessage').innerText = 'Predicting road types and generating map...';

    try {
        const response = await fetch('/predict_road_types', {
            method: 'POST'
        });

        const result = await response.json();

        if (result.status === 'Road type prediction and map generation completed successfully') {
            document.getElementById('statusMessage').innerText = 'Road types predicted and map generated!';
            document.getElementById('predictedMapContainer').style.display = 'flex';
            const iframe = document.createElement('iframe');
            iframe.src = result.map_url;
            iframe.width = "100%";
            iframe.height = "500";

            const openMapButton = document.createElement('button');
            openMapButton.innerText = 'Open Map in New Tab';
            openMapButton.onclick = function() {
                window.open(result.map_url, '_blank');
            };

            document.getElementById('predictedMap').innerHTML = '';
            document.getElementById('predictedMap').appendChild(iframe);
            document.getElementById('predictedMap').appendChild(openMapButton);
        } else {
            document.getElementById('statusMessage').innerText = 'Error: ' + result.error;
        }
    } catch (error) {
        document.getElementById('statusMessage').innerText = 'Error: ' + error.message;
    }
};

document.getElementById('calculateStatisticsBtn').onclick = async function() {
    document.getElementById('statusMessage').innerText = 'Calculating journey statistics...';

    try {
        const response = await fetch('/calculate_statistics', {
            method: 'POST'
        });

        const result = await response.json();

        if (result.status === 'Journey statistics calculated successfully') {
            document.getElementById('statusMessage').innerText = 'Journey statistics calculated!';
            document.getElementById('statisticsContainer').style.display = 'flex';
            
            const statisticsCards = document.getElementById('statisticsCards');
            statisticsCards.innerHTML = '';
            
            result.statistics.forEach(stat => {
                const card = document.createElement('div');
                card.className = 'statistic-card';
                card.innerHTML = `
                    <h3>${stat.metric}</h3>
                    <p>${stat.value}</p>
                `;
                if (stat.metric === 'Highway Distance') {
                    // Extract the numeric value from the highway distance string
                    const distanceValue = parseFloat(stat.value);
                    if (!isNaN(distanceValue)) {
                        globalHighwayDistance = distanceValue;
                    }
                }
                statisticsCards.appendChild(card);
            });
            // Enable the toll calculation section
            document.getElementById('tollCalculationContainer').style.display = 'block';
        } else {
            document.getElementById('statusMessage').innerText = 'Error: ' + result.error;
        }
    } catch (error) {
        document.getElementById('statusMessage').innerText = 'Error: ' + error.message;
    }
};

// Toll Calculation
const vehicleTypeSelect = document.getElementById('vehicleType');
const tariffDisplay = document.getElementById('tariffDisplay');
const calculateTollBtn = document.getElementById('calculateTollBtn');
const tollResult = document.getElementById('tollResult');

vehicleTypeSelect.addEventListener('change', function() {
    const selectedTariff = this.value;
    tariffDisplay.textContent = selectedTariff ? `₹${selectedTariff}` : '-';
});

calculateTollBtn.addEventListener('click', function() {
    const selectedTariff = parseFloat(vehicleTypeSelect.value);
    if (!selectedTariff) {
        tollResult.textContent = 'Please select a vehicle type.';
        return;
    }

    if (globalHighwayDistance === 0) {
        tollResult.textContent = 'Highway distance not available.';
        return;
    }

    const totalToll = selectedTariff * globalHighwayDistance;
    tollResult.textContent = `Estimated Toll: ₹${totalToll.toFixed(2)}`;
});

// Smooth scrolling for both top navigation and footer navigation
document.querySelectorAll('.nav-links a, .nav-button').forEach(link => {
    link.addEventListener('click', function(event) {
        event.preventDefault();
        const targetId = this.getAttribute('href');
        document.querySelector(targetId).scrollIntoView({ behavior: 'smooth' });
    });
});

// Tab functionality for displaying various sections
const tabLinks = document.querySelectorAll('.tab-link');
const tabContents = document.querySelectorAll('.tab-content');

tabLinks.forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        const targetTab = document.querySelector(this.getAttribute('href'));
        tabContents.forEach(content => content.classList.remove('active'));
        targetTab.classList.add('active');
    });
    
});
