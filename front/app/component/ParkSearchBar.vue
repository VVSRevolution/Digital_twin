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
              @click="handleAddPark"
          />

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
import { ref, watch } from 'vue'
import { formatCoolingStats, type CoolingAnalysisResult } from '@/services/eeService'

interface SearchResult {
  id: number
  lat: number
  lon: number
  tags?: {
    name?: string
    [key: string]: unknown
  }
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
  (e: 'addPark'): void
  (e: 'refresh'): void
  (e: 'export'): void
  (e: 'settings'): void
  (e: 'about'): void
  (e: 'togglePixels'): void
}>()

// CONTROLE DO MENU
const isMenuOpen = ref(false)
const selectedPark = ref<SearchResult | null>(null)

// FORMATADOR DE STATS
const formatStats = (data: CoolingAnalysisResult) => formatCoolingStats(data)

function toggleMenu() {
  isMenuOpen.value = !isMenuOpen.value
}

function handleAddPark() {
  isMenuOpen.value = false
  emit('addPark')
}

function handleSelectPark() {
  if (selectedPark.value) {
    isMenuOpen.value = false
    emit('select', selectedPark.value)
  }
}

function handleSearch() {
  emit('search')
}

function handleSelect(item: SearchResult) {
  emit('select', item)
}

function handleTogglePixels() {
  emit('togglePixels')
}

// FECHA O MENU AO CLICAR FORA
const menuCardRef = ref<HTMLElement | null>(null)

function handleClickOutside(event: MouseEvent) {
  if (menuCardRef.value && !menuCardRef.value.contains(event.target as Node)) {
    isMenuOpen.value = false
  }
}

watch(isMenuOpen, (newVal) => {
  if (newVal) {
    document.addEventListener('click', handleClickOutside)
  } else {
    document.removeEventListener('click', handleClickOutside)
  }
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
  width: 400px;
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
}
</style>