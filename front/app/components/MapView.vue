<script lang="ts" setup>
import {onMounted, onUnmounted, ref} from "vue"
import type {SearchParkResult} from '~/services/parkService'
import {searchPark} from "~/services/parkService"
import {analyzeParkCooling, getParkAnalyses, getParkAnalysesList, getParkAnalysisDetail} from "~/services/eeService"
import Feature from 'ol/Feature'
import type Geometry from 'ol/geom/Geometry'
import Style from "ol/style/Style"
import {Fill, Stroke} from "ol/style"
import {drawBuffers} from "~/utils/buffer"
import {XYZ} from "ol/source"
import GeoJSON from "ol/format/GeoJSON"
import {useNotifications} from '~/composables/useErrorHandler'
import ParkSearchBar from "~/components/ParkSearchBar.vue"
import type {CoolingAnalysisResult} from '~/types'
import {Overlay} from "ol";
import {Polygon} from "ol/geom";
import type {ParkSuggestion} from "~/types/parkSearch";

// ===== REFS =====
const loading = ref(false)
const mapEl = ref<HTMLDivElement | null>(null)
const search = ref("")
const results = ref<SearchParkResult[]>([])
const coolingData = ref<CoolingAnalysisResult | null>(null)
const parkAnalyses = ref<CoolingAnalysisResult[]>([])  // 🔥 LISTA DE ANÁLISES
const showStats = ref(false)
const parkName = ref("")
const analyzing = ref(false)
const isSearching = ref(false)
const showPixels = ref(true)
const gradientMin = ref<number | null>(null)
const gradientMax = ref<number | null>(null)
const totalPixels = ref(0)
let searchTimeout: ReturnType<typeof setTimeout> | null = null
const tooltipOverlay = ref<Overlay | null>(null)
const tooltipElement = ref<HTMLElement | null>(null)
const pixelOpacity = ref(0.50)
const predefinedParks = ref<SearchParkResult[]>([])
const {handleError, handleSuccess, handleInfo} = useNotifications()

// ===== VARIÁVEIS OPENLAYERS =====
let map: any
let vectorSource: any
let parkFeature: Feature<Geometry> | null = null
let pixelLayer: any = null
let fromLonLat: (coord: number[]) => number[]
const format = new GeoJSON()

// ===== FUNÇÃO PARA GERAR COR DO GRADIENTE =====
function getGradientColor(t: number): string {
  let r: number, g: number, b: number

  if (t < 0.2) {
    const p = t / 0.2
    r = 0
    g = Math.round(50 * p)
    b = Math.round(200 - 50 * p)
  } else if (t < 0.4) {
    const p = (t - 0.2) / 0.2
    r = 0
    g = Math.round(50 + 150 * p)
    b = Math.round(150 - 150 * p)
  } else if (t < 0.6) {
    const p = (t - 0.4) / 0.2
    r = Math.round(150 * p)
    g = Math.round(200)
    b = Math.round(50 - 50 * p)
  } else if (t < 0.8) {
    const p = (t - 0.6) / 0.2
    r = Math.round(150 + 105 * p)
    g = Math.round(200 - 100 * p)
    b = 0
  } else {
    const p = (t - 0.8) / 0.2
    r = 255
    g = Math.round(100 - 100 * p)
    b = 0
  }

  return `rgb(${r}, ${g}, ${b})`
}

// ===== FUNÇÃO PARA CRIAR/ATUALIZAR O TOOLTIP =====
function setupTooltip() {
  const el = document.createElement('div')
  el.style.cssText = `
    position: relative;
    background: rgba(0, 0, 0, 0.85);
    color: white;
    padding: 6px 12px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    pointer-events: none;
    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    backdrop-filter: blur(4px);
    border: 1px solid rgba(255,255,255,0.15);
    font-family: 'Titillium Web', sans-serif;
    transition: opacity 0.15s ease;
    opacity: 0;
    z-index: 1000;
  `
  tooltipElement.value = el

  const overlay = new Overlay({
    element: el,
    positioning: 'bottom-center',
    offset: [0, -10],
    stopEvent: false
  })
  tooltipOverlay.value = overlay
  map.addOverlay(overlay)
}

