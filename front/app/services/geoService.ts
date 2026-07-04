import * as turf from "@turf/turf"
import GeoJSON from "ol/format/GeoJSON";

export type OSMPlace = {
    lon: string
    lat: string
    display_name: string
}

const format = new GeoJSON()


export function convertParkToFeature(element: any) {
    const coords = element.geometry.map((p: any) => [
        Number(p.lon),
        Number(p.lat)
    ])

    // garante que o polígono está fechado
    const first = coords[0]
    const last = coords[coords.length - 1]

    if (first[0] !== last[0] || first[1] !== last[1]) {
        coords.push([...first])
    }

    return format.readFeature(
        {
            type: "Feature",
            geometry: {
                type: "Polygon",
                coordinates: [coords]
            },
            properties: {
                name: element.tags?.name
            }
        },
        {
            dataProjection: "EPSG:4326",
            featureProjection: "EPSG:3857"
        }
    )
}

// 🔎 busca OSM
export async function searchOSM(query: string): Promise<OSMPlace[]> {
    try {
        const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`
        const res = await fetch(url)

        if (!res.ok) {
            const errorMsg = `Erro HTTP ${res.status}: ${res.statusText}`
            const {handleError} = useNotifications()
            handleError(errorMsg, 'Erro ao buscar local')
            return []
        }

        return await res.json()
    } catch (error) {
        console.error('❌ Erro ao buscar OSM:', error)
        const {handleError} = useNotifications()
        const errorMsg = error instanceof Error ? error.message : 'Erro desconhecido'
        handleError(errorMsg, 'Erro ao buscar local')
        return []
    }
}

// 📍 ponto (sem tipo chato)
export function createPoint(lon: number, lat: number) {
    return turf.point([lon, lat])
}

// 📐 buffer (CORRETO sem Feature genérico)
export function createBuffer(point: any, distance = 500) {
    return turf.buffer(point, distance, {units: "meters"})
}