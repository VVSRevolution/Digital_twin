<!-- components/MainMenuOverlay.vue -->
<template>
  <div class="menu-wrapper overlay-wrapper">
    <Card class="menu-card">
      <template #content>
        <div class="menu-search-row">
          <!-- MENU SANDUÍCHE -->
          <div class="menu-container">
            <Button
                aria-label="Menu"
                icon="pi pi-bars"
                rounded
                severity="secondary"
                text
                @click="toggleMenu"
            />
          </div>

          <!-- PESQUISA -->
          <div ref="searchInputRef" class="search-input">
            <input
                v-model="search"
                class="search-field"
                placeholder="Pesquisar parque..."
                type="text"
                @blur="hideParkSuggestions"
                @input="onParkInput($event)"
                @keydown.enter="handleSearch"
            />
            <Button
                :loading="loading || analyzing"
                icon="pi pi-search"
                label="Buscar"
                @click="handleSearch"
            />
          </div>
        </div>

        <!-- OPÇÕES DO MENU -->
        <div v-if="isMenuOpen" class="menu-options">
          <Divider/>

          <!-- MODO NORMAL -->
          <template v-if="!isAddingPark">
            <div class="menu-section">
              <label class="menu-label"><i class="pi pi-map-marker"></i> Selecionar Parque</label>
              <Select
                  v-model="selectedPark"
                  :loading="loadingParks"
                  :options="parkList"
                  fluid
                  optionLabel="name"
                  placeholder="Selecione um parque..."
                  @change="handleSelectParkFromList"
              >
                <template #option="slotProps">
                  <div class="park-option">
                    <span class="park-option-name">{{ slotProps.option.name }}</span>
                    <span class="park-option-location">{{ slotProps.option.city }}, {{ slotProps.option.country }}</span>
                  </div>
                </template>
              </Select>
            </div>

            <Button
                fluid
                icon="pi pi-plus"
                label=" Adicionar Parque"
                @click="startAddPark"
            />
            <Button
                fluid
                icon="pi pi-trash"
                label=" Deletar Parque"
                outlined
                severity="danger"
                @click="showDeleteDialog = true"
            />
          </template>

          <ParkDeleteDialog
              v-model:visible="showDeleteDialog"
              @deleted="handleParkDeleted"
          />

          <!-- MODO CADASTRO -->
          <template v-if="isAddingPark">
            <!-- Nome do Parque -->
            <div class="menu-section">
              <label class="menu-label">
                <Tree :size="16"/>
                <span>Nome do Parque</span>
              </label>
              <div class="autocomplete-wrapper">
                <input
                    v-model="newParkName"
                    class="add-field"
                    placeholder="Digite o nome do parque..."
                    type="text"
                    @blur="hideParkSuggestions"
                    @input="onParkInput($event)"
                />
                <div v-if="parkSuggestions.length && showParkSuggestions && !showParkSugestionOnSeach"
                     class="autocomplete-list">
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

            <!-- País -->
            <div class="menu-section">
              <label class="menu-label"><i class="pi pi-globe"></i> País</label>
              <div class="autocomplete-wrapper">
                <input
                    v-model="newParkCountry"
                    class="add-field"
                    placeholder="Digite o país..."
                    type="text"
                    @blur="hideCountrySuggestions"
                    @input="onCountryInput"
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

            <!-- Cidade -->
            <div class="menu-section">
              <label class="menu-label"><i class="pi pi-map"></i> Cidade</label>
              <div ref="cityWrapperRef" class="autocomplete-wrapper">
                <input
                    v-model="newParkCity"
                    class="add-field"
                    placeholder="Digite a cidade..."
                    type="text"
                    @blur="onCityBlur"
                    @focus="onCityFocus"
                    @input="onCityInput"
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

            <!-- Buffers -->
            <div class="menu-section">
              <label class="menu-label">
                <PinRotate size="16"/>
                Configuração dos Buffers
              </label>
              <div class="buffer-config">
                <div class="buffer-field">
                  <label for="numBuffers">Número de anéis</label>
                  <input
                      id="numBuffers"
                      v-model.number="newNumBuffers"
                      class="add-field buffer-input"
                      max="20"
                      min="1"
                      type="number"
                  />
                </div>
                <div class="buffer-field">
                  <label for="bufferDistance">Distância (m)</label>
                  <input
                      id="bufferDistance"
                      v-model.number="newBufferDistance"
                      class="add-field buffer-input"
                      max="500"
                      min="10"
                      step="10"
                      type="number"
                  />
                </div>
              </div>
              <small class="buffer-hint">Padrão: 11 anéis de 90m. Ajuste conforme necessário.</small>
            </div>

            <!-- Período -->
            <div class="menu-section">
              <label class="menu-label"><i class="pi pi-calendar"></i> Período de Análise</label>
              <div class="date-range">
                <input
                    v-model="newParkStartDate"
                    class="add-field date-field"
                    placeholder="Data de início *"
                    type="date"
                />
                <template v-if="!isUpToDate">
                  <span class="date-separator">até</span>
                  <input
                      v-model="newParkEndDate"
                      class="add-field date-field"
                      placeholder="Data de fim"
                      type="date"
                  />
                </template>
                <span v-else class="date-hint"><i class="pi pi-satellite"></i> até a imagem mais recente</span>
              </div>
              <div class="toggle-update-wrapper">
                <ToggleSwitch v-model="isUpToDate"/>
                <label class="toggle-label">Manter atualizado (buscar imagem mais recente)</label>
              </div>
            </div>

            <!-- Satélites -->
            <div class="menu-section">
              <label class="menu-label">
                <Satellite :size="16"/>
                <span>Satélites</span>
              </label>
              <div class="satellite-select-wrapper">
                <MultiSelect
                    v-model="selectedSatellites"
                    :loading="loadingSatellites"
                    :options="availableSatellites"
                    filter
                    fluid
                    optionLabel="name"
                    optionValue="id"
                    placeholder="Selecione os satélites..."
                    showClear
                >
                  <template #option="slotProps">
                    <div class="satellite-option">
                      <div class="satellite-option-main">
                        <span class="satellite-option-name">{{ slotProps.option.name }}</span>
                        <span class="satellite-option-resolution">{{ slotProps.option.resolution_m }}m</span>
                      </div>
                      <div class="satellite-option-desc">{{ slotProps.option.description }}</div>
                    </div>
                  </template>
                </MultiSelect>
                <small class="satellite-hint">
                  {{ selectedSatellites.length }} satélite(s) selecionado(s)
                </small>
              </div>
            </div>

            <!-- Geometria Manual -->
            <div class="menu-section">
              <div class="geometry-manual-header">
                <label class="menu-label"><i class="pi pi-pencil"></i> Geometria Manual</label>
                <Button
                    :loading="drawingMode"
                    class="geometry-btn"
                    icon="pi pi-pencil"
                    label="Desenhar no Mapa"
                    severity="secondary"
                    size="small"
                    @click="toggleDrawingMode"
                />
              </div>
              <div v-if="manualPoints.length > 0" class="points-list">
                <div
                    v-for="(point, index) in manualPoints"
                    :key="index"
                    class="point-item"
                >
                  <span class="point-number">{{ index + 1 }}</span>
                  <span class="point-coords">
                    {{ point.lat.toFixed(6) }}, {{ point.lon.toFixed(6) }}
                  </span>
                  <Button
                      icon="pi pi-times"
                      rounded
                      severity="danger"
                      size="small"
                      text
                      @click="removePoint(index)"
                  />
                </div>
              </div>
              <small v-else class="geometry-hint">
                <i class="pi pi-info-circle"></i>
                Clique no botão acima e depois clique no mapa para adicionar pontos
              </small>
            </div>

            <div v-if="drawingMode" class="points-actions">
              <Button
                  icon="pi pi-times"
                  label="Cancelar"
                  severity="danger"
                  size="small"
                  @click="cancelDrawing"
              />
              <Button
                  icon="pi pi-check"
                  label="Usar Geometria"
                  severity="success"
                  size="small"
                  @click="useManualGeometry"
              />
            </div>

            <div class="menu-actions">
              <Button
                  fluid
                  icon="pi pi-arrow-left"
                  label="Voltar"
                  severity="secondary"
                  @click="cancelAddParkLocal()"
              />
              <Button
                  fluid
                  icon="pi pi-check"
                  label="Cadastrar"
                  @click="confirmAddPark"
              />
            </div>
          </template>
        </div>
      </template>
    </Card>

    <!-- AUTOCOMPLETE DA PESQUISA -->
    <div v-if="parkSuggestions.length && showParkSuggestions && showParkSugestionOnSeach"
         :style="autocompleteStyle"
         class="autocomplete-list-search">
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
</template>

