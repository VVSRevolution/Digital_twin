// services/parkService.ts
import type {ParkGeometry} from "~/types";

export interface SearchParkParams {
    query: string
    city?: string
    country?: string
    osm_id?: number | null
}

export interface SearchParkResult {
    id?: number
    name: string
    city?: string
    country?: string
    geometry: ParkGeometry      // GeoJSON (EPSG:4326)
    geometry_3857: ParkGeometry // GeoJSON (EPSG:3857) - já convertido
    tags?: any
    osm_id?: number
    osm_type?: string
}

export interface SearchParkResponse {
    success?: boolean
    source?: 'database' | 'overpass'
    results: SearchParkResult[]
    error?: string
}
function getApiUrl() {
    if (import.meta.client) {
        try {
            const { getApiUrl } = useApiConfig()
            return getApiUrl()
        } catch (e) {
            const config = useRuntimeConfig()
            return config.public.apiUrl || 'http://localhost:3001'
        }
    }
    const config = useRuntimeConfig()
    return config.public.apiUrl || 'http://localhost:3001'
}
/**
 * Busca parques no backend (que consulta DB + Overpass)
 */
export async function searchPark(params: SearchParkParams): Promise<SearchParkResponse> {
    const {handleError} = useNotifications()

    try {
        const response = await fetch(`${getApiUrl()}/api/park/search`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                query: params.query,
                city: params.city || '',
                country: params.country || 'Brasil',
                osm_id: params.osm_id || null
            })
        })

        const data = await response.json()

        // 🔥 SE A RESPOSTA NÃO FOR SUCESSO
        if (!response.ok || data.success === false) {
            const errorMsg = data.error || 'Erro ao buscar parque'
            handleError(errorMsg)
            return {
                success: false,
                results: [],
                error: errorMsg
            }
        }

        return {
            success: true,
            source: data.source || 'overpass',
            results: data.results || [],
            error: data.error
        }

    } catch (error) {
        console.error('❌ Erro ao buscar parque:', error)
        const errorMsg = error instanceof Error ? error.message : 'Erro desconhecido'
        handleError(errorMsg)
        return {
            success: false,
            results: [],
            error: errorMsg
        }
    }
}
