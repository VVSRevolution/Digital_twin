<!-- components/AnalysisOverlay.vue -->
<template>
  <div class="analysis-overlay overlay-wrapper" v-if="showStats && coolingData">
    <CollapsibleCard
        v-if="showStats && coolingData"
        :defaultExpanded="true"
        icon="pi pi-chart-bar"
        title="Análise Térmica"
    >
      <!-- HEADER -->
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

      <!-- DATA DA IMAGEM -->
      <div v-if="coolingData.image_date" class="stat-item image-date">
        <span><i class="pi pi-calendar"></i> Data da Imagem</span>
        <strong>{{ formatDate(coolingData.image_date) }}</strong>
      </div>

      <!-- BUFFERS INFO -->
      <div class="stat-item buffer-info">
        <label>
          <PinRotate color="#166534" size="16"/>
          <span>Buffers</span>
        </label>
        <strong>{{ coolingData.num_buffers || 11 }} anéis × {{ coolingData.buffer_distance || 30 }}m</strong>
      </div>

      <!-- STATS -->
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


      <!-- BUFFERS -->
      <template v-if="coolingData?.buffers">
        <Divider/>
        <div class="buffer-stats">
          <div class="buffer-header">
            <h4>
              <label>
                <SignalStream class="buffer-header-icon" size="28"/>
                <span>Anéis de Temperatura</span>
              </label>
            </h4>
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

      <!-- QA -->
      <template v-if="coolingData?.buffers">
        <Divider/>
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
        <transition name="expand">
          <div v-if="isQaExpanded" class="qa-content-wrapper">
            <div class="qa-content">
              <!-- QA_PIXEL -->
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

              <!-- ST_QA -->
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
import {PinRotate, SignalStream, Temperature, Tree} from 'reicon-vue';
import {ref} from 'vue'
import type {CoolingAnalysisResult} from '~/types'
import {formatCoolingStats} from '@/services'

// ============================================================
// 🔥 PROPS
// ============================================================
const props = defineProps<{
  showStats: boolean
  coolingData: CoolingAnalysisResult | null
  parkName: string
  pixelOpacity: number
  gradientMin: number | null
  gradientMax: number | null
  totalPixels: number
}>()


// ============================================================
// 🔥 STATE
// ============================================================
const isQaExpanded = ref(true)

// ============================================================
// 🔥 FUNÇÕES
// ============================================================
function formatDate(dateStr: string): string {
  if (!dateStr) return 'N/A'
  const date = new Date(dateStr)
  return date.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function toggleQaSection() {
  isQaExpanded.value = !isQaExpanded.value
}


// ============================================================
// 🔥 ST_QA FUNCTIONS
// ============================================================
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
  if (meanKelvin === null || meanKelvin === undefined) return 'pi pi-help-circle'
  if (meanKelvin < 3) return 'pi pi-check-circle'
  if (meanKelvin < 5) return 'pi pi-exclamation-circle'
  return 'pi pi-times-circle'
}

// ============================================================
// 🔥 BUFFER COLOR FUNCTIONS
// ============================================================
function getRelativeValue(value: number, min: number, max: number): number {
  if (max === min) return 0.5
  return (value - min) / (max - min)
}

function getBufferGradient(buffer: any, buffers: any[]): string {
  const mean = buffer.statistics?.mean
  if (mean === null || mean === undefined) return '#f5f5f5'

  const temps = buffers.map((b: any) => b.statistics?.mean ?? 0).filter((t: number) => t > 0)
  if (temps.length < 2) return '#f5f5f5'

  const min = Math.min(...temps)
  const max = Math.max(...temps)
  const relative = getRelativeValue(mean, min, max)

  const r = Math.round(59 + (196 * relative))
  const g = Math.round(130 - (100 * relative))
  const b = Math.round(246 - (200 * relative))

  return `linear-gradient(135deg, rgba(${r}, ${g}, ${b}, 0.15), rgba(${r}, ${g}, ${b}, 0.25))`
}

function getBufferBorderColor(buffer: any, buffers: any[]): string {
  const mean = buffer.statistics?.mean
  if (mean === null || mean === undefined) return '#d1d5db'

  const temps = buffers.map((b: any) => b.statistics?.mean ?? 0).filter((t: number) => t > 0)
  if (temps.length < 2) return '#d1d5db'

  const min = Math.min(...temps)
  const max = Math.max(...temps)
  const relative = getRelativeValue(mean, min, max)

  const r = Math.round(59 + (196 * relative))
  const g = Math.round(130 - (100 * relative))
  const b = Math.round(246 - (200 * relative))

  return `rgb(${r}, ${g}, ${b})`
}

function getBufferBarColor(buffer: any, buffers: any[]): string {
  const mean = buffer.statistics?.mean
  if (mean === null || mean === undefined) return '#d1d5db'

  const temps = buffers.map((b: any) => b.statistics?.mean ?? 0).filter((t: number) => t > 0)
  if (temps.length < 2) return '#d1d5db'

  const min = Math.min(...temps)
  const max = Math.max(...temps)
  const relative = getRelativeValue(mean, min, max)

  const r = Math.round(59 + (196 * relative))
  const g = Math.round(130 - (100 * relative))
  const b = Math.round(246 - (200 * relative))

  return `rgb(${r}, ${g}, ${b})`
}

function getBufferPercent(buffer: any, buffers: any[]): string {
  const mean = buffer.statistics?.mean
  if (mean === null || mean === undefined) return '0%'

  const temps = buffers.map((b: any) => b.statistics?.mean ?? 0).filter((t: number) => t > 0)
  if (temps.length < 2) return '50%'

  const min = Math.min(...temps)
  const max = Math.max(...temps)
  const relative = getRelativeValue(mean, min, max)

  return `${Math.max(5, Math.min(100, relative * 100))}%`
}
</script>

<style scoped>

.stats-header {
  padding-top: 10px;
  padding-left: 8px;
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




/* BUFFERS */
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
  padding: 0 5px;
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(65px, 1fr));
  gap: 5px;
}

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

.stats-pixels {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 12px;
  color: #575a61;
  margin-top: 1px;
}

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

/* QA */
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

/* ST_QA */
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

/* TRANSITION */
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

/* RESPONSIVE */
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
}
</style>