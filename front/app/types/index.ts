// Tipos de busca OSM
export type OSMPlace = {
    lon: string
    lat: string
    display_name: string
}

// Tipos de parque
export type OSMElement = {
    id: number
    lat: number
    lon: number
    tags?: {
        name?: string
        [key: string]: unknown
    }
    geometry?: Array<{ lat: number; lon: number }>
}

export type SearchResult = {
    elements: OSMElement[]
}

// Tipos de geometria
export type ParkGeometry = {
    type: 'Polygon' | 'MultiPolygon'
    coordinates: number[][][] | number[][][][]
}

// Tipos de temperatura
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

// Tipos de resultado de análise de cooling
export interface CoolingAnalysisResult {
    success: boolean
    park_lst: {
        kelvin: number | null
        celsius: number | null
    } | null
    buffers: BufferResult[]
    pci: number | null      // Park Cooling Intensity (em Celsius)
    pcd: number | null      // Park Cooling Distance (metros)
    pca: {
        ha: number | null
        m2: number | null
    } | null
    timestamp: string
    image_date?: string
    num_buffers?: number
    buffer_distance?: number
    error?: string
}

// Tipos de série temporal
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

// Tipo de classificação de cooling island
export type CoolingIslandType = 'regular' | 'declined' | 'increased' | 'other'

// Tipo de notificação
export interface Notification {
    id: string
    message: string
    type: 'error' | 'success' | 'info'
    duration?: number
    closable: boolean
}
