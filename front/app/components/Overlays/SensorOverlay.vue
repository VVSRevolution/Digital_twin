<!--\components\SensorOverlay.vue-->
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
            <i :class="{ 'pi-eye-slash': !showSensors }" class="pi pi-eye"></i>
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
              :loading="loading"
              icon="pi pi-refresh"
              label="Atualizar"
              severity="secondary"
              size="small"
              @click="refreshSensors"
          />
        </div>
      </div>
    </CollapsibleCard>
  </div>
</template>

<script lang="ts" setup>
import {computed, onMounted, ref} from 'vue'
import {getSensors} from '~/services/sensorService'
import type {SensorData} from '~/types'
import CollapsibleCard from '~/components/CollapsibleCard.vue'
import {useNotifications} from "~/composables/useErrorHandler";
import {useTimeZone} from "~/composables/useTimeZone";

const {handleError, handleSuccess, handleInfo} = useNotifications()
const {localToUTC, utcToLocal} = useTimeZone()


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
const lastUpdate = ref('')
const sensors = ref<SensorData[]>([])
const showSensors = ref(true)

const sensorCount = computed(() => sensors.value.length)

defineExpose({
  loadSensors
})


const selectedDateTime = ref('') // Hora LOCAL para exibição
const currentUtcDateTime = ref('') // Hora UTC para o backend

// ============================================================
// 🔥 FUNÇÕES
// ============================================================
async function loadSensors(datetime?: string) { // sempre espera UTC
  loading.value = true
  try {
    if (datetime) {
      // Guarda a data UTC
      currentUtcDateTime.value = datetime

      // Atualiza o input com hora LOCAL
      selectedDateTime.value = utcToLocal(datetime)
    }

    const result = await getSensors(datetime)
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
    // 🔥 CONVERTE LOCAL -> UTC COM Z
    const utcString = localToUTC(datetime)
    loadSensors(utcString)
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
  if (currentUtcDateTime.value) {
    // 🔥 USA A DATA UTC QUE JÁ FOI GUARDADA
    loadSensors(currentUtcDateTime.value)
  } else {
    loadSensors()
  }
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