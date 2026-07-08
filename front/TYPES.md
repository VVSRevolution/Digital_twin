# Tipos do Projeto - Digital Twin

Todos os tipos compartilhados estão centralizados em `app/types/index.ts`.

## 📦 Tipos Principais

### Parques & Busca

```typescript
// Elemento OSM (OpenStreetMap)
type OSMElement = {
  id: number
  lat: number
  lon: number
  tags?: {
    name?: string
    [key: string]: unknown
  }
  geometry?: Array<{ lat: number; lon: number }>
}

// Resultado de busca
type SearchResult = {
  elements: OSMElement[]
}

// Local OSM (Nominatim)
type OSMPlace = {
  lon: string
  lat: string
  display_name: string
}
```

### Geometria

```typescript
// Geometria em GeoJSON
type ParkGeometry = {
  type: 'Polygon' | 'MultiPolygon'
  coordinates: number[][][] | number[][][][]
}
```

### Dados de Temperatura (LST)

```typescript
// Pixel com temperatura
interface PixelTemperature {
  lat: number | null
  lon: number | null
  temperature: number
}

// Estatísticas de um buffer
interface BufferStatistics {
  count: number
  mean: number | null
  min: number | null
  max: number | null
  std: number | null
}

// Resultado de um buffer (anel)
interface BufferResult {
  distance: number           // Distância do buffer em metros
  distance_prev: number      // Distância anterior
  buffer_index: number       // Índice do buffer (0-10)
  pixels: PixelTemperature[] // Pixels com temperatura
  statistics: BufferStatistics
  area_ha: number           // Área em hectares
  area_m2: number           // Área em metros²
  lst_celsius: number | null
  lst_kelvin: number | null
}
```

### Resultado de Análise

```typescript
// Resultado completo da análise de cooling island
interface CoolingAnalysisResult {
  success: boolean
  park_lst: {
    kelvin: number | null
    celsius: number | null
  } | null
  buffers: BufferResult[]
  pci: number | null          // Park Cooling Intensity (°C)
  pcd: number | null          // Park Cooling Distance (m)
  pca: {
    ha: number | null         // Park Cooling Area (ha)
    m2: number | null
  } | null
  timestamp: string
  error?: string
}
```

### Série Temporal

```typescript
// Um ponto da série temporal
interface TimeseriesPoint {
  date: string
  lst: number | null
}

// Resultado da série temporal
interface TimeseriesResult {
  success: boolean
  timeseries: TimeseriesPoint[]
  count: number
  timestamp: string
  error?: string
}
```

### Classificação

```typescript
// Tipo de cooling island
type CoolingIslandType = 'regular' | 'declined' | 'increased' | 'other'
```

---

## 🔗 Como Usar

```typescript
import type {
  OSMElement,
  SearchResult,
  CoolingAnalysisResult,
  BufferResult,
  TimeseriesResult,
  CoolingIslandType,
} from '~/types'

// Usar em componentes
<script setup lang="ts">
const coolingData = ref<CoolingAnalysisResult | null>(null)
const buffers = ref<BufferResult[]>([])
const islandType = ref<CoolingIslandType>('other')
</script>
```

---

## 📊 Exemplo de Dado Real

```json
{
  "success": true,
  "park_lst": {
    "kelvin": 301.5,
    "celsius": 28.35
  },
  "pci": 2.14,
  "pcd": 450,
  "pca": {
    "ha": 12.5,
    "m2": 125000
  },
  "buffers": [
    {
      "distance": 90,
      "distance_prev": 0,
      "buffer_index": 0,
      "pixels": [...],
      "statistics": {
        "count": 1200,
        "mean": 30.49,
        "min": 29.2,
        "max": 31.8,
        "std": 0.65
      },
      "area_ha": 0.23,
      "area_m2": 2300,
      "lst_celsius": 30.49,
      "lst_kelvin": 303.64
    }
    // ... mais 10 buffers
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 🎯 Próximos Tipos a Adicionar

- `UserPreferences` - Preferências do usuário
- `AnalysisHistory` - Histórico de análises
- `MapStyle` - Configurações de estilo do mapa
- `ErrorMessage` - Mensagem de erro
- `NotificationEvent` - Evento de notificação
