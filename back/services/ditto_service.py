# services/ditto_service.py
import json
import requests
from config import Config
from typing import Dict, Any, Optional


class DittoService:
    """Serviço para comunicar com Eclipse Ditto"""

    @staticmethod
    def update_park_twin(park_id: str, park_data: Dict[str, Any]) -> bool:
        """Atualiza o gêmeo digital do parque no Ditto"""
        thing_id = f"org.eclipse.ditto:park-{park_id}"

        thing = {
            "thingId": thing_id,
            "policyId": f"{thing_id}-policy",
            "attributes": {
                "name": park_data.get('name'),
                "city": park_data.get('city'),
                "country": park_data.get('country')
            },
            "features": {
                "lst": {
                    "properties": {
                        "park_lst": park_data.get('park_lst'),
                        "pci": park_data.get('pci'),
                        "pcd": park_data.get('pcd'),
                        "pca": park_data.get('pca')
                    }
                },
                "buffers": {
                    "properties": {
                        "data": park_data.get('buffers', [])
                    }
                },
                "geometry": {
                    "properties": {
                        "geojson": park_data.get('geometry')
                    }
                }
            }
        }

        try:
            response = requests.put(
                f"{Config.DITTO_API}/things/{thing_id}",
                json=thing,
                headers={"Content-Type": "application/json"}
            )
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"❌ Erro ao atualizar Ditto: {e}")
            return False

    @staticmethod
    def get_park_twin(park_id: str) -> Optional[Dict]:
        """Busca o gêmeo digital do parque no Ditto"""
        thing_id = f"org.eclipse.ditto:park-{park_id}"

        try:
            response = requests.get(f"{Config.DITTO_API}/things/{thing_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"❌ Erro ao buscar Ditto: {e}")
            return None