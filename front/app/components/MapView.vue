<script lang="ts" setup>
import {onMounted, onUnmounted, ref} from "vue"
import {searchPark, type SearchParkParams} from "~/services/parkService"
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
import type {CoolingAnalysisResult, ParkGeometry, SearchParkResult} from '~/types'
import {Overlay} from "ol";
import {Polygon} from "ol/geom";
import type {ParkSuggestion} from "~/types/parkSearch";
import {toLonLat} from "ol/proj";

// ===== REFS =====
const loading = ref(false)
const mapEl = ref<HTMLDivElement | null>(null)
const search = ref("")
const results = ref<SearchParkResult[]>([])
const coolingData = ref<CoolingAnalysisResult | null>(null)
const parkAnalyses = ref<CoolingAnalysisResult[]>([])
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
const searchBarRef = ref<InstanceType<typeof ParkSearchBar> | null>(null)
const manualPoints = ref<Array<{ lat: number; lon: number }>>([])
const {handleError, handleSuccess, handleInfo} = useNotifications()

// ===== VARIÁVEIS OPENLAYERS =====
let map: any
let vectorSource: any
let parkFeature: Feature<Geometry> | null = null
let pixelLayer: any = null
let fromLonLat: (coord: number[]) => number[]
const format = new GeoJSON()
const manualGeometry = ref<ParkGeometry | null>(null)
// ===== CONTROLE DO SATÉLITE =====
const showSatellite = ref(false)
const currentSatellite = ref<'arcgis' | 'google'>('arcgis')

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

// ===== FUNÇÃO TOGGLE SATÉLITE =====
function toggleSatellite() {
  const layers = map.getLayers().getArray()
  let googleLayer = null
  let arcgisLayer = null

  for (const layer of layers) {
    if (layer.get('satelliteType') === 'google') googleLayer = layer
    if (layer.get('satelliteType') === 'arcgis') arcgisLayer = layer
  }

  // 🔥 ESTADOS ATUAIS
  const googleVisible = googleLayer?.getVisible()
  const arcgisVisible = arcgisLayer?.getVisible()

  // 🔥 CICLO: desativado → ArcGIS → Google → desativado → ...
  if (!googleVisible && !arcgisVisible) {
    // 🔥 NENHUM ATIVO → ATIVA ARCGIS
    arcgisLayer?.setVisible(true)
    googleLayer?.setVisible(false)
    showSatellite.value = true
    currentSatellite.value = 'arcgis'
  } else if (arcgisVisible) {
    // 🔥 ARCGIS ATIVO → TROCA PARA GOOGLE
    arcgisLayer?.setVisible(false)
    googleLayer?.setVisible(true)
    showSatellite.value = true
    currentSatellite.value = 'google'
  } else if (googleVisible) {
    // 🔥 GOOGLE ATIVO → DESATIVA TUDO
    googleLayer?.setVisible(false)
    arcgisLayer?.setVisible(false)
    showSatellite.value = false
  }

  // 🔥 ATUALIZA O BOTÃO
  const btn = document.getElementById('satellite-toggle-btn')
  if (btn) {
    if (!showSatellite.value) {
      btn.textContent = '🛰️'
      btn.title = 'Mapa base (sem satélite)'
      // 🔥 TOOLTIP COM ESTILO
      btn.setAttribute('data-tooltip', 'Mapa base')
    } else if (currentSatellite.value === 'arcgis') {
      btn.textContent = '🌍'
      btn.title = 'ArcGIS Satélite (clique para trocar para Google)'
      btn.setAttribute('data-tooltip', 'ArcGIS Satélite')
    } else {
      btn.textContent = '🗺️'
      btn.title = 'Google Satélite (clique para desativar)'
      btn.setAttribute('data-tooltip', 'Google Satélite')
    }
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
        const numBuffers = data.num_buffers || 11
        const bufferDistance = data.buffer_distance || 30
        drawBuffers(feature, vectorSource, numBuffers, bufferDistance)
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
  if (!search.value || loading.value || isSearching.value) return

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

    const payload: SearchParkParams = {
      query: search.value,
      country: selectedParkData?.country || 'Brazil'
    }

    if (selectedParkData?.city) {
      payload.city = selectedParkData.city
    }
    if (selectedParkData?.osm_id) {
      payload.osm_id = selectedParkData.osm_id
    }
    if (manualGeometry.value) {
      payload.geometry = manualGeometry.value
    }

    const data = await searchPark(payload)

    const elements = data.results || []

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

  // 🔥 CAMADA SATÉLITE 1 (Google)
  const satelliteLayer1 = new TileLayer({
    source: new XYZ({
      url: "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
      crossOrigin: 'anonymous'
    })
  })
  satelliteLayer1.set('isSatellite', true)
  satelliteLayer1.set('satelliteType', 'google')
  satelliteLayer1.setVisible(false)

  // 🔥 CAMADA SATÉLITE 2 (ArcGIS)
  const satelliteLayer2 = new TileLayer({
    source: new XYZ({
      url: "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      crossOrigin: 'anonymous'
    })
  })
  satelliteLayer2.set('isSatellite', true)
  satelliteLayer2.set('satelliteType', 'arcgis')
  satelliteLayer2.setVisible(false)

  // 🔥 CRIA A CAMADA BASE (SEM SATÉLITE)
  const baseLayer = new TileLayer({
    source: new XYZ({
      url: "https://{a-c}.basemaps.cartocdn.com/rastertiles/light_all/{z}/{x}/{y}{r}.png?key=cb1_2gax_1_89470145eca0c0cfd945f121",
      crossOrigin: 'anonymous'
    })
  })
  baseLayer.set('isBaseLayer', true)

  map = new Map({
    target: mapEl.value!,
    layers: [
      baseLayer,
      satelliteLayer1,
      satelliteLayer2,
      new VectorLayer({
        source: vectorSource
      })
    ],
    view: new View({
      center: fromLonLat([-49.2648, -16.6869]),
      zoom: 12
    })
  })

  map.on('click', (evt: any) => {
    if (!isDrawingMode.value) return

    const coords = evt.coordinate
    const lonLat = toLonLat(coords)

    const lat = lonLat[1]
    const lon = lonLat[0]

    if (lat !== undefined && lon !== undefined) {
      // 🔥 SE TIVER REFERÊNCIA DO FILHO, ADICIONA TAMBÉM
      if (searchBarRef.value) {
        searchBarRef.value.addPoint(lat, lon)
      }
    }
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
    let emoji_qa_pixel = null
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
              emoji_qa_pixel = pixelData.qa_pixel?.emojis || null
            }
          }
        }
      }
    }

    if (closestTemp !== null) {
      el.innerHTML = `🌡️ ${closestTemp.toFixed(2)}°C ${emoji_qa_pixel}`
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

  const btn = document.getElementById('satellite-toggle-btn')
  if (btn) {
    btn.setAttribute('data-tooltip', 'Ativar satélite')
  }
})

