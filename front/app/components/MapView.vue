<script lang="ts" setup>
import {onMounted, onUnmounted, ref} from "vue"
import {convertParkToFeature} from "~/services/geoService"
import {searchPark} from "~/services/parkService"
import {analyzeParkCooling, formatCoolingStats} from "~/services/eeService"
import type Feature from 'ol/Feature'
import type Geometry from 'ol/geom/Geometry'
import Style from "ol/style/Style"
import {Fill, Stroke} from "ol/style"
import {drawBuffers} from "~/utils/buffer"
import {XYZ} from "ol/source"
import GeoJSON from "ol/format/GeoJSON"
import {useNotifications} from '~/composables/useErrorHandler'
import ParkSearchBar from "~/components/ParkSearchBar.vue"
import type { SearchResult, CoolingAnalysisResult } from '~/types'

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


// ===== FUNÇÃO PARA CRIAR RASTER CONTÍNUO COM TRANSPARÊNCIA =====
async function addPixelLayer(buffers: any[]) {
  // Remove camada anterior
  if (pixelLayer) {
    map.removeLayer(pixelLayer)
    pixelLayer = null
  }

  if (!showPixels.value) return

  const allTemps: number[] = []
  const points: { lon: number; lat: number; temp: number }[] = []

  buffers.forEach((buffer) => {
    buffer.pixels?.forEach((pixel: any) => {
      if (pixel.lat && pixel.lon && pixel.temperature !== null) {
        points.push({
          lon: pixel.lon,
          lat: pixel.lat,
          temp: pixel.temperature
        })
        allTemps.push(pixel.temperature)
      }
    })
  })

  if (points.length === 0) return

  // 🔥 CALCULA EXTENSÃO DA ÁREA
  const lons = points.map(p => p.lon)
  const lats = points.map(p => p.lat)

  const margin = 0.0005
  const minLon = Math.min(...lons) - margin
  const maxLon = Math.max(...lons) + margin
  const minLat = Math.min(...lats) - margin
  const maxLat = Math.max(...lats) + margin

  // 🔥 RESOLUÇÃO (15 metros)
  const resolution = 0.00015
  const cols = Math.ceil((maxLon - minLon) / resolution)
  const rows = Math.ceil((maxLat - minLat) / resolution)

  // 🔥 CALCULA GRADIENTE LOCAL
  const minTemp = Math.min(...allTemps)
  const maxTemp = Math.max(...allTemps)
  const range = maxTemp - minTemp
  const gradientMinVal = minTemp - range * 0.05
  const gradientMaxVal = maxTemp + range * 0.05
  const gradientRange = gradientMaxVal - gradientMinVal

  gradientMin.value = gradientMinVal
  gradientMax.value = gradientMaxVal
  totalPixels.value = points.length

  console.log(`📊 Criando raster contínuo: ${cols}x${rows} = ${cols * rows} pixels`)

  // 🔥 CRIA ARRAY DE CORES (RGBA) COM TRANSPARÊNCIA
  const imageData = new Uint8ClampedArray(cols * rows * 4)
  const radius = resolution * 4
  const radiusSq = radius * radius

  // 🔥 DEFINE UM LIMITE MÍNIMO DE PESO PARA CONSIDERAR DADO VÁLIDO
  const MIN_WEIGHT = 0.01

  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      const lon = minLon + col * resolution
      const lat = minLat + row * resolution

      let weightedSum = 0
      let weightSum = 0

      for (const point of points) {
        const dx = point.lon - lon
        const dy = point.lat - lat
        const distSq = dx * dx + dy * dy

        if (distSq < radiusSq) {
          const dist = Math.sqrt(distSq)
          const weight = 1 / (dist + 0.001)
          weightedSum += point.temp * weight
          weightSum += weight
        }
      }

      const idx = (row * cols + col) * 4

      // 🔥 SE NÃO HOUVER DADOS SUFICIENTES, FAZ TRANSPARENTE
      if (weightSum < MIN_WEIGHT) {
        imageData[idx] = 0
        imageData[idx + 1] = 0
        imageData[idx + 2] = 0
        imageData[idx + 3] = 0 // 🔥 COMPLETAMENTE TRANSPARENTE
        continue
      }

      const temp = weightedSum / weightSum
      let normalized = (temp - gradientMinVal) / gradientRange
      normalized = Math.max(0, Math.min(1, normalized))

      const color = getGradientColor(normalized)
      const nums = color.match(/\d+/g)?.map(Number) ?? [0, 0, 0]
      const [r = 0, g = 0, b = 0] = nums

      imageData[idx] = r
      imageData[idx + 1] = g
      imageData[idx + 2] = b
      imageData[idx + 3] = 220 // 🔥 SEMI-TRANSPARENTE (opaco)
    }
  }

  // 🔥 CRIA IMAGEM
  const canvas = document.createElement('canvas')
  canvas.width = cols
  canvas.height = rows
  const ctx = canvas.getContext('2d')!
  const imageDataObj = new ImageData(imageData, cols, rows)
  ctx.putImageData(imageDataObj, 0, 0)
  const imageUrl = canvas.toDataURL('image/png')

  // 🔥 ADICIONA AO MAPA COMO RASTER
  const ImageLayer = (await import('ol/layer/Image')).default
  const ImageStatic = (await import('ol/source/ImageStatic')).default

  const [x1, y1] = fromLonLat([minLon, minLat]) as [number, number]
  const [x2, y2] = fromLonLat([maxLon, maxLat]) as [number, number]
  const extent: [number, number, number, number] = [x1, y1, x2, y2]

  pixelLayer = new ImageLayer({
    source: new ImageStatic({
      url: imageUrl,
      imageExtent: extent
    }),
    zIndex: 5,
    opacity: 0.75
  })

  map.addLayer(pixelLayer)
  console.log(`✅ Raster contínuo criado com ${cols * rows} pixels (áreas sem dados transparentes)`)
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
          }) as unknown as Style
      )

      vectorSource.clear()
      vectorSource.addFeature(feature)

      parkName.value = element?.tags?.name ?? "Parque sem nome"

      drawBuffers(feature, vectorSource)
      await analyzePark(feature)

      const extent = feature.getGeometry()!.getExtent()
      map.getView().fit(extent, {
        padding: [50, 50, 50, 50],
        duration: 800
      })

      results.value = []
    }

  } catch (error) {
    console.error("❌ Erro ao buscar parque:", error)
    const {handleError} = useNotifications()
    handleError(error, 'Erro ao buscar parque')
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
async function analyzePark(feature: Feature<Geometry>) {
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
      console.error('❌ Geometria não encontrada')
      const {handleError} = useNotifications()
      handleError('Geometria não encontrada')
      return
    }

    const result = await analyzeParkCooling(geojson.geometry as any)

    if (!result.success) {
      const {handleError} = useNotifications()
      handleError(result.error || 'Erro desconhecido', 'Análise falhou')
      coolingData.value = result
      return
    }

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
    const {handleSuccess} = useNotifications()
    handleSuccess('Análise concluída com sucesso!')
  } catch (error) {
    console.error("❌ Erro na análise:", error)
    const {handleError} = useNotifications()
    handleError(error, 'Erro na análise')
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

    const extent = feature.getGeometry()!.getExtent()
    map.getView().fit(extent, {
      padding: [50, 50, 50, 50],
      duration: 800
    })

    await analyzePark(feature)

    results.value = []
    search.value = ""

  } catch (error) {
    console.error("❌ Erro ao selecionar parque:", error)
    const {handleError} = useNotifications()
    handleError(error, 'Erro ao selecionar parque')
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

      <ParkSearchBar
          v-model:search="search"
          v-model:showPixels="showPixels"
          :loading="loading"
          :analyzing="analyzing"
          :results="results"
          :predefinedParks="predefinedParks"
          :showStats="showStats"
          :coolingData="coolingData"
          :parkName="parkName"
          :gradientMin="gradientMin"
          :gradientMax="gradientMax"
          :totalPixels="totalPixels"
          @search="searchPlace"
          @select="selectPark"
          @addPark="openAddParkModal"
          @refresh="refreshData"
          @export="exportReport"
          @settings="openSettings"
          @about="showAbout"
          @togglePixels="togglePixels"
      />
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


:global(.ol-zoom) {
  position: absolute !important;
  bottom: 20px !important;
  right: 20px !important;
  top: auto !important;
  left: auto !important;
  z-index: 9999;
}

:global(.ol-rotate) {
  position: absolute !important;
  bottom: 65px !important; /* fica acima do zoom */
  right: 20px !important;
  top: auto !important;
  left: auto !important;
  z-index: 9999;
}

:global(.ol-control button) {
  width: 36px !important;
  height: 36px !important;
  border-radius: 8px !important;

  background-color: #ffffff !important;
  color: #333 !important;

  border: 1px solid rgba(0, 0, 0, 0.1) !important;

  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15) !important;

  margin: 5px 5px !important;

  font-size: 18px !important;
  cursor: pointer;
  transition: all 0.2s ease;
}
</style>