// ============================================================
// 🔥  DESENHAR PARQUE
// ============================================================
function drawParkOnMap(park: SearchParkResult): Feature<Geometry> | null {
  results.value = [park]
  try {
    const geom = park.geometry_3857 || park.geometry
    if (!geom?.coordinates?.length) return null

    // 🔥 PEGA AS COORDENADAS DIRETO
    let coords = geom.coordinates

    if (geom.type === 'MultiPolygon') {
      coords = (coords as any)[0]
    }

    if (!coords?.length) {
      handleError('❌ Geometria sem coordenadas')
      return null
    }

    const feature = new Feature({
      geometry: new Polygon(coords as number[][][])
    })

    feature.setStyle(
        new Style({
          stroke: new Stroke({
            color: "#00aa00",
            width: 3,
            lineDash: [10, 10]
          }),
          fill: new Fill({
            color: 'rgba(0, 170, 0, 0.1)'
          })
        })
    )

    // Limpa e adiciona ao source
    vectorSource.clear()
    vectorSource.addFeature(feature)

    // Desenha os buffers (linhas vazias)
    drawBuffers(feature, vectorSource)

    // Ajusta a visão
    const extent = feature.getGeometry()!.getExtent()
    map.getView().fit(extent, {
      padding: [50, 50, 50, 50],
      duration: 800
    })

    // Atualiza o nome
    parkName.value = park.tags?.name || park.name || "Parque sem nome"

    console.log('✅ Polígono desenhado com sucesso!')
    return feature

  } catch (error) {
    console.error('❌ Erro ao desenhar polígono:', error)
    handleError('Erro ao desenhar polígono')
    return null
  }
}

// ============================================================
// 🔥  CARREGAR ANÁLISE
// ============================================================
async function loadParkAnalysis(park: SearchParkResult, feature: Feature<Geometry>) {
  console.log('📊 Carregando análise para:', park.name)

  // Se tem ID, tenta buscar do cache
  if (park.id) {
    try {
      const data = await getParkAnalyses(park.id)
      console.log('📥 Dados do cache:', data)

      const analyses = await getParkAnalysesList(park.id)
      console.log('📊 Lista Análises encontradas:', analyses.length)
      parkAnalyses.value = analyses

      if (data.success) {
        // Tem análise em cache
        console.log('📊 Buffers do cache:', data.buffers?.length || 0)

        updateCoolingData(data)
        handleSuccess(`Análise do parque "${park.name}" carregada!`)
        isSearching.value = false
        return
      }
      isSearching.value = false
    } catch (error) {
      console.warn('⚠️ Erro ao buscar cache:', error)
      isSearching.value = false
    }
  }
  console.log('🔄 Sem cache, analisando...')
  await analyzePark(feature, park)
}

// ============================================================
// 🔥  SELECIONAR PARQUE
// ============================================================
async function selectPark(park: SearchParkResult) {

  if (analyzing.value) {
    handleError(`analyzing=${analyzing.value}`)
    return
  }

  console.log('🎯 Selecionando parque:', park.name)

  // 🔥 VERIFICA SE TEM GEOMETRIA
  if (!park.geometry && !park.geometry_3857) {
    handleError('Parque sem geometria')
    return
  }

  // Limpa pixels antigos
  if (pixelLayer) {
    map.removeLayer(pixelLayer)
    pixelLayer = null
  }

  // Reseta dados
  coolingData.value = null
  showStats.value = false
  gradientMin.value = null
  gradientMax.value = null
  totalPixels.value = 0
  parkAnalyses.value = []

  // Desenha o polígono
  const feature = drawParkOnMap(park)
  if (!feature) {
    handleError('Falha ao desenhar polígono')
    return
  }
  // Carrega a análise
  await loadParkAnalysis(park, feature)

  // Limpa resultados da busca
  search.value = ""
}

// ============================================================
// 🔥 FUNÇÃO PARA ATUALIZAR OS DADOS DE COOLING
// ============================================================
function updateCoolingData(data: CoolingAnalysisResult) {
  console.log('🔥 updateCoolingData:', data)
  coolingData.value = data

  // Atualiza os pixels no mapa
  if (data.buffers && data.buffers.length > 0) {
    console.log('✅ Chamando addPixelLayer com', data.buffers.length, 'buffers')
    addPixelLayer(data.buffers)
  } else {
    console.log('⚠️ Nenhum buffer para adicionar')
  }
  showStats.value = true
}