// 🔥 MODO DE DESENHO
const isDrawingMode = ref(false)

function startDrawing() {
  isDrawingMode.value = true
  map.getTargetElement().style.cursor = 'crosshair'
}

function stopDrawing() {
  isDrawingMode.value = false
  map.getTargetElement().style.cursor = 'default'
}

// 🔥 ADICIONAR UMA CAMADA PARA OS PONTOS TEMPORÁRIOS
let tempPointsLayer: any = null
let tempPolygonLayer: any = null

// 🔥 FUNÇÃO PARA DESENHAR PONTOS TEMPORÁRIOS NO MAPA
async function updateTempPoints(points: Array<{ lat: number; lon: number }>) {

  // 🔥 REMOVE CAMADAS ANTERIORES (FORÇADO)
  if (tempPointsLayer) {
    map.removeLayer(tempPointsLayer)
    tempPointsLayer = null
  }
  if (tempPolygonLayer) {
    map.removeLayer(tempPolygonLayer)
    tempPolygonLayer = null
  }

  if (points.length === 0) {
    return
  }

  // 🔥 CRIA NOVOS SOURCES
  const VectorSource = (await import('ol/source/Vector')).default
  const Feature = (await import('ol/Feature')).default
  const Point = (await import('ol/geom/Point')).default
  const Style = (await import('ol/style/Style')).default
  const CircleStyle = (await import('ol/style/Circle')).default
  const FillStyle = (await import('ol/style/Fill')).default
  const StrokeStyle = (await import('ol/style/Stroke')).default
  const TextStyle = (await import('ol/style/Text')).default
  const VectorLayer = (await import('ol/layer/Vector')).default
  const Polygon = (await import('ol/geom/Polygon')).default

  // 🔥 DESENHA PONTOS
  const pointSource = new VectorSource()
  const features: any[] = []

  points.forEach((p, index) => {
    const coords = fromLonLat([p.lon, p.lat])

    const feature = new Feature({
      geometry: new Point(coords)
    })

    feature.setStyle(new Style({
      image: new CircleStyle({
        radius: 14,
        fill: new FillStyle({
          color: "#3b82f6"
        }),
        stroke: new StrokeStyle({
          color: '#ffffff',
          width: 3
        })
      }),
      text: new TextStyle({
        text: String(index + 1),
        font: 'bold 11px "Titillium Web", Arial, sans-serif',
        fill: new FillStyle({color: '#ffffff'}),
        stroke: new StrokeStyle({
          color: 'rgba(0,0,0,0.3)',
          width: 2
        }),
        textAlign: 'center',
        textBaseline: 'middle'
      })
    }))
    features.push(feature)
  })

  pointSource.addFeatures(features)

  tempPointsLayer = new VectorLayer({
    source: pointSource,
    zIndex: 10
  })
  map.addLayer(tempPointsLayer)


  // 🔥 SE TIVER MAIS DE 2 PONTOS, DESENHA O POLÍGONO
  if (points.length >= 3) {
    // 🔥 VERIFICAÇÃO DE SEGURANÇA
    const firstPoint = points[0]
    if (!firstPoint) {
      return
    }

    const coords3857 = points.map(p => fromLonLat([p.lon, p.lat]))

    // 🔥 VERIFICA SE O PRIMEIRO EXISTE
    const firstCoord = coords3857[0]
    if (!firstCoord) {
      return
    }

    coords3857.push(firstCoord) // Fecha o polígono

    const polygonFeature = new Feature({
      geometry: new Polygon([coords3857])
    })

    polygonFeature.setStyle(new Style({
      stroke: new StrokeStyle({
        color: '#3b82f6',
        width: 2.5,
        lineDash: [8, 6],
        lineDashOffset: 4
      }),
      fill: new FillStyle({
        color: 'rgba(59, 130, 246, 0.1)'
      })
    }))

    const polygonSource = new VectorSource()
    polygonSource.addFeature(polygonFeature)

    tempPolygonLayer = new VectorLayer({
      source: polygonSource,
      zIndex: 9
    })

    polygonFeature.setStyle(new Style({
      stroke: new StrokeStyle({
        color: '#3b82f6',
        width: 2.5,
        lineDash: [8, 6],
        lineDashOffset: 4
      }),
      fill: new FillStyle({
        color: 'rgba(59, 130, 246, 0.1)'
      })
    }))

    map.addLayer(tempPolygonLayer)
  }
}

