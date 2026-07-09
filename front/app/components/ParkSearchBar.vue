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
                      @mousedown.prevent="selectCountryHandler(country)"
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
                      @mousedown.prevent="selectCityHandler(city)"
                  >
                    <span class="city-name">{{ city.name }}</span>
                    <span class="city-state">{{ city.state || '' }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 🔥 BUFFERS CONFIG -->
            <div class="menu-section">
              <label class="menu-label">📐 Configuração dos Buffers</label>
              <div class="buffer-config">
                <div class="buffer-field">
                  <label for="numBuffers">Número de anéis</label>
                  <input
                      id="numBuffers"
                      v-model.number="newNumBuffers"
                      type="number"
                      min="1"
                      max="20"
                      class="add-field buffer-input"
                  />
                </div>
                <div class="buffer-field">
                  <label for="bufferDistance">Distância (m)</label>
                  <input
                      id="bufferDistance"
                      v-model.number="newBufferDistance"
                      type="number"
                      min="10"
                      max="500"
                      step="10"
                      class="add-field buffer-input"
                  />
                </div>
              </div>
              <small class="buffer-hint">Padrão: 11 anéis de 90m. Ajuste conforme necessário.</small>
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

          <!-- 🔥 DATA DA IMAGEM -->
          <div v-if="coolingData.image_date" class="stat-item image-date">
            <span>📅 Data da Imagem</span>
            <strong>{{ formatDate(coolingData.image_date) }}</strong>
          </div>

          <div
              v-for="stat in formatCoolingStats(coolingData)"
              :key="stat.label"
              class="stat-item"
          >
            <span>{{ stat.label }}</span>
            <strong :style="{ color: stat.color }">{{ stat.value }}</strong>
          </div>

          <!-- 🔥 INFO DOS BUFFERS USADOS -->
          <div class="stat-item buffer-info">
            <span>📐 Buffers</span>
            <strong>{{ coolingData.num_buffers || 11 }} anéis × {{ coolingData.buffer_distance || 90 }}m</strong>
          </div>

          <div v-if="coolingData.error" class="error-msg">
            ⚠️ {{ coolingData.error }}
          </div>

          <!-- PIXELS -->
          <template v-if="coolingData?.buffers">
            <Divider />
            <div class="controls">
              <div class="toggle-wrapper">
                <Checkbox v-model="showPixels"
                          binary
                          @update:model-value="handleTogglePixels"
                />
                <label>Mostrar pixels de temperatura</label>
              </div>

              <!-- 🔥 CONTROLE DE OPACIDADE (NOVO) -->
              <div v-if="showPixels" class="opacity-control">
                <label>Opacidade: {{ Math.round(pixelOpacity * 100) }}%</label>
                <input
                    type="range"
                    min="0"
                    max="100"
                    :value="pixelOpacity * 100"
                    @input="handleOpacityChange($event)"
                    class="opacity-slider"
                />
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
import { useParkSearch } from '~/composables/useParkSearch'
import { useCountrySearch } from '~/composables/useCountrySearch'
import { useCitySearch } from '~/composables/useCitySearch'
import { useAddParkForm } from '~/composables/useAddParkForm'
import { useParkMenu } from '~/composables/useParkMenu'
import { debounce, formatDate } from '@/utils/parkSearchUtils'
import type { SearchResult, AddParkData } from '@/types/parkSearch'

const { handleError, handleSuccess, handleInfo } = useNotifications()
const { parkSuggestions, showParkSuggestions, searchParks, hideSuggestions: hideParkSuggestions } = useParkSearch()
const { countrySuggestions, showCountrySuggestions, searchCountries, hideSuggestions: hideCountrySuggestions, getCountryByCode } = useCountrySearch()
const { citySuggestions, showCitySuggestions, searchCities, hideSuggestions: hideCitySuggestions } = useCitySearch()
const { isAddingPark, newParkName, newParkCountry, newParkCity, newParkStartDate, newParkEndDate, selectedCountryCode, startAddPark, cancelAddPark, confirmAddPark: confirmAddParkForm, selectCountry } = useAddParkForm()
const { isMenuOpen, selectedPark, menuCardRef, toggleMenu } = useParkMenu()

// ============================================================
// 🔥 BUFFERS CONFIG
// ============================================================
const newNumBuffers = ref(11)
const newBufferDistance = ref(90)

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
  pixelOpacity: number
  gradientMin: number | null
  gradientMax: number | null
  totalPixels: number
}>()

// EMITS
const emit = defineEmits<{
  (e: 'search'): void
  (e: 'select', park: SearchResult): void
  (e: 'addPark', data: AddParkData & { numBuffers: number; bufferDistance: number }): void
  (e: 'refresh'): void
  (e: 'export'): void
  (e: 'settings'): void
  (e: 'about'): void
  (e: 'togglePixels'): void
  (e: 'updateOpacity', value: number): void
}>()

