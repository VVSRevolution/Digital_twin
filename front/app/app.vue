<template>
  <div>
    <NuxtPage/>
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

.p-tooltip .p-tooltip-text {
  align-content: center !important;
  justify-content: center !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  font-family: 'Titillium Web', sans-serif !important;
  background: rgba(0, 0, 0, 0.85) !important;
  color: white !important;
  padding: 4px 10px !important;
  border-radius: 6px !important;
  backdrop-filter: blur(4px) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  line-height: 1.4 !important;
  letter-spacing: 0.3px !important;
  max-width: 300px !important;
  text-align: center !important;
}

.p-tooltip .p-tooltip-arrow {
  border-top-color: rgba(0, 0, 0, 0.85) !important;
}
</style>
