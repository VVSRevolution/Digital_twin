<template>
  <div class="layer-controls-overlay overlay-wrapper">
    <CollapsibleCard
        :defaultExpanded="true"
        icon="pi pi-th-large"
        title="Camadas"
    >
      <!-- 🔥 PIXELS DE TEMPERATURA -->
      <div v-if="coolingData?.buffers" class="layer-section">
        <div class="layer-toggle">
          <div class="layer-toggle-left">
            <!-- 🔥 MUDA PARA TOGGLESWITCH -->
            <ToggleSwitch
                v-model="showPixels"
                @update:model-value="handleTogglePixels"
            />
            <label class="layer-toggle-label">
              <Temperature :size="20" class="layer-icon"/>
              <span>Pixels de temperatura</span>
            </label>
          </div>
          <Badge
              v-if="showPixels"
              :value="`${totalPixels} px`"
              class="layer-badge"
              severity="info"
          />
        </div>

        <!-- OPACIDADE E GRADIENTE DOS PIXELS -->
        <div v-if="showPixels" class="layer-controls">
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
                <i class="pi pi-thermometer gradient-icon" style="color: #ef4444;"></i>
              </div>
            </div>
            <div class="gradient-bar"></div>
            <div class="gradient-labels">
              <span class="gradient-min">{{ gradientMin.toFixed(1) }}°C</span>
              <span class="gradient-max">{{ gradientMax.toFixed(1) }}°C</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 🔥 NDVI -->
      <Divider v-if="(coolingData?.buffers && showPixels) || showNdvi"/>

      <div class="layer-section">
        <!-- TOGGLE NDVI -->
        <div class="layer-toggle">
          <div class="layer-toggle-left">
            <!-- 🔥 MUDA PARA TOGGLESWITCH -->
            <ToggleSwitch
                v-model="showNdvi"
                @update:model-value="handleToggleNdvi"
            />
            <label class="layer-toggle-label">
              <i class="pi pi-chart-line" style="color: #22c55e; font-size: 18px;"></i>
              <span>NDVI (Vegetação)</span>
            </label>
          </div>
          <Badge
              v-if="showNdvi && ndviTotalPixels > 0"
              :value="`${ndviTotalPixels} px`"
              class="layer-badge"
              severity="success"
          />
        </div>

        <!-- CONTROLES NDVI (só aparece quando ativado) -->
        <template v-if="showNdvi">
          <!-- OPACIDADE NDVI -->
          <div v-if="ndviData" class="layer-controls">
            <div class="opacity-control">
              <div class="opacity-header">
                <i class="pi pi-eye opacity-icon"></i>
                <span class="opacity-label">Opacidade NDVI</span>
                <span class="opacity-value">{{ Math.round(ndviOpacity * 100) }}%</span>
              </div>
              <input
                  :value="ndviOpacity * 100"
                  class="opacity-slider"
                  max="100"
                  min="0"
                  type="range"
                  @input="handleNdviOpacityChange($event)"
              />
            </div>

            <div class="gradient-legend-ndvi">
              <div class="gradient-header">
                <div class="gradient-header-left">
                  <i class="pi pi-chart-line gradient-icon" style="color: #22c55e;"></i>
                  <span class="gradient-title">NDVI</span>
                </div>
                <Badge :value="`${ndviTotalPixels} px`" class="gradient-badge" severity="secondary"/>
              </div>
              <div class="gradient-bar-ndvi"></div>
              <div class="gradient-labels">
                <span class="gradient-min">-0.1</span>
                <span class="gradient-max">1.0</span>
              </div>
            </div>
          </div>

          <!-- STATUS DE CARREGAMENTO -->
          <div v-if="loadingNdvi" class="loading-status">
            <i class="pi pi-spin pi-spinner"></i>
            Carregando NDVI...
          </div>
          <div v-if="error" class="error-msg-ndvi">
            <i class="pi pi-exclamation-triangle"></i>
            {{ error }}
          </div>

          <!-- LISTA DE DATAS (SELECT) -->
          <div v-if="dateOptions.length > 0" class="ndvi-dates-list">
            <div class="dates-header">
              <span class="dates-title">📅 Data disponível</span>
              <Badge :value="dateOptions.length" severity="info"/>
            </div>
            <Select
                v-model="selectedDate"
                :options="dateOptions"
                class="dates-select"
                optionLabel="label"
                optionValue="value"
                placeholder="Selecione uma data"
                @change="handleDateChange"
            />
          </div>
        </template>
      </div>
    </CollapsibleCard>
  </div>
