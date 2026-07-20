/**
 * Utilidades para o sistema de busca de parques
 */

export function debounce<T extends (...args: any[]) => any>(fn: T, delay: number = 400): (...args: Parameters<T>) => void {
    let timeoutId: ReturnType<typeof setTimeout> | null = null
    return (...args: Parameters<T>) => {
        if (timeoutId) clearTimeout(timeoutId)
        timeoutId = setTimeout(() => fn(...args), delay)
    }
}

export function formatDate(dateStr: string): string {
    if (!dateStr) return 'N/A'

    try {
        // Verifica se tem Z (UTC)
        const isUTC = dateStr.includes('Z')

        // Limpa a string
        let clean = dateStr
            .replace('Z', '')
            .replace('T', ' ')
            .split('.')[0]

        // 🔥 VALIDA SE TEM DATA
        if (!clean) return dateStr

        const parts = clean.split(' ')
        const datePart = parts[0]
        const timePart = parts[1]

        // 🔥 VALIDA SE TEM DATA
        if (!datePart) return dateStr

        const dateParts = datePart.split('-')
        if (dateParts.length < 3) return dateStr

        const [year, month, day] = dateParts
        const [hour, minute] = timePart?.split(':') || ['00', '00']

        // 🔥 VALIDA SE YEAR, MONTH, DAY SÃO VÁLIDOS
        if (!year || !month || !day) return dateStr

        const utcSuffix = isUTC ? ' (UTC)' : ''

        return `${day}/${month}/${year} ${hour}:${minute}h${utcSuffix}`

    } catch (e) {
        return dateStr
    }
}