// ============================================================
// 🔥 FUNÇÃO PARA SELECIONAR UMA ANÁLISE DO TIMELINE
// ============================================================
async function handleAnalysisSelect(analysis: CoolingAnalysisResult) {
  console.log('🎯 Análise selecionada:', analysis)

  // 🔥 SE NÃO TEM BUFFERS, BUSCA O DETALHE
  if (!analysis.buffers || analysis.buffers.length === 0) {
    const parkId = analysis.park_id
    const analysisId = analysis.analysis_id
    console.log(parkId)
    console.log(analysisId)

    if (parkId && analysisId) {
      const detail = await getParkAnalysisDetail(parkId, analysisId)
      if (detail) {
        coolingData.value = detail
        if (detail.buffers && detail.buffers.length > 0) {
          await addPixelLayer(detail.buffers)
        }
        showStats.value = true
        handleSuccess(`Análise de ${detail.image_date} carregada!`)
        return
      }
    }
  }

  // 🔥 SE JÁ TEM BUFFERS, USA DIRETO
  coolingData.value = analysis
  if (analysis.buffers && analysis.buffers.length > 0) {
    await addPixelLayer(analysis.buffers)
  }
  showStats.value = true
  handleSuccess(`Análise de ${analysis.image_date} carregada!`)
}

// ============================================================
// 🔥 FUNÇÃO DE ANÁLISE (quando não tem cache)
// ============================================================
async function analyzePark(feature: Feature<Geometry>, park: SearchParkResult) {
  if (analyzing.value) return

  console.log('🔬 Analisando parque:', park.name)
  analyzing.value = true

  try {
    const geojson = format.writeFeatureObject(feature, {
      featureProjection: "EPSG:3857",
      dataProjection: "EPSG:4326"
    })

    if (!geojson.geometry) {
      handleError('Geometria não encontrada')
      return
    }

    const result = await analyzeParkCooling(
        geojson.geometry as any,
        park
    )

    if (!result.success) {
      handleError(result.error || 'Erro desconhecido', 'Análise falhou')
      coolingData.value = result
      return
    }

    updateCoolingData(result)
    handleSuccess('Análise concluída com sucesso!')

  } catch (error) {
    console.error("❌ Erro na análise:", error)
    handleError(error, 'Erro na análise')
    analyzing.value = false
  } finally {
    analyzing.value = false
  }
}

// ===== FUNÇÃO COM GRID PERFEITO =====
async function addPixelLayer(buffers: any[]) {
  if (pixelLayer) {
    map.removeLayer(pixelLayer)
    pixelLayer = null
  }

  if (!showPixels.value) return

  const points: { lon: number; lat: number; temp: number }[] = []

  buffers.forEach((buffer) => {
    buffer.pixels?.forEach((pixel: any) => {
      if (pixel.lat && pixel.lon && pixel.temperature !== null) {
        points.push({
          lon: pixel.lon,
          lat: pixel.lat,
          temp: pixel.temperature
        })
      }
    })
  })

  if (points.length === 0) return

  const temps = points.map(p => p.temp)
  const minTemp = Math.min(...temps)
  const maxTemp = Math.max(...temps)
  const range = maxTemp - minTemp
  const gradientMinVal = minTemp - range * 0.05
  const gradientMaxVal = maxTemp + range * 0.05
  const gradientRange = gradientMaxVal - gradientMinVal

  gradientMin.value = gradientMinVal
  gradientMax.value = gradientMaxVal
  totalPixels.value = points.length

  const VectorLayer = (await import('ol/layer/Vector')).default
  const VectorSource = (await import('ol/source/Vector')).default
  const Feature = (await import('ol/Feature')).default
  const Style = (await import('ol/style/Style')).default
  const FillStyle = (await import('ol/style/Fill')).default
  const StrokeStyle = (await import('ol/style/Stroke')).default
  const Polygon = (await import('ol/geom/Polygon')).default

  const pixelSizeDegrees = 0.00026
  const source = new VectorSource()
  const features: any[] = []

  points.forEach(p => {
    let normalized = (p.temp - gradientMinVal) / gradientRange
    normalized = Math.max(0, Math.min(1, normalized))
    const color = getGradientColor(normalized)

    const half = pixelSizeDegrees / 2
    const [x1, y1] = fromLonLat([p.lon - half, p.lat - half]) as [number, number]
    const [x2, y2] = fromLonLat([p.lon + half, p.lat + half]) as [number, number]

    const square = new Polygon([[
      [x1, y1],
      [x1, y2],
      [x2, y2],
      [x2, y1],
      [x1, y1]
    ]])

    const feature = new Feature({
      geometry: square,
      temperature: p.temp
    })

    feature.setStyle(new Style({
      fill: new FillStyle({color}),
      stroke: new StrokeStyle({
        color: 'rgba(255,255,255,0.2)',
        width: 0.5
      })
    }))

    features.push(feature)
  })

  source.addFeatures(features)

  pixelLayer = new VectorLayer({
    source: source,
    zIndex: 5,
    opacity: pixelOpacity.value,
  })

  map.addLayer(pixelLayer)
}

