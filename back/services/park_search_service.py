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
            osm_id: Optional[str] = None  # 👈 Optional[str]
    ):
        """Busca parque: DB primeiro, depois Overpass"""

        # 🔥 1. BUSCAR NO DB POR OSM_ID
        if osm_id:
            park = Park.query.filter_by(osm_id=osm_id).first()
            if park:
                return {
                    'source': 'database',
                    'results': [park.to_dict()]
                }

        # 🔥 2. BUSCAR POR NOME NO DB
        db_query = Park.query
        if city:
            db_query = db_query.filter(Park.city.ilike(f"%{city}%"))
        if country:
            db_query = db_query.filter(Park.country.ilike(f"%{country}%"))

        db_results = db_query.filter(Park.name.ilike(f"%{query}%")).all()
        if db_results:
            return {
                'source': 'database',
                'results': [p.to_dict() for p in db_results]
            }

        # 🔥 3. BUSCAR NO OVERPASS
        overpass_results = OverpassService.search_park(query, city, country)

        if not overpass_results:
            return {'source': 'overpass', 'results': []}

        # 🔥 4. SALVAR NO DB
        saved_results = []
        for item in overpass_results:
            tags = item["tags"]

            park = DatabaseService.save_park(
                name=tags["name"],
                city=city,
                country=country or "Brazil",
                geometry=item["geometry"],
                osm_id=item["id"],
                osm_type=item["type"],
                tags=tags
            )

            saved_results.append(park.to_dict())

        return overpass_results
