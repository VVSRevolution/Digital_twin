<template>
  <div class="search-wrapper">
    <!-- 🔥 MENU SANDUÍCHE (ESQUERDA) -->
    <div class="menu-container" ref="menuContainerRef">
      <button class="hamburger-btn" @click="toggleMenu">
        <span class="hamburger-icon">
          <span></span>
          <span></span>
          <span></span>
        </span>
      </button>

      <!-- 🔥 MENU DROPDOWN -->
      <div v-if="isMenuOpen" class="menu-dropdown">
        <!-- 🔥 SELETOR DE PARQUES -->
        <div class="menu-section">
          <label class="menu-label">📍 Selecionar Parque</label>
          <select class="menu-select" v-model="selectedPark" @change="handleSelectPark">
            <option v-for="park in predefinedParks" :key="park.id" :value="park">
              {{ park.tags?.name || 'Parque sem nome' }}
            </option>
          </select>
        </div>

        <hr class="menu-divider" />

        <!-- 🔥 BOTÃO ADICIONAR PARQUE -->
        <div class="menu-item add-park-btn" @click="handleAddPark">
          ➕ Adicionar Parque
        </div>

        <hr class="menu-divider" />

        <div class="menu-item" @click="handleRefresh">
          🔄 Atualizar Dados
        </div>
        <div class="menu-item" @click="handleExport">
          📤 Exportar Relatório
        </div>
        <div class="menu-item" @click="handleSettings">
          ⚙️ Configurações
        </div>
        <hr class="menu-divider" />
        <div class="menu-item" @click="handleAbout">
          ℹ️ Sobre
        </div>
      </div>
    </div>

    <!-- 🔥 PESQUISA + RESULTADOS (DIREITA) -->
    <div class="search-container">
      <!-- INPUT DE PESQUISA -->
      <div class="search-input">
        <input
            v-model="search"
            placeholder="Pesquisar parque..."
            @keydown.enter="handleSearch"
        />
        <button :disabled="loading || analyzing" @click="handleSearch">
          {{ loading ? 'Buscando...' : analyzing ? 'Analisando...' : '🔍 Buscar' }}
        </button>
      </div>

      <!-- RESULTADOS DA ANÁLISE -->
      <div v-if="showStats && coolingData" class="stats">
        <div class="stats-header">
          <h4>🌳 {{ parkName }}</h4>
          <span :class="coolingData.success ? 'success' : 'error'" class="badge">
            {{ coolingData.success ? '✅ OK' : '❌ Falha' }}
          </span>
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
      </div>

      <!-- CONTROLE DE VISUALIZAÇÃO DOS PIXELS -->
      <div v-if="showStats && coolingData?.buffers" class="controls">
        <label class="toggle-label">
          <input v-model="showPixels" type="checkbox" @change="handleTogglePixels" />
          Mostrar pixels de temperatura
        </label>

        <!-- LEGENDA COM GRADIENTE LOCAL -->
        <div v-if="gradientMin !== null && gradientMax !== null" class="gradient-legend">
          <div class="gradient-header">
            <span>🌡️ Temperatura dos Pixels</span>
            <span class="pixel-count">{{ totalPixels }} pixels</span>
          </div>
          <div class="gradient-bar"></div>
          <div class="gradient-labels">
            <span>{{ gradientMin.toFixed(1) }}°C</span>
            <span>{{ gradientMax.toFixed(1) }}°C</span>
          </div>
          <div style="font-size: 10px; color: #999; text-align: center; margin-top: 2px;">
            Gradiente baseado nos valores mínimo e máximo locais
          </div>
        </div>
      </div>

      <!-- ESTATÍSTICAS DOS BUFFERS -->
      <div v-if="showStats && coolingData?.buffers" class="buffer-stats">
        <h4>📊 Estatísticas por Anel</h4>
        <div class="stats-grid">
          <div
              v-for="buffer in coolingData.buffers"
              :key="buffer.distance"
              :style="{
              background: (buffer.statistics?.mean ?? null) !== null
                ? `rgba(255, 100, 0, ${Math.max(0, Math.min(1, ((buffer.statistics?.mean ?? 0) - 25) / 10))})`
                : '#f5f5f5'
            }"
              class="stats-item"
          >
            <span class="label">{{ buffer.distance }}m</span>
            <span class="mean">{{ buffer.statistics?.mean?.toFixed(1) ?? 'N/A' }}°C</span>
            <span class="count">{{ buffer.statistics?.count ?? 0 }}px</span>
          </div>
        </div>
      </div>

      <!-- DROPDOWN DE RESULTADOS DA PESQUISA -->
      <div v-if="results.length" class="dropdown">
        <div
            v-for="item in results"
            :key="item.id"
            class="dropdown-item"
            @click="handleSelect(item)"
        >
          🌳 {{ item.tags?.name || 'Parque sem nome' }}
        </div>
      </div>
    </div>

    <slot />
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

