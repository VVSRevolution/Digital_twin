<script lang="ts" setup>
import {onMounted, onUnmounted, ref} from "vue"
import {convertParkToFeature} from "@/services/geoService"
import {searchPark} from "@/services/parkService"
import {analyzeParkCooling, type CoolingAnalysisResult, formatCoolingStats} from "@/services/eeService"
import Style from "ol/style/Style"
import {Circle, Fill, Stroke} from "ol/style"
import {drawBuffers} from "~/utils/buffer"
import {XYZ} from "ol/source"
import GeoJSON from "ol/format/GeoJSON"
import {Feature} from "ol"
import {Point} from "ol/geom"

// ===== TIPOS =====
interface SearchResult {
  elements: Array<{
    id: number
    lat: number
    lon: number
    tags?: {
      name?: string
      [key: string]: unknown
    }
  }>
}

// ===== REFS =====
const loading = ref(false)
const mapEl = ref<HTMLDivElement | null>(null)
const search = ref("")
const results = ref<SearchResult['elements']>([])
const coolingData = ref<CoolingAnalysisResult | null>(null)
const showStats = ref(false)
const parkName = ref("")
const analyzing = ref(false)
const isSearching = ref(false)
const showPixels = ref(true)
const gradientMin = ref<number | null>(null)
const gradientMax = ref<number | null>(null)
const totalPixels = ref(0)
let searchTimeout: ReturnType<typeof setTimeout> | null = null

// ===== VARIÁVEIS OPENLAYERS =====
let map: any
let vectorSource: any
let pixelLayer: any = null
let fromLonLat: (coord: number[]) => number[]
const format = new GeoJSON()

// ===== FUNÇÃO PARA GERAR COR DO GRADIENTE =====
function getGradientColor(t: number): string {
  // t = 0 (frio) → t = 1 (quente)
  // Gradiente: Azul → Ciano → Verde → Amarelo → Laranja → Vermelho

  let r: number, g: number, b: number

  if (t < 0.2) {
    // Azul → Ciano (0 → 0.2)
    const p = t / 0.2
    r = 0
    g = Math.round(50 * p)
    b = Math.round(200 - 50 * p)
  } else if (t < 0.4) {
    // Ciano → Verde (0.2 → 0.4)
    const p = (t - 0.2) / 0.2
    r = 0
    g = Math.round(50 + 150 * p)
    b = Math.round(150 - 150 * p)
  } else if (t < 0.6) {
    // Verde → Amarelo (0.4 → 0.6)
    const p = (t - 0.4) / 0.2
    r = Math.round(150 * p)
    g = Math.round(200)
    b = Math.round(50 - 50 * p)
  } else if (t < 0.8) {
    // Amarelo → Laranja (0.6 → 0.8)
    const p = (t - 0.6) / 0.2
    r = Math.round(150 + 105 * p)
    g = Math.round(200 - 100 * p)
    b = 0
  } else {
    // Laranja → Vermelho (0.8 → 1.0)
    const p = (t - 0.8) / 0.2
    r = 255
    g = Math.round(100 - 100 * p)
    b = 0
  }

  return `rgb(${r}, ${g}, ${b})`
}

