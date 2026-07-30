<template>
  <div class="timeline-overlay">
    <!-- HEADER -->
    <div class="timeline-header" @click="toggleExpand">
      <span>📊</span>
      <span class="badge">{{ events.length }}</span>
      <span class="arrow">{{ isExpanded ? '▲' : '▼' }}</span>
    </div>

    <!-- TIMELINE -->
    <div v-show="isExpanded" class="timeline-wrapper">
      <div
          v-for="event in events"
          :key="event.id"
          :class="{ 'selected': isSelected(event) }"
          class="timeline-item"
          @click="selectEvent(event)"
      >
        <!-- CARD DA DATA (ESQUERDA) -->
        <div class="timeline-date-card">
          <div class="timeline-date">
            <span class="date-day">{{ event.day }}</span>
            <span class="date-month">{{ event.month }}</span>
            <span class="date-time">{{ event.time }}</span>
          </div>

          <!-- DETALHES QUE APARECEM NO HOVER -->
          <div class="timeline-details">
            <div class="detail-temp">🌡️LST: {{ event.temp }}°C</div>
            <div class="detail-pci">❄️ PCI: {{ event.pci }}°C</div>
            <div class="detail-pcd">📏 PCD: {{ event.pcd }}m</div>
            <div class="detail-buffers">📊 {{ event.numBuffers }} x {{ event.buffer_distance }} m</div>
            <div class="detail-satellite">🛰️ {{ event.satellite }}</div>
          </div>
        </div>

        <!-- LINHA + PONTO (DIREITA) -->
        <div class="timeline-line">
          <div class="timeline-vertical-line"></div>
          <div
              :class="{ 'selected-dot': isSelected(event) }"
              :style="{ background: getDotColor(event.temp) }"
              class="timeline-dot"
          ></div>
        </div>
      </div>
    </div>

    <div v-if="events.length === 0" class="empty">
      Nenhuma análise
    </div>
  </div>
</template>

<script lang="ts" setup>
import {computed, ref, watch} from 'vue'
import type {CoolingAnalysisResult} from '~/types'

const props = defineProps<{
  analyses: CoolingAnalysisResult[]
  selectedAnalysis?: CoolingAnalysisResult | null
}>()

const emit = defineEmits<{
  (e: 'select', analysis: CoolingAnalysisResult): void
}>()


// STATE
const isExpanded = ref(true)
const selectedId = ref<string | null>(null)


// Processa os eventos sem filtro
const events = computed(() => {
  if (!props.analyses || props.analyses.length === 0) return []

  return props.analyses
      .filter(a => a.image_date)
      .sort((a, b) => new Date(b.image_date!).getTime() - new Date(a.image_date!).getTime())
      .map(a => {
        const date = new Date(a.image_date!)
        return {
          id: a.analysis_id || String(Math.random()),
          date: a.image_date,
          dateFormatted: date.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
          }),
          day: date.getDate().toString().padStart(2, '0'),
          month: date.toLocaleDateString('pt-BR', {month: 'short'}),
          time: date.toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit',
          }),
          temp: a.park_lst_celsius.toFixed(2) || 'N/A',
          pci: a.pci?.toFixed(2) || 'N/A',
          pcd: a.pcd || 'N/A',
          numBuffers: a.num_buffers || 0,
          buffer_distance: a.buffer_distance || 0,
          satellite: a.satellite_name || 'Landsat',
          raw: a,
        }
      })
})
watch(
    [events, () => props.selectedAnalysis],
    ([newEvents, selectedAnalysis]) => {
      // Prioridade 1: seleção externa (vinda do pai)
      if (selectedAnalysis) {
        const event = newEvents.find(e => e.raw === selectedAnalysis)
        if (event) {
          selectedId.value = String(event.id)
          return
        }
      }

      // Prioridade 2: primeiro evento da lista (mais recente)
      if (newEvents.length > 0 && !selectedId.value) {
        selectedId.value = String(newEvents[0].id)
      }
    },
    {immediate: true}
)

// METHODS
function isSelected(event: any): boolean {
  return Number(selectedId.value) === Number(event.id)
}

function getDotColor(temp: string): string {
  const t = parseFloat(temp)
  if (isNaN(t)) return '#6b7280'
  if (t < 20) return '#3b82f6'
  if (t < 25) return '#22c55e'
  if (t < 30) return '#f59e0b'
  if (t < 35) return '#f97316'
  return '#ef4444'
}

function toggleExpand() {
  isExpanded.value = !isExpanded.value
}

function selectEvent(event: any) {
  if (event?.raw) {
    selectedId.value = event.id
    emit('select', event.raw)
  }
}
</script>
<style scoped>
/* TIMELINE OVERLAY - DIREITA */
.timeline-overlay {
  position: absolute;
  top: 50%;
  right: 12px;
  transform: translateY(-50%);
  z-index: 1000;
  width: auto;
  max-height: 80vh;
  background: transparent;
  overflow: visible;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

/* HEADER - ESTILO IGUAL AOS OUTROS MENUS */
.timeline-header {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  padding: 8px 14px;
  cursor: pointer;
  font-size: 14px;
  color: #1f2937;
  flex-shrink: 0;
  background: white;
  border-radius: 8px;
  margin-bottom: 6px;
  align-self: flex-end;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.2s ease;
}

.timeline-header:hover {
  background: #f8fafc;
  border-color: #d1d5db;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.badge {
  background: #3b82f6;
  color: white;
  padding: 0 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 700;
  min-width: 18px;
  text-align: center;
}

.arrow {
  font-size: 11px;
  color: #6b7280;
}

/* TIMELINE WRAPPER */
.timeline-wrapper {
  flex: 1;
  overflow-y: auto;
  overflow-x: visible;
  max-height: 70vh;
  padding: 8px 8px 8px 8px;
  display: flex;
  flex-direction: column;
  gap: 0;
  align-items: flex-end;
}

.timeline-wrapper::-webkit-scrollbar {
  width: 4px;
}

.timeline-wrapper::-webkit-scrollbar-track {
  background: transparent;
}

.timeline-wrapper::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.15);
  border-radius: 4px;
}

