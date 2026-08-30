<template>
  <div class="search-wrapper">
    <!-- 🔥 CARD 1: MENU + PESQUISA (LADO A LADO) -->
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

          <!-- 🔥 MODO NORMAL: SELECIONAR PARQUE -->
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
                    <span class="park-option-location">{{ slotProps.option.city }}, {{
                        slotProps.option.country
                      }}</span>
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
          </template>

          <!-- 🔥 MODO CADASTRO: FORMULÁRIO COMPLETO -->
          <template v-if="isAddingPark">
            <!-- 🔥 PARQUE (com autocomplete) -->
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
                <div v-if="parkSuggestions.length && showParkSuggestions &&  !showParkSugestionOnSeach"
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

            <!-- 🔥 PAÍS (com autocomplete, Brasil pré-selecionado) -->
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

            <!-- 🔥 CIDADE (com autocomplete, filtrada pelo país) -->
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

            <!-- 🔥 BUFFERS CONFIG -->
            <div class="menu-section">
              <label class="menu-label"><i class="pi pi-sitemap"></i> Configuração dos Buffers</label>
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

            <!-- 🔥 PERÍODO DE ANÁLISE -->
            <div class="menu-section">
              <label class="menu-label"><i class="pi pi-calendar"></i> Período de Análise</label>

              <!-- 🔥 DATA DE INÍCIO (SEMPRE OBRIGATÓRIA) -->
              <div class="date-range">
                <input
                    v-model="newParkStartDate"
                    class="add-field date-field"
                    placeholder="Data de início *"
                    type="date"
                />

                <!-- 🔥 DATA DE FIM (só aparece se NÃO estiver atualizado) -->
                <template v-if="!isUpToDate">
                  <span class="date-separator">até</span>
                  <input
                      v-model="newParkEndDate"
                      class="add-field date-field"
                      placeholder="Data de fim"
                      type="date"
                  />
                </template>

                <!-- 🔥 INDICADOR DE ATUALIZADO -->
                <span v-else class="date-hint"><i class="pi pi-satellite"></i> até a imagem mais recente</span>
              </div>

              <!-- 🔥 TOGGLE: Manter atualizado -->
              <div class="toggle-update-wrapper">
                <ToggleSwitch v-model="isUpToDate"/>
                <label class="toggle-label">Manter atualizado (buscar imagem mais recente)</label>
              </div>
            </div>

            <!-- 🔥 SATÉLITES (Multiselect) -->
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

            <!-- 🔥 GEOMETRIA MANUAL -->
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

              <!-- LISTA DE PONTOS -->
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

    <!-- 🔥 AUTOCOMPLETE DA PESQUISA (FORA DO CARD, ABSOLUTO) -->
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

    <!-- 🔥 CARD 2: RESULTADOS DA PESQUISA -->
    <CollapsibleCard
        v-if="results.length"
        :badge="results.length"
        :defaultExpanded="true"
        icon="pi pi-list"
        title="Resultados"
    >
      <div
          v-for="item in results"
          :key="item.id"
          class="result-item"
          @click="handleSelect(item)"
      >
        <label class="result-name">
          <Tree :size="16"/>
          <span>{{ item.tags?.name || item.name || 'Parque sem nome' }}</span>
        </label>
        <label class="result-location">
          <i class="pi pi-map-marker"></i>
          {{ item.city }}, {{ item.country }}
        </label>
        <label class="result-osm-id">
          <i class="pi pi-tag"></i>
          ID: {{ item.osm_id }}
        </label>
      </div>
    </CollapsibleCard>

    <!-- 🔥 CARD 3: ANÁLISE TÉRMICA -->
    <CollapsibleCard
        v-if="showStats && coolingData"
        :defaultExpanded="true"
        icon="pi pi-chart-bar"
        title="Análise Térmica"
    >
      <!-- RESULTADOS DA ANÁLISE -->
      <div class="stats-header">
        <h4>
          <label>
            <Tree :size="16"/>
            <span>{{ parkName }}</span>
          </label>
        </h4>
        <Tag
            :severity="coolingData.success ? 'success' : 'danger'"
            :value="coolingData.success ? 'OK' : 'Falha'"
        />
      </div>

      <!-- 🔥 DATA DA IMAGEM -->
      <div v-if="coolingData.image_date" class="stat-item image-date">
        <span><i class="pi pi-calendar"></i> Data da Imagem</span>
        <strong>{{ formatDate(coolingData.image_date) }}</strong>
      </div>

      <!-- 🔥 INFO DOS BUFFERS USADOS -->
      <div class="stat-item buffer-info">
        <span><i class="pi pi-sitemap"></i> Buffers</span>
        <strong>{{ coolingData.num_buffers || 11 }} anéis × {{ coolingData.buffer_distance || 30 }}m</strong>
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
        <i class="pi pi-exclamation-triangle"></i>
        {{ coolingData.error }}
      </div>

      <!-- PIXELS -->
      <template v-if="coolingData?.buffers">
        <Divider/>
        <div class="pixels-section">
          <!-- TOGGLE PRINCIPAL -->
          <div class="pixels-toggle-wrapper">
            <div class="pixels-toggle-left">
              <Checkbox
                  v-model="showPixels"
                  binary
                  @update:model-value="handleTogglePixels"
              />
              <label class="pixels-toggle-label">
                <i class="pi pi-th-large pixels-icon"></i>
                <span>Mostrar pixels de temperatura</span>
              </label>
            </div>
            <Badge
                v-if="showPixels"
                :value="`${totalPixels} px`"
                class="pixels-badge"
                severity="info"
            />
          </div>

          <!-- CONTROLES EXPANDIDOS -->
          <div v-if="showPixels" class="pixels-controls">
            <!-- OPACIDADE -->
            <div class="opacity-control">
              <div class="opacity-header">
                <i class="pi pi-eye opacity-icon"></i>
                <span class="opacity-label">Opacidade</span>
                <span class="opacity-value">{{ Math.round(pixelOpacity * 100) }}%</span>
              </div>
              <input
                  :value="pixelOpacity * 100"
                  class="opacity-slider"
                  max="100"
                  min="0"
                  type="range"
                  @input="handleOpacityChange($event)"
              />
            </div>

            <!-- GRADIENTE DE TEMPERATURA -->
            <div v-if="gradientMin !== null && gradientMax !== null" class="gradient-legend">
              <div class="gradient-header">
                <div class="gradient-header-left">
                  <i class="pi pi-thermometer gradient-icon"></i>
                  <span class="gradient-title">Temperatura</span>
                </div>
                <Badge :value="`${totalPixels} px`" class="gradient-badge" severity="secondary"/>
              </div>
              <div class="gradient-bar"></div>
              <div class="gradient-labels">
                <span class="gradient-min">{{ gradientMin.toFixed(1) }}°C</span>
                <span class="gradient-max">{{ gradientMax.toFixed(1) }}°C</span>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- BUFFERS -->
      <template v-if="coolingData?.buffers">
        <Divider/>
        <div class="buffer-stats">
          <div class="buffer-header">
            <h4><i class="pi pi-sitemap buffer-header-icon"></i> Anéis de Temperatura</h4>
            <span class="buffer-total">{{ coolingData.buffers.length }} anéis</span>
          </div>

          <div class="stats-grid">
            <div
                v-for="(buffer, index) in coolingData.buffers"
                :key="buffer.distance"
                :style="{
            background: getBufferGradient(buffer, coolingData.buffers),
            borderColor: getBufferBorderColor(buffer, coolingData.buffers),
          }"
                :title="`${buffer.distance}m - ${buffer.statistics?.mean?.toFixed(1) ?? 'N/A'}°C - ${buffer.statistics?.count ?? 0} pixels`"
                class="stats-item"
            >
              <div class="stats-item-header">
          <span class="stats-distance">
            <i class="pi pi-arrow-right" style="font-size: 7px;"></i>
            {{ buffer.distance }}m
          </span>
                <span class="stats-badge">{{ index + 1 }}</span>
              </div>

              <div class="stats-temperature">
                <span class="stats-value">{{ buffer.statistics?.mean?.toFixed(1) ?? 'N/A' }}</span>
                <span class="stats-unit">°C</span>
              </div>

              <div class="stats-pixels">
                <span>{{ buffer.statistics?.count ?? 0 }}p</span>
              </div>

              <!-- BARRA DE PROGRESSO RELATIVA -->
              <div class="stats-bar-wrapper">
                <div
                    :style="{
              width: getBufferPercent(buffer, coolingData.buffers),
              background: getBufferBarColor(buffer, coolingData.buffers)
            }"
                    class="stats-bar"
                ></div>
              </div>
            </div>
          </div>

        </div>
      </template>

      <!-- 🔥 QA - COM HEADER CLICÁVEL PARA RECOLHER -->
      <template v-if="coolingData?.buffers">
        <Divider/>

        <!-- HEADER CLICÁVEL DA SEÇÃO QA -->
        <div
            :class="{ 'qa-collapsed': !isQaExpanded }"
            class="qa-section-header"
            @click="toggleQaSection"
        >
          <div class="qa-section-header-left">
            <i class="pi pi-shield qa-header-icon"></i>
            <span class="qa-section-title">Qualidade da Imagem (QA)</span>
          </div>
          <div class="qa-section-header-right">
            <i :class="isQaExpanded ? 'pi pi-chevron-up' : 'pi pi-chevron-down'" class="qa-toggle-icon"></i>
          </div>
        </div>

        <!-- CONTEÚDO QA (EXPANDE/ENCOLHE) -->
        <transition name="expand">
          <div v-if="isQaExpanded" class="qa-content-wrapper">
            <div class="qa-content">
              <!-- 🔥 QA_PIXEL -->
              <div v-if="coolingData.qa_pixel" class="qa-section">
                <div class="qa-header">
                  <div class="qa-header-left">
                    <i class="pi pi-chart-pie qa-header-icon"></i>
                    <span class="qa-header-title">Qualidade dos Pixels</span>
                  </div>
                  <Badge :value="`${coolingData.qa_pixel.total} pixels`" severity="info"/>
                </div>

                <div class="qa-types">
                  <div
                      v-for="(type, key) in coolingData.qa_pixel.types"
                      :key="key"
                      class="qa-type-item"
                  >
                    <div class="qa-type-row">
                      <span class="qa-emoji">{{ type.emoji || '❓' }}</span>
                      <span class="qa-description">{{ type.description }}</span>
                    </div>
                    <div class="qa-type-row">
                      <span class="qa-count">{{ type.count }} px</span>
                      <ProgressBar
                          :showValue="false"
                          :value="type.percent"
                          class="qa-progress"
                      />
                      <span class="qa-percent">{{ type.percent }}%</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 🔥 ST_QA -->
              <div v-if="coolingData.st_qa" class="qa-section">
                <Divider/>
                <div class="qa-header">
                  <div class="qa-header-left">
                    <i class="pi pi-gauge qa-header-icon"></i>
                    <span class="qa-header-title">Incerteza da Temperatura</span>
                  </div>
                  <Badge :value="`${coolingData.st_qa.count} pixels`" severity="info"/>
                </div>

                <div class="st-qa-stats">
                  <div class="st-qa-item">
                    <span class="st-qa-label">Média</span>
                    <span :class="getStQaClass(coolingData.st_qa.mean_kelvin)" class="st-qa-value">
                {{ coolingData.st_qa.mean_kelvin }} K
              </span>
                  </div>
                  <div class="st-qa-item">
                    <span class="st-qa-label">Mínimo</span>
                    <span class="st-qa-value">{{ coolingData.st_qa.min_kelvin }} K</span>
                  </div>
                  <div class="st-qa-item">
                    <span class="st-qa-label">Máximo</span>
                    <span class="st-qa-value">{{ coolingData.st_qa.max_kelvin }} K</span>
                  </div>
                </div>

                <div :class="getStQaStatus(coolingData.st_qa.mean_kelvin)" class="st-qa-status">
                  <label>
                    <i :class="getStatusIcon(coolingData.st_qa.mean_kelvin)"></i>
                    <span>{{ getStQaMessage(coolingData.st_qa.mean_kelvin) }}</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        </transition>
      </template>
    </CollapsibleCard>

  </div>
