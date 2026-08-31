<template>
  <Dialog
      :closable="true"
      :header="title"
      :modal="true"
      :style="{ width: '420px', maxWidth: '90vw' }"
      :visible="visible"
      class="confirm-dialog"
      @update:visible="handleVisibleChange"
  >
    <div class="confirm-dialog-content">
      <div :class="type" class="confirm-dialog-icon">
        <i :class="icon"></i>
      </div>
      <div class="confirm-dialog-message">
        <p class="confirm-dialog-text">{{ message }}</p>
        <p v-if="detail" class="confirm-dialog-detail">{{ detail }}</p>
      </div>
    </div>

    <template #footer>
      <Button
          :label="`Cancelar`"
          icon="pi pi-times"
          severity="secondary"
          @click="handleCancel"
      />
      <Button
          :icon="confirmIcon"
          :label="confirmLabel"
          :loading="loading"
          :severity="severity"
          @click="handleConfirm"
      />
    </template>
  </Dialog>
</template>

<script lang="ts" setup>

// ============================================================
// 🔥 PROPS E EMITS
// ============================================================
const props = defineProps<{
  visible: boolean
  title?: string
  message: string
  detail?: string
  type?: 'danger' | 'warning' | 'info'
  confirmLabel?: string
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

// ============================================================
// 🔥 COMPUTED
// ============================================================
const icon = computed(() => {
  switch (props.type) {
    case 'danger':
      return 'pi pi-exclamation-triangle'
    case 'warning':
      return 'pi pi-exclamation-circle'
    case 'info':
      return 'pi pi-info-circle'
    default:
      return 'pi pi-question-circle'
  }
})

const severity = computed(() => {
  switch (props.type) {
    case 'danger':
      return 'danger'
    case 'warning':
      return 'warning'
    default:
      return 'primary'
  }
})

const confirmIcon = computed(() => {
  switch (props.type) {
    case 'danger':
      return 'pi pi-trash'
    default:
      return 'pi pi-check'
  }
})

// ============================================================
// 🔥 FUNÇÕES
// ============================================================
function handleVisibleChange(value: boolean) {
  emit('update:visible', value)
  if (!value) {
    emit('cancel')
  }
}

function handleConfirm() {
  emit('confirm')
}

function handleCancel() {
  emit('update:visible', false)
  emit('cancel')
}

function closeDialog() {
  emit('update:visible', false)
}
</script>

<style scoped>
.confirm-dialog-content {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 8px 0;
}

.confirm-dialog-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  flex-shrink: 0;
  font-size: 24px;
}

.confirm-dialog-icon.danger {
  background: #fef2f2;
  color: #dc2626;
}

.confirm-dialog-icon.warning {
  background: #fffbeb;
  color: #f59e0b;
}

.confirm-dialog-icon.info {
  background: #eff6ff;
  color: #3b82f6;
}

.confirm-dialog-message {
  flex: 1;
}

.confirm-dialog-text {
  font-size: 15px;
  font-weight: 500;
  color: #1f2937;
  margin: 0 0 4px 0;
}

.confirm-dialog-detail {
  font-size: 13px;
  color: #6b7280;
  margin: 0;
}

/* RESPONSIVIDADE */
@media (max-width: 480px) {
  .confirm-dialog-content {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
}
</style>