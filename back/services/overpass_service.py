# services/overpass_service.py
import time
from typing import Optional

import requests


class OverpassService:
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # segundos

    @staticmethod
    def search_park(
            query: str,
            city: Optional[str] = None,
            country: Optional[str] = None,
            osm_id: Optional[str] = None
    ):
        """
        Busca parque primeiro por OSM_ID, depois por nome
        """
        # 🔥 PRIORIDADE 1: BUSCAR POR OSM_ID
        if osm_id:
            print(f"🔍 Tentando buscar por OSM_ID: {osm_id}")
            result = OverpassService.search_by_osm_id(osm_id)
            if result and len(result) > 0:
                print(f"✅ Encontrado por OSM_ID: {osm_id}")
                return result
            else:
                print(f"⚠️ Nenhum resultado para OSM_ID {osm_id}, tentando por nome...")

        # 🔥 PRIORIDADE 2: BUSCAR POR NOME (código existente)
        print(f"🔍 Tentando buscar por nome: {query}")
        return OverpassService.search_by_name(query, city, country)

    @staticmethod
    def search_by_osm_id(osm_id: str):
        """
        Busca um parque diretamente pelo OSM ID
        """
        overpass_query = f"""
                            [out:json][timeout:30];
                            (
                              way({osm_id});
                              relation({osm_id});
                            );
                            out body geom;
                        """

        print("========== OVERPASS QUERY (OSM ID) ==========")
        print(overpass_query)
        print("=============================================")

        try:
            response = requests.post(
                OverpassService.OVERPASS_URL,
                data={"data": overpass_query},
                timeout=30,
                headers={
                    "User-Agent": "DigitalTwin/1.0 (contato@meusite.com)"
                }
            )

            if response.status_code == 200:
                data = response.json()
                if "elements" in data and data["elements"]:
                    print(f"✅ Encontrado elemento com OSM ID {osm_id}")
                    return data["elements"]
                else:
                    print(f"⚠️ Nenhum elemento encontrado para OSM ID {osm_id}")
                    return []
            else:
                print(f"❌ Erro {response.status_code}: {response.text[:200]}")
                return []

        except Exception as e:
            print(f"❌ Erro ao buscar por OSM ID: {e}")
            return []

    @staticmethod
    def search_by_name(
            query: str,
            city: Optional[str] = None,
            country: Optional[str] = None
    ):
        """
        Busca parques por nome (código existente)
        """
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

        print("========== OVERPASS QUERY (NOME) ==========")
        print(overpass_query)
        print("============================================")

        last_error = None

        for attempt in range(1, OverpassService.MAX_RETRIES + 1):
            try:
                print(f"🔄 Tentativa {attempt}/{OverpassService.MAX_RETRIES}...")

                response = requests.post(
                    OverpassService.OVERPASS_URL,
                    data={"data": overpass_query},
                    timeout=60,
                    headers={
                        "User-Agent": "DigitalTwin/1.0 (contato@meusite.com)"
                    }
                )

                print(f"📊 STATUS: {response.status_code}")
                print(f"📊 RESPONSE: {response}")

                if response.status_code == 200:
                    data = response.json()
                    if "elements" in data:
                        print(f"✅ Encontrados {len(data['elements'])} elementos")
                        return data["elements"]
                    else:
                        print("⚠️ Nenhum elemento encontrado")
                        return []

                elif response.status_code == 504:
                    print(f"⚠️ Timeout na tentativa {attempt}")
                    last_error = "O servidor do OpenStreetMap está ocupado. Tentando novamente..."

                    if attempt < OverpassService.MAX_RETRIES:
                        time.sleep(OverpassService.RETRY_DELAY)
                    continue

                else:
                    print(f"❌ Erro {response.status_code}: {response.text[:200]}")
                    last_error = f"Erro {response.status_code} ao buscar parque"
                    return []

            except requests.exceptions.Timeout:
                print(f"⏰ Timeout na tentativa {attempt}")
                last_error = "O servidor do OpenStreetMap demorou muito para responder"

                if attempt < OverpassService.MAX_RETRIES:
                    time.sleep(OverpassService.RETRY_DELAY)
                continue

            except requests.exceptions.RequestException as e:
                print(f"❌ Erro de requisição: {e}")
                last_error = str(e)
                return []

            except Exception as e:
                print(f"❌ Erro: {e}")
                last_error = str(e)
                return []

        # 🔥 SE CHEGOU AQUI, TODAS AS TENTATIVAS FALHARAM
        print(f"❌ Todas as {OverpassService.MAX_RETRIES} tentativas falharam")
        raise Exception(last_error or "Overpass API não respondeu após várias tentativas")
