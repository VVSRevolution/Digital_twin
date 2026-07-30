import GeoJSON from "ol/format/GeoJSON"
import type Feature from 'ol/Feature'
import type Geometry from 'ol/geom/Geometry'
import type {OSMElement, ParkGeometry} from '~/types'
import {fromLonLat} from "ol/proj";

const format = new GeoJSON()
const DEFAULT_PROJECTIONS = {
    dataProjection: "EPSG:4326",
    featureProjection: "EPSG:3857"
} as const

type FeatureProjectionOptions = Partial<typeof DEFAULT_PROJECTIONS>

function isLatLonGeometry(
    geometry: OSMElement['geometry']
): geometry is Array<{ lat: number; lon: number }> {
    return Array.isArray(geometry)
}

function closePolygonRing(coordinates: number[][]): number[][] {
    const first = coordinates[0]
    const last = coordinates[coordinates.length - 1]

    if (first && last && (first[0] !== last[0] || first[1] !== last[1])) {
        coordinates.push([...first])
    }

    return coordinates
}

function getFeatureGeometry(element: OSMElement): ParkGeometry {
    const geometry = element.geometry

    if (!geometry) {
        throw new Error('Parque encontrado sem geometria')
    }

    if (isLatLonGeometry(geometry)) {
        const coordinates = closePolygonRing(
            geometry.map((point) => [Number(point.lon), Number(point.lat)])
        )

        return {
            type: "Polygon",
            coordinates: [coordinates]
        }
    }

    return geometry
}


export function convertParkToFeature(element: any): Feature<Geometry> {
    // 🔥 USA geometry (NÃO geometry_3857)
    let geometry = element.geometry

    if (!geometry) {
        throw new Error('Elemento sem geometria')
    }

    // 🔥 SE FOR GEOJSON, USA DIRETO
    if (geometry.type && geometry.coordinates) {
        // Se for 4326, converte para 3857
        if (geometry.type === 'Polygon' && geometry.coordinates) {
            const coords3857 = geometry.coordinates.map((ring: any[]) =>
                ring.map((coord: number[]) => fromLonLat(coord))
            )
            geometry = {
                type: geometry.type,
                coordinates: coords3857
            }
        }
    }

    return format.readFeature(
        {
            type: "Feature",
            geometry: geometry,
            properties: {
                name: element.tags?.name || element.name || 'Parque sem nome'
            }
        },
        {
            dataProjection: "EPSG:3857",
            featureProjection: "EPSG:3857"
        }
    ) as Feature<Geometry>
}


