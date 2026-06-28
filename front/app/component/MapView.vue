<script setup>
import {onMounted, ref} from "vue"
import {convertParkToFeature} from "@/services/geoService"
import {searchPark} from "@/services/parkService"
import Style from "ol/style/Style"
import {Fill, Stroke} from "ol/style.d.ts";
import {drawBuffers} from "~/utils/buffer"
import {XYZ} from "ol/source.d.ts";

const loading = ref(false)
const mapEl = ref(null)
const search = ref("")
const results = ref([])

let map
let vectorSource
let fromLonLat

async function searchPlace() {
  if (!search.value || loading.value) return

  loading.value = true

  try {
    const data = await searchPark(search.value)

    results.value = data.elements || []

    // opcional: desenhar o primeiro automaticamente
    if (data.elements?.length) {
      const feature = convertParkToFeature(data.elements[0])
      feature.setStyle(
          new Style({
            fill: new Fill({
              color: "rgb(22 152 7 / 0.35)"
            }),
            stroke: new Stroke({
              color: "#00aa00",
              width: 2,
              lineDash: [10, 10]
            })
          })
      )

      vectorSource.clear()
      vectorSource.addFeature(feature)

      drawBuffers(feature, vectorSource)


      //  ZOOM AUTOMÁTICO NO PARQUE
      const extent = feature.getGeometry().getExtent()
      map.getView().fit(extent, {
        padding: [50, 50, 50, 50],
        duration: 800
      })

      results.value = []
    }

  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  const {Map, View} = await import("ol")

  const TileLayer = (await import("ol/layer/Tile")).default
  const VectorLayer = (await import("ol/layer/Vector")).default
  const VectorSource = (await import("ol/source/Vector")).default

  const proj = await import("ol/proj")
  fromLonLat = proj.fromLonLat

  vectorSource = new VectorSource()

  map = new Map({
    target: mapEl.value,
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
</script>

<template>
  <div class="page">
    <div class="map-wrapper">

      <!-- MAPA -->
      <div ref="mapEl" class="map"></div>

      <!-- SEARCH -->
      <div class="search-bar">
        <div>
          <input v-model="search" placeholder="Pesquisar parque..." @keydown.enter="searchPlace"
          />

          <button
              :disabled="loading"
              @click="searchPlace"
          >
            {{ loading ? "Buscando..." : "Buscar" }}
          </button>
        </div>
        <!-- LISTA DE RESULTADOS -->
        <div v-if="results.length" class="dropdown">
          <div
              v-for="(item, index) in results"
              :key="index"
              class="item"
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

/* SEARCH */
.search-bar {
  position: absolute;
  top: 12px;
  left: 100px;

  display: flex;
  gap: 8px;
  flex-direction: column;

  background: white;
  padding: 10px;
  border-radius: 8px;

  z-index: 1000;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

/* DROPDOWN */
.dropdown {
  max-height: 250px;
  overflow: auto;
  background: white;
  border-radius: 6px;
}

.item {
  padding: 8px;
  cursor: pointer;
}

.item:hover {
  background: #eee;
}
</style>