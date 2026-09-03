//services/eeService.ts
import {useNotifications} from '~/composables/useErrorHandler'
import type {CoolingAnalysisResult, ParkGeometry, ParkListResponse, SearchParkResult,} from '~/types'

function getApiUrl() {
    // No cliente, usa o composable
    if (import.meta.client) {
        const {getApiUrl} = useApiConfig()
        return getApiUrl()
    }
    // No servidor, fallback
    const config = useRuntimeConfig()
    return config.public.apiUrl || 'http://localhost:3001'
}

// ============================================================
// 🔥 FUNÇÕES DE DELETE
// ============================================================

/**
 * Deleta um parque e todas as suas análises
 */
export async function deletePark(parkId: number): Promise<{
    success: boolean
    message?: string
    park_id?: number
    park_name?: string
    analyses_deleted?: number
    error?: string
}> {
    try {
        const API_URL = getApiUrl()
        const response = await fetch(`${API_URL}/api/parks/${parkId}`, {
            method: 'DELETE'
        })
        return await response.json()
    } catch (error) {
        console.error('❌ Erro ao deletar parque:', error)
        return {success: false, error: String(error)}
    }
}

/**
 * Deleta todas as análises de um parque
 */
export async function deleteAllAnalyses(parkId: number): Promise<{
    success: boolean
    message?: string
    park_id?: number
    park_name?: string
    analyses_deleted?: number
    error?: string
}> {
    try {
        const API_URL = getApiUrl()
        const response = await fetch(`${API_URL}/api/parks/${parkId}/analyses`, {
            method: 'DELETE'
        })
        return await response.json()
    } catch (error) {
        console.error('❌ Erro ao deletar análises:', error)
        return {success: false, error: String(error)}
    }
}

/**
 * Deleta uma análise específica
 */
export async function deleteAnalysis(parkId: number, analysisId: number): Promise<{
    success: boolean
    message?: string
    analysis_id?: number
    park_id?: number
    park_name?: string
    error?: string
}> {
    try {
        const API_URL = getApiUrl()
        const response = await fetch(`${API_URL}/api/parks/${parkId}/analyses/${analysisId}`, {
            method: 'DELETE'
        })
        return await response.json()
    } catch (error) {
        console.error('❌ Erro ao deletar análise:', error)
        return {success: false, error: String(error)}
    }
}

// ============================================================
// 🔥 FUNÇÕES EXISTENTES
// ============================================================

/**
 * Analisa o Park Cooling Island para uma geometria de parque
 */
export async function analyzeParkCooling(
    geometry: ParkGeometry,
    metadata: Partial<SearchParkResult>
): Promise<CoolingAnalysisResult> {
    try {
        const API_URL = getApiUrl()
        console.log('📡 Enviando requisição para:', `${API_URL}/api/park/analyze`, geometry, metadata)
        const payload: any = {
            geometry: geometry,
            ...metadata
        }

        const response = await fetch(`${API_URL}/api/park/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        })

        const data = await response.json()
        console.log('✅ Dados recebidos do backend:', data)
        return data as CoolingAnalysisResult

    } catch (error) {
        const {handleError} = useNotifications()
        handleError(error, 'Erro ao analisar park cooling')
        return {success: false, error: String(error)}
    }
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

// ============================================================
// 🔥 PARQUES
// ============================================================

/**
 * Busca a lista de parques disponíveis no banco
 */
export async function getParks(): Promise<ParkListResponse> {
    try {
        const API_URL = getApiUrl()

        const response = await fetch(`${API_URL}/api/parks`)

        if (!response.ok) {
            throw new Error(`Erro HTTP ${response.status}`)
        }

        const data = await response.json()
        console.log('📋 Parques recebidos:', data)

        if (data.success && data.parks) {
            data.parks = data.parks.map((p: any) => ({
                ...p,
                geometry: p.geometry || null,
                geometry_3857: p.geometry_3857 || null
            }))
        }

        return data

    } catch (error) {
        console.error('❌ Erro ao buscar parques:', error)
        return {success: false, count: 0, parks: []}
    }
}

/**
 * Busca as análises de um parque específico
 */
export async function getParkAnalyses(parkId: number): Promise<CoolingAnalysisResult> {
    try {
        const API_URL = getApiUrl()

        const response = await fetch(`${API_URL}/api/parks/${parkId}/analyses`)
        const data = await response.json()

        if (data.success) {
            return data
        }

        return {success: false, error: data.error}
    } catch (error) {
        return {success: false, error: String(error)}
    }
}

export async function getParkAnalysesList(parkId: number): Promise<CoolingAnalysisResult[]> {
    try {
        const API_URL = getApiUrl()

        const response = await fetch(`${API_URL}/api/parks/${parkId}/analyses/list`)
        const {handleError} = useNotifications()
        if (!response.ok) {
            handleError(`❌ Erro ao buscar análises: ${response.status}`)
            return []
        }
        const data = await response.json()
        if (!data.success || !data.analyses) {
            return []
        }
        return data.analyses

    } catch (error) {
        const {handleError} = useNotifications()
        handleError('❌ Erro ao buscar lista de análises:', String(error))
        console.error('❌ Erro ao buscar lista de análises:', error)
        return []
    }
}

export async function getParkAnalysisDetail(parkId: number, analysisId: number): Promise<CoolingAnalysisResult | null> {
    try {
        const API_URL = getApiUrl()

        const response = await fetch(`${API_URL}/api/parks/${parkId}/analyses/${analysisId}`)

        if (!response.ok) {
            console.error(`❌ Erro ao buscar detalhe da análise: ${response.status}`)
            return null
        }

        const data = await response.json()
        console.log(`📥 Detalhe da análise ${analysisId}:`, data)

        if (!data.success) {
            return null
        }

        return data

    } catch (error) {
        console.error('❌ Erro ao buscar detalhe da análise:', error)
        return null
    }
}

/**
 * Busca detalhes de um parque específico
 */
export async function getParkDetail(parkId: number): Promise<{
    success: boolean;
    park?: any;
    error?: string;
}> {
    try {
        const API_URL = getApiUrl()

        const response = await fetch(`${API_URL}/api/parks/${parkId}`)

        if (!response.ok) {
            throw new Error(`Erro HTTP ${response.status}`)
        }

        return await response.json()

    } catch (error) {
        console.error('❌ Erro ao buscar parque:', error)
        return {success: false, error: String(error)}
    }
}