</template>

<script lang="ts" setup>
import {Satellite, Tree} from 'reicon-vue';
import {onMounted, ref, watch} from 'vue'
import {
  analyzeParkCooling,
  type CoolingAnalysisResult,
  formatCoolingStats,
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
// 🔥 ITEM SELECIONADO (O QUE O USUÁRIO ESCOLHEU)
// ============================================================
const selectedParkData = ref<ParkSuggestion | null>(null)
const selectedCityData = ref<CitySuggestion | null>(null)
const selectedCountryData = ref<CountrySuggestion | null>(null)

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

// 🔥 CONTROLE DE EXPANSÃO DA SEÇÃO QA
const isQaExpanded = ref(true)

function toggleQaSection() {
  isQaExpanded.value = !isQaExpanded.value
}

// 🔥 GEOMETRIA MANUAL
const drawingMode = ref(false)
const manualPoints = ref<Array<{ lat: number; lon: number }>>([])
let drawInteraction: any = null

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
    const results = await searchParks(
        query,
        selectedCountryCode.value,
        newParkCity.value
    )
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
// 🔥 geometrica manual
// ============================================================

function toggleDrawingMode() {
  if (drawingMode.value) {
    // 🔥 CANCELA O DESENHO
    drawingMode.value = false
    manualPoints.value = []
    emit('pointsUpdated', manualPoints.value)
    emit('stopDrawing')
    handleSuccess('Desenho cancelado')
  } else {
    // 🔥 ATIVA O DESENHO
    drawingMode.value = true
    emit('startDrawing')
    handleInfo('Clique no mapa para adicionar pontos')
  }
}

function cancelDrawing() {
  // 🔥 LIMPA OS PONTOS
  manualPoints.value = []

  // 🔥 SAI DO MODO DE DESENHO
  drawingMode.value = false

  // 🔥 EMITE O EVENTO PARA O PAI
  emit('pointsUpdated', manualPoints.value)
  emit('stopDrawing')

  // 🔥 LIMPA OS PONTOS DO MAPA (emite evento para o pai)
  handleSuccess('Desenho cancelado')
}

function cancelAddParkLocal() {
  // 🔥 CANCELA O DESENHO SE ESTIVER ATIVO
  if (drawingMode.value) {
    drawingMode.value = false
    manualPoints.value = []
    emit('pointsUpdated', manualPoints.value)
    emit('stopDrawing')
  }

  // 🔥 CANCELA O CADASTRO (CHAMA A DO COMPOSABLE)
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

  // 🔥 VERIFICAÇÃO DE SEGURANÇA
  const firstPoint = manualPoints.value[0]
  if (!firstPoint) {
    handleError('Erro ao obter o primeiro ponto')
    return
  }


  drawingMode.value = false
  emit('stopDrawing')

  // emit('select', {
  //   name: 'Geometria Manual',
  //   city: newParkCity.value || 'Local',
  //   country: newParkCountry.value || 'Brasil',
  //   geometry: geometry,
  //   tags: { name: 'Geometria Manual' }
  // } as SearchParkResult)
  //
  // // Limpa os pontos
  // manualPoints.value = []
  // handleSuccess('Geometria manual criada!')
}

// 🔥 EXPORTA A FUNÇÃO PARA O PAI ADICIONAR PONTO
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
      // Fallback
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
// 🔥 HANDLER - SELECIONAR PARQUE DA LISTA
// ============================================================
const isResultsExpanded = ref(false)

function toggleResults() {
  isResultsExpanded.value = !isResultsExpanded.value
}

function handleSelectParkFromList() {
  if (selectedPark.value) {
    isMenuOpen.value = false

    // 🔥 CRIA UM OBJETO SearchParkResult COMPLETO COM A GEOMETRIA
    const parkData = parkToSearchResult(selectedPark.value)


    // Emite o select com os dados completos
    emit('select', parkData)
    handleSuccess(`Parque "${selectedPark.value.name}" selecionado!`)
  }
}

// ============================================================
// 🔥 EVENT HANDLERS - PARQUE
// ============================================================

function onParkInput(event: Event) {
  const target = event.target as HTMLInputElement
  const value = target.value
  debouncedSearchParks(value)
  showParkSugestionOnSeach.value = target.classList.contains('search-field');

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

// ============================================================
// 🔥 EVENT HANDLERS - PAÍS
// ============================================================
function onCountryInput() {
  debouncedSearchCountries(newParkCountry.value)
}

function selectCountryHandler(country: CountrySuggestion) {
  selectedCountryData.value = country


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

function selectCityHandler(city: CitySuggestion) {
  selectedCityData.value = city

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

    // 🔥 SE NÃO TIVER OSM_ID, BUSCA NO NOMINATIM
    if (!osmId) {
      const nominatimResults = await searchParks(name, selectedCountryCode.value, city)

      if (!nominatimResults || nominatimResults.length === 0) {
        handleError('Parque não encontrado. Verifique o nome e tente novamente.')
        return
      }

      // 🔥 PEGA O PRIMEIRO RESULTADO (COM VERIFICAÇÃO)
      const selected = nominatimResults[0]
      if (!selected) {
        handleError('Erro ao obter dados do parque')
        return
      }

      osmId = selected.osm_id ?? null

      // 🔥 ATUALIZA O PARQUE SELECIONADO
      selectedParkData.value = selected
    }


    // 🔥 PRIORIDADE: GEOMETRIA MANUAL
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

    // 🔥 VERIFICA SE TEM OSM_ID ANTES DE ENVIAR
    if (!geometryToSend && !osmId) {
      handleError('Não foi possível obter o ID do parque ou geometria manual')
      return
    }

    const payload: SearchParkParams = {
      query: name,
      city: city,
      country: country,
    }
    if (osmId) {
      payload.osm_id = osmId
    }
    if (geometryToSend) {
      payload.geometry = geometryToSend
    }
    // 🔥 ENVIA PARA O BACKEND
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

    // 🔥 ANALISAR
    const analysisResult = await analyzeParkCooling(
        element.geometry,
        baseData
    )

    emit('updateCoolingData', analysisResult)
    handleSuccess(`Análise do "${element.name}" concluída!`)

  } catch (error) {
    console.error('❌ Erro:', error)
    handleError('Falha ao analisar')
  }
}

function handleSelectPark() {
  if (selectedPark.value) {
    isMenuOpen.value = false
    emit('select', selectedPark.value)
  }
}

function handleSearch() {
  console.log(selectedParkData.value)
  if (!search.value || search.value.trim().length < 2) {
    handleError('Digite pelo menos 2 caracteres para buscar')
    return
  }
  emit('search', selectedParkData.value)
}

function handleSelect(item: SearchParkResult) {
  emit('select', item)
  handleSuccess(`Parque "${item.tags?.name || 'sem nome'}" selecionado!`)
}

function handleTogglePixels() {
  emit('togglePixels')
}

function handleOpacityChange(event: Event) {
  const target = event.target as HTMLInputElement
  const value = parseFloat(target.value)
  emit('updateOpacity', value)
}

function getStQaClass(value: number | null | undefined): string {
  if (value === null || value === undefined) return ''
  if (value < 3) return 'good'
  if (value < 5) return 'medium'
  return 'poor'
}

function getStQaStatus(value: number | null | undefined): string {
  if (value === null || value === undefined) return ''
  if (value < 3) return 'good'
  if (value < 5) return 'medium'
  return 'poor'
}

function getStQaMessage(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'Sem dados'
  if (value < 3) return 'Temperatura confiável (incerteza < 3K)'
  if (value < 5) return 'Temperatura com incerteza moderada (3-5K)'
  return 'Temperatura NÃO é confiável (incerteza > 5K)'
}

function getStatusIcon(meanKelvin: number | null | undefined): string {
  if (meanKelvin === null || meanKelvin === undefined) return 'pi pi-help-circle';
  if (meanKelvin < 3) return 'pi pi-check-circle';
  if (meanKelvin < 5) return 'pi pi-exclamation-circle';
  return 'pi pi-times-circle';
}

// 🔥 FUNÇÕES PARA CORES RELATIVAS DOS BUFFERS

// 🔥 CALCULA O PERCENTUAL RELATIVO DA TEMPERATURA
function getRelativeValue(value: number, min: number, max: number): number {
  if (max === min) return 0.5;
  return (value - min) / (max - min);
}

// 🔥 OBTÉM O GRADIENTE RELATIVO
function getBufferGradient(buffer: any, buffers: any[]): string {
  const mean = buffer.statistics?.mean;
  if (mean === null || mean === undefined) return '#f5f5f5';

  const temps = buffers.map(b => b.statistics?.mean ?? 0).filter(t => t > 0);
  if (temps.length < 2) return '#f5f5f5';

  const min = Math.min(...temps);
  const max = Math.max(...temps);
  const relative = getRelativeValue(mean, min, max);

  // 🔥 GRADIENTE DO AZUL (MAIS FRIO) PARA VERMELHO (MAIS QUENTE)
  const r = Math.round(59 + (196 * relative));  // 59 -> 255
  const g = Math.round(130 - (100 * relative)); // 130 -> 30
  const b = Math.round(246 - (200 * relative)); // 246 -> 46

  return `linear-gradient(135deg, rgba(${r}, ${g}, ${b}, 0.15), rgba(${r}, ${g}, ${b}, 0.25))`;
}

// 🔥 OBTÉM A COR DA BORDA RELATIVA
function getBufferBorderColor(buffer: any, buffers: any[]): string {
  const mean = buffer.statistics?.mean;
  if (mean === null || mean === undefined) return '#d1d5db';

  const temps = buffers.map(b => b.statistics?.mean ?? 0).filter(t => t > 0);
  if (temps.length < 2) return '#d1d5db';

  const min = Math.min(...temps);
  const max = Math.max(...temps);
  const relative = getRelativeValue(mean, min, max);

  const r = Math.round(59 + (196 * relative));
  const g = Math.round(130 - (100 * relative));
  const b = Math.round(246 - (200 * relative));

  return `rgb(${r}, ${g}, ${b})`;
}

// 🔥 OBTÉM A COR DA BARRA RELATIVA
function getBufferBarColor(buffer: any, buffers: any[]): string {
  const mean = buffer.statistics?.mean;
  if (mean === null || mean === undefined) return '#d1d5db';

  const temps = buffers.map(b => b.statistics?.mean ?? 0).filter(t => t > 0);
  if (temps.length < 2) return '#d1d5db';

  const min = Math.min(...temps);
  const max = Math.max(...temps);
  const relative = getRelativeValue(mean, min, max);

  // 🔥 GRADIENTE DO AZUL PARA VERMELHO
  const r = Math.round(59 + (196 * relative));
  const g = Math.round(130 - (100 * relative));
  const b = Math.round(246 - (200 * relative));

  return `rgb(${r}, ${g}, ${b})`;
}

// 🔥 OBTÉM O PERCENTUAL RELATIVO PARA BARRA
function getBufferPercent(buffer: any, buffers: any[]): string {
  const mean = buffer.statistics?.mean;
  if (mean === null || mean === undefined) return '0%';

  const temps = buffers.map(b => b.statistics?.mean ?? 0).filter(t => t > 0);
  if (temps.length < 2) return '50%';

  const min = Math.min(...temps);
  const max = Math.max(...temps);
  const relative = getRelativeValue(mean, min, max);

  return `${Math.max(5, Math.min(100, relative * 100))}%`;
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
  max-height: 98vh;
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

.search-wrapper::-webkit-scrollbar {
  width: 8px;
}

.search-wrapper::-webkit-scrollbar-track {
  background: transparent;
}

.search-wrapper::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.30);
  border-radius: 4px;
}

.search-wrapper::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.40);
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