</template>

<script lang="ts" setup>
import {ref, watch} from 'vue'
import {Temperature} from 'reicon-vue'
import type {CoolingAnalysisResult} from '~/types'
import {getLatestNdvi, getNdviByDate, getNdviList} from '~/services/ndviService'
import {useTimeZone} from '~/composables/useTimeZone'
import type {NDVIBuffer} from "~/types/ndvi";

const {utcToLocalFormatted} = useTimeZone()

// ============================================================
// 🔥 PROPS
// ============================================================
const props = defineProps<{
  parkId: number
  showStats: boolean
  coolingData: CoolingAnalysisResult | null
  totalPixels: number
  pixelOpacity: number
  gradientMin: number | null
  gradientMax: number | null
}>()

// ============================================================
// 🔥 MODELS
// ============================================================
const showPixels = defineModel<boolean>('showPixels', {default: true})
const showNdvi = defineModel<boolean>('showNdvi', {default: false})

// ============================================================
// 🔥 EMITS
// ============================================================
const emit = defineEmits<{
  (e: 'togglePixels'): void
  (e: 'updatePixelOpacity', value: number): void
  (e: 'ndviDataLoaded', data: NDVIBuffer[] | null): void
  (e: 'toggleNdviVisibility', visible: boolean): void
}>()

// ============================================================
// 🔥 STATE
// ============================================================
const ndviOpacity = defineModel<number>('ndviOpacity', {default: 0.70})
const ndviData = ref<NDVIBuffer[] | null>(null)
const ndviTotalPixels = ref(0)
const loadingNdvi = ref(false)
const error = ref<string | null>(null)
const dateOptions = ref<Array<{ label: string; value: string }>>([])
const selectedDate = ref<string | null>(null)
const isInitialLoad = ref(true)

// ============================================================
// 🔥 FUNÇÕES
// ============================================================
async function fetchNdviList() {
  if (!props.parkId) return

  loadingNdvi.value = true
  error.value = null
  try {
    const result = await getNdviList(props.parkId)
    if (result.success && result.dates.length > 0) {
      // 🔥 USA O COMPOSABLE PARA FORMATAR AS DATAS EM LOCAL
      dateOptions.value = result.dates.map((d: string) => ({
        label: utcToLocalFormatted(d, "dd/MM/yyyy"),
        value: d
      }))

      if (isInitialLoad.value && dateOptions.value.length > 0) {
        const firstDate = dateOptions.value[0]
        if (firstDate) {
          selectedDate.value = firstDate.value
          await loadLatestNdvi()
        }
        isInitialLoad.value = false
      }
    } else {
      error.value = result.error || 'Nenhuma data disponível'
    }
  } catch (err) {
    console.error('Erro ao buscar lista NDVI:', err)
    error.value = 'Erro ao carregar lista de datas'
  } finally {
    loadingNdvi.value = false
  }
}

async function loadNdvi() {
  if (!selectedDate.value) {
    await loadLatestNdvi()
    return
  }

  loadingNdvi.value = true
  error.value = null
  try {
    const result = await getNdviByDate(props.parkId, selectedDate.value)
    if (result.success && result.ndvi) {
      ndviData.value = result.ndvi
      ndviTotalPixels.value = result.total_pixels || 0

      if (showNdvi.value) {
        emit('ndviDataLoaded', result.ndvi)
      }
    } else {
      error.value = result.error || 'Erro ao carregar NDVI'
    }
  } catch (err) {
    console.error('Erro ao carregar NDVI:', err)
    error.value = 'Erro ao carregar NDVI'
  } finally {
    loadingNdvi.value = false
  }
}

async function loadLatestNdvi() {
  loadingNdvi.value = true
  error.value = null
  try {
    const result = await getLatestNdvi(props.parkId)
    if (result.success && result.ndvi) {
      ndviData.value = result.ndvi
      ndviTotalPixels.value = result.total_pixels || 0
      selectedDate.value = result.image_date
      if (showNdvi.value) {
        emit('ndviDataLoaded', result.ndvi)
      }
    } else {
      error.value = result.error || 'Nenhum NDVI disponível'
    }
  } catch (err) {
    console.error('Erro ao carregar NDVI mais recente:', err)
    error.value = 'Erro ao carregar NDVI mais recente'
  } finally {
    loadingNdvi.value = false
  }
}