<script lang="ts" setup>
import ParkDeleteDialog from "~/components/ParkDeleteDialog.vue";
import {PinRotate, Satellite, Tree} from 'reicon-vue';
import {onMounted, ref, watch} from 'vue'
import {
  type CoolingAnalysisResult,
  getParks,
  type Park,
  parkToSearchResult,
  type SearchParkResult
} from '@/services'
import {useNotifications} from '~/composables/useErrorHandler'
import {useParkSearch} from '~/composables/useParkSearch'
import {useCountrySearch} from '~/composables/useCountrySearch'
import {useCitySearch} from '~/composables/useCitySearch'
import {useAddParkForm} from '~/composables/useAddParkForm'
import {useParkMenu} from '~/composables/useParkMenu'
import {debounce} from '@/utils/parkSearchUtils'
import type {AddParkData, CitySuggestion, CountrySuggestion, ParkSuggestion} from '@/types/parkSearch'
import {fetchSatellites} from "~/services/satelliteService";
import {searchPark, type SearchParkParams} from "~/services/parkService";
import {analyzeParkCooling} from "~/services/eeService";

const {handleError, handleSuccess, handleInfo} = useNotifications()
const {parkSuggestions, showParkSuggestions, searchParks, hideSuggestions: hideParkSuggestions} = useParkSearch()
const showParkSugestionOnSeach = ref<boolean>(false)
const {
  countrySuggestions,
  showCountrySuggestions,
  searchCountries,
  hideSuggestions: hideCountrySuggestions,
  getCountryByCode
} = useCountrySearch()
const {citySuggestions, showCitySuggestions, searchCities, hideSuggestions: hideCitySuggestions} = useCitySearch()
const {
  isAddingPark,
  newParkName,
  newParkCountry,
  newParkCity,
  newParkStartDate,
  newParkEndDate,
  selectedCountryCode,
  startAddPark,
  cancelAddPark,
  confirmAddPark: confirmAddParkForm,
  selectCountry,
  newBufferDistance,
  newNumBuffers,
  isUpToDate
} = useAddParkForm()
const {isMenuOpen, selectedPark, menuCardRef, toggleMenu} = useParkMenu()



