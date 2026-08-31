<template>
  <!-- DIALOG PRINCIPAL -->
  <Dialog
      :closable="true"
      :modal="true"
      :style="{ width: '700px', maxWidth: '90vw' }"
      :visible="visible"
      class="delete-dialog"
      header="Gerenciar Parques"
      @update:visible="handleVisibleChange"
  >
    <div class="delete-dialog-content">
      <!-- ALERTA -->
      <div class="delete-dialog-alert">
        <i class="pi pi-info-circle" style="color: #f59e0b;"></i>
        <span>
          Clique em um parque para ver suas análises.
          <strong>Deletar um parque remove TODAS as suas análises.</strong>
        </span>
      </div>

      <!-- LOADING -->
      <div v-if="loading" class="delete-loading">
        <i class="pi pi-spin pi-spinner"></i>
        Carregando parques...
      </div>

      <!-- SEM PARQUES -->
      <div v-else-if="parks.length === 0" class="delete-empty">
        <i class="pi pi-inbox"></i>
        <span>Nenhum parque cadastrado</span>
      </div>

      <!-- LISTA DE PARQUES -->
      <div v-else class="delete-list">
        <div
            v-for="park in parks"
            :key="park.id"
            :class="{ 'delete-park-expanded': expandedParkId === park.id }"
            class="delete-park-item"
        >
          <!-- HEADER DO PARQUE -->
          <div class="delete-park-header" @click="togglePark(park.id!)">
            <div class="delete-park-info">
              <span class="delete-park-name">{{ park.name }}</span>
              <span class="delete-park-location">{{ park.city }}, {{ park.country }}</span>
            </div>
            <div class="delete-park-actions">
              <!-- BOTÃO DELETAR TODAS ANÁLISES -->
              <div class="tooltip-wrapper">
                <Button
                    v-tooltip.top="'Deletar todas as análises deste parque'"
                    :loading="deletingAllAnalysesId === park.id"
                    class="delete-all-analyses-btn"
                    rounded
                    severity="warning"
                    size="small"
                    text
                    @click.stop="openDeleteAllAnalysesConfirm(park.id!)"
                >
                  <template #icon>
                    <Eraser :size="18" color="#f59e0b"/>
                  </template>
                </Button>
              </div>

              <!-- BOTÃO DELETAR PARQUE -->
              <div class="tooltip-wrapper">
                <Button
                    v-tooltip.top="'Deletar parque e todas as análises'"
                    :loading="deletingParkId === park.id"
                    class="delete-park-btn"
                    icon="pi pi-trash"
                    rounded
                    severity="danger"
                    size="small"
                    text
                    @click.stop="openDeleteParkConfirm(park.id!)"
                />
              </div>
              <i
                  :class="expandedParkId === park.id ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"
                  class="delete-park-toggle"
              />
            </div>
          </div>

          <!-- ANÁLISES DO PARQUE (EXPANDIDO) -->
          <div v-if="expandedParkId === park.id" class="delete-analyses-container">
            <div v-if="loadingAnalyses[park.id!]" class="delete-analyses-loading">
              <i class="pi pi-spin pi-spinner"></i>
              Carregando análises...
            </div>
            <div v-else-if="!analyses[park.id!] || analyses[park.id!]?.length === 0" class="delete-analyses-empty">
              <i class="pi pi-info-circle"></i>
              <span>Nenhuma análise encontrada para este parque</span>
            </div>
            <div v-else class="delete-analyses-list">
              <div
                  v-for="analysis in analyses[park.id!]"
                  :key="analysis.analysis_id"
                  class="delete-analysis-item"
              >
                <div class="delete-analysis-info">
                  <!-- DATA -->
                  <div class="delete-analysis-field">
                    <i class="pi pi-calendar"></i>
                    <span class="delete-analysis-label">Data:</span>
                    <span class="delete-analysis-value">{{ formatDate(analysis.image_date || '') }}</span>
                  </div>

                  <!-- HORA (se tiver) -->
                  <div v-if="analysis.analyzed_at" class="delete-analysis-field">
                    <i class="pi pi-clock"></i>
                    <span class="delete-analysis-label">Hora:</span>
                    <span class="delete-analysis-value">{{ formatTime(analysis.analyzed_at) }}</span>
                  </div>

                  <!-- TEMPERATURA -->
                  <div v-if="analysis.park_lst_celsius !== undefined && analysis.park_lst_celsius !== null"
                       class="delete-analysis-field">
                    <i class="pi pi-thermometer"></i>
                    <span class="delete-analysis-label">LST:</span>
                    <span :style="{ color: getTemperatureColor(analysis.park_lst_celsius) }"
                          class="delete-analysis-value">
                      {{ analysis.park_lst_celsius.toFixed(1) }}°C
                    </span>
                  </div>

                  <!-- SATÉLITE -->
                  <div class="delete-analysis-field">
                    <i class="pi pi-satellite"></i>
                    <span class="delete-analysis-label">Satélite:</span>
                    <span class="delete-analysis-value">{{ analysis.satellite_name || 'Landsat 8' }}</span>
                  </div>

                  <!-- STATUS -->
                </div>
                <!-- BOTÃO DELETAR ANÁLISE -->
                <div class="tooltip-wrapper">
                  <Button
                      v-tooltip.top="'Deletar esta análise'"
                      :loading="deletingAnalysisId === analysis.analysis_id"
                      class="delete-analysis-btn"
                      rounded
                      severity="danger"
                      size="small"
                      text
                      @click.stop="openDeleteAnalysisConfirm(park.id!, analysis.analysis_id!)"
                  >
                    <template #icon>
                      <i class="pi pi-trash" style="font-size: 14px;"></i>
                    </template>
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <Button
          :label="`Fechar`"
          icon="pi pi-times"
          severity="secondary"
          @click="closeDialog"
      />
    </template>
  </Dialog>

  <!-- 🔥 CONFIRM DIALOG PARA DELETAR PARQUE -->
  <ConfirmDialog
      v-model:visible="showConfirmDeletePark"
      :detail="deleteParkDetail"
      :loading="deletingParkId !== null"
      :message="deleteParkMessage"
      confirm-label="Deletar Parque"
      title="Deletar Parque"
      type="danger"
      @cancel="parkToDelete = null"
      @confirm="confirmDeletePark"
  />

  <!-- 🔥 CONFIRM DIALOG PARA DELETAR ANÁLISE -->
  <ConfirmDialog
      v-model:visible="showConfirmDeleteAnalysis"
      :detail="deleteAnalysisDetail"
      :loading="deletingAnalysisId !== null"
      :message="'Tem certeza que deseja deletar esta análise?'"
      confirm-label="Deletar Análise"
      title="🗑️ Deletar Análise"
      type="warning"
      @cancel="analysisToDelete = null"
      @confirm="confirmDeleteAnalysis"
  />
