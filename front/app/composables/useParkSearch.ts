import { ref } from 'vue'
import { useNotifications } from '~/composables/useErrorHandler'
import type { ParkSuggestion } from '@/types/parkSearch'

export function useParkSearch() {
  const { handleError, handleSuccess, handleInfo } = useNotifications()

  const parkSuggestions = ref<ParkSuggestion[]>([])
  const showParkSuggestions = ref(false)
  const parkCache = new Map<string, ParkSuggestion[]>()

  async function searchParks(query: string, countryCode: string): Promise<ParkSuggestion[]> {
    if (!query || query.length < 2) return []

    const cacheKey = `${query.toLowerCase()}_${countryCode}`
    if (parkCache.has(cacheKey)) return parkCache.get(cacheKey) || []

    try {
      const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&addressdetails=1&countrycodes=${countryCode}&limit=15`
      const response = await fetch(url, {
        headers: { 'User-Agent': 'DigitalTwinApp/1.0' }
      })

      if (response.status === 429) {
        handleInfo('Muitas requisições. Aguarde um momento...')
        return []
      }

      if (!response.ok) throw new Error(`Erro HTTP: ${response.status}`)

      const data = await response.json()

      const results = data
          .filter((item: any) => {
            const displayName = (item.display_name || '').toLowerCase()
            const name = (item.name || '').toLowerCase()
            const type = item.class || ''
            const tags = item.tags || {}

            const isPark =
                displayName.includes('parque') ||
                displayName.includes('park') ||
                type === 'leisure' ||
                tags.leisure === 'park' ||
                tags.boundary === 'national_park'

            const isSpecificPlace =
                name.includes('vaca brava') ||
                displayName.includes('vaca brava') ||
                name.includes('parque') ||
                displayName.includes('parque')

            return isPark || isSpecificPlace
          })
          .map((item: any) => {
            const address = item.address || {}
            const city = address.city || address.town || address.village || ''
            const country = address.country || ''
            const name = item.display_name?.split(',')[0] || item.name || ''

            return {
              id: item.place_id,
              name: name,
              city: city,
              country: country,
              lat: parseFloat(item.lat),
              lon: parseFloat(item.lon),
              display_name: item.display_name || name
            }
          })
          .slice(0, 10)

      if (results.length > 0) parkCache.set(cacheKey, results)
      return results
    } catch (error) {
      handleError(error, 'Erro ao buscar parques')
      return []
    }
  }

  function hideSuggestions() {
    setTimeout(() => { showParkSuggestions.value = false }, 300)
  }

  return {
    parkSuggestions,
    showParkSuggestions,
    searchParks,
    hideSuggestions
  }
}
