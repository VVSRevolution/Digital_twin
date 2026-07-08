# services/park_service.py
import json
import requests
from config import Config
from typing import List, Optional, Dict, Any


class ParkService:
    """Serviço para buscar parques no OpenStreetMap (Overpass + Nominatim)"""

    @staticmethod
    def search_park_by_name(name: str, country_code: str = 'BR') -> List[Dict]:
        """Busca parques pelo nome (usando Nominatim)"""
        url = f"{Config.NOMINATIM_URL}?q={name}&format=json&addressdetails=1&countrycodes={country_code}&limit=10"

        response = requests.get(url, headers={'User-Agent': 'DigitalTwinApp/1.0'})

        if response.status_code != 200:
            return []

        data = response.json()
        results = []

        for item in data:
            address = item.get('address', {})
            results.append({
                'id': item.get('place_id'),
                'name': item.get('display_name', '').split(',')[0] or item.get('name', ''),
                'city': address.get('city') or address.get('town') or address.get('village') or '',
                'country': address.get('country', ''),
                'lat': float(item.get('lat', 0)),
                'lon': float(item.get('lon', 0)),
                'display_name': item.get('display_name', ''),
                'osm_type': item.get('osm_type'),
                'osm_id': item.get('osm_id')
            })

        return results

    @staticmethod
    def fetch_park_polygon(park_name: str, city: str) -> Optional[Dict]:
        """Busca o polígono/contorno do parque usando Overpass API"""
        overpass_query = f"""
            [out:json][timeout:25];
            (
                way["leisure"="park"]["name"~"{park_name}"];
                relation["leisure"="park"]["name"~"{park_name}"];
            );
            out geom;
        """

        url = f"{Config.OVERPASS_URL}?data={overpass_query}"
        response = requests.get(url)

        if response.status_code != 200:
            return None

        data = response.json()
        elements = data.get('elements', [])

        if not elements:
            return None

        # 🔥 Extrai o primeiro polígono encontrado
        for el in elements:
            if el.get('geometry'):
                return {
                    'type': 'Polygon',
                    'coordinates': [[[p['lon'], p['lat']] for p in el['geometry']]]
                }

        return None