/* 🔥 ESTILO GLOBAL PARA LABELS COM ÍCONES */
label:has(i, svg, .pi) {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 🔥 ALINHA ÍCONES DENTRO DE LABELS */
label i,
label svg,
label .pi {
  display: inline-flex;
  flex-shrink: 0;
  vertical-align: middle;
}

/* 🔥 AUTOCOMPLETE DA PESQUISA (FORA DO CARD, POSIÇÃO FIXA) */
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
  color: #575a61;;
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

  border: none !important;
}

.buffer-info span {
  color: #15803d;
}

.buffer-info strong {
  color: #166534;
}

/* 🔥 IMAGE DATE */
.image-date {
  background: #f0f9ff;
  border-radius: 4px;
  padding: 4px 8px !important;
  margin-bottom: 4px;
  margin-top: 4px;
  border: none !important;
}

.image-date span {
  color: #0369a1;
}

.image-date strong {
  color: #0c4a6e;
  font-weight: 600;
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


/* 🔥 ITEM */
.result-item {
  padding: 10px 0;
  cursor: pointer;
  border-bottom: 1px solid #f3f4f6;
  transition: all 0.15s ease;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.result-item:last-child {
  border-bottom: none;
}

.result-item:hover {
  background: #f0f7ff;
  padding-left: 18px;
}

.result-name {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
}

.result-location {
  font-size: 12px;
  color: #6b7280;
}

.result-osm-id {
  font-size: 10px;
  color: #9ca3af;
}

/* 🔥 TRANSIÇÃO */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
  max-height: 300px;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
}

.expand-enter-to,
.expand-leave-from {
  max-height: 300px;
  opacity: 1;
}


.stats-header {
  padding-top: 10px;
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
  padding: 4px 8px;
  font-size: 13px;

}

.stat-item i,
.buffer-info i,
.image-date i {
  display: inline-flex;
  align-items: center;
  margin-right: 4px;
}

.stat-item:last-of-type {
  border-bottom: none !important;
}

.error-msg {
  padding: 8px 12px;
  background: #fee2e2;
  color: #991b1b;
  border-radius: 4px;
  font-size: 12px;
  margin-top: 4px;
}

/* 🔥 PIXELS SECTION - DESIGN MELHORADO */
.pixels-section {
  margin-top: 4px;
}

/* 🔥 TOGGLE PRINCIPAL */
.pixels-toggle-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s ease;
}

