<!-- components/ParkSearchResults.vue -->
<template>
  <div class="result-overlay overlay-wrapper" v-if="results.length">
    <CollapsibleCard
        v-if="results.length"
        :badge="results.length"
        :defaultExpanded="true"
        icon="pi pi-list"
        title="Resultados"
    >
      <div
          v-for="item in results"
          :key="item.id"
          class="result-item"
          @click="handleSelect(item)"
      >
        <label class="result-name">
          <Tree :size="16"/>
          <span>{{ item.tags?.name || item.name || 'Parque sem nome' }}</span>
        </label>
        <label class="result-location">
          <i class="pi pi-map-marker"></i>
          {{ item.city }}, {{ item.country }}
        </label>
        <label class="result-osm-id">
          <i class="pi pi-tag"></i>
          ID: {{ item.osm_id }}
        </label>
      </div>
    </CollapsibleCard>
  </div>
</template>

<script lang="ts" setup>
import {Tree} from 'reicon-vue';
import type { SearchParkResult } from '@/types'

defineProps<{
  results: SearchParkResult[]
}>()

const emit = defineEmits<{
  (e: 'select', park: SearchParkResult): void
}>()

function handleSelect(item: SearchParkResult) {
  emit('select', item)
}
</script>

<style scoped>
.result-item {
  padding: 10px 0;
  cursor: pointer;
  border-bottom: 1px solid #f3f4f6;
  transition: all 0.15s ease;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.result-item:last-child {
  border-bottom: none;
}

.result-item:hover {
  background: #f0f7ff;
  padding-left: 18px;
}

.result-name {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
}

.result-location {
  font-size: 12px;
  color: #6b7280;
}

.result-osm-id {
  font-size: 10px;
  color: #9ca3af;
}
</style>