// services/sensorService.ts
import type {SensorData} from '~/types'

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


export async function getSensors(datetime?: string): Promise<{
    success: boolean
    count: number
    sensors: SensorData[]
}> {
    try {
        let url = `${getApiUrl()}/api/sensors`
        if (datetime) {
            url += `?datetime=${encodeURIComponent(datetime)}`
        }

        const response = await fetch(url)
        return await response.json()
    } catch (error) {
        console.error('❌ Erro ao buscar sensores:', error)
        return { success: false, count: 0, sensors: [] }
    }
}