// ============================================================
// 🔥 ITEM SELECIONADO
// ============================================================
const selectedParkData = ref<ParkSuggestion | null>(null)

// ============================================================
// 🔥 Satellites CONFIG
// ============================================================
const availableSatellites = ref<Array<{ id: string, name: string, active: boolean }>>([])
const selectedSatellites = ref<string[]>(['Landsat 8'])
const loadingSatellites = ref(false)

// MODELOS
const search = defineModel<string>('search', {required: true})
const showPixels = defineModel<boolean>('showPixels', {default: true})

// PROPS
const props = defineProps<{
  loading: boolean
  analyzing: boolean
  results: SearchParkResult[]
  predefinedParks?: SearchParkResult[]
  showStats: boolean
  coolingData: CoolingAnalysisResult | null
  parkName: string
  pixelOpacity: number
  gradientMin: number | null
  gradientMax: number | null
  totalPixels: number
  manualGeometry?: any
}>()

// EMITS
const emit = defineEmits<{
  (e: 'search', selectedPark?: ParkSuggestion | null): void
  (e: 'select', park: SearchParkResult): void
  (e: 'parkDeleted', parkId: number): void
  (e: 'addPark', data: AddParkData & { numBuffers: number; bufferDistance: number }): void
  (e: 'refresh'): void
  (e: 'export'): void
  (e: 'settings'): void
  (e: 'about'): void
  (e: 'togglePixels'): void
  (e: 'updateOpacity', value: number): void
  (e: 'updateCoolingData', data: CoolingAnalysisResult): void
  (e: 'startDrawing'): void
  (e: 'stopDrawing'): void
  (e: 'pointsUpdated', points: Array<{ lat: number; lon: number }>): void
}>()

