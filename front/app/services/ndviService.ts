// services/ndviService.ts
import type { NDVIListResponse, NDVILatestResponse, NDVIDetailResponse, NDVIMetadata } from '~/types/ndvi'

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
 * Busca a lista de datas disponíveis de NDVI para um parque
 */
export async function getNdviList(parkId: number): Promise<NDVIListResponse> {
    try {
        const url = `${getApiUrl()}/api/parks/${parkId}/ndvi/list`
        const response = await fetch(url)
        const data = await response.json()

        return data
    } catch (error) {
        console.error('❌ Erro ao buscar lista NDVI:', error)
        return {
            success: false,
            park_id: parkId,
            park_name: '',
            count: 0,
            dates: [],
            metadata: [],
            error: 'Erro ao buscar lista de NDVI'
        }
    }
}

/**
 * Busca o NDVI mais recente de um parque
 */
export async function getLatestNdvi(parkId: number): Promise<NDVILatestResponse> {
    try {
        const url = `${getApiUrl()}/api/parks/${parkId}/ndvi/latest`
        const response = await fetch(url)
        const data = await response.json()

        return data
    } catch (error) {
        console.error('❌ Erro ao buscar NDVI mais recente:', error)
        return {
            success: false,
            image_date: '',
            satellite_name: '',
            ndvi: [],
            total_pixels: 0,
            statistics: null,
            error: 'Erro ao buscar NDVI mais recente'
        }
    }
}

/**
 * Busca NDVI por data específica
 */
export async function getNdviByDate(parkId: number, date: string): Promise<NDVIDetailResponse> {
    try {
        const url = `${getApiUrl()}/api/parks/${parkId}/ndvi/${encodeURIComponent(date)}`
        const response = await fetch(url)
        const data = await response.json()

        return data
    } catch (error) {
        console.error('❌ Erro ao buscar NDVI por data:', error)
        return {
            success: false,
            image_date: '',
            satellite_name: '',
            ndvi: [],
            total_pixels: 0,
            statistics: null,
            error: 'Erro ao buscar NDVI por data'
        }
    }
}