// ============================================================
// 🔥 HANDLERS
// ============================================================
function handleTogglePixels() {
  emit('togglePixels')
}

function handleOpacityChange(event: Event) {
  const target = event.target as HTMLInputElement
  const value = parseFloat(target.value)
  emit('updatePixelOpacity', value)
}

function handleToggleNdvi(value: boolean) {
  if (value) {
    if (dateOptions.value.length === 0) {
      fetchNdviList()
    } else if (ndviData.value) {
      emit('ndviDataLoaded', ndviData.value)
    } else {
      loadLatestNdvi()
    }
  } else {
    emit('toggleNdviVisibility', false)
  }
}

function handleNdviOpacityChange(event: Event) {
  const target = event.target as HTMLInputElement
  const value = parseFloat(target.value)
  ndviOpacity.value = value / 100
}

function handleDateChange(event: any) {
  const date = event.value
  if (date) {
    loadNdvi()
  }
}

// ============================================================
// 🔥 WATCH
// ============================================================
watch(() => props.parkId, (newParkId) => {
  if (newParkId) {
    isInitialLoad.value = true
    dateOptions.value = []
    selectedDate.value = null
    ndviData.value = null
    fetchNdviList()
  }
}, {immediate: true})
</script>
<style scoped>
.layer-controls-overlay {
  width: 100%;
}

.layer-controls-overlay::-webkit-scrollbar {
  width: 4px;
}

.layer-controls-overlay::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.20);
  border-radius: 4px;
}

/* LAYER TOGGLE */
.layer-toggle {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 4px;
}

.layer-toggle-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.layer-toggle-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
  cursor: pointer;
  user-select: none;
}

.layer-icon {
  color: #6366f1;
}

.layer-badge {
  font-size: 10px;
  font-weight: 600;
}

/* CONTROLES */
.layer-controls {
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

/* OPACIDADE */
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

/* GRADIENTE TEMPERATURA */
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

/* GRADIENTE NDVI */
.gradient-legend-ndvi {
  padding: 8px 12px;
  background: #fafbfc;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.gradient-bar-ndvi {
  width: 100%;
  height: 10px;
  border-radius: 4px;
  background: linear-gradient(to right,
  #b41e1e, /* Vermelho escuro - solo/água */ #ff3c1e, /* Vermelho - solo exposto */ #ff7d1e, /* Laranja - vegetação muito esparsa */ #ffc81e, /* Amarelo - vegetação esparsa */ #dcf000, /* Amarelo-esverdeado - vegetação moderada */ #8cf000, /* Verde claro - vegetação boa */ #23b423 /* Verde escuro - vegetação densa */
  );
  border: 1px solid #e5e7eb;
  margin: 2px 0;
}

/* NDVI DATES LIST */
.ndvi-dates-list {
  margin-top: 8px;
}

.dates-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.dates-title {
  font-size: 12px;
  font-weight: 500;
  color: #4b5563;
}

.dates-select {
  width: 100%;
  font-size: 12px;
}

.dates-select :deep(.p-select-label) {
  font-size: 12px;
  padding: 6px 10px;
}

.dates-select :deep(.p-select-dropdown) {
  width: 2rem;
}

.dates-select :deep(.p-select-option) {
  font-size: 12px;
  padding: 6px 10px;
}

.dates-select :deep(.p-select-option.p-select-option-selected) {
  background: #dcfce7;
  color: #166534;
}

/* STATUS */
.loading-status {
  text-align: center;
  padding: 8px;
  font-size: 13px;
  color: #6b7280;
}

.loading-status i {
  margin-right: 6px;
}

.error-msg-ndvi {
  padding: 8px 12px;
  background: #fee2e2;
  color: #991b1b;
  border-radius: 4px;
  font-size: 12px;
  margin-top: 4px;
}

/* RESPONSIVE */
@media (max-width: 480px) {
  .layer-controls-overlay {
    left: 8px;
    right: 8px;
    width: auto;
  }

  .layer-toggle {
    flex-wrap: wrap;
  }

  .opacity-value {
    font-size: 10px;
    min-width: 30px;
    padding: 0 4px;
  }
}
</style>