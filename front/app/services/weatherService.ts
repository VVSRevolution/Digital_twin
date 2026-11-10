// app/services/weatherService.ts
import { useNotifications } from '~/composables/useErrorHandler'

export interface ForecastCell {
    latitude: number
    longitude: number
    temperature_2m: number | null
    time: string | null
    isSeasonal?: boolean
    anomaly?: number | null
    trend?: 'above' | 'below' | 'normal' | null
}

export interface ForecastBatchOptions {
    targetDatetime?: string | null
}

interface CacheEntry {
    data: ForecastCell[]
    timestamp: number
}

const CACHE_TTL_MS = 10 * 60 * 1000
const MAX_COORDS_PER_REQUEST = 50

const cache = new Map<string, CacheEntry>()
let inFlight: Promise<ForecastCell[]> | null = null

function makeCacheKey(lats: number[], lons: number[], target: string | null): string {
    const latKey = lats.map(v => v.toFixed(2)).join(',')
    const lonKey = lons.map(v => v.toFixed(2)).join(',')
    return `${latKey}|${lonKey}|${target ?? 'now'}`
}

function parseResults(
    data: any,
    lats: number[],
    lons: number[],
    targetHour: string | null,
    isSeasonal: boolean
): ForecastCell[] {
    const results = Array.isArray(data) ? data : [data]

    return results.map((r: any, i: number) => {
        // 🔥 SAZONAL: média do ensemble + tendência
        if (isSeasonal) {
            const daily = r?.daily
            let value: number | null = null

            if (daily) {
                const keys = Object.keys(daily).filter(k => k.startsWith('temperature_2m_max'))
                const values: number[] = []
                for (const k of keys) {
                    const arr = daily[k]
                    if (Array.isArray(arr) && arr[0] != null) values.push(arr[0])
                }
                if (values.length > 0) {
                    value = values.reduce((a, b) => a + b, 0) / values.length
                }
            }

            let trend: 'above' | 'below' | 'normal' | null = null
            let anomaly: number | null = null

            const rawAnomaly = r?.daily?.temperature_2m_max_anomaly?.[0]
            if (typeof rawAnomaly === 'number') {
                anomaly = rawAnomaly
                trend = rawAnomaly > 0.5 ? 'above' : rawAnomaly < -0.5 ? 'below' : 'normal'
            }

            return {
                latitude: lats[i]!,
                longitude: lons[i]!,
                temperature_2m: value,
                time: null,
                isSeasonal: true,
                anomaly,
                trend
            }
        }

        // 🔥 DETERMINÍSTICO: hora exata
        let temp: number | null = null
        if (r?.hourly?.time && r?.hourly?.temperature_2m && targetHour) {
            const idx = r.hourly.time.indexOf(targetHour)
            if (idx >= 0) temp = r.hourly.temperature_2m[idx]
        } else if (r?.current?.temperature_2m !== undefined) {
            temp = r.current.temperature_2m
        }

        return {
            latitude: lats[i]!,
            longitude: lons[i]!,
            temperature_2m: temp,
            time: targetHour ?? r?.current?.time ?? null,
            isSeasonal: false
        }
    })
}

function buildUrl(
    lats: number[],
    lons: number[],
    targetDatetime: string | null
): { url: string; targetHour: string | null; isSeasonal: boolean; error?: string } {
    const latStr = lats.map(v => v.toFixed(4)).join(',')
    const lonStr = lons.map(v => v.toFixed(4)).join(',')

    // Sem data: previsão atual
    if (!targetDatetime) {
        return {
            url: `https://api.open-meteo.com/v1/forecast?latitude=${latStr}&longitude=${lonStr}&current=temperature_2m&timezone=auto`,
            targetHour: null,
            isSeasonal: false
        }
    }

    const datePart = targetDatetime.split('T')[0]!
    const hourPart = targetDatetime.split('T')[1]?.substring(0, 2) ?? '00'
    const targetHour = `${datePart}T${hourPart}:00`

    const target = new Date(targetDatetime)
    const now = new Date()
    const diffDays = (target.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)

    // Futuro próximo (até 16 dias): determinístico
    if (diffDays >= -1 && diffDays <= 16) {
        return {
            url: `https://api.open-meteo.com/v1/forecast?latitude=${latStr}&longitude=${lonStr}&start_date=${datePart}&end_date=${datePart}&hourly=temperature_2m&timezone=auto`,
            targetHour,
            isSeasonal: false
        }
    }

    // Passado: histórico de previsões (desde ~2021)
    if (diffDays < -1) {
        return {
            url: `https://historical-forecast-api.open-meteo.com/v1/forecast?latitude=${latStr}&longitude=${lonStr}&start_date=${datePart}&end_date=${datePart}&hourly=temperature_2m&timezone=auto`,
            targetHour,
            isSeasonal: false
        }
    }

    // Futuro distante (> 16 dias): sazonal probabilístico
    return {
        url: `https://seasonal-api.open-meteo.com/v1/seasonal?latitude=${latStr}&longitude=${lonStr}&start_date=${datePart}&end_date=${datePart}&daily=temperature_2m_max&timezone=auto`,
        targetHour: null,
        isSeasonal: true
    }
}