function createManualGeometry(points: Array<{ lat: number; lon: number }>): ParkGeometry | null {
  if (points.length < 3) return null

  const coords = points.map(p => [p.lon, p.lat])

  const firstPoint = coords[0]
  if (!firstPoint) return null

  coords.push(firstPoint)
  return {
    type: 'Polygon',
    coordinates: [coords] as number[][][]
  }
}

function handlePointsUpdated(points: Array<{ lat: number; lon: number }>) {
  manualPoints.value = points
  updateTempPoints(points)

  if (points.length >= 3) {
    const geometry = createManualGeometry(points)
    if (geometry) {
      manualGeometry.value = geometry
    }
  } else {
    manualGeometry.value = null
  }
}

function handleParkDeleted(parkId: number) {
  // 🔥 LIMPA OS DADOS DO PARQUE SELECIONADO
  coolingData.value = null
  showStats.value = false
  parkName.value = ''

  if (vectorSource) {
    vectorSource.clear()
  }
  if (pixelLayer) {
    map.removeLayer(pixelLayer)
    pixelLayer = null
  }
  handleSuccess(`Parque deletado com sucesso!`)
}

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
      <!-- 🔥 BOTÃO TOGGLE SATÉLITE (AO LADO DO ZOOM) -->
      <button
          id="satellite-toggle-btn"
          :data-tooltip="showSatellite ? (currentSatellite === 'arcgis' ? 'Satélite (Google)' : 'Mapa') : 'Satélite (ArcGIS)'"
          :title="showSatellite ? (currentSatellite === 'arcgis' ? 'ArcGIS Satélite' : 'Google Satélite') : 'Mapa'"
          class="satellite-toggle-btn"
          @click="toggleSatellite"
      >
        🛰️
      </button>
      <ParkSearchBar
          ref="searchBarRef"
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
          @parkDeleted="handleParkDeleted"
          @pointsUpdated="handlePointsUpdated"
          @search="searchPlace"
          @select="selectPark"
          @startDrawing="startDrawing"
          @stopDrawing="stopDrawing"
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

/* 🔥 BOTÃO TOGGLE SATÉLITE */
:global(.satellite-toggle-btn) {
  position: absolute !important;
  bottom: 25px !important;
  right: 125px !important;
  z-index: 9999 !important;

  width: 55px !important;
  height: 55px !important;
  border-radius: 8px !important;
  background-color: #ffffff !important;
  color: #333 !important;
  border: 1px solid rgba(0, 0, 0, 0.1) !important;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15) !important;
  font-size: 36px !important;
  cursor: pointer !important;
  transition: all 0.2s ease !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

:global(.satellite-toggle-btn:hover) {
  background-color: #f0f0f0 !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
  transform: scale(1.05);
}

:global(.satellite-toggle-btn:active) {
  transform: scale(0.95);
}

/*  SATÉLITE TOOLTIP*/
.satellite-toggle-btn::after {
  content: attr(data-tooltip);
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.85);
  color: white;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  font-family: 'Titillium Web', sans-serif;
  white-space: nowrap;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.2s ease;
  backdrop-filter: blur(4px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  z-index: 10000;
}

.satellite-toggle-btn:hover::after {
  opacity: 1;
}

.satellite-toggle-btn::before {
  content: '';
  position: absolute;
  bottom: calc(100% + 2px);
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: rgba(0, 0, 0, 0.85);
  opacity: 0;
  transition: opacity 0.2s ease;
  z-index: 10000;
}

.satellite-toggle-btn:hover::before {
  opacity: 1;
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