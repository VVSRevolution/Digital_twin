from typing import Optional

import requests


class OverpassService:
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"

    @staticmethod
    def search_park(
            query: str,
            city: Optional[str] = None,
            country: Optional[str] = None
    ):
        try:
            area_filter = ""
            area_filter_query = ""

            if city and country:
                area_filter = f"""
                area["name"="{country}"]["boundary"="administrative"]["admin_level"="2"]->.country;
                area["name"="{city}"]["boundary"="administrative"](area.country)->.searchArea;
                """
                area_filter_query = "(area.searchArea)"

            elif city:
                area_filter = f"""
                area["name"="{city}"]->.searchArea;
                """
                area_filter_query = "(area.searchArea)"

            elif country:
                area_filter = f"""
                area["name"="{country}"]["boundary"="administrative"]["admin_level"="2"]->.searchArea;
                """
                area_filter_query = "(area.searchArea)"

            overpass_query = f"""
[out:json][timeout:60];
{area_filter}
(
  way["leisure"="park"]["name"~"{query}", i]{area_filter_query};
  relation["leisure"="park"]["name"~"{query}", i]{area_filter_query};
);
out geom;
"""

            print("========== OVERPASS QUERY ==========")
            print(overpass_query)
            print("====================================")

            response = requests.post(
                OverpassService.OVERPASS_URL,
                data={"data": overpass_query},
                timeout=60,
                headers={
                    "User-Agent": "MyApp/1.0 (contato@meusite.com)"
                }
            )

            print("STATUS:", response.status_code)

            if response.status_code != 200:
                print(response.text)
                return []

            data = response.json()

            if "elements" not in data:
                print(data)
                return []

            return data["elements"]

        except requests.exceptions.RequestException as e:
            print("Erro de requisição:", e)
            return []

        except Exception as e:
            print("Erro:", e)
            return []