</template>

<script lang="ts" setup>
import {computed, ref, watch} from 'vue'
import {getParks, type Park} from '@/services'
import {useNotifications} from '~/composables/useErrorHandler'
import {getParkAnalysesList} from '~/services/eeService'
import type {CoolingAnalysisResult} from '~/types'
import ConfirmDialog from '~/components/ConfirmDialog.vue'
import {Eraser} from 'reicon-vue'

const {handleError, handleSuccess} = useNotifications()

// ============================================================
// 🔥 PROPS E EMITS
// ============================================================
const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'deleted', parkId: number): void
  (e: 'analysisDeleted', analysisId: number): void
}>()

// ============================================================
// 🔥 STATE
// ============================================================
const loading = ref(false)
const parks = ref<Park[]>([])
const expandedParkId = ref<number | null>(null)
const analyses = ref<Record<number, CoolingAnalysisResult[]>>({})
const loadingAnalyses = ref<Record<number, boolean>>({})
const deletingParkId = ref<number | null>(null)
const deletingAllAnalysesId = ref<number | null>(null)
const deletingAnalysisId = ref<number | null>(null)

// 🔥 CONFIRM DIALOGS
const showConfirmDeletePark = ref(false)
const showConfirmDeleteAllAnalyses = ref(false)
const showConfirmDeleteAnalysis = ref(false)
const parkToDelete = ref<Park | null>(null)
const parkToDeleteAllAnalyses = ref<Park | null>(null)
const analysisToDelete = ref<CoolingAnalysisResult | null>(null)
const analysesCount = ref(0)