/* ITEM */
.timeline-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 0;
  cursor: pointer;
  position: relative;
  justify-content: flex-end;
}

/* LINHA VERTICAL */
.timeline-line {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 32px;
  height: 100%;
  flex-shrink: 0;
}

.timeline-vertical-line {
  position: absolute;
  top: -8px;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 2.5px;
  background: #e5e7eb;
  border-radius: 2px;
  z-index: 0;
}

.timeline-item:first-child .timeline-vertical-line {
  top: 50%;
}

.timeline-item:last-child .timeline-vertical-line {
  bottom: 50%;
}

.timeline-item:only-child .timeline-vertical-line {
  display: none;
}

.timeline-item.selected .timeline-vertical-line {
  background: #3b82f6;
  box-shadow: 0 0 12px rgba(59, 130, 246, 0.3);
}

/* BOLA */
.timeline-dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2.5px solid white;
  box-shadow: 0 0 0 1.5px rgba(0, 0, 0, 0.08), 0 2px 8px rgba(0, 0, 0, 0.12);
  transition: all 0.3s ease;
  cursor: pointer;
  position: relative;
  z-index: 1;
}

.timeline-item:hover .timeline-dot {
  transform: scale(1.25);
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.15), 0 2px 12px rgba(0, 0, 0, 0.15);
}

/* BOLA SELECIONADA - DOURADA */
.timeline-dot.selected-dot {
  width: 22px;
  height: 22px;
  border-color: #fbbf24;
  box-shadow: 0 0 0 3px rgba(251, 191, 36, 0.25),
  0 0 20px rgba(251, 191, 36, 0.2),
  0 2px 12px rgba(0, 0, 0, 0.15);
  transform: scale(1.15);
  animation: pulse-gold 2s ease-in-out infinite;
}

@keyframes pulse-gold {
  0%, 100% {
    box-shadow: 0 0 0 3px rgba(251, 191, 36, 0.25),
    0 0 20px rgba(251, 191, 36, 0.2),
    0 2px 12px rgba(0, 0, 0, 0.15);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(251, 191, 36, 0.12),
    0 0 30px rgba(251, 191, 36, 0.15),
    0 2px 12px rgba(0, 0, 0, 0.15);
  }
}

/* CARD DA DATA - ESTILO IGUAL AOS CARDS DO MENU */
.timeline-date-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 8px 14px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
  position: relative;
  min-width: 100px;
}

.timeline-item:hover .timeline-date-card {
  background: #f8fafc;
  border-color: #d1d5db;
  transform: scale(1.04);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.timeline-item.selected .timeline-date-card {
  background: #f0f7ff;
  border-color: #3b82f6;
  box-shadow: 0 0 0 1px #3b82f6, 0 4px 16px rgba(59, 130, 246, 0.12);
}

/* DATA DENTRO DO CARD */
.timeline-date {
  display: flex;
  align-items: center;
  gap: 8px;
  text-align: right;
  line-height: 1.2;
  white-space: nowrap;
}

.date-day {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
}

.date-month {
  font-size: 14px;
  font-weight: 600;
  color: #4b5563;
  text-transform: uppercase;
}

.date-time {
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
}

/* DETALHES - APARECEM NO HOVER */
.timeline-details {
  max-height: 0;
  overflow: hidden;
  opacity: 0;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-top: 0;
}

.timeline-item:hover .timeline-details {
  max-height: 200px;
  opacity: 1;
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid #f3f4f6;
}

.detail-temp {
  color: #dc2626;
  font-size: 13px;
  font-weight: 600;
}

.detail-pci {
  color: #2563eb;
  font-size: 12px;
}

.detail-pcd {
  color: #059669;
  font-size: 12px;
}

.detail-buffers {
  color: #7c3aed;
  font-size: 12px;
}

.detail-satellite {
  color: #d97706;
  font-size: 11px;
}

.empty {
  padding: 12px 4px;
  text-align: center;
  color: #6b7280;
  font-size: 12px;
}

@media (max-width: 420px) {
  .timeline-overlay {
    right: 6px;
  }

  .date-day {
    font-size: 17px;
  }

  .date-month {
    font-size: 12px;
  }

  .date-time {
    font-size: 12px;
  }

  .timeline-date-card {
    padding: 6px 10px;
  }

  .timeline-dot {
    width: 16px;
    height: 16px;
  }

  .timeline-dot.selected-dot {
    width: 20px;
    height: 20px;
  }

  .timeline-line {
    width: 26px;
  }

  .detail-temp {
    font-size: 12px;
  }

  .detail-pci,
  .detail-pcd,
  .detail-buffers {
    font-size: 11px;
  }

  .detail-satellite {
    font-size: 10px;
  }
}
</style>