// ===== FUNÇÃO PARA VISUALIZAR PIXELS COM GRADIENTE LOCAL =====
async function addPixelLayer(buffers: any[]) {
  // Remove camada anterior
  if (pixelLayer) {
    map.removeLayer(pixelLayer)
    pixelLayer = null
  }

  if (!showPixels.value) return

  const pixelFeatures: Feature[] = []

  // 🔥 COLETA TODAS AS TEMPERATURAS DOS PIXELS
  const allTemps: number[] = []

  buffers.forEach((buffer) => {
    buffer.pixels?.forEach((pixel: any) => {
      if (pixel.temperature !== null && pixel.temperature !== undefined) {
        allTemps.push(pixel.temperature)
      }
    })
  })

  // 🔥 CALCULA MÍNIMO E MÁXIMO LOCAL
  let minTemp = Infinity
  let maxTemp = -Infinity

  if (allTemps.length > 0) {
    minTemp = Math.min(...allTemps)
    maxTemp = Math.max(...allTemps)
  } else {
    // Fallback se não houver dados
    minTemp = 25
    maxTemp = 35
  }

  // 🔥 ADICIONA UMA MARGEM PARA O GRADIENTE (5% de cada lado)
  const range = maxTemp - minTemp
  const margin = range * 0.05
  const gradientMinVal = minTemp - margin
  const gradientMaxVal = maxTemp + margin
  const gradientRange = gradientMaxVal - gradientMinVal

  // Atualiza as refs para a legenda
  gradientMin.value = gradientMinVal
  gradientMax.value = gradientMaxVal

  console.log(`📊 Gradiente local: ${gradientMinVal.toFixed(2)}°C → ${gradientMaxVal.toFixed(2)}°C (${allTemps.length} pixels)`)

  buffers.forEach((buffer) => {
    buffer.pixels?.forEach((pixel: any) => {
      if (pixel.lat && pixel.lon && pixel.temperature !== null) {
        const coords = fromLonLat([pixel.lon, pixel.lat])

        const feature = new Feature({
          geometry: new Point(coords),
          temperature: pixel.temperature,
          bufferDistance: buffer.distance
        })

        // 🔥 CALCULA A COR BASEADA NO GRADIENTE LOCAL
        const temp = pixel.temperature
        let normalized = 0

        if (gradientRange > 0) {
          normalized = (temp - gradientMinVal) / gradientRange
          // Garante que fique entre 0 e 1
          normalized = Math.max(0, Math.min(1, normalized))
        }

        // 🔥 COR DO GRADIENTE
        const color = getGradientColor(normalized)

        // Tamanho baseado na distância (pixels mais distantes são ligeiramente maiores)
        const size = 4 + (buffer.distance / 990) * 4

        feature.setStyle(
            new Style({
              image: new Circle({
                radius: size,
                fill: new Fill({color}),
                stroke: new Stroke({
                  color: 'rgba(255,255,255,0.15)',
                  width: 0.5
                })
              })
            })
        )

        pixelFeatures.push(feature)
      }
    })
  })

  // 🔥 CRIA CAMADA DE PIXELS
  const VectorLayer = (await import('ol/layer/Vector')).default
  const VectorSource = (await import('ol/source/Vector')).default

  const pixelSource = new VectorSource({
    features: pixelFeatures
  })

  pixelLayer = new VectorLayer({
    source: pixelSource,
    zIndex: 10,
    opacity: 0.85
  })

  map.addLayer(pixelLayer)

  // 🔥 RETORNA OS VALORES PARA A LEGENDA
  return {min: gradientMinVal, max: gradientMaxVal}
}

// ===== FUNÇÃO PRINCIPAL =====
async function searchPlace() {
  console.log('🔍 searchPlace chamado')

  if (!search.value || loading.value || isSearching.value) {
    console.log('⏭️ Ignorando (já em execução)')
    return
  }

  loading.value = true
  isSearching.value = true
  showStats.value = false
  coolingData.value = null
  parkName.value = ""
  gradientMin.value = null
  gradientMax.value = null
  totalPixels.value = 0

  // Remove camada de pixels anterior
  if (pixelLayer) {
    map.removeLayer(pixelLayer)
    pixelLayer = null
  }

  try {
    const data = await searchPark(search.value) as SearchResult
    results.value = data.elements || []

    if (data.elements?.length) {
      const element = data.elements[0]
      const feature = convertParkToFeature(element)

      feature.setStyle(
          new Style({
            fill: new Fill({
              color: "rgba(22, 152, 7, 0.35)"
            }),
            stroke: new Stroke({
              color: "#00aa00",
              width: 3,
              lineDash: [10, 10]
            })
          })
      )

      vectorSource.clear()
      vectorSource.addFeature(feature)

      parkName.value = element.tags?.name || "Parque sem nome"

      drawBuffers(feature, vectorSource)
      await analyzePark(feature)

      const extent = feature.getGeometry().getExtent()
      map.getView().fit(extent, {
        padding: [50, 50, 50, 50],
        duration: 800
      })

      results.value = []
    }

  } catch (error) {
    console.error("Erro:", error)
  } finally {
    loading.value = false
    isSearching.value = false
  }
}

