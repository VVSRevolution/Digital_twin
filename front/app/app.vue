<script setup lang="ts">
import MapView from "~/components/MapView.vue";
import NotificationCenter from "~/components/NotificationCenter.vue";
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
@import url('https://fonts.googleapis.com/css2?family=Titillium+Web:wght@400;600;700&display=swap');
 * {
   font-family: 'Titillium Web', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
  body {
    display: block;
    margin: 0;
  }

</style>
