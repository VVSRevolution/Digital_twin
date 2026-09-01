<template>
  <div class="sensor-overlay">
    <CollapsibleCard
        :defaultExpanded="true"
        icon="pi pi-calendar"
        title="Data/Hora dos Sensores"
    >
      <div class="sensor-content">
        <!-- 🔥 CHECKBOX PARA ATIVAR/DESATIVAR SENSORES -->
        <div class="sensor-toggle">
          <Checkbox
              v-model="showSensors"
              binary
              @update:model-value="onToggleSensors"
          />
          <label class="sensor-toggle-label">
            <i class="pi pi-eye" :class="{ 'pi-eye-slash': !showSensors }"></i>
            {{ showSensors ? 'Mostrar sensores no mapa' : 'Ocultar sensores' }}
          </label>
          <Badge
              v-if="sensorCount > 0"
              :value="`${sensorCount} ativos`"
              severity="info"
              size="small"
          />
        </div>

        <div class="datetime-control">
          <input
              v-model="selectedDateTime"
              class="datetime-input"
              type="datetime-local"
              @change="onDateTimeChange"
          />
          <Button
              icon="pi pi-refresh"
              label="Atualizar"
              severity="secondary"
              size="small"
              :loading="loading"
              @click="refreshSensors"
          />
        </div>
        <div class="datetime-info">
          <span v-if="lastUpdate" class="last-update">
            Última atualização: {{ formatDateTime(lastUpdate) }}
          </span>
          <span v-else class="last-update">Carregando dados...</span>
        </div>
      </div>
    </CollapsibleCard>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue'
import { getSensors } from '~/services/sensorService'
import type { SensorData } from '~/types'
import CollapsibleCard from '~/components/CollapsibleCard.vue'

// ============================================================
// 🔥 EMITS
// ============================================================
const emit = defineEmits<{
  (e: 'sensorsUpdated', sensors: SensorData[]): void
  (e: 'toggleSensors', show: boolean): void
}>()

// ============================================================
// 🔥 STATE
// ============================================================
const loading = ref(false)
const selectedDateTime = ref('')
const lastUpdate = ref('')
const sensors = ref<SensorData[]>([])
const showSensors = ref(true)

const sensorCount = computed(() => sensors.value.length)

// ============================================================
// 🔥 FUNÇÕES
// ============================================================
async function loadSensors(datetime?: string) {
  loading.value = true
  try {
    // 🔥 SE TIVER DATETIME, CONVERTE PARA O FORMATO COM ESPAÇO
    let formattedDatetime = datetime
    if (datetime) {
      // '2024-05-19T11:01:00' -> '2024-05-19 11:01:00'
      formattedDatetime = datetime.replace('T', ' ')
    }

    const result = await getSensors(formattedDatetime)
    if (result.success) {
      sensors.value = result.sensors
      lastUpdate.value = new Date().toISOString()
      if (showSensors.value) {
        emit('sensorsUpdated', sensors.value)
      }
    }
  } catch (error) {
    console.error('Erro ao carregar sensores:', error)
  } finally {
    loading.value = false
  }
}

function onDateTimeChange() {
  const datetime = selectedDateTime.value
  if (datetime) {
    // 🔥 O INPUT JÁ VEM COM 'T', SÓ ADICIONA OS SEGUNDOS
    const formatted = datetime + ':00'
    loadSensors(formatted)
  } else {
    loadSensors()
  }
}

function onToggleSensors() {
  if (showSensors.value) {
    emit('sensorsUpdated', sensors.value)
  } else {
    emit('sensorsUpdated', [])
  }
  emit('toggleSensors', showSensors.value)
}


function refreshSensors() {
  loadSensors()
}

function formatDateTime(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// ============================================================
// 🔥 MOUNT - CARREGA SEM DATA (MAIS RECENTE)
// ============================================================
onMounted(() => {
  loadSensors()
})
</script>

<style scoped>
/* 🔥 SENSOR OVERLAY - CANTO SUPERIOR DIREITO */
.sensor-overlay {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 1000;
  width: 340px;
}

.sensor-content {
  padding: 8px 0;
}

/* 🔥 TOGGLE SENSORES */
.sensor-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 4px 10px 4px;
  border-bottom: 1px solid #f3f4f6;
  margin-bottom: 10px;
}

.sensor-toggle-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
  cursor: pointer;
  user-select: none;
}

.sensor-toggle-label i {
  font-size: 16px;
  color: #6366f1;
}

.sensor-toggle-label .pi-eye-slash {
  color: #9ca3af;
}

/* 🔥 DATETIME CONTROL */
.datetime-control {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.datetime-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  color: #4b5563;
}

.datetime-input {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  min-width: 150px;
}

.datetime-input:focus {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.datetime-info {
  margin-top: 8px;
  text-align: center;
}

.last-update {
  font-size: 11px;
  color: #9ca3af;
}

/* RESPONSIVIDADE */
@media (max-width: 480px) {
  .sensor-overlay {
    left: 12px;
    right: 12px;
    width: auto;
    top: 12px;
  }
}
</style>