// ===== FUNÇÃO DEBOUNCE MANUAL =====
function debouncedSearch() {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(() => {
    searchPlace()
  }, 500)
}

// ===== FUNÇÃO DE ANÁLISE =====
async function analyzePark(feature: any) {
  if (analyzing.value) {
    console.log('⏭️ Análise já em execução')
    return
  }

  analyzing.value = true

  try {
    const geojson = format.writeFeatureObject(feature, {
      featureProjection: "EPSG:3857",
      dataProjection: "EPSG:4326"
    })

    if (!geojson.geometry) {
      throw new Error("Geometria não encontrada")
    }

    const result = await analyzeParkCooling(geojson.geometry as any)
    coolingData.value = result

    // 🔥 VISUALIZA OS PIXELS COM GRADIENTE LOCAL
    if (result.buffers && result.buffers.length > 0) {
      await addPixelLayer(result.buffers)

      // 🔥 CONTA TOTAL DE PIXELS
      let count = 0
      result.buffers.forEach((b: any) => {
        count += b.statistics?.count || 0
      })
      totalPixels.value = count
    }

    console.log("🌡️ Análise do Cooling Island:")
    console.log(`  🏠 Parque: ${parkName.value}`)
    console.log(`  🌡️ LST do Parque: ${result.park_lst?.celsius?.toFixed(2) ?? 'N/A'}°C`)
    console.log(`  ❄️ PCI: ${result.pci?.toFixed(2) ?? 'N/A'}°C`)
    console.log(`  📏 PCD: ${result.pcd ?? 'N/A'}m`)
    console.log(`  📐 PCA: ${result.pca?.ha?.toFixed(2) ?? 'N/A'} ha`)

    console.log("\n📊 Estatísticas por buffer:")
    result.buffers.forEach((b: any) => {
      const stats = b.statistics
      console.log(`  Anel ${b.buffer_index}: ${b.distance_prev}-${b.distance}m → ${stats.mean?.toFixed(2) ?? 'N/A'}°C (${stats.count} pixels)`)
    })

    showStats.value = true
  } catch (error) {
    console.error("❌ Erro na análise:", error)
  } finally {
    analyzing.value = false
  }
}

// ===== SELEÇÃO DE PARQUE =====
async function selectPark(item: SearchResult['elements'][0]) {
  if (isSearching.value || analyzing.value) return

  try {
    const feature = convertParkToFeature(item)
    vectorSource.clear()
    vectorSource.addFeature(feature)

    parkName.value = item.tags?.name || "Parque sem nome"

    drawBuffers(feature, vectorSource)
    await analyzePark(feature)

    const extent = feature.getGeometry().getExtent()
    map.getView().fit(extent, {
      padding: [50, 50, 50, 50],
      duration: 800
    })

    results.value = []
    search.value = ""

  } catch (error) {
    console.error("Erro ao selecionar parque:", error)
  }
}

// ===== TOGGLE PIXELS =====
async function togglePixels() {
  showPixels.value = !showPixels.value
  if (showPixels.value && coolingData.value?.buffers) {
    await addPixelLayer(coolingData.value.buffers)
  } else if (pixelLayer) {
    map.removeLayer(pixelLayer)
    pixelLayer = null
  }
}

// ===== SETUP DO MAPA =====
onMounted(async () => {
  const {Map, View} = await import("ol")
  const TileLayer = (await import("ol/layer/Tile")).default
  const VectorLayer = (await import("ol/layer/Vector")).default
  const VectorSource = (await import("ol/source/Vector")).default
  const proj = await import("ol/proj")

  fromLonLat = proj.fromLonLat
  vectorSource = new VectorSource()

  map = new Map({
    target: mapEl.value!,
    layers: [
      new TileLayer({
        source: new XYZ({
          url: "https://{a-c}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"
        })
      }),
      new VectorLayer({
        source: vectorSource
      })
    ],
    view: new View({
      center: fromLonLat([-49.2648, -16.6869]),
      zoom: 12
    })
  })
})

