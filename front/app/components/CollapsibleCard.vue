<!-- components/CollapsibleCard.vue -->
<template>
  <Card :class="{ 'collapsed': !isExpanded }" class="collapsible-card">
    <template #content>
      <!-- HEADER CLICÁVEL -->
      <div class="card-header" @click="toggle">
        <div class="card-header-left">
          <span class="card-icon">{{ icon }}</span>
          <span class="card-title">{{ title }}</span>
          <span v-if="badge !== undefined" class="card-badge">{{ badge }}</span>
        </div>
        <div class="card-header-right">
          <span class="card-toggle">{{ isExpanded ? '▲' : '▼' }}</span>
        </div>
      </div>

      <!-- CONTEÚDO -->
      <transition name="expand">
        <div v-if="isExpanded" class="card-body">
          <slot/>
        </div>
      </transition>
    </template>
  </Card>
</template>

<script lang="ts" setup>
import {ref} from 'vue'

const props = defineProps<{
  title: string
  icon?: string
  badge?: number | string
  defaultExpanded?: boolean
}>()

const isExpanded = ref(props.defaultExpanded !== undefined ? props.defaultExpanded : true)

function toggle() {
  isExpanded.value = !isExpanded.value
}
</script>

<style scoped>
/* 🔥 MESMO ESTILO DO CARD 1 */
.collapsible-card :deep(.p-card) {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  overflow: visible !important;
}

.collapsible-card :deep(.p-card-body) {
  padding: 0 !important;
  border-radius: 8px; /* 🔥 MANTÉM BORDAS */
  overflow: hidden; /* 🔥 GARANTE QUE AS BORDAS FICAM ARREDONDADAS */
}

.collapsible-card :deep(.p-card-content) {
  padding: 12px 16px !important;
  border-radius: 8px; /* 🔥 MANTÉM BORDAS */
}

/* 🔥 QUANDO RECOLHIDO, MANTÉM AS BORDAS */
.collapsible-card.collapsed :deep(.p-card-body) {
  border-radius: 8px !important;
}

.collapsible-card.collapsed :deep(.p-card-content) {
  border-radius: 8px !important;
}

/* 🔥 HEADER */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background: #f8fafc;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
  transition: all 0.2s ease;
  user-select: none;
  border-radius: 8px; /* 🔥 SEMPRE ARREDONDADO */
  margin: -12px -16px;
}

/* 🔥 QUANDO EXPANDIDO, A BORDA DE BAIXO FICA RETA */
.collapsible-card:not(.collapsed) .card-header {
  border-radius: 8px 8px 0 0;
}

/* 🔥 QUANDO RECOLHIDO, A BORDA FICA COMPLETAMENTE ARREDONDADA */
.collapsible-card.collapsed .card-header {
  border-radius: 8px !important;
}

.card-header:hover {
  background: #eef2ff;
}

.card-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-icon {
  font-size: 16px;
}

.card-title {
  font-weight: 600;
}

.card-badge {
  background: #3b82f6;
  color: white;
  padding: 0 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 700;
  min-width: 18px;
  text-align: center;
}

.card-toggle {
  font-size: 12px;
  color: #6b7280;
  transition: transform 0.3s;
}

/* 🔥 CORPO DO CARD */
.card-body {
  margin-top: 12px;
  padding-top: 0;
  border-top: 1px solid #e5e7eb;
}

/* 🔥 TRANSIÇÃO */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
  max-height: 500px;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
}

.expand-enter-to,
.expand-leave-from {
  max-height: 500px;
  opacity: 1;
}
</style>