onMounted(() => {
  loadSatellites()
  loadParks()
})


// 🔥 GEOMETRIA MANUAL
const drawingMode = ref(false)
const manualPoints = ref<Array<{ lat: number; lon: number }>>([])

// LOCAL STATE
const cityWrapperRef = ref<HTMLElement | null>(null)
const searchInputRef = ref<HTMLElement | null>(null)

// 🔥 CALCULAR POSIÇÃO DO AUTOCOMPLETE
const autocompleteStyle = computed(() => {
  if (!searchInputRef.value) return {}
  const rect = searchInputRef.value.getBoundingClientRect()
  return {
    position: 'fixed' as const,
    top: `${rect.bottom + 4}px`,
    left: `${rect.left}px`,
    width: `${rect.width}px`,
    zIndex: 9999
  }
})

// Debounced search functions
const debouncedSearchParks = debounce(async (query: string) => {
  if (query.length >= 2) {
    const results = await searchParks(query, selectedCountryCode.value, newParkCity.value)
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

const parkList = ref<Park[]>([])
const loadingParks = ref(false)
const showDeleteDialog = ref(false)

async function loadParks() {
  loadingParks.value = true
  try {
    const data = await getParks()
    if (data.success) {
      parkList.value = data.parks
    }
  } catch (error) {
    console.error('Erro ao carregar parques:', error)
  } finally {
    loadingParks.value = false
  }
}

// ============================================================
// 🔥 GEOMETRIA MANUAL
// ============================================================
function toggleDrawingMode() {
  if (drawingMode.value) {
    drawingMode.value = false
    manualPoints.value = []
    emit('pointsUpdated', manualPoints.value)
    emit('stopDrawing')
    handleSuccess('Desenho cancelado')
  } else {
    drawingMode.value = true
    emit('startDrawing')
    handleInfo('Clique no mapa para adicionar pontos')
  }
}

function cancelDrawing() {
  manualPoints.value = []
  drawingMode.value = false
  emit('pointsUpdated', manualPoints.value)
  emit('stopDrawing')
  handleSuccess('Desenho cancelado')
}

function cancelAddParkLocal() {
  if (drawingMode.value) {
    drawingMode.value = false
    manualPoints.value = []
    emit('pointsUpdated', manualPoints.value)
    emit('stopDrawing')
  }
  cancelAddPark()
}

function addPoint(lat: number, lon: number) {
  manualPoints.value.push({lat, lon})
  emit('pointsUpdated', manualPoints.value)
}

function removePoint(index: number) {
  manualPoints.value.splice(index, 1)
  emit('pointsUpdated', manualPoints.value)
}

function useManualGeometry() {
  if (manualPoints.value.length < 3) {
    handleError('Precisa de pelo menos 3 pontos para formar um polígono')
    return
  }
  drawingMode.value = false
  emit('stopDrawing')
}

defineExpose({
  addPoint,
  drawingMode,
  manualPoints
})

// ============================================================
// 🔥 CARREGAR SATÉLITES
// ============================================================
async function loadSatellites() {
  loadingSatellites.value = true
  try {
    const data = await fetchSatellites()
    if (data && data.length > 0) {
      availableSatellites.value = data.filter(s => s.active)
    } else {
      availableSatellites.value = [
        {id: 'Landsat 8', name: 'Landsat 8', active: true},
      ]
      selectedSatellites.value = ['Landsat 8']
    }
  } catch (error) {
    console.error('Erro ao carregar satélites:', error)
  } finally {
    loadingSatellites.value = false
  }
}

// ============================================================
// 🔥 HANDLERS
// ============================================================
function handleSelectParkFromList() {
  if (selectedPark.value) {
    isMenuOpen.value = false
    const parkData = parkToSearchResult(selectedPark.value)
    emit('select', parkData)
    handleSuccess(`Parque "${selectedPark.value.name}" selecionado!`)
  }
}

function onParkInput(event: Event) {
  const target = event.target as HTMLInputElement
  const value = target.value
  debouncedSearchParks(value)
  showParkSugestionOnSeach.value = target.classList.contains('search-field')
}

function selectPark(park: ParkSuggestion) {
  selectedParkData.value = park
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
  search.value = park.name
  showParkSuggestions.value = false
  handleSuccess(`Parque "${park.name}" selecionado!`)
}

function onCountryInput() {
  debouncedSearchCountries(newParkCountry.value)
}

function selectCountryHandler(country: CountrySuggestion) {
  selectCountry(country.name)
  newParkCountry.value = country.name
  selectedCountryCode.value = country.code
  showCountrySuggestions.value = false
  newParkCity.value = ''
  citySuggestions.value = []
}

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

function selectCityHandler(city: CitySuggestion) {
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
// 🔥 CONFIRMAR CADASTRO
// ============================================================
async function confirmAddPark() {
  const baseData = confirmAddParkForm()
  if (!baseData) return

  const name = newParkName.value
  const city = newParkCity.value
  const country = newParkCountry.value

  if (!name || !city || !country) {
    handleError('Preencha todos os campos do parque')
    return
  }

  try {
    let osmId = selectedParkData.value?.osm_id ?? null
    let geometryToSend = null

    if (!osmId) {
      const nominatimResults = await searchParks(name, selectedCountryCode.value, city)
      if (!nominatimResults || nominatimResults.length === 0) {
        handleError('Parque não encontrado. Verifique o nome e tente novamente.')
        return
      }
      const selected = nominatimResults[0]
      if (!selected) {
        handleError('Erro ao obter dados do parque')
        return
      }
      osmId = selected.osm_id ?? null
      selectedParkData.value = selected
    }

    if (manualPoints.value.length >= 3) {
      const coords: number[][] = manualPoints.value.map(p => [p.lon, p.lat])
      const firstPoint = coords[0]
      if (!firstPoint) {
        handleError('Erro ao criar geometria: primeiro ponto não encontrado')
        return
      }
      coords.push(firstPoint)
      geometryToSend = {
        type: 'Polygon' as const,
        coordinates: [coords]
      }
    }

    if (!geometryToSend && !osmId) {
      handleError('Não foi possível obter o ID do parque ou geometria manual')
      return
    }

    const payload: SearchParkParams = {
      query: name,
      city: city,
      country: country,
    }
    if (osmId) payload.osm_id = osmId
    if (geometryToSend) payload.geometry = geometryToSend

    const result = await searchPark(payload)
    if (!result.results || result.results.length === 0) {
      handleError('Parque não encontrado no backend')
      return
    }

    const element = result.results[0]
    if (!element) {
      handleError('Parque não encontrado no backend')
      return
    }
    if (!element.geometry) {
      handleError('Parque encontrado mas sem geometria')
      return
    }

    const analysisResult = await analyzeParkCooling(element.geometry, baseData)
    emit('updateCoolingData', analysisResult)
    handleSuccess(`Análise do "${element.name}" concluída!`)

  } catch (error) {
    console.error('❌ Erro:', error)
    handleError('Falha ao analisar')
  }
}

function handleSearch() {
  if (!search.value || search.value.trim().length < 2) {
    handleError('Digite pelo menos 2 caracteres para buscar')
    return
  }
  emit('search', selectedParkData.value)
}

function handleParkDeleted(parkId: number) {
  loadParks()
  if (selectedPark.value?.id === parkId) {
    selectedPark.value = null
    emit('parkDeleted', parkId)
  }
}
</script>

<style scoped>
/* 🔥 WRAPPER */
.menu-wrapper {
  top: 12px;
  left: 12px;
  z-index: 1000;
  width: 360px;
}

/* 🔥 CARDS */
.menu-wrapper :deep(.p-card) {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  overflow: visible !important;
}

.menu-wrapper :deep(.p-card-body) {
  padding: 0 !important;
}

.menu-wrapper :deep(.p-card-content) {
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
}

.menu-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.menu-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.menu-label i,
.menu-label svg {
  display: flex;
  align-items: center;
  flex-shrink: 0;
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

/* 🔥 AUTOCOMPLETE DA PESQUISA */
.autocomplete-list-search {
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  max-height: 200px;
  overflow-y: auto;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.autocomplete-list-search .autocomplete-item {
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background 0.15s;
}

.autocomplete-list-search .autocomplete-item:hover {
  background: #f3f4f6;
}

.autocomplete-list-search .park-name {
  font-weight: 500;
  color: #1f2937;
}

.autocomplete-list-search .park-location {
  font-size: 12px;
  color: #575a61;
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

.date-hint {
  font-size: 12px;
  color: #6b7280;
  padding: 4px 0;
  font-style: italic;
}

.toggle-update-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 0;
}

.toggle-label {
  font-size: 13px;
  color: #4b5563;
  cursor: pointer;
}

/* 🔥 SATÉLITES */
.satellite-select-wrapper {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.satellite-hint {
  font-size: 11px;
  color: #9ca3af;
}

.satellite-select-wrapper :deep(.p-multiselect) {
  width: 100%;
}

.satellite-option {
  display: flex;
  width: 100%;
  flex-direction: column;
  padding: 2px 0;
  gap: 1px;
}

.satellite-option-main {
  display: flex;
  width: 100%;
  justify-content: space-between;
  align-items: center;
}

.satellite-option-name {
  font-size: 16px;
  font-weight: 500;
  color: #1f2937;
}

.satellite-option-resolution {
  font-size: 12px;
  font-weight: 400;
  color: #6b7280;
  background: #f3f4f6;
  padding: 0 8px;
  border-radius: 10px;
}

.satellite-option-desc {
  font-size: 12px;
  font-weight: 300;
  color: #9ca3af;
  margin-top: 0;
  line-height: 1.3;
}

.park-option {
  display: flex;
  flex-direction: column;
  padding: 2px 0;
}

.park-option-name {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
}

.park-option-location {
  font-size: 11px;
  color: #6b7280;
}

/* 🔥 GEOMETRIA MANUAL */
.geometry-manual-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.points-list {
  margin-top: 8px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 4px;
  max-height: 150px;
  overflow-y: auto;
}

.point-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-bottom: 1px solid #f3f4f6;
  font-size: 12px;
  font-family: 'Courier New', monospace;
}

.point-item:last-child {
  border-bottom: none;
}

.point-number {
  font-weight: 700;
  color: #3b82f6;
  font-size: 11px;
  min-width: 24px;
  background: #eef2ff;
  padding: 0 6px;
  border-radius: 10px;
  text-align: center;
  font-family: 'Titillium Web', sans-serif;
}

.point-coords {
  color: #1f2937;
  flex: 1;
}

.points-actions {
  display: flex;
  gap: 4px;
  padding: 4px;
  justify-content: flex-end;
}

.geometry-hint {
  font-size: 11px;
  color: #9ca3af;
  font-style: italic;
  display: block;
  margin-top: 4px;
}

.menu-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

/* RESPONSIVO */
@media (max-width: 480px) {
  .menu-wrapper {
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
</style>