// ============================================================
// 🔥 TIPOS EXISTENTES
// ============================================================

// Tipos de busca OSM
export type OSMPlace = {
    lon: string
    lat: string
    display_name: string
}

// Tipos de parque
export type OSMElement = {
    id: number | string
    lat?: number
    lon?: number
    name?: string
    osm_id?: number | string | null
    osm_type?: string | null
    city?: string | null
    country?: string | null
    tags?: {
        name?: string
        [key: string]: unknown
    }
    geometry?: Array<{ lat: number; lon: number }> | ParkGeometry | null
}

export type SearchResult = {
    elements: OSMElement[]
}

export type SearchParkResponse = {
    source?: string
    results: OSMElement[]
    elements: OSMElement[]
}

// Tipos de geometria
export type ParkGeometry = {
    type: 'Polygon' | 'MultiPolygon'
    coordinates: number[][][] | number[][][][]
}

// ============================================================
// 🔥 PARK (UNIFICADO)
// ============================================================

/**
 * Parque completo do banco de dados
 * UNIFICA OSMElement + dados do banco
 */
export interface Park {
    id: number
    name: string
    osm_id: number | null
    osm_type: string | null
    city: string
    country: string
    area_ha: number | null
    geometry: ParkGeometry | null
    geometry_3857: ParkGeometry | null
    tags: {
        name?: string
        leisure?: string
        wikidata?: string
        wikipedia?: string
        [key: string]: string | undefined
    }
    created_at: string
    updated_at: string
}

/**
 * Resultado de busca de parque (UNIFICA OSMElement + Park)
 * Usado para: search, select, list
 */
export interface SearchParkResult {
    id?: number
    name: string
    city?: string
    country?: string
    osm_id?: number
    osm_type?: string
    geometry: ParkGeometry
    geometry_3857?: ParkGeometry
    tags?: Park['tags']
    area_ha?: number
    lat?: number
    lon?: number
    display_name?: string
}

// ============================================================
// 🔥 TEMPERATURA E BUFFERS
// ============================================================

export interface PixelTemperature {
    lat: number | null
    lon: number | null
    temperature: number
}

// Tipos de estatísticas de buffer
export interface BufferStatistics {
    count: number
    mean: number | null
    min: number | null
    max: number | null
    std: number | null
}

// Tipos de resultado de buffer
export interface BufferResult {
    distance: number
    distance_prev: number
    buffer_index: number
    pixels: PixelTemperature[]
    statistics: BufferStatistics
    area_ha: number
    area_m2: number
    lst_celsius: number | null
    lst_kelvin: number | null
}

// ============================================================
// 🔥 ANÁLISE
// ============================================================

export interface CoolingAnalysisResult {
    success: boolean
    park_id?: number
    park_name?: string
    analysis_id?: number
    image_date?: string
    analyzed_at?: string
    satellite_name?: string
    num_buffers?: number
    buffer_distance?: number
    ditto_updated?: boolean
    park_lst?: {
        kelvin: number
        celsius: number
    }
    buffers?: BufferResult[]
    pci?: number
    pcd?: number
    pca?: {
        ha: number
        m2: number
    }
    total_pixels?: number
    timestamp?: string
    error?: string
}

// ============================================================
// 🔥 RESPOSTAS DA API
// ============================================================

export interface ParkListResponse {
    success: boolean
    count: number
    parks: Park[]
}

export interface ParkDetailResponse {
    success: boolean
    park: Park
}

// ============================================================
// 🔥 SÉRIE TEMPORAL
// ============================================================

export interface TimeseriesPoint {
    date: string
    lst: number | null
}

export interface TimeseriesResult {
    success: boolean
    timeseries: TimeseriesPoint[]
    count: number
    timestamp: string
    error?: string
}

// ============================================================
// 🔥 CLASSIFICAÇÃO
// ============================================================

export type CoolingIslandType = 'regular' | 'declined' | 'increased' | 'other'

// ============================================================
// 🔥 NOTIFICAÇÃO
// ============================================================

export interface Notification {
    id: string
    message: string
    type: 'error' | 'success' | 'info'
    duration?: number
    closable: boolean
}

// ============================================================
// 🔥 FUNÇÕES AUXILIARES
// ============================================================

/**
 * Converte Park para SearchParkResult
 */
export function parkToSearchResult(park: Park): SearchParkResult {
    return {
        id: park.id,
        name: park.name,
        city: park.city,
        country: park.country,
        osm_id: park.osm_id || Number(park.id),
        osm_type: park.osm_type || 'relation',
        geometry: park.geometry!,
        geometry_3857: park.geometry_3857 || undefined,
        tags: park.tags || {name: park.name},
        area_ha: park.area_ha || undefined
    }
}

/**
 * Converte OSMElement para SearchParkResult
 */
export function osmToSearchResult(element: OSMElement): SearchParkResult {
    const geometry = element.geometry as ParkGeometry

    return {
        id: Number(element.id),
        name: element.name || element.tags?.name || 'Parque sem nome',
        city: element.city || undefined,
        country: element.country || undefined,
        osm_id: Number(element.osm_id || element.id),
        osm_type: element.osm_type || 'relation',
        geometry: geometry || {type: 'Polygon', coordinates: []},
        tags: element.tags as Park['tags'],
        lat: element.lat,
        lon: element.lon
    }
}