# services/park_search_service.py
from typing import Optional

from models import Park
from services.database_service import DatabaseService
from services.overpass_service import OverpassService


class ParkSearchService:

    @staticmethod
    def search(
            query: str,
            city: Optional[str] = None,
            country: Optional[str] = None,
            osm_id: Optional[str] = None
    ):
        """Busca parque: DB primeiro, depois Overpass"""

        try:

            # 🔥 1. BUSCAR NO DB POR OSM_ID
            if osm_id:
                park = Park.query.filter_by(osm_id=osm_id).first()
                if park:
                    return {
                        'success': True,
                        'source': 'database',
                        'results': [park.to_dict()]
                    }

            # 2. BUSCAR POR NOME NO DB
            db_query = Park.query
            if city:
                db_query = db_query.filter(Park.city.ilike(f"%{city}%"))
            if country:
                db_query = db_query.filter(Park.country.ilike(f"%{country}%"))

            db_results = db_query.filter(Park.name.ilike(f"%{query}%")).all()
            if db_results:
                return {
                    'success': True,
                    'source': 'database',
                    'results': [p.to_dict() for p in db_results]
                }

            # 3. BUSCAR NO OVERPASS (COM RETRY)
            try:
                overpass_results = OverpassService.search_park(query, city, country)
            except Exception as e:
                return {
                    'success': False,
                    'source': 'overpass',
                    'results': [],
                    'error': str(e)
                }

            if not overpass_results:
                return {
                    'success': True,
                    'source': 'overpass',
                    'results': []
                }

            # 🔥 4. SALVAR NO DB
            saved_results = []
            for item in overpass_results:
                tags = item.get("tags", {})

                park = DatabaseService.save_park(
                    name=tags.get("name", ""),
                    country=country or "Brazil",
                    geometry=item.get("geometry"),
                    city=city,
                    osm_id=item.get("id"),
                    osm_type=item.get("type"),
                    tags=tags
                )
                saved_results.append(park.to_dict())

            return {
                'success': True,
                'source': 'overpass',
                'results': saved_results
            }

        except Exception as e:
            return {
                'success': False,
                'source': 'error',
                'results': [],
                'error': str(e)
            }