// ===== LIMPA MAPA =====
onUnmounted(() => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  if (pixelLayer) {
    map?.removeLayer(pixelLayer)
  }
  if (map) {
    map.setTarget(undefined)
    map.dispose()
  }
})
</script>

<template>
  <div class="page">
    <div class="map-wrapper">

      <!-- MAPA -->
      <div ref="mapEl" class="map"></div>

      <!-- SEARCH BAR -->
      <div class="search-bar">
        <div class="search-input">
          <input
              v-model="search"
              placeholder="Pesquisar parque..."
              @keydown.enter="debouncedSearch"
          />
          <button :disabled="loading || analyzing" @click="debouncedSearch">
            {{ loading ? "Buscando..." : analyzing ? "Analisando..." : "🔍 Buscar" }}
          </button>
        </div>

        <!-- RESULTADOS DA ANÁLISE -->
        <div v-if="showStats && coolingData" class="stats">
          <div class="stats-header">
            <h4>🌳 {{ parkName }}</h4>
            <span :class="coolingData.success ? 'success' : 'error'" class="badge">
              {{ coolingData.success ? "✅ OK" : "❌ Falha" }}
            </span>
          </div>

          <div
              v-for="stat in formatCoolingStats(coolingData)"
              :key="stat.label"
              class="stat-item"
          >
            <span>{{ stat.label }}</span>
            <strong :style="{ color: stat.color }">{{ stat.value }}</strong>
          </div>

          <div v-if="coolingData.error" class="error-msg">
            ⚠️ {{ coolingData.error }}
          </div>
        </div>

        <!-- 🔥 CONTROLE DE VISUALIZAÇÃO DOS PIXELS -->
        <div v-if="showStats && coolingData?.buffers" class="controls">
          <label class="toggle-label">
            <input v-model="showPixels" type="checkbox" @change="togglePixels"/>
            Mostrar pixels de temperatura
          </label>

          <!-- 🔥 LEGENDA COM GRADIENTE LOCAL -->
          <div v-if="gradientMin !== null && gradientMax !== null" class="gradient-legend">
            <div class="gradient-header">
              <span>🌡️ Temperatura dos Pixels</span>
              <span class="pixel-count">{{ totalPixels }} pixels</span>
            </div>
            <div class="gradient-bar"></div>
            <div class="gradient-labels">
              <span>{{ gradientMin.toFixed(1) }}°C</span>
              <span>{{ gradientMax.toFixed(1) }}°C</span>
            </div>
            <div style="font-size: 10px; color: #999; text-align: center; margin-top: 2px;">
              Gradiente baseado nos valores mínimo e máximo locais
            </div>
          </div>
        </div>

        <!-- 🔥 ESTATÍSTICAS DOS BUFFERS -->
        <div v-if="showStats && coolingData?.buffers" class="buffer-stats">
          <h4>📊 Estatísticas por Anel</h4>
          <div class="stats-grid">
            <div
                v-for="buffer in coolingData.buffers"
                :key="buffer.distance"
                :style="{
                background: buffer.statistics?.mean !== null
                  ? `rgba(255, 100, 0, ${Math.max(0, Math.min(1, (buffer.statistics.mean - 25) / 10))})`
                  : '#f5f5f5'
              }"
                class="stats-item"
            >
              <span class="label">{{ buffer.distance }}m</span>
              <span class="mean">{{ buffer.statistics?.mean?.toFixed(1) ?? 'N/A' }}°C</span>
              <span class="count">{{ buffer.statistics?.count ?? 0 }}px</span>
            </div>
          </div>
        </div>

        <!-- DROPDOWN DE RESULTADOS -->
        <div v-if="results.length" class="dropdown">
          <div
              v-for="(item, index) in results"
              :key="index"
              class="dropdown-item"
              @click="selectPark(item)"
          >
            🌳 {{ item.tags?.name || "Parque sem nome" }}
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.page {
  position: relative;
  height: 100vh;
}

.map-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
}

.map {
  width: 100%;
  height: 100%;
}