// ============================================================
// 🔥 COMPUTED PARA MENSAGENS
// ============================================================
const deleteParkMessage = computed(() => {
  const name = parkToDelete.value?.name || ''
  return `Tem certeza que deseja deletar o parque "${name}"?`
})

const deleteParkDetail = computed(() => {
  return `Todas as análises deste parque também serão removidas.`
})

const deleteAnalysisDetail = computed(() => {
  const date = analysisToDelete.value?.image_date || 'N/A'
  const temp = analysisToDelete.value?.park_lst_celsius
  const tempStr = temp !== undefined && temp !== null ? ` | LST: ${temp.toFixed(1)}°C` : ''
  return `Data: ${formatDate(date)}${tempStr}`
})

// ============================================================
// 🔥 FUNÇÕES AUXILIARES
// ============================================================
function formatDate(dateStr: string): string {
  if (!dateStr) return 'N/A'
  const date = new Date(dateStr)
  return date.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

function formatTime(dateStr: string): string {
  if (!dateStr) return 'N/A'
  const date = new Date(dateStr)
  return date.toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

function getTemperatureColor(temp: number): string {
  if (temp < 20) return '#3b82f6'  // Azul - frio
  if (temp < 25) return '#10b981'  // Verde - ameno
  if (temp < 30) return '#f59e0b'  // Amarelo - morno
  if (temp < 35) return '#f97316'  // Laranja - quente
  return '#ef4444'  // Vermelho - muito quente
}

// ============================================================
// 🔥 FUNÇÃO PARA CONTROLAR VISIBILIDADE
// ============================================================
function handleVisibleChange(value: boolean) {
  emit('update:visible', value)
  if (!value) {
    expandedParkId.value = null
    analyses.value = {}
  }
}

// ============================================================
// 🔥 CARREGAR PARQUES
// ============================================================
async function loadParks() {
  loading.value = true
  try {
    const data = await getParks()
    if (data.success) {
      parks.value = data.parks
    }
  } catch (error) {
    console.error('Erro ao carregar parques:', error)
    handleError('Erro ao carregar lista de parques')
  } finally {
    loading.value = false
  }
}

// ============================================================
// 🔥 EXPANDIR/RECOLHER PARQUE
// ============================================================
async function togglePark(parkId: number) {
  if (expandedParkId.value === parkId) {
    expandedParkId.value = null
    return
  }

  expandedParkId.value = parkId
  await loadAnalyses(parkId)
}

// ============================================================
// 🔥 CARREGAR ANÁLISES DO PARQUE
// ============================================================
async function loadAnalyses(parkId: number) {
  if (analyses.value[parkId]) return

  loadingAnalyses.value[parkId] = true
  try {
    const data = await getParkAnalysesList(parkId)
    analyses.value[parkId] = data || []
  } catch (error) {
    console.error('Erro ao carregar análises:', error)
    analyses.value[parkId] = []
  } finally {
    loadingAnalyses.value[parkId] = false
  }
}

// ============================================================
// 🔥 DELETAR TODAS AS ANÁLISES - ABRIR CONFIRMAÇÃO
// ============================================================
function openDeleteAllAnalysesConfirm(parkId: number) {
  const park = parks.value.find(p => p.id === parkId)
  if (!park) {
    handleError('Parque não encontrado')
    return
  }

  parkToDeleteAllAnalyses.value = park
  analysesCount.value = analyses.value[parkId]?.length || 0

  if (analysesCount.value === 0) {
    handleError('Este parque não tem análises para deletar')
    return
  }

  showConfirmDeleteAllAnalyses.value = true
}

// ============================================================
// 🔥 CONFIRMAR DELETAR TODAS AS ANÁLISES
// ============================================================
async function confirmDeleteAllAnalyses() {
  if (!parkToDeleteAllAnalyses.value || !parkToDeleteAllAnalyses.value.id) return

  const parkId = parkToDeleteAllAnalyses.value.id
  const parkName = parkToDeleteAllAnalyses.value.name

  deletingAllAnalysesId.value = parkId
  showConfirmDeleteAllAnalyses.value = false

  try {
    // 🔥 ENDPOINT PARA DELETAR TODAS AS ANÁLISES DO PARQUE
    const response = await fetch(`http://localhost:3001/api/parks/${parkId}/analyses`, {
      method: 'DELETE'
    })

    const data = await response.json()

    if (data.success) {
      handleSuccess(`Todas as ${data.analyses_deleted || 0} análises do parque "${parkName}" foram deletadas!`)

      // 🔥 LIMPA AS ANÁLISES DO PARQUE NA LISTA
      if (analyses.value[parkId]) {
        analyses.value[parkId] = []
      }

      // 🔥 RECARREGA AS ANÁLISES (agora vazio)
      await loadAnalyses(parkId)
    } else {
      handleError(data.error || 'Erro ao deletar análises')
    }
  } catch (error) {
    console.error('❌ Erro ao deletar análises:', error)
    handleError('Erro ao deletar análises')
  } finally {
    deletingAllAnalysesId.value = null
    parkToDeleteAllAnalyses.value = null
  }
}

// ============================================================
// 🔥 DELETAR PARQUE - ABRIR CONFIRMAÇÃO
// ============================================================
function openDeleteParkConfirm(parkId: number) {
  const park = parks.value.find(p => p.id === parkId)
  if (!park) {
    handleError('Parque não encontrado')
    return
  }

  parkToDelete.value = park
  analysesCount.value = analyses.value[parkId]?.length || 0
  showConfirmDeletePark.value = true
}

// ============================================================
// 🔥 CONFIRMAR DELETAR PARQUE
// ============================================================
async function confirmDeletePark() {
  if (!parkToDelete.value || !parkToDelete.value.id) return

  const parkId = parkToDelete.value.id
  const parkName = parkToDelete.value.name

  deletingParkId.value = parkId
  showConfirmDeletePark.value = false

  try {
    const response = await fetch(`http://localhost:3001/api/parks/${parkId}`, {
      method: 'DELETE'
    })

    const data = await response.json()

    if (data.success) {
      handleSuccess(`Parque "${parkName}" e ${data.analyses_deleted || 0} análises deletados!`)

      parks.value = parks.value.filter(p => p.id !== parkId)
      delete analyses.value[parkId]
      delete loadingAnalyses.value[parkId]

      if (expandedParkId.value === parkId) {
        expandedParkId.value = null
      }

      emit('deleted', parkId)
    } else {
      handleError(data.error || 'Erro ao deletar parque')
    }
  } catch (error) {
    console.error('❌ Erro ao deletar parque:', error)
    handleError('Erro ao deletar parque')
  } finally {
    deletingParkId.value = null
    parkToDelete.value = null
  }
}

// ============================================================
// 🔥 DELETAR ANÁLISE - ABRIR CONFIRMAÇÃO
// ============================================================
function openDeleteAnalysisConfirm(parkId: number, analysisId: number) {
  const parkAnalyses = analyses.value[parkId] || []
  const analysis = parkAnalyses.find(a => a.analysis_id === analysisId)

  if (!analysis) {
    handleError('Análise não encontrada')
    return
  }

  analysisToDelete.value = analysis
  showConfirmDeleteAnalysis.value = true
}

// ============================================================
// 🔥 CONFIRMAR DELETAR ANÁLISE
// ============================================================
async function confirmDeleteAnalysis() {
  if (!analysisToDelete.value) return

  const analysisId = analysisToDelete.value.analysis_id
  const parkId = analysisToDelete.value.park_id

  if (!analysisId || !parkId) {
    handleError('ID da análise ou parque não encontrado')
    return
  }

  deletingAnalysisId.value = analysisId
  showConfirmDeleteAnalysis.value = false

  try {
    const response = await fetch(`http://localhost:3001/api/parks/${parkId}/analyses/${analysisId}`, {
      method: 'DELETE'
    })

    const data = await response.json()

    if (data.success) {
      handleSuccess(`Análise deletada com sucesso!`)

      // 🔥 VERIFICA ANTES DE FILTRAR
      if (analyses.value[parkId]) {
        analyses.value[parkId] = analyses.value[parkId].filter(a => a.analysis_id !== analysisId)
      }

      emit('analysisDeleted', analysisId)
    } else {
      handleError(data.error || 'Erro ao deletar análise')
    }
  } catch (error) {
    console.error('❌ Erro ao deletar análise:', error)
    handleError('Erro ao deletar análise')
  } finally {
    deletingAnalysisId.value = null
    analysisToDelete.value = null
  }
}

// ============================================================
// 🔥 FECHAR DIALOG
// ============================================================
function closeDialog() {
  handleVisibleChange(false)
}

// ============================================================
// 🔥 WATCH
// ============================================================
watch(() => props.visible, (newVal) => {
  if (newVal) {
    loadParks()
  } else {
    expandedParkId.value = null
    analyses.value = {}
  }
})

// ============================================================
// 🔥 TOOLTIP POSITION - CORRIGIDO
// ============================================================
function updateTooltipPosition(event: Event) {
  const target = event.currentTarget as HTMLElement
  if (!target) return

  const rect = target.getBoundingClientRect()
  const x = rect.left + rect.width / 2
  const y = rect.top

  target.style.setProperty('--tooltip-x', x + 'px')
  target.style.setProperty('--tooltip-y', y + 'px')
}

// ============================================================
// 🔥 ADICIONAR EVENTOS NO MOUNT
// ============================================================
onMounted(() => {
  // Usa setTimeout para garantir que o DOM está renderizado
  setTimeout(() => {
    document.querySelectorAll('.tooltip-wrapper').forEach(el => {
      el.addEventListener('mouseenter', updateTooltipPosition)
    })
  }, 100)
})

// ============================================================
// 🔥 REMOVER EVENTOS NO UNMOUNT
// ============================================================
onUnmounted(() => {
  document.querySelectorAll('.tooltip-wrapper').forEach(el => {
    el.removeEventListener('mouseenter', updateTooltipPosition)
  })
})
</script>


<style scoped>
.delete-dialog-content {
  padding: 4px 0;
}

.delete-dialog-alert {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  color: #6b7280;
  background: #fefce8;
  padding: 10px 12px;
  border-radius: 6px;
  border: 1px solid #fde68a;
  margin-bottom: 12px;
}

.delete-dialog-alert i {
  margin-top: 2px;
  flex-shrink: 0;
}

.delete-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  color: #6b7280;
}

.delete-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 30px;
  color: #9ca3af;
}