// ===== FUNÇÃO DE BUSCA =====
async function searchPlace(selectedParkData: ParkSuggestion | null | undefined) {
  console.log("searchPlace")
  if (!search.value || loading.value || isSearching.value) return
  // results.value = []

  loading.value = true
  isSearching.value = true
  showStats.value = false
  coolingData.value = null
  parkName.value = ""
  gradientMin.value = null
  gradientMax.value = null
  totalPixels.value = 0

  if (pixelLayer) {
    map.removeLayer(pixelLayer)
    pixelLayer = null
  }

  try {
    const data = await searchPark({
      query: search.value,
      city: selectedParkData?.city || '',
      country: selectedParkData?.country || 'Brazil',
      osm_id: selectedParkData?.osm_id || undefined
    })

    const elements = data.results || []
    // results.value = elements

    if (elements.length === 0) {
      handleInfo('Nenhum parque encontrado')
      return
    }

    // Seleciona o primeiro resultado automaticamente
    const element = elements[0]
    if (element && element.geometry) {
      await selectPark(element)
    }

  } catch (error) {
    console.error("❌ Erro ao buscar parque:", error)
    handleError(error, 'Erro ao buscar parque')
    results.value = []
  } finally {
    loading.value = false
    isSearching.value = false
  }
}


// ===== FUNÇÃO PARA ATUALIZAR OPACIDADE =====
function updatePixelOpacity(value: number) {
  pixelOpacity.value = value / 100
  if (pixelLayer) {
    pixelLayer.setOpacity(pixelOpacity.value)
  }
}

// ===== FUNÇÃO TOGGLE PIXELS =====
async function togglePixels() {
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

  map.on('pointermove', (evt: any) => {
    const overlay = tooltipOverlay.value
    const el = tooltipElement.value
    if (!overlay || !el) return

    const coordinate = evt.coordinate
    const lonLat = proj.toLonLat(coordinate)

    if (!lonLat || !Array.isArray(lonLat) || lonLat.length < 2) {
      el.style.opacity = '0'
      overlay.setPosition(undefined)
      return
    }

    const lon = lonLat[0] as number
    const lat = lonLat[1] as number

    let closestTemp = null
    let closestDist = Infinity

    if (coolingData.value?.buffers) {
      for (const buffer of coolingData.value.buffers) {
        for (const pixelData of (buffer.pixels || [])) {
          if (pixelData.lat != null && pixelData.lon != null && pixelData.temperature != null) {
            const dx = pixelData.lon - lon
            const dy = pixelData.lat - lat
            const dist = Math.sqrt(dx * dx + dy * dy)

            if (dist < 0.0003 && dist < closestDist) {
              closestDist = dist
              closestTemp = pixelData.temperature
            }
          }
        }
      }
    }

    if (closestTemp !== null) {
      el.innerHTML = `🌡️ ${closestTemp.toFixed(2)}°C`
      el.style.opacity = '1'
      el.style.transform = 'translate(-50%, -100%)'
      overlay.setPosition(coordinate)
    } else {
      el.style.opacity = '0'
      overlay.setPosition(undefined)
    }
  })

  map.getTargetElement().addEventListener('mouseleave', () => {
    if (tooltipElement.value) {
      tooltipElement.value.style.opacity = '0'
    }
    if (tooltipOverlay.value) {
      tooltipOverlay.value.setPosition(undefined)
    }
  })

  setupTooltip()
})

// ===== LIMPA MAPA =====
onUnmounted(() => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  if (pixelLayer) {
    map?.removeLayer(pixelLayer)
  }
  if (tooltipOverlay.value) {
    map?.removeOverlay(tooltipOverlay.value)
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
          :analyzing="analyzing"
          :coolingData="coolingData"
          :gradientMax="gradientMax"
          :gradientMin="gradientMin"
          :loading="loading"
          :parkName="parkName"
          :pixelOpacity="pixelOpacity"
          :predefinedParks="predefinedParks"
          :results="results"
          :showStats="showStats"
          :totalPixels="totalPixels"
          @search="searchPlace"
          @select="selectPark"
          @togglePixels="togglePixels"
          @updateCoolingData="updateCoolingData"
          @updateOpacity="updatePixelOpacity"
      />

      <TimelineOverlay
          v-if="parkAnalyses.length > 0"
          :analyses="parkAnalyses"
          :selectedAnalysis="coolingData"
          @select="handleAnalysisSelect"
      />
    </div>
  </div>
</template>

<style scoped>

/* 🔥 TODOS OS COMPONENTES FLUTUANTES USAM A MESMA CLASSE */
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