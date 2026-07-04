// services/eeService.ts

const isProduction = import.meta.env.PROD || import.meta.env.NODE_ENV === 'production'

const API_URL = isProduction
    ? 'http://200.137.197.69:55235'  // Produção
    : 'http://localhost:3001'         // Desenvolvimento

console.log(`🔧 API_URL: ${API_URL} (${isProduction ? 'produção' : 'desenvolvimento'})`)

// ===== TIPOS =====

export interface PixelTemperature {
    lat: number | null
    lon: number | null
    temperature: number
}

export interface BufferStatistics {
    count: number
    mean: number | null
    min: number | null
    max: number | null
    std: number | null
}

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
    error?: string
}

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

export interface ParkGeometry {
    type: 'Polygon' | 'MultiPolygon'
    coordinates: number[][][] | number[][][][]
}

// ===== FUNÇÕES =====

/**
 * Analisa o Park Cooling Island para uma geometria de parque
 * @param geometry - Geometria do parque em GeoJSON (EPSG:4326)
 * @returns Dados do cooling island (PCI, PCD, PCA, buffers)
 */
export async function analyzeParkCooling(
    geometry: ParkGeometry
): Promise<CoolingAnalysisResult> {
    try {
        console.log('📡 Enviando requisição para:', `${API_URL}/park-cooling`)

        const response = await fetch(`${API_URL}/park-cooling`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({geometry}),
        })

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}))
            const errorMsg = errorData?.error || `Erro HTTP ${response.status}: ${response.statusText}`
            const { handleError } = useNotifications()
            handleError(errorMsg, 'Erro ao analisar park cooling')
            return {
                success: false,
                park_lst: null,
                buffers: [],
                pci: null,
                pcd: null,
                pca: null,
                timestamp: new Date().toISOString(),
                error: errorMsg,
            }
        }

        const data = await response.json()
        console.log('✅ Dados recebidos do backend:', data)
        return data as CoolingAnalysisResult

    } catch (error) {
        console.error('❌ Erro ao analisar park cooling:', error)
        const { handleError } = useNotifications()
        const errorMsg = error instanceof Error ? error.message : 'Erro desconhecido'
        handleError(errorMsg, 'Erro ao analisar park cooling')
        return {
            success: false,
            park_lst: null,
            buffers: [],
            pci: null,
            pcd: null,
            pca: null,
            timestamp: new Date().toISOString(),
            error: errorMsg,
        }
    }
}

/**
 * Obtém série temporal de LST para um parque
 * @param geometry - Geometria do parque em GeoJSON (EPSG:4326)
 * @returns Série temporal de LST por data
 */
export async function getParkLSTTimeseries(
    geometry: ParkGeometry
): Promise<TimeseriesResult> {
    try {
        const response = await fetch(`${API_URL}/park-lst-timeseries`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({geometry}),
        })

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}))
            const errorMsg = errorData?.error || `Erro HTTP ${response.status}: ${response.statusText}`
            const { handleError } = useNotifications()
            handleError(errorMsg, 'Erro ao obter série temporal')
            return {
                success: false,
                timeseries: [],
                count: 0,
                timestamp: new Date().toISOString(),
                error: errorMsg,
            }
        }

        const data = await response.json()
        return data as TimeseriesResult

    } catch (error) {
        console.error('❌ Erro ao obter série temporal:', error)
        const { handleError } = useNotifications()
        const errorMsg = error instanceof Error ? error.message : 'Erro desconhecido'
        handleError(errorMsg, 'Erro ao obter série temporal')
        return {
            success: false,
            timeseries: [],
            count: 0,
            timestamp: new Date().toISOString(),
            error: errorMsg,
        }
    }
}

/**
 * Obtém o LST atual para um ponto específico
 * @param lon - Longitude
 * @param lat - Latitude
 * @returns Dados de LST no ponto
 */
export async function getLSTAtPoint(
    lon: number,
    lat: number
): Promise<{
    success: boolean
    kelvin: number | null
    celsius: number | null
    error?: string
}> {
    try {
        const response = await fetch(`${API_URL}/lst-point`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({lon, lat}),
        })

        if (!response.ok) {
            const errorMsg = `Erro HTTP ${response.status}`
            const { handleError } = useNotifications()
            handleError(errorMsg, 'Erro ao obter LST')
            return {
                success: false,
                kelvin: null,
                celsius: null,
                error: errorMsg,
            }
        }

        return await response.json()

    } catch (error) {
        console.error('❌ Erro ao obter LST no ponto:', error)
        const { handleError } = useNotifications()
        const errorMsg = error instanceof Error ? error.message : 'Erro desconhecido'
        handleError(errorMsg, 'Erro ao obter LST')
        return {
            success: false,
            kelvin: null,
            celsius: null,
            error: errorMsg,
        }
    }
}

/**
 * Calcula o PCI (Park Cooling Intensity) a partir dos dados de buffer
 * @param parkLST - LST interno do parque (em Celsius)
 * @param buffers - Lista de buffers com LST (em Celsius)
 * @returns PCI, PCD e PCA
 */