.delete-empty i {
  font-size: 32px;
}

/* LISTA DE PARQUES */
.delete-list {
  max-height: 400px;
  overflow-y: auto; /* mantém o scroll */
  overflow-x: visible; /* 🔥 MUDA PARA VISIBLE */
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}

.delete-park-item {
  border-bottom: 1px solid #f3f4f6;
  position: relative; /* 🔥 ADICIONA */
  overflow: visible; /* 🔥 ADICIONA */
}

.delete-park-item:last-child {
  border-bottom: none;
}

.delete-park-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  cursor: pointer;
  transition: all 0.15s ease;
  background: white;
  position: relative; /* 🔥 ADICIONA */
  z-index: 2; /* 🔥 ADICIONA */
}

.delete-park-header:hover {
  background: #f9fafb;
}

.delete-park-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.delete-park-name {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
}

.delete-park-location {
  font-size: 12px;
  color: #6b7280;
}

.delete-park-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.delete-park-badge {
  font-size: 10px;
}

.delete-park-toggle {
  font-size: 14px;
  color: #9ca3af;
  transition: transform 0.2s ease;
}

.delete-park-expanded .delete-park-header {
  background: #f0f4ff;
  border-bottom: 1px solid #e5e7eb;
}

/* ANÁLISES */
.delete-analyses-container {
  background: #fafbfc;
  padding: 8px 14px 12px 14px;
  border-top: 1px solid #e5e7eb;
}

