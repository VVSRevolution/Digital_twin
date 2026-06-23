import * as turf from "@turf/turf"
import GeoJSON from "ol/format/GeoJSON"

export type OSMPlace = {
    lon: string
    lat: string
    display_name: string
}

export function convertParkToFeature(element: any) {
    const coords = element.geometry.map((p: any) => [
        p.lon,
        p.lat
    ])

    const geojson = {
        type: "Feature",
        geometry: {
            type: "Polygon",
            coordinates: [coords]
        },
        properties: {
            name: element.tags?.name
        }
    }

    return new GeoJSON().readFeature(geojson, {
        featureProjection: "EPSG:3857"
    })
}

// 🔎 busca OSM
export async function searchOSM(query: string): Promise<OSMPlace[]> {
    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`

    const res = await fetch(url)
    return await res.json()
}

// 📍 ponto (sem tipo chato)
export function createPoint(lon: number, lat: number) {
    return turf.point([lon, lat])
}

// 📐 buffer (CORRETO sem Feature genérico)
export function createBuffer(point: any, distance = 500) {
    return turf.buffer(point, distance, {units: "meters"})
}