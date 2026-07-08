import { ref } from 'vue'
import type { CountrySuggestion } from '@/types/parkSearch'

const COUNTRY_LIST: CountrySuggestion[] = [
  { id: 'BR', name: 'Brasil', code: 'BR' },
  { id: 'US', name: 'Estados Unidos', code: 'US' },
  { id: 'PT', name: 'Portugal', code: 'PT' },
  { id: 'FR', name: 'França', code: 'FR' },
  { id: 'DE', name: 'Alemanha', code: 'DE' },
  { id: 'IT', name: 'Itália', code: 'IT' },
  { id: 'ES', name: 'Espanha', code: 'ES' },
  { id: 'GB', name: 'Reino Unido', code: 'GB' },
  { id: 'AR', name: 'Argentina', code: 'AR' },
  { id: 'CL', name: 'Chile', code: 'CL' },
  { id: 'CO', name: 'Colômbia', code: 'CO' },
  { id: 'MX', name: 'México', code: 'MX' },
  { id: 'PE', name: 'Peru', code: 'PE' },
  { id: 'UY', name: 'Uruguai', code: 'UY' },
  { id: 'PY', name: 'Paraguai', code: 'PY' },
]

export function useCountrySearch() {
  const countrySuggestions = ref<CountrySuggestion[]>([])
  const showCountrySuggestions = ref(false)
  const countryCache = new Map<string, CountrySuggestion[]>()

  function searchCountries(query: string): CountrySuggestion[] {
    if (!query || query.length < 1) return []

    const cacheKey = query.toLowerCase()
    if (countryCache.has(cacheKey)) return countryCache.get(cacheKey) || []

    const results = COUNTRY_LIST
        .filter(c => c.name.toLowerCase().includes(query.toLowerCase()) ||
            c.code.toLowerCase().includes(query.toLowerCase()))
        .slice(0, 8)

    if (results.length > 0) countryCache.set(cacheKey, results)
    return results
  }

  function hideSuggestions() {
    setTimeout(() => { showCountrySuggestions.value = false }, 300)
  }

  function getCountryList() {
    return COUNTRY_LIST
  }

  function getCountryByCode(code: string): CountrySuggestion | undefined {
    return COUNTRY_LIST.find(c => c.code === code)
  }

  function getCodeByName(name: string): string | undefined {
    return COUNTRY_LIST.find(c => c.name.toLowerCase() === name.toLowerCase())?.code
  }

  return {
    countrySuggestions,
    showCountrySuggestions,
    searchCountries,
    hideSuggestions,
    getCountryList,
    getCountryByCode,
    getCodeByName
  }
}
