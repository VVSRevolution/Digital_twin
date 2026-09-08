<!-- components/Overlays/LayerControlsOverlay.vue -->
<template>
  <div class="layer-controls-overlay overlay-wrapper">
    <CollapsibleCard
        :defaultExpanded="true"
        icon="pi pi-layer"
        title="Camadas"
    >
      <!-- 🔥 PIXELS DE TEMPERATURA -->
      <div class="layer-section">
        <div class="layer-toggle">
          <div class="layer-toggle-left">
            <Checkbox
                v-model="showPixels"
                binary
                @update:model-value="handleTogglePixels"
            />
            <label class="layer-toggle-label">
              <Temperature :size="20" class="layer-icon"/>
              <span>Pixels de temperatura</span>
            </label>
          </div>
          <Badge
              v-if="showPixels && totalPixels > 0"
              :value="`${totalPixels} px`"
              class="layer-badge"
              severity="info"
          />
        </div>

        <!-- OPACIDADE E GRADIENTE DOS PIXELS -->
        <div v-if="showPixels" class="layer-controls">
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

      <!-- 🔥 NDVI -->
      <Divider v-if="showPixels || (ndviData && showNdvi)"/>

      <div class="layer-section" v-if="ndviData">
        <div class="layer-toggle">
          <div class="layer-toggle-left">
            <Checkbox
                v-model="showNdvi"
                binary
                @update:model-value="handleToggleNdvi"
            />
            <label class="layer-toggle-label">
              <i class="pi pi-chart-line" style="color: #22c55e; font-size: 18px;"></i>
              <span>NDVI (Vegetação)</span>
            </label>
          </div>
          <Badge
              v-if="showNdvi && ndviData"
              :value="`${ndviTotalPixels} px`"
              class="layer-badge"
              severity="success"
          />
        </div>

        <!-- CONTROLES NDVI -->
        <div v-if="showNdvi && ndviData" class="layer-controls">
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
      </div>
    </CollapsibleCard>
  </div>
</template>

<script lang="ts" setup>
import {ref, computed, watch} from 'vue'
import {Temperature} from 'reicon-vue'
import type {CoolingAnalysisResult} from '~/types'

// ============================================================
// 🔥 PROPS
// ============================================================
const props = defineProps<{
  showStats: boolean
  coolingData: CoolingAnalysisResult | null
  totalPixels: number
  pixelOpacity: number
  gradientMin: number | null
  gradientMax: number | null
  ndviData: any
  ndviTotalPixels?: number
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
  (e: 'updateOpacity', value: number): void
  (e: 'toggleNdvi', show: boolean): void
  (e: 'updateNdviOpacity', value: number): void
}>()

// ============================================================
// 🔥 STATE
// ============================================================
const ndviOpacity = ref(0.70)
const isQaExpanded = ref(true)

// ============================================================
// 🔥 FUNÇÕES
// ============================================================
function handleTogglePixels() {
  emit('togglePixels')
}

function handleOpacityChange(event: Event) {
  const target = event.target as HTMLInputElement
  const value = parseFloat(target.value)
  emit('updateOpacity', value)
}

function handleToggleNdvi() {
  emit('toggleNdvi', showNdvi.value)
}

function handleNdviOpacityChange(event: Event) {
  const target = event.target as HTMLInputElement
  const value = parseFloat(target.value)
  ndviOpacity.value = value / 100
  emit('updateNdviOpacity', ndviOpacity.value)
}
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
  #8b5cf6,
  #6366f1,
  #3b82f6,
  #22c55e,
  #16a34a,
  #15803d,
  #166534
  );
  border: 1px solid #e5e7eb;
  margin: 2px 0;
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
}
</style>