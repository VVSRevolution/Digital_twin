// services/eeService.ts

const API_URL = 'http://localhost:3001'

// ===== TIPOS =====

export interface BufferResult {
    distance: number
    lst: number | null
    area: number
}

export interface CoolingAnalysisResult {
    success: boolean
    park_lst: number | null
    buffers: BufferResult[]
    pci: number | null      // Park Cooling Intensity
    pcd: number | null      // Park Cooling Distance (metros)
    pca: number | null      // Park Cooling Area (hectares)
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
        const response = await fetch(`${API_URL}/park-cooling`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({geometry}),
        })

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}))
            throw new Error(
                errorData?.error || `Erro HTTP ${response.status}: ${response.statusText}`
            )
        }

        const data = await response.json()
        return data as CoolingAnalysisResult
    } catch (error) {
        console.error('❌ Erro ao analisar park cooling:', error)
        return {
            success: false,
            park_lst: null,
            buffers: [],
            pci: null,
            pcd: null,
            pca: null,
            timestamp: new Date().toISOString(),
            error: error instanceof Error ? error.message : 'Erro desconhecido',
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
            throw new Error(
                errorData?.error || `Erro HTTP ${response.status}: ${response.statusText}`
            )
        }

        const data = await response.json()
        return data as TimeseriesResult
    } catch (error) {
        console.error('❌ Erro ao obter série temporal:', error)
        return {
            success: false,
            timeseries: [],
            count: 0,
            timestamp: new Date().toISOString(),
            error: error instanceof Error ? error.message : 'Erro desconhecido',
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
            throw new Error(`Erro HTTP ${response.status}`)
        }

        return await response.json()
    } catch (error) {
        console.error('❌ Erro ao obter LST no ponto:', error)
        return {
            success: false,
            kelvin: null,
            celsius: null,
            error: error instanceof Error ? error.message : 'Erro desconhecido',
        }
    }
}

/**
 * Calcula o PCI (Park Cooling Intensity) a partir dos dados de buffer
 * @param parkLST - LST interno do parque
 * @param buffers - Lista de buffers com LST
 * @returns PCI, PCD e PCA
 */
export function calculatePCI(
    parkLST: number,
    buffers: BufferResult[]
): {
    pci: number | null
    pcd: number | null
    pca: number | null
} {
    // 🔥 VALIDAÇÃO INICIAL
    if (parkLST === null || parkLST === undefined || !buffers || buffers.length === 0) {
        return {pci: null, pcd: null, pca: null}
    }

    // 🔥 FILTRA buffers com LST válido
    const validBuffers = buffers.filter(b => b.lst !== null && b.lst !== undefined) as BufferResult[]

    if (validBuffers.length < 2) {
        return {pci: null, pcd: null, pca: null}
    }

    // Encontra o primeiro ponto de inflexão (variação < 0.1°C)
    let pci: number | null = null
    let pcd: number | null = null
    let pca: number | null = null

    for (let i = 1; i < validBuffers.length; i++) {
        // 🔥 GARANTE QUE OS VALORES EXISTEM
        const current = validBuffers[i]
        const previous = validBuffers[i - 1]

        if (!current || !previous) continue
        if (current.lst === null || current.lst === undefined) continue
        if (previous.lst === null || previous.lst === undefined) continue

        const diff = current.lst - previous.lst

        // Ponto de inflexão quando a variação é pequena
        if (diff < 0.1) {
            pci = previous.lst - parkLST
            pcd = previous.distance
            pca = previous.area
            break
        }
    }

    // Se não encontrou, usa o último buffer válido
    if (pci === null && validBuffers.length > 0) {
        const last = validBuffers[validBuffers.length - 1]

        // 🔥 VERIFICA SE O ÚLTIMO BUFFER É VÁLIDO
        if (last && last.lst !== null && last.lst !== undefined) {
            pci = last.lst - parkLST
            pcd = last.distance
            pca = last.area
        }
    }

    return {pci, pcd, pca}
}

/**
 * Classifica o tipo de cooling island baseado na curva de LST
 * @param buffers - Lista de buffers com LST
 * @returns Tipo de cooling island
 */
export function classifyCoolingIsland(
    buffers: BufferResult[]
): 'regular' | 'declined' | 'increased' | 'other' {
    // 🔥 VALIDAÇÃO INICIAL
    if (!buffers || buffers.length < 3) return 'other'

    // 🔥 FILTRA VALORES VÁLIDOS (garante que são números)
    const lsts: number[] = buffers
        .map(b => b.lst)
        .filter((v): v is number => v !== null && v !== undefined && typeof v === 'number' && !isNaN(v))

    if (lsts.length < 3) return 'other'

    // Verifica tendência geral
    let increases = 0
    let decreases = 0

    // 🔥 PERCORRE COM ÍNDICE E VERIFICA CADA ACESSO
    for (let i = 1; i < lsts.length; i++) {
        // 🔥 GARANTE QUE OS VALORES EXISTEM
        const current = lsts[i]
        const previous = lsts[i - 1]

        // 🔥 VERIFICA SE EXISTEM ANTES DE USAR
        if (current === undefined || previous === undefined) continue

        const diff = current - previous

        if (diff > 0.05) increases++
        else if (diff < -0.05) decreases++
    }

    // Classifica
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
    if (!result || !result.success || result.park_lst === null || result.park_lst === undefined) {
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
            value: `${result.park_lst.toFixed(2)}°C`,
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
            value: `${result.pca?.toFixed(2) ?? 'N/A'} ha`,
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
 * Utilitário para extrair LST de um buffer com segurança
 */
export function getBufferLST(buffer: BufferResult): number | null {
    if (!buffer) return null
    if (buffer.lst === null || buffer.lst === undefined) return null
    if (!isValidNumber(buffer.lst)) return null
    return buffer.lst
}

/**
 * Utilitário para obter o último buffer válido
 */
export function getLastValidBuffer(buffers: BufferResult[]): BufferResult | null {
    if (!buffers || buffers.length === 0) return null

    for (let i = buffers.length - 1; i >= 0; i--) {
        const buffer = buffers[i]
        if (buffer && buffer.lst !== null && buffer.lst !== undefined) {
            return buffer
        }
    }

    return null
}