// 🔥 MODELOS
const search = defineModel<string>('search', { required: true })
const showPixels = defineModel<boolean>('showPixels', { default: true })

// 🔥 PROPS
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

// 🔥 EMITS
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

// 🔥 CONTROLE DO MENU
const isMenuOpen = ref(false)
const menuContainerRef = ref<HTMLElement | null>(null)
const selectedPark = ref<SearchResult | null>(null)

// 🔥 FUNÇÃO PARA FORMATAR STATS (vinda do pai ou local)
const formatStats = (data: CoolingAnalysisResult) => {
  return formatCoolingStats(data)
}

// 🔥 FECHA O MENU AO CLICAR FORA
function handleClickOutside(event: MouseEvent) {
  if (menuContainerRef.value && !menuContainerRef.value.contains(event.target as Node)) {
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

function toggleMenu() {
  isMenuOpen.value = !isMenuOpen.value
}

// 🔥 FUNÇÕES DO MENU
function handleAddPark() {
  isMenuOpen.value = false
  emit('addPark')
}

function handleRefresh() {
  isMenuOpen.value = false
  emit('refresh')
}

function handleExport() {
  isMenuOpen.value = false
  emit('export')
}

function handleSettings() {
  isMenuOpen.value = false
  emit('settings')
}

function handleAbout() {
  isMenuOpen.value = false
  emit('about')
}

function handleSelectPark() {
  if (selectedPark.value) {
    isMenuOpen.value = false
    emit('select', selectedPark.value)
  }
}

// 🔥 FUNÇÕES DE PESQUISA
function handleSearch() {
  emit('search')
}

function handleSelect(item: SearchResult) {
  emit('select', item)
}

function handleTogglePixels() {
  emit('togglePixels')
}
</script>

<style scoped>
/* 🔥 WRAPPER PRINCIPAL */
.search-wrapper {
  position: absolute;
  top: 12px;
  left: 12px;
  right: 12px;
  display: flex;
  gap: 12px;
  align-items: flex-start;
  z-index: 1000;
  min-width: 280px;
  max-width: 350px;
}

/* 🔥 MENU CONTAINER (ESQUERDA) */
.menu-container {
  position: relative;
  flex-shrink: 0;
  background: white;
  padding: 10px 14px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 48px;
  cursor: pointer;
  transition: background 0.2s;
}

.menu-container:hover {
  background: #f8f9fa;
}

.menu-title {
  font-weight: 600;
  font-size: 14px;
  color: #333;
  white-space: nowrap;
}

/* 🔥 BOTÃO HAMBÚRGUER */
.hamburger-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hamburger-icon {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hamburger-icon span {
  display: block;
  width: 24px;
  height: 2.5px;
  background: #333;
  border-radius: 2px;
  transition: 0.3s;
}

/* 🔥 MENU DROPDOWN */
.menu-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  min-width: 220px;
  padding: 12px 0;
  z-index: 1001;
  border: 1px solid #eee;
}

.menu-section {
  padding: 0 12px;
  margin-bottom: 8px;
}

.menu-label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #888;
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.menu-select {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  background: white;
  cursor: pointer;
  outline: none;
  color: #333;
}

.menu-select:focus {
  border-color: #1a73e8;
  box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.2);
}

.menu-item {
  padding: 10px 16px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  transition: background 0.15s;
  white-space: nowrap;
}

.menu-item:hover {
  background: #f0f7ff;
}

.menu-divider {
  border: none;
  border-top: 1px solid #eee;
  margin: 4px 12px;
}

.add-park-btn {
  color: #28a745;
  font-weight: 600;
}

.add-park-btn:hover {
  background: #e8f5e9 !important;
}

/* 🔥 SEARCH CONTAINER (DIREITA) */
.search-container {
  flex: 1;
  min-width: 200px;
  background: white;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 80vh;
  overflow-y: auto;
}

.search-input {
  display: flex;
  gap: 8px;
}

.search-input input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  min-width: 120px;
}