.pixels-toggle-wrapper:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.pixels-toggle-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pixels-toggle-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
  cursor: pointer;
  user-select: none;
}

.pixels-icon {
  font-size: 14px;
  color: #6366f1;
}

.pixels-badge {
  font-size: 10px;
  font-weight: 600;
}

/* 🔥 CONTROLES EXPANDIDOS */
.pixels-controls {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  animation: slideDown 0.25s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 🔥 OPACIDADE */
.opacity-control {
  padding: 8px 12px;
  background: #fafbfc;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.opacity-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.opacity-icon {
  font-size: 12px;
  color: #6b7280;
}

.opacity-label {
  font-size: 12px;
  font-weight: 500;
  color: #4b5563;
  flex: 1;
}

.opacity-value {
  font-size: 12px;
  font-weight: 600;
  color: #6366f1;
  background: #eef2ff;
  padding: 0 8px;
  border-radius: 10px;
  min-width: 40px;
  text-align: center;
}

.opacity-slider {
  width: 100%;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: linear-gradient(to right, #3b82f6, #8b5cf6);
  border-radius: 2px;
  outline: none;
  margin-top: 2px;
  cursor: pointer;
}

.opacity-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #6366f1;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(99, 102, 241, 0.3);
  transition: all 0.15s ease;
}

.opacity-slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.4);
}

