<script setup>
import { ref, onMounted } from "vue"

const mapEl = ref(null)
const search = ref("")
let map
let vectorSource

// 🔎 buscar no OSM (Nominatim)
async function searchPlace() {
  if (!search.value) return

  const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(search.value)}`

  const res = await fetch(url)
  const data = await res.json()

  if (!data.length) return

  const place = data[0]

  const lon = parseFloat(place.lon)
  const lat = parseFloat(place.lat)

  // move mapa
  const view = map.getView()
  view.setCenter([lon, lat].map(fromLonLat))
  view.setZoom(16)
}

onMounted(async () => {
  const { Map, View } = await import("ol")
  const TileLayer = (await import("ol/layer/Tile")).default
  const VectorLayer = (await import("ol/layer/Vector")).default
  const VectorSource = (await import("ol/source/Vector")).default
  const OSM = (await import("ol/source/OSM")).default
  const { fromLonLat } = await import("ol/proj")

  vectorSource = new VectorSource()

  map = new Map({
    target: mapEl.value,
    layers: [
      new TileLayer({
        source: new OSM()
      }),
      new VectorLayer({
        source: vectorSource
      })
    ],
    view: new View({
      center: fromLonLat([-49.2648, -16.6869]), // Goiânia
      zoom: 12
    })
  })
})
</script>

<template><div class="page">
  <div class="map-wrapper">
    <div class="map" ref="mapEl"></div>

      <div class="search-bar">
        <input v-model="search" placeholder="Pesquisar lugar..." />
        <button @click="searchPlace">Buscar</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.map-wrapper {
  width: 100%;
  height: 600px;
  position: relative;
}

.map {
  width: 100%;
  height: 100vh;
}

.page {
  position: relative;
  height: 100vh;
}


.search-bar {
  position: absolute;
  top: 12px;
  left: 100px;

  display: flex;
  gap: 8px;

  background: white;
  padding: 10px;
  border-radius: 8px;

  z-index: 1000; /* fica por cima do mapa */
  box-shadow: 0 2px 10px rgba(0,0,0,0.2);
}

.search-bar input {
  padding: 6px;
  width: 250px;
}
</style>