.search-input input:focus {
  border-color: #1a73e8;
  box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.2);
}

.search-input button {
  padding: 8px 16px;
  background: #1a73e8;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
  transition: background 0.2s;
}

.search-input button:hover:not(:disabled) {
  background: #1557b0;
}

.search-input button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* 🔥 STATS */
.stats {
  border-top: 2px solid #eee;
  padding-top: 12px;
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.stats-header h4 {
  margin: 0;
  color: #333;
  font-size: 14px;
  font-weight: 600;
}

.badge {
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 12px;
  font-weight: 600;
}

.badge.success {
  background: #d4edda;
  color: #155724;
}

.badge.error {
  background: #f8d7da;
  color: #721c24;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  padding: 5px 0;
  font-size: 13px;
  border-bottom: 1px solid #f5f5f5;
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-item span {
  color: #666;
}

.stat-item strong {
  font-weight: 600;
}

.error-msg {
  margin-top: 8px;
  padding: 8px 12px;
  background: #f8d7da;
  color: #721c24;
  border-radius: 4px;
  font-size: 12px;
}

/* 🔥 CONTROLS */
.controls {
  border-top: 2px solid #eee;
  padding-top: 12px;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  cursor: pointer;
  color: #333;
}

.gradient-legend {
  margin-top: 8px;
  padding: 10px 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.gradient-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #555;
  margin-bottom: 6px;
}

.gradient-header span {
  font-weight: 600;
}

.pixel-count {
  font-weight: 400;
  color: #999;
  font-size: 11px;
}

.gradient-bar {
  width: 100%;
  height: 14px;
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
  border: 1px solid #dee2e6;
}

.gradient-labels {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  font-weight: 600;
  color: #495057;
  margin-top: 3px;
}

/* 🔥 BUFFER STATS */
.buffer-stats {
  border-top: 2px solid #eee;
  padding-top: 12px;
}

.buffer-stats h4 {
  font-size: 13px;
  margin: 0 0 8px 0;
  color: #333;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(70px, 1fr));
  gap: 4px;
  max-height: 200px;
  overflow-y: auto;
}

.stats-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6px 4px;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
  font-size: 11px;
  transition: all 0.2s;
}

.stats-item:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.stats-item .label {
  font-weight: 600;
  color: #555;
}

.stats-item .mean {
  font-weight: 700;
  color: #1a1a1a;
}

.stats-item .count {
  font-size: 9px;
  color: #999;
}

/* 🔥 DROPDOWN DE RESULTADOS */
.dropdown {
  max-height: 200px;
  overflow: auto;
  background: white;
  border-radius: 6px;
  border: 1px solid #eee;
  margin-top: 4px;
}

.dropdown-item {
  padding: 8px 12px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.15s;
}

.dropdown-item:hover {
  background: #f0f7ff;
}

/* 🔥 RESPONSIVIDADE */
@media (max-width: 768px) {
  .search-wrapper {
    flex-direction: column;
    left: 12px;
    right: 12px;
    top: 12px;
  }

  .menu-container {
    width: 100%;
  }

  .search-container {
    width: 100%;
  }

  .menu-dropdown {
    left: 0;
    right: 0;
    min-width: unset;
  }
}

/* 🔥 SCROLLBAR */
.search-container::-webkit-scrollbar,
.stats-grid::-webkit-scrollbar,
.dropdown::-webkit-scrollbar {
  width: 4px;
}

.search-container::-webkit-scrollbar-track,
.stats-grid::-webkit-scrollbar-track,
.dropdown::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.search-container::-webkit-scrollbar-thumb,
.stats-grid::-webkit-scrollbar-thumb,
.dropdown::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 4px;
}

.search-container::-webkit-scrollbar-thumb:hover,
.stats-grid::-webkit-scrollbar-thumb:hover,
.dropdown::-webkit-scrollbar-thumb:hover {
  background: #aaa;
}
</style>