.opacity-slider::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #6366f1;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(99, 102, 241, 0.3);
}

/* 🔥 GRADIENTE */
.gradient-legend {
  padding: 8px 12px;
  background: #fafbfc;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.gradient-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.gradient-header-left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.gradient-icon {
  font-size: 12px;
  color: #ef4444;
}

.gradient-title {
  font-size: 12px;
  font-weight: 500;
  color: #4b5563;
}

.gradient-badge {
  font-size: 10px;
}

.gradient-bar {
  width: 100%;
  height: 10px;
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
  margin: 2px 0;
}

.gradient-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: #6b7280;
  font-weight: 500;
}

.gradient-min {
  color: #3b82f6;
}

.gradient-max {
  color: #ef4444;
}

/* 🔥 RESPONSIVO */
@media (max-width: 480px) {
  .pixels-toggle-wrapper {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
    padding: 8px 10px;
  }

  .pixels-toggle-left {
    width: 100%;
  }

  .pixels-badge {
    align-self: flex-start;
  }

  .opacity-control,
  .gradient-legend {
    padding: 6px 10px;
  }
}

/* 🔥 BUFFERS - ESTILO COMPACTO */
.buffer-stats {
  margin-top: 6px;
}

.buffer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.buffer-header h4 {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.buffer-header-icon {
  font-size: 14px;
  color: #6366f1;
  background: #eef2ff;
  padding: 2px 5px;
  border-radius: 4px;
}

.buffer-total {
  font-size: 11px;
  font-weight: 500;
  color: #6b7280;
  background: #f3f4f6;
  padding: 1px 10px;
  border-radius: 10px;
}

/* 🔥 GRID MAIS COMPACTO */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(65px, 1fr));
  gap: 5px;
}

