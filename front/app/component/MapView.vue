<script setup>
import { onMounted, ref, nextTick } from "vue"

const mapEl = ref(null)

onMounted(async () => {
  const { Map, View } = await import("ol")
  const TileLayer = (await import("ol/layer/Tile")).default
  const OSM = (await import("ol/source/OSM")).default

  await nextTick()

  new Map({
    target: mapEl.value,
    layers: [
      new TileLayer({
        source: new OSM()
      })
    ],
    view: new View({
      center: [0, 0],
      zoom: 2
    })
  })
})
</script>

<template>
  <div class="map-wrapper">
    <div ref="mapEl" class="map"></div>
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
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
}
</style>