export async function fetchForecastBatch(
    lats: number[],
    lons: number[],
    options: ForecastBatchOptions = {}
): Promise<ForecastCell[]> {
    if (lats.length === 0 || lats.length !== lons.length) return []

    // Limita coordenadas por requisição
    if (lats.length > MAX_COORDS_PER_REQUEST) {
        const step = Math.ceil(lats.length / MAX_COORDS_PER_REQUEST)
        lats = lats.filter((_, i) => i % step === 0).slice(0, MAX_COORDS_PER_REQUEST)
        lons = lons.filter((_, i) => i % step === 0).slice(0, MAX_COORDS_PER_REQUEST)
    }

    const target = options.targetDatetime ?? null
    const cacheKey = makeCacheKey(lats, lons, target)

    const cached = cache.get(cacheKey)
    if (cached && Date.now() - cached.timestamp < CACHE_TTL_MS) {
        return cached.data
    }

    if (inFlight) {
        await inFlight
        const after = cache.get(cacheKey)
        if (after && Date.now() - after.timestamp < CACHE_TTL_MS) return after.data
    }

    const { url, targetHour, isSeasonal, error } = buildUrl(lats, lons, target)

    if (error || !url) {
        const { handleError } = useNotifications()
        handleError(error ?? 'Não foi possível consultar a previsão para esta data.')
        return []
    }

    const promise = (async (): Promise<ForecastCell[]> => {
        try {
            const response = await fetch(url)

            if (response.status === 429) {
                const { handleInfo } = useNotifications()
                handleInfo('Muitas requisições à API de previsão. Aguarde um momento.')
                const stale = cache.get(cacheKey)
                return stale ? stale.data : []
            }

            if (!response.ok) {
                let reason = `Erro HTTP ${response.status}`
                try {
                    const errBody = await response.json()
                    if (errBody?.reason) reason = errBody.reason
                } catch { /* ignore */ }
                const { handleError } = useNotifications()
                handleError(`Open-Meteo: ${reason}`)
                return []
            }

            const data = await response.json()
            return parseResults(data, lats, lons, targetHour, isSeasonal)
        } catch (err) {
            const { handleError } = useNotifications()
            handleError(err, 'Erro de rede ao consultar a previsão.')
            return []
        } finally {
            inFlight = null
        }
    })()

    inFlight = promise
    const result = await promise

    if (result.length > 0) {
        cache.set(cacheKey, { data: result, timestamp: Date.now() })
    }

    // 🔥 INFORMA O TIPO DE PREVISÃO
    if (result.length > 0) {
        const { handleInfo } = useNotifications()
        if (isSeasonal) {
            handleInfo('Previsão sazonal (probabilística, 36 km, ensemble SEAS5) — não é previsão determinística.')
        } else if (target && !options.targetDatetime) {
            handleInfo('Previsão atual (Open-Meteo, ~9 km).')
        } else if (target) {
            const diffDays = (new Date(target).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
            if (diffDays < -1) {
                handleInfo('Previsão histórica (o que o modelo previa naquela data).')
            } else {
                handleInfo('Previsão determinística (Open-Meteo, ~9 km).')
            }
        } else {
            handleInfo('Previsão atual (Open-Meteo, ~9 km).')
        }
    }

    return result
}