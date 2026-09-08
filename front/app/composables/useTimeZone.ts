// composables/useTimeZone.ts
import { format, parseISO } from 'date-fns'
import { fromZonedTime, toZonedTime } from 'date-fns-tz'

/**
 * Composable para conversões de fuso horário
 *
 * O backend sempre envia/recebe UTC
 * O frontend exibe em hora LOCAL
 */
export function useTimeZone() {
    const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone

    /**
     * LOCAL → UTC (para enviar ao backend)
     * Ex: '2026-09-01T01:00' → '2026-09-01T04:00:00.000Z'
     */
    function localToUTC(localString: string): string {
        const utcDate = fromZonedTime(localString, timeZone)
        return utcDate.toISOString()
    }

    /**
     * UTC → LOCAL (para exibir no input)
     * Ex: '2026-09-01T04:00:00.000Z' → '2026-09-01T01:00'
     */
    function utcToLocal(utcString: string): string {
        const date = parseISO(utcString)
        const localDate = toZonedTime(date, timeZone)
        return format(localDate, "yyyy-MM-dd'T'HH:mm")
    }

    /**
     * UTC → LOCAL (para exibir data formatada)
     * Ex: '2026-09-01T04:00:00.000Z' → '01/09/2026 01:00'
     */
    function utcToLocalFormatted(utcString: string, formatStr: string = "dd/MM/yyyy HH:mm"): string {
        const date = parseISO(utcString)
        const localDate = toZonedTime(date, timeZone)
        return format(localDate, formatStr)
    }

    /**
     * LOCAL → UTC (sem converter, apenas valida se está em UTC)
     */
    function isUTC(dateString: string): boolean {
        return dateString.includes('Z') || dateString.includes('+')
    }

    /**
     * Formata data local para exibição
     */
    function formatLocal(date: Date, formatStr: string = "dd/MM/yyyy HH:mm"): string {
        return format(date, formatStr)
    }

    return {
        timeZone,
        localToUTC,
        utcToLocal,
        utcToLocalFormatted,
        isUTC,
        formatLocal
    }
}