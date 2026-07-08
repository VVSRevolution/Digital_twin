# Digital Twin - Frontend (Nuxt)

Aplicação frontend do projeto Digital Twin, construída com **Nuxt 3** + **Vue 3** + **TypeScript**.

## 📁 Estrutura do Projeto

```
app/
├── app.vue                 # Componente root da aplicação
├── components/             # Componentes Vue reutilizáveis
│   ├── MapView.vue        # Visualizador de mapa
│   ├── NotificationCenter.vue
│   └── ParkSearchBar.vue
├── composables/            # Vue Composables (lógica reutilizável)
│   └── useErrorHandler.ts
├── layouts/                # Layouts Nuxt (estrutura de página)
├── middleware/             # Middlewares Nuxt (interceptadores de rota)
├── pages/                  # Páginas automáticas (Nuxt routing)
├── services/               # Serviços/APIs (lógica de integração)
│   ├── eeService.ts       # Earth Engine + Backend API
│   ├── geoService.ts      # Geo utilities + OSM
│   └── parkService.ts     # Parques (Overpass API)
├── stores/                 # Pinia stores (gerenciamento de estado)
├── types/                  # Types/Interfaces TypeScript
│   └── index.ts           # Tipos centralizados
└── utils/                  # Funções utilitárias
    └── buffer.ts
```

## 📚 Documentação

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Arquitetura completa, fluxo de dados e convenções
- **[TYPES.md](./TYPES.md)** - Documentação de todos os tipos centralizados
- **[README.md (app/)](./app/)** - Documentação da pasta app

## 🎯 Guia de Pastas

### `components/`
Componentes Vue reutilizáveis. Seguem a convenção PascalCase.
- Usados em múltiplos lugares
- Props bem definidas
- Isolados e testáveis

### `composables/`
Vue Composables - lógica reutilizável entre componentes.
- Prefixo: `use*`
- Exemplo: `useErrorHandler`

### `services/`
Serviços de integração com APIs e lógica de negócio.
- `eeService.ts` - Earth Engine + Backend
- `geoService.ts` - Geo utilities
- `parkService.ts` - Busca de parques
- Chamadas HTTP centralizadas
- Transformação de dados

### `stores/`
Gerenciamento de estado global com Pinia.
- Estado compartilhado entre componentes
- Ações e mutations
- (Preparado para implementação)

### `types/`
Definições TypeScript (interfaces, types, enums).
- Tipos compartilhados
- Modelos de dados
- **Todos exportados de `types/index.ts`**

### `utils/`
Funções utilitárias e helpers.
- `buffer.ts` - Desenho de buffers
- Funções puras
- Cálculos e transformações

### `layouts/`
Layouts Nuxt - estrutura visual de páginas.
- (Preparado para implementação)

### `pages/`
Páginas automáticas - cada arquivo = uma rota.
- (Preparado para implementação)

### `middleware/`
Interceptadores de rota - autenticação, redirecionamento, etc.
- (Preparado para implementação)

---

## 🔄 Fluxo de Dados Principal

```
Usuário digita parque
    ↓
parkService.searchPark() [Overpass API]
    ↓
geoService.convertParkToFeature()
    ↓
utils.drawBuffers() [Turf.js]
    ↓
eeService.analyzeParkCooling() [Backend Python API]
    ↓
MapView exibe mapa + gradiente + estatísticas
    ↓
useErrorHandler() → Notificações
```

---

## 🎨 Tipos Centralizados

Todos os tipos estão em `app/types/index.ts`:

```typescript
import type {
  OSMPlace,
  OSMElement,
  SearchResult,
  CoolingAnalysisResult,
  BufferResult,
  TimeseriesResult,
  CoolingIslandType,
} from '~/types'
```

📖 Ver [TYPES.md](./TYPES.md) para documentação completa.

---

## 🚀 Setup

Make sure to install dependencies:

```bash
# npm
npm install

# pnpm
pnpm install

# yarn
yarn install

# bun
bun install
```

## 🛠️ Development Server

Start the development server on `http://localhost:3000`:

```bash
# npm
npm run dev

# pnpm
pnpm dev

# yarn
yarn dev

# bun
bun run dev
```

## 📦 Production

Build the application for production:

```bash
# npm
npm run build

# pnpm
pnpm build

# yarn
yarn build

# bun
bun run build
```

Locally preview production build:

```bash
# npm
npm run preview

# pnpm
pnpm preview

# yarn
yarn preview

# bun
bun run preview
```

Check out the [deployment documentation](https://nuxt.com/docs/getting-started/deployment) for more information.

---

## 📖 Convenções de Código

### Imports
```typescript
// Usar alias ~ (configurado em nuxt.config.ts)
import { MapView } from '~/components'
import { useErrorHandler } from '~/composables'
import { parkService } from '~/services'
import type { CoolingAnalysisResult } from '~/types'
import { drawBuffers } from '~/utils/buffer'
```

### Nomes
- **Components**: PascalCase (ex: `MapView.vue`)
- **Composables**: `use*` camelCase (ex: `useErrorHandler.ts`)
- **Services**: camelCase (ex: `parkService.ts`)
- **Utils**: camelCase (ex: `buffer.ts`)
- **Types**: PascalCase ou UPPER_CASE (ex: `CoolingAnalysisResult`)

### Estrutura de Componentes
```vue
<script setup lang="ts">
// 1. Imports
// 2. Types/Interfaces
// 3. Refs/Reactive
// 4. Computed
// 5. Methods
// 6. Hooks (onMounted, etc)
</script>

<template>
  <!-- JSX -->
</template>

<style scoped>
/* estilos */
</style>
```

---

## 🚀 Próximos Passos

1. **Implementar Pinia Stores** - Cache, estado global
2. **Criar Pages** - Home, Histórico, Sobre
3. **Adicionar Middleware** - Validações, proteção
4. **Testes Unitários** - Services, Utils
5. **Melhorias UI** - Responsividade, temas

---

## 📚 Recursos

- [Nuxt Docs](https://nuxt.com/docs)
- [Vue 3 Docs](https://vuejs.org/)
- [TypeScript](https://www.typescriptlang.org/)
- [OpenLayers](https://openlayers.org/)
- [Turf.js](https://turfjs.org/)
- [Pinia](https://pinia.vuejs.org/)

Make sure to install dependencies:

```bash
# npm
npm install

# pnpm
pnpm install

# yarn
yarn install

# bun
bun install
```

## Development Server

Start the development server on `http://localhost:3000`:

```bash
# npm
npm run dev

# pnpm
pnpm dev

# yarn
yarn dev

# bun
bun run dev
```

## Production

Build the application for production:

```bash
# npm
npm run build

# pnpm
pnpm build

# yarn
yarn build

# bun
bun run build
```

Locally preview production build:

```bash
# npm
npm run preview

# pnpm
pnpm preview

# yarn
yarn preview

# bun
bun run preview
```

Check out the [deployment documentation](https://nuxt.com/docs/getting-started/deployment) for more information.

---

## 🎯 Convenções de Código

### Naming Conventions
- **Components**: PascalCase (ex: `MapView.vue`)
- **Composables**: camelCase com prefixo `use` (ex: `useErrorHandler.ts`)
- **Services**: camelCase (ex: `parkService.ts`)
- **Stores**: camelCase (ex: `parkStore.ts`)

### Estrutura de Componentes
```vue
<script setup lang="ts">
// imports
// props
// composables
// refs/reactive
// computed
// methods
</script>

<template>
  <!-- JSX -->
</template>

<style scoped>
/* estilos */
</style>
```

### Serviços
```typescript
// parkService.ts
export const parkService = {
  async getParks() { /* ... */ },
  async getParkById(id: string) { /* ... */ },
  // ...
}
```

---

## 🚀 Próximos Passos

1. **Configurar `pages/`** - Adicionar páginas automáticas do Nuxt
2. **Configurar `stores/`** - Implementar Pinia stores se necessário
3. **Adicionar types** - Documentar tipos em `types/`
4. **Criar middleware** - Autenticação, proteção de rotas, etc.

---

## 📖 Recursos

- [Nuxt Docs](https://nuxt.com/docs)
- [Vue 3 Docs](https://vuejs.org/)
- [TypeScript](https://www.typescriptlang.org/)
- [Pinia](https://pinia.vuejs.org/)
