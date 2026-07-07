<template>
  <div class="search-wrapper">
    <!-- 🔥 CARD 1: MENU + PESQUISA (LADO A LADO) -->
    <Card class="menu-card">
      <template #content>
        <div class="menu-search-row">
          <!-- MENU SANDUÍCHE -->
          <div class="menu-container">
            <Button
                icon="pi pi-bars"
                severity="secondary"
                text
                rounded
                @click="toggleMenu"
                aria-label="Menu"
            />
          </div>

          <!-- PESQUISA -->
          <div class="search-input">
            <input
                v-model="search"
                type="text"
                placeholder="Pesquisar parque..."
                class="search-field"
                @keydown.enter="handleSearch"
            />
            <Button
                icon="pi pi-search"
                label="Buscar"
                :loading="loading || analyzing"
                @click="handleSearch"
            />
          </div>
        </div>

        <!-- OPÇÕES DO MENU -->
        <div v-if="isMenuOpen" class="menu-options">
          <Divider />

          <!-- 🔥 MODO NORMAL: SELECIONAR PARQUE -->
          <template v-if="!isAddingPark">
            <div class="menu-section">
              <label class="menu-label">📍 Selecionar Parque</label>
              <Select
                  v-model="selectedPark"
                  :options="predefinedParks"
                  optionLabel="tags.name"
                  placeholder="Selecione um parque..."
                  fluid
                  @change="handleSelectPark"
              />
            </div>

            <Button
                icon="pi pi-plus"
                label=" Adicionar Parque"
                fluid
                @click="startAddPark"
            />
          </template>

          <!-- 🔥 MODO CADASTRO: FORMULÁRIO COMPLETO -->
          <template v-if="isAddingPark">
            <!-- 🔥 PARQUE (com autocomplete) -->
            <div class="menu-section">
              <label class="menu-label">🌳 Nome do Parque</label>
              <div class="autocomplete-wrapper">
                <input
                    v-model="newParkName"
                    type="text"
                    placeholder="Digite o nome do parque..."
                    class="add-field"
                    @input="onParkInput"
                    @blur="hideParkSuggestions"
                />
                <div v-if="parkSuggestions.length && showParkSuggestions" class="autocomplete-list">
                  <div
                      v-for="park in parkSuggestions"
                      :key="park.id"
                      class="autocomplete-item"
                      @mousedown.prevent="selectPark(park)"
                  >
                    <span class="park-name">{{ park.name || 'Parque sem nome' }}</span>
                    <span class="park-location">{{ park.city || '' }}, {{ park.country || '' }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 🔥 PAÍS (com autocomplete, Brasil pré-selecionado) -->
            <div class="menu-section">
              <label class="menu-label">🌍 País</label>
              <div class="autocomplete-wrapper">
                <input
                    v-model="newParkCountry"
                    type="text"
                    placeholder="Digite o país..."
                    class="add-field"
                    @input="onCountryInput"
                    @blur="hideCountrySuggestions"
                />
                <div v-if="countrySuggestions.length && showCountrySuggestions" class="autocomplete-list">
                  <div
                      v-for="country in countrySuggestions"
                      :key="country.id"
                      class="autocomplete-item"
                      @mousedown.prevent="selectCountry(country)"
                  >
                    <span class="country-name">{{ country.name }}</span>
                    <span class="country-code">{{ country.code }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 🔥 CIDADE (com autocomplete, filtrada pelo país) -->
            <div class="menu-section">
              <label class="menu-label">📍 Cidade</label>
              <div class="autocomplete-wrapper" ref="cityWrapperRef">
                <input
                    v-model="newParkCity"
                    type="text"
                    placeholder="Digite a cidade..."
                    class="add-field"
                    @input="onCityInput"
                    @focus="onCityFocus"
                    @blur="onCityBlur"
                />
                <div v-if="citySuggestions.length && showCitySuggestions" class="autocomplete-list">
                  <div
                      v-for="city in citySuggestions"
                      :key="city.id"
                      class="autocomplete-item"
                      @mousedown.prevent="selectCity(city)"
                  >
                    <span class="city-name">{{ city.name }}</span>
                    <span class="city-state">{{ city.state || '' }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="menu-section">
              <label class="menu-label">📅 Período de Análise</label>
              <div class="date-range">
                <input
                    v-model="newParkStartDate"
                    type="date"
                    class="add-field date-field"
                />
                <span class="date-separator">até</span>
                <input
                    v-model="newParkEndDate"
                    type="date"
                    class="add-field date-field"
                />
              </div>
            </div>

            <div class="menu-actions">
              <Button
                  label="Voltar"
                  icon="pi pi-arrow-left"
                  severity="secondary"
                  fluid
                  @click="cancelAddPark"
              />
              <Button
                  label="Cadastrar"
                  icon="pi pi-check"
                  severity="success"
                  fluid
                  @click="confirmAddPark"
              />
            </div>
          </template>
        </div>
      </template>
    </Card>

    <!-- 🔥 CARD 3: RESULTADOS -->
    <Card v-if="results.length || (showStats && coolingData)" class="results-card">
      <template #content>
        <!-- RESULTADOS DA PESQUISA -->
        <div v-if="results.length" class="results-list">
          <div
              v-for="item in results"
              :key="item.id"
              class="result-item"
              @click="handleSelect(item)"
          >
            🌳 {{ item.tags?.name || 'Parque sem nome' }}
          </div>
        </div>

        <!-- RESULTADOS DA ANÁLISE -->
        <template v-if="showStats && coolingData">
          <Divider v-if="results.length" />

          <div class="stats-header">
            <h4>🌳 {{ parkName }}</h4>
            <Tag
                :value="coolingData.success ? 'OK' : 'Falha'"
                :severity="coolingData.success ? 'success' : 'danger'"
            />
          </div>

          <div
              v-for="stat in formatCoolingStats(coolingData)"
              :key="stat.label"
              class="stat-item"
          >
            <span>{{ stat.label }}</span>
            <strong :style="{ color: stat.color }">{{ stat.value }}</strong>
          </div>

          <div v-if="coolingData.error" class="error-msg">
            ⚠️ {{ coolingData.error }}
          </div>

          <!-- PIXELS -->
          <template v-if="coolingData?.buffers">
            <Divider />
            <div class="controls">
              <div class="toggle-wrapper">
                <Checkbox v-model="showPixels" binary @change="handleTogglePixels" />
                <label>Mostrar pixels de temperatura</label>
              </div>

              <div v-if="gradientMin !== null && gradientMax !== null" class="gradient-legend">
                <div class="gradient-header">
                  <span>🌡️ Temperatura</span>
                  <Badge :value="`${totalPixels} px`" />
                </div>
                <div class="gradient-bar"></div>
                <div class="gradient-labels">
                  <span>{{ gradientMin.toFixed(1) }}°C</span>
                  <span>{{ gradientMax.toFixed(1) }}°C</span>
                </div>
              </div>
            </div>
          </template>

          <!-- BUFFERS -->
          <template v-if="coolingData?.buffers">
            <Divider />
            <div class="buffer-stats">
              <h4>📊 Anéis</h4>
              <div class="stats-grid">
                <div
                    v-for="buffer in coolingData.buffers"
                    :key="buffer.distance"
                    class="stats-item"
                    :style="{
                    background: (buffer.statistics?.mean ?? null) !== null
                      ? `rgba(255, 100, 0, ${Math.max(0, Math.min(1, ((buffer.statistics?.mean ?? 0) - 25) / 10))})`
                      : '#f5f5f5'
                  }"
                >
                  <span>{{ buffer.distance }}m</span>
                  <span>{{ buffer.statistics?.mean?.toFixed(1) ?? 'N/A' }}°C</span>
                  <span>{{ buffer.statistics?.count ?? 0 }}px</span>
                </div>
              </div>
            </div>
          </template>
        </template>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { formatCoolingStats, type CoolingAnalysisResult } from '@/services/eeService'
import { useNotifications } from '~/composables/useErrorHandler'

const { handleError, handleSuccess, handleInfo } = useNotifications()

// 🔥 INTERFACES
interface SearchResult {
  id: number
  lat: number
  lon: number
  tags?: { name?: string; [key: string]: unknown }
}

interface ParkSuggestion {
  id: number
  name: string
  city: string
  country: string
  lat: number
  lon: number
  display_name: string
}

interface CountrySuggestion {
  id: string
  name: string
  code: string
}

interface CitySuggestion {
  id: number
  name: string
  state: string
  country: string
  lat: number
  lon: number
}

// MODELOS
const search = defineModel<string>('search', { required: true })
const showPixels = defineModel<boolean>('showPixels', { default: true })

// PROPS
const props = defineProps<{
  loading: boolean
  analyzing: boolean
  results: SearchResult[]
  predefinedParks?: SearchResult[]
  showStats: boolean
  coolingData: CoolingAnalysisResult | null
  parkName: string
  gradientMin: number | null
  gradientMax: number | null
  totalPixels: number
}>()

// EMITS
const emit = defineEmits<{
  (e: 'search'): void
  (e: 'select', park: SearchResult): void
  (e: 'addPark', data: { city: string; country: string; name: string; startDate: string; endDate: string }): void
  (e: 'refresh'): void
  (e: 'export'): void
  (e: 'settings'): void
  (e: 'about'): void
  (e: 'togglePixels'): void
}>()

// CONTROLE DO MENU
const isMenuOpen = ref(false)
const selectedPark = ref<SearchResult | null>(null)

// 🔥 CONTROLE DO CADASTRO
const isAddingPark = ref(false)
const newParkName = ref('')
const newParkCountry = ref('Brasil')
const newParkCity = ref('')
const newParkStartDate = ref('')
const newParkEndDate = ref('')
const selectedCountryCode = ref('BR')

// 🔥 AUTOCOMPLETE - PARQUE
const parkSuggestions = ref<ParkSuggestion[]>([])
const showParkSuggestions = ref(false)
const parkCache = new Map<string, ParkSuggestion[]>()

// 🔥 AUTOCOMPLETE - PAÍS
const countrySuggestions = ref<CountrySuggestion[]>([])
const showCountrySuggestions = ref(false)
const countryCache = new Map<string, CountrySuggestion[]>()

// 🔥 AUTOCOMPLETE - CIDADE
const cityCache = new Map<string, CitySuggestion[]>()
const citySuggestions = ref<CitySuggestion[]>([])
const showCitySuggestions = ref(false)
const cityWrapperRef = ref<HTMLElement | null>(null)

// 🔥 LISTA DE PAÍSES
const countryList: CountrySuggestion[] = [
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

const formatStats = (data: CoolingAnalysisResult) => formatCoolingStats(data)

function toggleMenu() {
  isMenuOpen.value = !isMenuOpen.value
}

// 🔥 FUNÇÃO DEBOUNCE
function debounce<T extends (...args: any[]) => any>(fn: T, delay: number = 400): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null
  return (...args: Parameters<T>) => {
    if (timeoutId) clearTimeout(timeoutId)
    timeoutId = setTimeout(() => fn(...args), delay)
  }
}

// ============================================================
// 🔥 BUSCA PARQUES
// ============================================================
async function searchParks(query: string): Promise<ParkSuggestion[]> {
  if (!query || query.length < 2) return []

  const cacheKey = `${query.toLowerCase()}_${selectedCountryCode.value}`
  if (parkCache.has(cacheKey)) return parkCache.get(cacheKey) || []

  try {
    // 🔥 ADICIONA countrycodes PARA FILTRAR PELO PAÍS SELECIONADO
    const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&addressdetails=1&countrycodes=${selectedCountryCode.value}&limit=15`
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
const debouncedSearchParks = debounce(async (query: string) => {
  if (query.length >= 2) {
    const results = await searchParks(query)
    parkSuggestions.value = results
    showParkSuggestions.value = results.length > 0
  } else {
    parkSuggestions.value = []
    showParkSuggestions.value = false
  }
}, 600)

function onParkInput() {
  debouncedSearchParks(newParkName.value)
}

function selectPark(park: ParkSuggestion) {
  newParkName.value = park.name
  if (park.city) newParkCity.value = park.city
  if (park.country) {
    newParkCountry.value = park.country
    const found = countryList.find(c => c.name.toLowerCase() === park.country.toLowerCase())
    if (found) selectedCountryCode.value = found.code
  }
  showParkSuggestions.value = false
  handleSuccess(`Parque "${park.name}" selecionado!`)
}

function hideParkSuggestions() {
  setTimeout(() => { showParkSuggestions.value = false }, 300)
}

// ============================================================
// 🔥 BUSCA PAÍSES
// ============================================================
function searchCountries(query: string): CountrySuggestion[] {
  if (!query || query.length < 1) return []

  const cacheKey = query.toLowerCase()
  if (countryCache.has(cacheKey)) return countryCache.get(cacheKey) || []

  const results = countryList
      .filter(c => c.name.toLowerCase().includes(query.toLowerCase()) ||
          c.code.toLowerCase().includes(query.toLowerCase()))
      .slice(0, 8)

  if (results.length > 0) countryCache.set(cacheKey, results)
  return results
}

const debouncedSearchCountries = debounce((query: string) => {
  if (query.length >= 1) {
    const results = searchCountries(query)
    countrySuggestions.value = results
    showCountrySuggestions.value = results.length > 0
  } else {
    countrySuggestions.value = []
    showCountrySuggestions.value = false
  }
}, 300)

function onCountryInput() {
  debouncedSearchCountries(newParkCountry.value)
}

function selectCountry(country: CountrySuggestion) {
  newParkCountry.value = country.name
  selectedCountryCode.value = country.code
  showCountrySuggestions.value = false
  newParkCity.value = ''
  citySuggestions.value = []
}

function hideCountrySuggestions() {
  setTimeout(() => { showCountrySuggestions.value = false }, 300)
}

// ============================================================
// 🔥 BUSCA CIDADES
// ============================================================


// 🔥 BUSCA CIDADES
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
    console.log('📊 Dados da cidade (brutos):', data)

    // 🔥 SEM FILTRO - USA TUDO QUE VEIO DO NOMINATIM
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

    console.log('📊 Cidades encontradas (sem filtro):', results)

    if (results.length > 0) {
      cityCache.set(cacheKey, results)
    }
    return results
  } catch (error) {
    console.error('Erro ao buscar cidades:', error)
    return []
  }
}

// 🔥 DEBOUNCE DA CIDADE (IGUAL AO PARQUE)
const debouncedSearchCities = debounce(async (query: string) => {
  console.log('🔍 Buscando cidades:', query, 'País:', selectedCountryCode.value)

  if (query.length >= 2 && selectedCountryCode.value) {
    const results = await searchCities(query, selectedCountryCode.value)
    citySuggestions.value = results
    showCitySuggestions.value = results.length > 0  // 🔥 MESMA LÓGICA DO PARQUE!
    console.log('📊 Sugestões de cidade:', results.length, 'Mostrar:', showCitySuggestions.value)
  } else {
    citySuggestions.value = []
    showCitySuggestions.value = false
  }
}, 600) // 🔥 MESMO DELAY DO PARQUE

// 🔥 INPUT DA CIDADE
function onCityInput() {
  console.log('✏️ Input cidade:', newParkCity.value)
  debouncedSearchCities(newParkCity.value)
}

// 🔥 SELECIONA CIDADE
function selectCity(city: CitySuggestion) {
  console.log('✅ Cidade selecionada:', city.name)
  newParkCity.value = city.name
  citySuggestions.value = []
  showCitySuggestions.value = false  // 🔥 FECHA AS SUGESTÕES
}

// 🔥 ESCONDE SUGESTÕES (IGUAL AO PARQUE)
function hideCitySuggestions() {
  setTimeout(() => {
    showCitySuggestions.value = false
  }, 300)  // 🔥 MESMO DELAY DO PARQUE
}

// 🔥 CLICK FORA FECHA AS SUGESTÕES (IGUAL AO PARQUE)
function handleClickOutsideCity(event: MouseEvent) {
  if (cityWrapperRef.value && !cityWrapperRef.value.contains(event.target as Node)) {
    showCitySuggestions.value = false
  }
}

// 🔥 LISTENER GLOBAL
watch(showCitySuggestions, (newVal) => {
  if (newVal) {
    document.addEventListener('click', handleClickOutsideCity)
  } else {
    document.removeEventListener('click', handleClickOutsideCity)
  }
})
// ============================================================
// 🔥 FUNÇÕES DO CADASTRO
// ============================================================
function startAddPark() {
  isAddingPark.value = true
  newParkName.value = ''
  newParkCountry.value = 'Brasil'
  newParkCity.value = ''
  newParkStartDate.value = ''
  newParkEndDate.value = ''
  selectedCountryCode.value = 'BR'
  parkSuggestions.value = []
  countrySuggestions.value = []
  citySuggestions.value = []
  showParkSuggestions.value = false
  showCountrySuggestions.value = false
  showCitySuggestions.value = false
}

function cancelAddPark() {
  isAddingPark.value = false
  handleInfo('Cadastro cancelado')
}

function confirmAddPark() {
  if (!newParkCity.value || !newParkCountry.value || !newParkName.value ||
      !newParkStartDate.value || !newParkEndDate.value) {
    handleError('Preencha todos os campos obrigatórios')
    return
  }

  emit('addPark', {
    city: newParkCity.value,
    country: newParkCountry.value,
    name: newParkName.value,
    startDate: newParkStartDate.value,
    endDate: newParkEndDate.value
  })

  isAddingPark.value = false
  isMenuOpen.value = false
  handleSuccess(`Parque "${newParkName.value}" cadastrado com sucesso!`)
}

function handleSelectPark() {
  if (selectedPark.value) {
    isMenuOpen.value = false
    emit('select', selectedPark.value)
  }
}

function handleSearch() {
  if (!search.value || search.value.trim().length < 2) {
    handleError('Digite pelo menos 2 caracteres para buscar')
    return
  }
  emit('search')
}

function handleSelect(item: SearchResult) {
  emit('select', item)
  handleSuccess(`Parque "${item.tags?.name || 'sem nome'}" selecionado!`)
}

function handleTogglePixels() {
  emit('togglePixels')
}

// FECHA O MENU AO CLICAR FORA
const menuCardRef = ref<HTMLElement | null>(null)

function handleClickOutside(event: MouseEvent) {
  if (menuCardRef.value && !menuCardRef.value.contains(event.target as Node)) {
    isMenuOpen.value = false
    if (isAddingPark.value) isAddingPark.value = false
  }
}

watch(isMenuOpen, (newVal) => {
  if (newVal) {
    document.addEventListener('click', handleClickOutside)
  } else {
    document.removeEventListener('click', handleClickOutside)
  }
})

// 🔥 PRÉ-SELECIONA BRASIL AO INICIAR
onMounted(() => {
  newParkCountry.value = 'Brasil'
  selectedCountryCode.value = 'BR'
})
</script>

<style scoped>
/* 🔥 WRAPPER */
.search-wrapper {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 420px;
  max-height: 90vh;
  overflow-y: auto;
}

/* 🔥 CARDS */
.search-wrapper :deep(.p-card) {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  overflow: visible !important;
}

.search-wrapper :deep(.p-card-body) {
  padding: 0 !important;
}

.search-wrapper :deep(.p-card-content) {
  padding: 12px 16px !important;
}

/* 🔥 LINHA MENU + PESQUISA */
.menu-search-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.menu-container {
  flex-shrink: 0;
}

/* 🔥 PESQUISA */
.search-input {
  display: flex;
  flex: 1;
  gap: 8px;
  align-items: center;
}

.search-field {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  background: white;
  color: #1f2937;
  min-width: 0;
}

.search-field:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* 🔥 MENU OPÇÕES */
.menu-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 8px;
}

.menu-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.menu-label {
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 🔥 AUTOCOMPLETE */
.autocomplete-wrapper {
  position: relative;
  width: 100%;
}

.autocomplete-list {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 100;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.autocomplete-item {
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background 0.15s;
}

.autocomplete-item:hover {
  background: #f3f4f6;
}

.park-name,
.city-name,
.country-name {
  font-weight: 500;
  color: #1f2937;
}

.park-location,
.city-state,
.country-code {
  font-size: 12px;
  color: #6b7280;
}

/* 🔥 CADASTRO */
.add-field {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  background: white;
  width: 100%;
}

.add-field:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.date-range {
  display: flex;
  align-items: center;
  gap: 8px;
}

.date-field {
  flex: 1;
  min-width: 0;
}

.date-separator {
  color: #6b7280;
  font-size: 12px;
}

.menu-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

/* 🔥 RESULTADOS */
.results-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.result-item {
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.15s;
  font-size: 14px;
}

.result-item:hover {
  background: #f3f4f6;
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.stats-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  font-size: 13px;
  border-bottom: 1px solid #f3f4f6;
}

.stat-item:last-child {
  border-bottom: none;
}

.error-msg {
  padding: 8px 12px;
  background: #fee2e2;
  color: #991b1b;
  border-radius: 4px;
  font-size: 12px;
  margin-top: 4px;
}

/* CONTROLS */
.controls {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.toggle-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.gradient-legend {
  padding: 8px 12px;
  background: #f9fafb;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.gradient-header {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  margin-bottom: 4px;
}

.gradient-bar {
  width: 100%;
  height: 12px;
  border-radius: 4px;
  background: linear-gradient(to right,
  rgb(0, 0, 200),
  rgb(0, 100, 150),
  rgb(0, 180, 80),
  rgb(50, 200, 50),
  rgb(200, 200, 0),
  rgb(255, 150, 0),
  rgb(255, 80, 0),
  rgb(200, 0, 0)
  );
  border: 1px solid #e5e7eb;
}

.gradient-labels {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
}

/* BUFFERS */
.buffer-stats h4 {
  font-size: 13px;
  margin: 0 0 4px 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(65px, 1fr));
  gap: 4px;
  max-height: 150px;
  overflow-y: auto;
}

.stats-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4px;
  border-radius: 4px;
  border: 1px solid #e5e7eb;
  font-size: 10px;
  text-align: center;
}

.stats-item span {
  line-height: 1.4;
}

/* RESPONSIVIDADE */
@media (max-width: 768px) {
  .search-wrapper {
    left: 8px;
    right: 8px;
    width: auto;
    top: 8px;
  }

  .date-range {
    flex-direction: column;
    gap: 4px;
  }

  .menu-actions {
    flex-direction: column;
  }
}
</style>