/* 🔥 CARD DO ANEL - MENOR */
.stats-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4px 4px 6px 4px;
  border-radius: 6px;
  border: 1.5px solid #e5e7eb;
  transition: all 0.2s ease;
  position: relative;
  min-height: 52px;
  background: #fafafa;
}

.stats-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border-color: #6366f1;
  z-index: 1;
}

/* 🔥 HEADER DO ANEL - MENOR */
.stats-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  margin-bottom: 1px;
}

.stats-distance {
  font-size: 12px;
  font-weight: 600;
  color: #4b5563;
  display: flex;
  align-items: center;
  gap: 1px;
}

.stats-badge {
  font-size: 10px;
  font-weight: 700;
  color: #6b7280;
  background: #f3f4f6;
  padding: 0 4px;
  border-radius: 8px;
  line-height: 14px;
}

/* 🔥 TEMPERATURA - MENOR */
.stats-temperature {
  display: flex;
  align-items: baseline;
  gap: 1px;
  margin: 0;
  line-height: 1;
}

.stats-value {
  font-size: 16px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1.1;
}

.stats-unit {
  font-size: 9px;
  font-weight: 500;
  color: #6b7280;
}

/* 🔥 PIXELS - MENOR */
.stats-pixels {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 12px;
  color: #575a61;
  margin-top: 1px;
}

