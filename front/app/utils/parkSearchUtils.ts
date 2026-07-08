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
    const parts = dateStr.split('T')[0].split('-')
    if (parts.length === 3) {
      const [year, month, day] = parts
      return `${day}/${month}/${year}`
    }
    return dateStr
  } catch (e) {
    return dateStr
  }
}