export function calculatePCI(
    parkLST: number,
    buffers: BufferResult[]
): {
    pci: number | null
    pcd: number | null
    pca: { ha: number | null; m2: number | null } | null
} {
    // Validação inicial
    if (parkLST === null || parkLST === undefined || !buffers || buffers.length === 0) {
        return {pci: null, pcd: null, pca: null}
    }

    // Filtra buffers com LST válido (usa Celsius)
    const validBuffers = buffers.filter(
        (b): b is BufferResult & { lst_celsius: number } =>
            b.lst_celsius !== null &&
            b.lst_celsius !== undefined &&
            typeof b.lst_celsius === 'number' &&
            !isNaN(b.lst_celsius)
    )

    if (validBuffers.length < 2) {
        return {pci: null, pcd: null, pca: null}
    }

    let pci: number | null = null
    let pcd: number | null = null
    let pcaHa: number | null = null
    let pcaM2: number | null = null

    for (let i = 1; i < validBuffers.length; i++) {
        const current = validBuffers[i]
        const previous = validBuffers[i - 1]

        if (!current || !previous) continue

        const diff = current.lst_celsius - previous.lst_celsius

        // Ponto de inflexão quando a variação é pequena (< 0.1°C)
        if (diff < 0.1) {
            pci = previous.lst_celsius - parkLST
            pcd = previous.distance
            pcaHa = previous.area_ha
            pcaM2 = previous.area_m2
            break
        }
    }

    // Fallback: usa o último buffer válido
    if (pci === null && validBuffers.length > 0) {
        const last = validBuffers[validBuffers.length - 1]
        if (last) {
            pci = last.lst_celsius - parkLST
            pcd = last.distance
            pcaHa = last.area_ha
            pcaM2 = last.area_m2
        }
    }

    return {
        pci,
        pcd,
        pca: (pcaHa !== null && pcaM2 !== null) ? {ha: pcaHa, m2: pcaM2} : null
    }
}

/**
 * Classifica o tipo de cooling island baseado na curva de LST
 * @param buffers - Lista de buffers com LST
 * @returns Tipo de cooling island
 */
export function classifyCoolingIsland(
    buffers: BufferResult[]
): 'regular' | 'declined' | 'increased' | 'other' {
    // Validação inicial
    if (!buffers || buffers.length < 3) return 'other'

    // Filtra valores válidos (usa Celsius)
    const lsts: number[] = buffers
        .map(b => b.lst_celsius)
        .filter((v): v is number => v !== null && v !== undefined && typeof v === 'number' && !isNaN(v))

    if (lsts.length < 3) return 'other'

    let increases = 0
    let decreases = 0

    for (let i = 1; i < lsts.length; i++) {
        const current = lsts[i]
        const previous = lsts[i - 1]

        if (current === undefined || previous === undefined) continue

        const diff = current - previous

        if (diff > 0.05) increases++
        else if (diff < -0.05) decreases++
    }

    const total = lsts.length - 1
    if (total === 0) return 'other'

    const incRatio = increases / total
    const decRatio = decreases / total

    if (incRatio > 0.6 && decRatio < 0.2) return 'increased'
    if (decRatio > 0.3 && incRatio > 0.3) return 'declined'
    if (incRatio > 0.4 && decRatio > 0.4) return 'regular'

    return 'other'
}

/**
 * Formata dados de cooling island para exibição
 */
export function formatCoolingStats(result: CoolingAnalysisResult): {
    label: string
    value: string
    color: string
}[] {
    if (!result || !result.success || !result.park_lst) {
        return [
            {label: 'Status', value: '❌ Falha na análise', color: '#dc3545'},
        ]
    }

    const pciValue = result.pci ?? 0

    const pciColor =
        pciValue > 3
            ? '#28a745'
            : pciValue > 1.5
                ? '#ffc107'
                : '#6c757d'

    return [
        {
            label: '🌡️ LST do Parque',
            value: `${result.park_lst.celsius?.toFixed(2) ?? 'N/A'}°C`,
            color: '#17a2b8',
        },
        {
            label: '❄️ PCI (Intensidade)',
            value: `${result.pci?.toFixed(2) ?? 'N/A'}°C`,
            color: pciColor,
        },
        {
            label: '📏 PCD (Distância)',
            value: `${result.pcd ?? 'N/A'}m`,
            color: '#28a745',
        },
        {
            label: '📐 PCA (Área)',
            value: `${result.pca?.ha?.toFixed(2) ?? 'N/A'} ha`,
            color: '#6f42c1',
        },
        {
            label: '📊 Buffers Analisados',
            value: `${result.buffers?.length ?? 0}`,
            color: '#6c757d',
        },
    ]
}

/**
 * Utilitário para verificar se um valor é um número válido
 */
export function isValidNumber(value: unknown): value is number {
    return typeof value === 'number' && !isNaN(value) && isFinite(value)
}

/**
 * Utilitário para extrair LST (Celsius) de um buffer com segurança
 */
export function getBufferLSTCelsius(buffer: BufferResult): number | null {
    if (!buffer) return null
    if (buffer.lst_celsius === null || buffer.lst_celsius === undefined) return null
    if (!isValidNumber(buffer.lst_celsius)) return null
    return buffer.lst_celsius
}

/**
 * Utilitário para extrair LST (Kelvin) de um buffer com segurança
 */
export function getBufferLSTKelvin(buffer: BufferResult): number | null {
    if (!buffer) return null
    if (buffer.lst_kelvin === null || buffer.lst_kelvin === undefined) return null
    if (!isValidNumber(buffer.lst_kelvin)) return null
    return buffer.lst_kelvin
}

/**
 * Utilitário para obter o último buffer válido (com LST em Celsius)
 */
export function getLastValidBuffer(buffers: BufferResult[]): BufferResult | null {
    if (!buffers || buffers.length === 0) return null

    for (let i = buffers.length - 1; i >= 0; i--) {
        const buffer = buffers[i]
        if (buffer && buffer.lst_celsius !== null && buffer.lst_celsius !== undefined) {
            return buffer
        }
    }

    return null
}