// front/app/services/satelliteService.ts
import {API_URL} from './eeService'

export interface Satellite {
    id: string
    name: string
    platform: string
    sensor: string
    band_thermal: string
    resolution: number
    description: string
    active: boolean
    collection: string
}

/**
 * Busca a lista de satélites disponíveis no backend
 */
export async function fetchSatellites(): Promise<Satellite[]> {
    try {
        const url = `${API_URL}/api/satellites`
        console.log('📡 Buscando satélites:', url)

        const response = await fetch(url)

        if (!response.ok) {
            console.error('❌ Erro ao buscar satélites:', response.status)
            return getDefaultSatellites()
        }

        const data = await response.json()

        if (data.success && data.satellites) {

            console.log('✅ Satélites carregados:', data.satellites.length, data.satellites)
            return data.satellites
        }

        return getDefaultSatellites()

    } catch (error) {
        console.error('❌ Erro ao buscar satélites:', error)
        return getDefaultSatellites()
    }
}

/**
 * Satélites padrão (fallback)
 */
function getDefaultSatellites(): Satellite[] {
    return [
        {
            id: 'LANDSAT_8',
            name: 'Landsat 8',
            platform: 'Landsat',
            sensor: 'OLI/TIRS',
            band_thermal: 'Band 10',
            resolution: 30,
            description: 'Landsat 8 OLI/TIRS',
            active: true,
            collection: 'LANDSAT/LC08/C02/T1_L2'
        },
        {
            id: 'LANDSAT_9',
            name: 'Landsat 9',
            platform: 'Landsat',
            sensor: 'OLI-2/TIRS-2',
            band_thermal: 'Band 10',
            resolution: 30,
            description: 'Landsat 9 OLI-2/TIRS-2',
            active: true,
            collection: 'LANDSAT/LC09/C02/T1_L2'
        }
    ]
}