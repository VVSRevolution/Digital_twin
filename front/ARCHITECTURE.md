# Arquitetura Frontend - Digital Twin

## 📂 Estrutura do Projeto

```
app/
├── app.vue                    # Componente root da aplicação
│
├── 🎨 COMPONENTES (components/)
│   ├── MapView.vue           # Mapa principal com análise
│   ├── ParkSearchBar.vue      # Barra de busca e controles
│   └── NotificationCenter.vue # Sistema de notificações
│
├── 🎭 COMPOSABLES (composables/)
│   └── useErrorHandler.ts    # Gerenciamento de erros e notificações
│
├── 📡 SERVIÇOS (services/)
│   ├── eeService.ts          # Earth Engine + Backend API
│   │   ├── Análise de cooling island
│   │   ├── Série temporal de LST
│   │   └── Classificação de tipos
│   │
│   ├── geoService.ts         # Geo utilities + OSM
│   │   ├── Conversão de features
│   │   ├── Busca no OSM
│   │   └── Operações geográficas
│   │
│   └── parkService.ts        # Parques API
│       └── Busca de parques (Overpass)
│
├── 🛠️ UTILIDADES (utils/)
│   └── buffer.ts             # Desenho de buffers concêntricos
│
├── 📝 TIPOS (types/)
│   └── index.ts              # Tipos e interfaces compartilhadas
│
├── 💾 STORES (stores/)        # Pinia stores (vazio - preparado)
├── 📄 PAGES (pages/)          # Pages Nuxt (vazio - preparado)
├── 🎴 LAYOUTS (layouts/)      # Layouts Nuxt (vazio - preparado)
└── 🚦 MIDDLEWARE (middleware/)# Middlewares Nuxt (vazio - preparado)
```

---

## 🔄 Fluxo de Dados

```
MapView.vue (busca)
    ↓
parkService.searchPark()
    ↓
geoService.convertParkToFeature()
    ↓
utils.drawBuffers()
    ↓
eeService.analyzeParkCooling()  [Backend API]
    ↓
composables.useErrorHandler()   [Notificações]
    ↓
MapView.vue (exibe resultados)
```

---

## 📦 Tipos Centralizados (types/index.ts)

Todos os tipos são exportados de um único arquivo para facilitar imports:

```typescript
import type {
  OSMPlace,
  OSMElement,
  SearchResult,
  ParkGeometry,
  CoolingAnalysisResult,
  BufferResult,
  TimeseriesResult,
  CoolingIslandType,
} from '~/types'
```

---

## 📡 Services

### `eeService.ts`
Integração com Earth Engine API (via backend Python)

**Funções Principais:**
- `analyzeParkCooling()` - Análise completa de cooling island
- `getParkLSTTimeseries()` - Série temporal de LST
- `getLSTAtPoint()` - LST em um ponto específico
- `calculatePCI()` - Cálculo do Park Cooling Intensity
- `classifyCoolingIsland()` - Classificação do tipo
- `formatCoolingStats()` - Formatação para UI

### `geoService.ts`
Operações geográficas e busca no OpenStreetMap

**Funções Principais:**
- `convertParkToFeature()` - OSM Element → OpenLayers Feature
- `searchOSM()` - Busca lugares no Nominatim
- `createPoint()` - Cria ponto (Turf.js)
- `createBuffer()` - Cria buffer (Turf.js)

### `parkService.ts`
Busca de parques via Overpass API

**Funções Principais:**
- `searchPark()` - Busca por nome

---

## 🎨 Components

### `MapView.vue`
Componente principal que coordena:
- Inicialização do mapa OpenLayers
- Busca de parques
- Visualização de buffers
- Exibição de gradiente de temperatura
- Gerenciamento de estado local

**Props:** Nenhuma (componente independente)

**Events:** Nenhum (coordena tudo internamente)

### `ParkSearchBar.vue`
Barra lateral com:
- Campo de busca
- Resultados em dropdown
- Estatísticas de cooling
- Controles de visualização

### `NotificationCenter.vue`
Sistema de notificações (toast/alerts)

---

## 🎭 Composables

### `useErrorHandler`
Hook para gerenciamento centralizado de erros

```typescript
const { handleError, handleSuccess, handleWarning } = useErrorHandler()
handleError(error, 'Título da notificação')
```

---

## 🛠️ Utils

### `buffer.ts`
Desenha 11 buffers concêntricos (90m cada) com:
- Conversão GeoJSON → Feature
- Cálculo de anéis (diferenças)
- Estilo visual

---

## 📝 Convenções de Código

### Imports
```typescript
// Usar alias ~ (configurado no nuxt.config.ts)
import { Component } from '~/components'
import { useHook } from '~/composables'
import { service } from '~/services'
import type { Type } from '~/types'
import { util } from '~/utils'
```

### Nomes de Arquivos
- **Components:** PascalCase (ex: `MapView.vue`)
- **Composables:** camelCase com prefixo `use` (ex: `useErrorHandler.ts`)
- **Services:** camelCase + `Service` (ex: `parkService.ts`)
- **Utils:** kebab-case (ex: `buffer.ts`)

### Nomes de Funções
- **Serviços:** camelCase (ex: `analyzeParkCooling()`)
- **Hooks:** prefixo `use` + camelCase (ex: `useErrorHandler()`)
- **Utilidades:** camelCase (ex: `drawBuffers()`)

### Estrutura de Componentes
```vue
<script setup lang="ts">
// 1. Imports
// 2. Tipos
// 3. Refs/Reactive
// 4. Computed
// 5. Methods
// 6. Hooks (onMounted, etc)
</script>

<template>
  <!-- JSX -->
</template>

<style scoped>
/* Estilos */
</style>
```

---

## 🚀 Próximos Passos

1. **Implementar Stores (Pinia)**
   - `parkStore` - Cache de parques
   - `uiStore` - Estado global da UI
   - `analysisStore` - Histórico de análises

2. **Criar Pages**
   - `index.vue` - Home
   - `history.vue` - Histórico de análises
   - `about.vue` - Sobre o projeto

3. **Adicionar Middleware**
   - Proteção de rotas
   - Validações

4. **Testes Unitários**
   - Services (mocking APIs)
   - Utils (funções puras)
   - Composables

5. **Melhorias UI/UX**
   - Responsividade
   - Temas (light/dark)
   - Internacionalização (i18n)

---

## 📚 Dependências Principais

- **Nuxt 3** - Framework
- **Vue 3** - UI
- **TypeScript** - Type safety
- **OpenLayers** - Mapas
- **Turf.js** - Operações geográficas
- **Pinia** - State management (preparado)

---

## 🔗 Links Úteis

- [Nuxt Docs](https://nuxt.com)
- [Vue 3 Docs](https://vuejs.org)
- [OpenLayers Docs](https://openlayers.org)
- [Turf.js Docs](https://turfjs.org)
- [Pinia Docs](https://pinia.vuejs.org)