/* SEARCH BAR */
.search-bar {
  position: absolute;
  top: 12px;
  left: 100px;
  display: flex;
  gap: 8px;
  flex-direction: column;
  background: white;
  padding: 15px;
  border-radius: 8px;
  z-index: 1000;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  min-width: 280px;
  max-width: 350px;
  max-height: 80vh;
  overflow-y: auto;
}

.search-input {
  display: flex;
  gap: 8px;
}

.search-input input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
}

.search-input input:focus {
  border-color: #1a73e8;
  box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.2);
}

.search-input button {
  padding: 8px 16px;
  background: #1a73e8;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
  transition: background 0.2s;
}

.search-input button:hover:not(:disabled) {
  background: #1557b0;
}

.search-input button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* STATS */
.stats {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 2px solid #eee;
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.stats-header h4 {
  margin: 0;
  color: #333;
  font-size: 14px;
  font-weight: 600;
}

.badge {
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 12px;
  font-weight: 600;
}

.badge.success {
  background: #d4edda;
  color: #155724;
}

.badge.error {
  background: #f8d7da;
  color: #721c24;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  padding: 5px 0;
  font-size: 13px;
  border-bottom: 1px solid #f5f5f5;
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-item span {
  color: #666;
}

.stat-item strong {
  font-weight: 600;
}

.error-msg {
  margin-top: 8px;
  padding: 8px 12px;
  background: #f8d7da;
  color: #721c24;
  border-radius: 4px;
  font-size: 12px;
}

/* CONTROLS */
.controls {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 2px solid #eee;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  cursor: pointer;
  color: #333;
}

/* GRADIENT LEGEND */
.gradient-legend {
  margin-top: 8px;
  padding: 10px 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.gradient-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #555;
  margin-bottom: 6px;
}

.gradient-header span {
  font-weight: 600;
}

.pixel-count {
  font-weight: 400;
  color: #999;
  font-size: 11px;
}

.gradient-bar {
  width: 100%;
  height: 14px;
  border-radius: 4px;
  background: linear-gradient(to right,
  rgb(0, 0, 200),
  rgb(0, 100, 150),
  rgb(0, 180, 80),
  rgb(50, 200, 50),
  rgb(200, 200, 0),
  rgb(255, 150, 0),
  rgb(255, 80, 0),
  rgb(200, 0, 0)
  );
  border: 1px solid #dee2e6;
}

.gradient-labels {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  font-weight: 600;
  color: #495057;
  margin-top: 3px;
}

/* BUFFER STATS */
.buffer-stats {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 2px solid #eee;
}

.buffer-stats h4 {
  font-size: 13px;
  margin: 0 0 8px 0;
  color: #333;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(70px, 1fr));
  gap: 4px;
  max-height: 200px;
  overflow-y: auto;
}

.stats-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6px 4px;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
  font-size: 11px;
  transition: all 0.2s;
}

.stats-item:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.stats-item .label {
  font-weight: 600;
  color: #555;
}

.stats-item .mean {
  font-weight: 700;
  color: #1a1a1a;
}

.stats-item .count {
  font-size: 9px;
  color: #999;
}

/* DROPDOWN */
.dropdown {
  max-height: 200px;
  overflow: auto;
  background: white;
  border-radius: 6px;
  margin-top: 4px;
  border: 1px solid #eee;
}

.dropdown-item {
  padding: 8px 12px;
  cursor: pointer;
  border-bottom: 1px solid #f5f5f5;
  font-size: 14px;
  transition: background 0.15s;
}

.dropdown-item:hover {
  background: #f0f7ff;
}

.dropdown-item:last-child {
  border-bottom: none;
}

/* RESPONSIVIDADE */
@media (max-width: 768px) {
  .search-bar {
    top: 12px;
    left: 50%;
    transform: translateX(-50%);
    width: 90%;
    max-width: 400px;
    min-width: unset;
  }
}

/* SCROLLBAR */
.search-bar::-webkit-scrollbar {
  width: 4px;
}

.search-bar::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.search-bar::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 4px;
}

.search-bar::-webkit-scrollbar-thumb:hover {
  background: #aaa;
}
</style>