.delete-analyses-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  color: #6b7280;
  font-size: 13px;
}

.delete-analyses-empty {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  color: #9ca3af;
  font-size: 13px;
}

.delete-analyses-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.delete-analysis-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  background: white;
  border-radius: 4px;
  border: 1px solid #e5e7eb;
  transition: all 0.15s ease;
}

.delete-analysis-item:hover {
  background: #f9fafb;
}

.delete-analysis-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #1f2937;
}

.delete-analysis-info i {
  color: #6b7280;
  font-size: 14px;
}

.delete-analysis-date {
  font-weight: 500;
}

.delete-analysis-item .p-button {
  flex-shrink: 0;
}

/* RESPONSIVIDADE */
@media (max-width: 480px) {
  .delete-park-header {
    flex-wrap: wrap;
    gap: 4px;
  }

  .delete-park-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .delete-analysis-info {
    flex-wrap: wrap;
    gap: 4px;
  }
}

/* 🔥 ESTILOS PARA OS CAMPOS DA ANÁLISE */
.delete-analysis-info {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 12px;
  flex: 1;
}

.delete-analysis-field {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #1f2937;
}

.delete-analysis-field i {
  font-size: 12px;
  color: #6b7280;
}

.delete-analysis-label {
  color: #6b7280;
  font-weight: 400;
}

