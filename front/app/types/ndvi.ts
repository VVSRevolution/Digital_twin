// types/ndvi.ts

export interface NDVIPixel {
    lat: number
    lon: number
    ndvi: number
}

export interface NDVIBuffer {
    distance: number
    buffer_index: number
    pixels: NDVIPixel[]
    statistics: {
        count: number
        mean: number | null
        min: number | null
        max: number | null
        std: number | null
    }
}

export interface NDVIMetadata {
    id: number
    park_id: number
    satellite_name: string
    image_date: string
    created_at: string | null
}

// 🔥 RESPOSTA DO ENDPOINT /list
export interface NDVIListResponse {
    success: boolean
    park_id: number
    park_name: string
    count: number
    dates: string[]
    metadata: NDVIMetadata[]
    error?: string
}

// 🔥 RESPOSTA DO ENDPOINT /latest
export interface NDVILatestResponse {
    success: boolean
    image_date: string
    satellite_name: string
    ndvi: NDVIBuffer[]
    total_pixels: number
    statistics: {
        mean: number | null
        min: number | null
        max: number | null
    } | null
    error?: string
}

// 🔥 RESPOSTA DO ENDPOINT /<date>
export interface NDVIDetailResponse {
    success: boolean
    image_date: string
    satellite_name: string
    ndvi: NDVIBuffer[]
    total_pixels: number
    statistics: {
        mean: number | null
        min: number | null
        max: number | null
    } | null
    requested_date?: string
    error?: string
}