// LOCAL STATE
const cityWrapperRef = ref<HTMLElement | null>(null)

// Debounced search functions
const debouncedSearchParks = debounce(async (query: string) => {
  if (query.length >= 2) {
    const results = await searchParks(query, selectedCountryCode.value)
    parkSuggestions.value = results
    showParkSuggestions.value = results.length > 0
  } else {
    parkSuggestions.value = []
    showParkSuggestions.value = false
  }
}, 600)

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

const debouncedSearchCities = debounce(async (query: string) => {
  if (query.length >= 2 && selectedCountryCode.value) {
    const results = await searchCities(query, selectedCountryCode.value)
    citySuggestions.value = results
    showCitySuggestions.value = results.length > 0
  } else {
    citySuggestions.value = []
    showCitySuggestions.value = false
  }
}, 600)

const formatStats = (data: CoolingAnalysisResult) => formatCoolingStats(data)


// ============================================================
// 🔥 EVENT HANDLERS - PARQUE
// ============================================================
function onParkInput() {
  debouncedSearchParks(newParkName.value)
}

function selectPark(park: any) {
  newParkName.value = park.name
  if (park.city) newParkCity.value = park.city
  if (park.country) {
    newParkCountry.value = park.country
    const code = park.country.split(',')[0]?.trim()
    if (code) {
      const country = getCountryByCode(code.substring(0, 2))
      if (country) selectedCountryCode.value = country.code
    }
  }
  showParkSuggestions.value = false
  handleSuccess(`Parque "${park.name}" selecionado!`)
}

// ============================================================
// 🔥 EVENT HANDLERS - PAÍS
// ============================================================
function onCountryInput() {
  debouncedSearchCountries(newParkCountry.value)
}

function selectCountryHandler(country: any) {
  selectCountry(country.name)
  newParkCountry.value = country.name
  selectedCountryCode.value = country.code
  showCountrySuggestions.value = false
  newParkCity.value = ''
  citySuggestions.value = []
}

// ============================================================
// 🔥 EVENT HANDLERS - CIDADE
// ============================================================
function onCityInput() {
  debouncedSearchCities(newParkCity.value)
}

function onCityFocus() {
  if (newParkCity.value.length >= 2 && citySuggestions.value.length > 0) {
    showCitySuggestions.value = true
  }
}

function onCityBlur() {
  hideCitySuggestions()
}

function selectCityHandler(city: any) {
  newParkCity.value = city.name
  citySuggestions.value = []
  showCitySuggestions.value = false
}

function handleClickOutsideCity(event: MouseEvent) {
  if (cityWrapperRef.value && !cityWrapperRef.value.contains(event.target as Node)) {
    showCitySuggestions.value = false
  }
}

watch(showCitySuggestions, (newVal) => {
  if (newVal) {
    document.addEventListener('click', handleClickOutsideCity)
  } else {
    document.removeEventListener('click', handleClickOutsideCity)
  }
})

// ============================================================
// 🔥 EVENT HANDLERS - CADASTRO
// ============================================================
function confirmAddPark() {
  const baseData = confirmAddParkForm()
  if (baseData) {
    const data = {
      ...baseData,
      numBuffers: newNumBuffers.value,
      bufferDistance: newBufferDistance.value
    }
    isMenuOpen.value = false
    emit('addPark', data)
  }
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
  console.log(" updade pixel")
  emit('togglePixels')
}

function handleOpacityChange(event: Event) {
  const target = event.target as HTMLInputElement
  const value = parseFloat(target.value)
  emit('updateOpacity', value)
}
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
  width: 360px;
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

/* 🔥 BUFFER CONFIG */
.buffer-config {
  display: flex;
  gap: 12px;
}

.buffer-field {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.buffer-field label {
  font-size: 12px;
  font-weight: 500;
  color: #4b5563;
}

.buffer-input {
  width: 100% !important;
}

.buffer-hint {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 2px;
  font-style: italic;
}

/* 🔥 BUFFER INFO NO RESULTADO */
.buffer-info {
  background: #f0fdf4;
  border-radius: 4px;
  padding: 4px 8px !important;
  margin-bottom: 4px;
}

.buffer-info span {
  color: #15803d;
}

.buffer-info strong {
  color: #166534;
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
@media (max-width: 360px) {
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

  .buffer-config {
    flex-direction: column;
    gap: 8px;
  }
}
/* 🔥 CONTROLE DE OPACIDADE */
.opacity-control {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 4px 0;
}

.opacity-control label {
  font-size: 12px;
  font-weight: 500;
  color: #4b5563;
}

.opacity-slider {
  width: 100%;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: linear-gradient(to right, #3b82f6, #8b5cf6);
  border-radius: 2px;
  outline: none;
}

.opacity-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.opacity-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: 2px solid white;
}
</style>