.delete-analysis-value {
  font-weight: 500;
  color: #1f2937;
}

/* 🔥 BOTÕES DE AÇÃO */
.delete-park-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

/* 🔥 BOTÃO DELETAR TODAS ANÁLISES */
.delete-all-analyses-btn {
  transition: all 0.2s ease !important;
  background: rgba(245, 158, 11, 0.08) !important;
  border-radius: 50% !important;
  padding: 6px !important;
}

.delete-all-analyses-btn:hover {
  background: rgba(245, 158, 11, 0.2) !important;
  transform: scale(1.1) !important;
}

.delete-all-analyses-btn:active {
  transform: scale(0.9) !important;
}

/* 🔥 BOTÃO DELETAR PARQUE */
.delete-park-btn {
  transition: all 0.2s ease !important;
  background: rgba(239, 68, 68, 0.08) !important;
  border-radius: 50% !important;
  padding: 6px !important;
}

.delete-park-btn:hover {
  background: rgba(239, 68, 68, 0.2) !important;
  transform: scale(1.1) !important;
}

.delete-park-btn:active {
  transform: scale(0.9) !important;
}

/* 🔥 INFO DO PARQUE COM STATS */
.delete-park-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.delete-park-name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.delete-park-location {
  font-size: 12px;
  color: #6b7280;
}

.delete-park-stats {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 2px;
}

.delete-park-stats .p-badge {
  font-size: 10px !important;
  padding: 0 8px !important;
}

/* 🔥 FORÇA O ESTILO DO TOOLTIP DO PRIMEVUE */
.p-tooltip .p-tooltip-text {
  font-size: 11px !important;
  font-weight: 500 !important;
  font-family: 'Titillium Web', sans-serif !important;
  background: rgba(0, 0, 0, 0.85) !important;
  color: white !important;
  padding: 4px 10px !important;
  border-radius: 6px !important;
  backdrop-filter: blur(4px) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  line-height: 1.4 !important;
  letter-spacing: 0.3px !important;
  max-width: 300px !important;
}

.p-tooltip-arrow {
  border-top-color: rgba(0, 0, 0, 0.85) !important;
}
</style>