<script setup lang="ts">
import MapView from "~/component/MapView.vue";
import NotificationCenter from "~/component/NotificationCenter.vue";
</script>
<template>
  <div>
    <client-only>
      <NotificationCenter />
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