/* 🔥 BARRA DE PROGRESSO - MAIS FINA */
.stats-bar-wrapper {
  width: 100%;
  height: 3px;
  background: #f3f4f6;
  border-radius: 2px;
  margin-top: 4px;
  overflow: hidden;
}

.stats-bar {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
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

/* 🔥 TOGGLE UPDATE */
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

.date-hint {
  font-size: 12px;
  color: #6b7280;
  padding: 4px 0;
  font-style: italic;
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

/* Melhorar o MultiSelect */
.satellite-select-wrapper :deep(.p-multiselect) {
  width: 100%;
}

/* 🔥 SATÉLITE OPTION */
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

/* 🔥 QA SECTION */
.qa-section {
  margin-top: 12px;
}

.qa-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 10px;
  color: #1f2937;
}

.qa-types {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.qa-type-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  background: #f8f9fa;
  border-radius: 6px;
  font-size: 13px;
  border: 1px solid #f1f3f5;
  transition: background 0.2s;
}

.qa-type-item:hover {
  background: #f1f5f9;
}

.qa-type-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.qa-emoji {
  font-size: 18px;
  flex-shrink: 0;
}

.qa-description {
  font-size: 13px;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.qa-type-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.qa-count {
  font-size: 12px;
  color: #6b7280;
  min-width: 50px;
  text-align: right;
}

.qa-progress {
  width: 150px;
  height: 6px;
  border-radius: 3px;
}

.qa-progress :deep(.p-progressbar-value) {
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
  border-radius: 3px;
}

.qa-percent {
  font-weight: 600;
  font-size: 13px;
  min-width: 45px;
  text-align: right;
  color: #1f2937;
}

/* 🔥 ST_QA */
.st-qa-stats {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.st-qa-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #f8f9fa;
  padding: 8px 16px;
  border-radius: 6px;
  flex: 1;
  min-width: 60px;
  border: 1px solid #f1f3f5;
}

.st-qa-label {
  font-size: 10px;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.st-qa-value {
  font-weight: 700;
  font-size: 16px;
  margin-top: 2px;
}

.st-qa-value.good {
  color: #16a34a;
}

.st-qa-value.medium {
  color: #f59e0b;
}

.st-qa-value.poor {
  color: #dc2626;
}

/* 🔥 ST_QA STATUS */
.st-qa-status {
  margin-top: 8px;
  padding: 10px 14px;
  border-radius: 6px;
  text-align: center;
  font-weight: 600;
  font-size: 13px;
  border: 1px solid transparent;
}

.st-qa-status.good {
  background: #dcfce7;
  color: #166534;
  border-color: #86efac;
}

.st-qa-status.medium {
  background: #fef3c7;
  color: #92400e;
  border-color: #fcd34d;
}

.st-qa-status.poor {
  background: #fee2e2;
  color: #991b1b;
  border-color: #fca5a5;
}


/* 🔥 RESPONSIVIDADE PARA QA */
@media (max-width: 480px) {
  .qa-type-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
    padding: 8px 10px;
  }

  .qa-type-right {
    width: 100%;
    justify-content: space-between;
  }

  .qa-progress {
    width: 60px;
  }

  .st-qa-stats {
    flex-direction: column;
    gap: 6px;
  }

  .st-qa-item {
    flex-direction: row;
    justify-content: space-between;
    padding: 6px 12px;
  }

  .st-qa-label {
    text-transform: none;
    font-size: 12px;
  }

  .st-qa-value {
    font-size: 14px;
  }

  .st-qa-status {
    font-size: 12px;
    padding: 8px 10px;
  }
}

/* 🔥 QA SECTION HEADER (CLICÁVEL) - MAIS VISÍVEL */
.qa-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  background: linear-gradient(135deg, #f0f4ff 0%, #e8edf5 100%);
  border: 2px solid #c7d2fe;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  user-select: none;
  margin: 12px 0 4px 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.qa-section-header:hover {
  background: linear-gradient(135deg, #e8edff 0%, #dce3f5 100%);
  border-color: #818cf8;
  box-shadow: 0 4px 8px rgba(99, 102, 241, 0.15);
  transform: translateY(-1px);
}

.qa-section-header:active {
  transform: scale(0.98);
}

.qa-section-header.qa-collapsed {
  background: linear-gradient(135deg, #f8f9fa 0%, #f1f3f5 100%);
  border-color: #d1d5db;
}

.qa-section-header.qa-collapsed:hover {
  background: linear-gradient(135deg, #f1f3f5 0%, #e5e7eb 100%);
  border-color: #9ca3af;
}

.qa-section-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.qa-header-icon {
  font-size: 20px;
  color: #6366f1;
  background: white;
  padding: 6px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(99, 102, 241, 0.15);
}

.qa-section-title {
  font-size: 16px;
  font-weight: 700;
  color: #1f2937;
}

.qa-status-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 10px;
}

.qa-section-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.qa-toggle-icon {
  font-size: 18px;
  color: #6366f1;
  transition: transform 0.3s ease;
  font-weight: 700;
}

.qa-toggle-label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

/* 🔥 WRAPPER DO CONTEÚDO EXPANSÍVEL */
.qa-content-wrapper {
  background: #fafbfc;
  border-radius: 8px;
  padding: 4px;
  margin-top: 4px;
  border: 1px solid #e5e7eb;
}

.qa-content {
  padding: 8px 12px 12px 12px;
}

/* 🔥 HEADERS DAS SEÇÕES INTERNAS */
.qa-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0 8px 0;
}

.qa-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.qa-header-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

/* 🔥 RESPONSIVIDADE */
@media (max-width: 480px) {
  .qa-section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
    padding: 12px 14px;
  }

  .qa-section-header-right {
    width: 100%;
    justify-content: flex-start;
  }

  .qa-toggle-label {
    font-size: 11px;
  }
}

/* 🔥 TRANSIÇÃO SUAVE */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
  max-height: 1000px;
  overflow: hidden;
  opacity: 1;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
}


/* 🔥 SCROLLBAR DA LISTA DE TIPOS */
.qa-types::-webkit-scrollbar {
  width: 3px;
}

.qa-types::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.qa-types::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}

.qa-types::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

/* 🔥 ANIMAÇÃO DE CARREGAMENTO DOS QA */
.qa-type-item {
  animation: fadeInUp 0.3s ease forwards;
  opacity: 0;
}

.qa-type-item:nth-child(1) {
  animation-delay: 0.05s;
}

.qa-type-item:nth-child(2) {
  animation-delay: 0.10s;
}

.qa-type-item:nth-child(3) {
  animation-delay: 0.15s;
}

.qa-type-item:nth-child(4) {
  animation-delay: 0.20s;
}

.qa-type-item:nth-child(5) {
  animation-delay: 0.25s;
}

.qa-type-item:nth-child(6) {
  animation-delay: 0.30s;
}


@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.qa-type-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #f1f3f5;
}

.qa-type-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.qa-type-row:first-child {
  font-weight: 500;
}

.qa-emoji {
  font-size: 18px;
  flex-shrink: 0;
}

.qa-description {
  font-size: 13px;
  color: #1f2937;
}

.qa-count {
  font-size: 12px;
  color: #6b7280;
  min-width: 50px;
}

.qa-progress {
  flex: 1;
  height: 6px;
  max-width: 200px;
}

.qa-percent {
  font-weight: 600;
  font-size: 13px;
  min-width: 45px;
  text-align: right;
  color: #1f2937;
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
</style>