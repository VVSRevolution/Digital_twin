import { ref } from 'vue'
import { useNotifications } from '~/composables/useErrorHandler'
import type { CitySuggestion } from '@/types/parkSearch'

export function useCitySearch() {
  const { handleInfo } = useNotifications()

  const citySuggestions = ref<CitySuggestion[]>([])
  const showCitySuggestions = ref(false)
  const cityCache = new Map<string, CitySuggestion[]>()

  async function searchCities(query: string, countryCode: string): Promise<CitySuggestion[]> {
    if (!query || query.length < 2) return []

    const cacheKey = `${query.toLowerCase()}_${countryCode}`
    if (cityCache.has(cacheKey)) return cityCache.get(cacheKey) || []

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

      const results = data.map((item: any) => {
        const address = item.address || {}
        return {
          id: item.place_id,
          name: item.display_name?.split(',')[0] || item.name || '',
          state: address.state || address.region || '',
          country: address.country || '',
          lat: parseFloat(item.lat),
          lon: parseFloat(item.lon)
        }
      }).slice(0, 10)

      if (results.length > 0) {
        cityCache.set(cacheKey, results)
      }
      return results
    } catch (error) {
      console.error('Erro ao buscar cidades:', error)
      return []
    }
  }

  function hideSuggestions() {
    setTimeout(() => {
      showCitySuggestions.value = false
    }, 300)
  }

  return {
    citySuggestions,
    showCitySuggestions,
    searchCities,
    hideSuggestions
  }
}
