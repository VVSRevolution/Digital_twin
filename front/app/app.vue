<script setup lang="ts">
import MapView from "~/component/MapView.vue";
</script>
<template>
  <div>
    <client-only>
      <MapView/>
    </client-only>
  </div>
</template>
<style>
  body {
    display: block;
    margin: 0;
  }
</style>
