# config.py
import os

class Config:
    # Google Earth Engine
    PROJECT_ID = os.environ.get('PROJECT_ID', 'digital-twin-501202')
    GCP_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', './credentials.json')
    DITTO_URL = os.environ.get('DITTO_URL', 'http://localhost:8080')

    # Ditto
    DITTO_URL = os.environ.get('DITTO_URL', 'http://localhost:8080')
    DITTO_API = f"{DITTO_URL}/api/2"

    # Overpass API
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"
    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL',
                                        'postgresql://digital_twin:DigitalTwin2024!@localhost:5432/digital_twin')
    SQLALCHEMY_TRACK_MODIFICATIONS = False