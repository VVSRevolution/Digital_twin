<!-- app/pages/debug/index.vue -->
<template>
  <div class="debug-page">
    <div class="container">
      <h1>🔧 Debug API</h1>

      <!-- Status -->
      <div class="card">
        <h2>📡 Status da Conexão</h2>
        <div class="status-row">
          <span class="label">URL Atual:</span>
          <code class="url">{{ apiUrl }}</code>
          <span v-if="isCustom" class="badge custom">Personalizada</span>
          <span v-else class="badge default">Padrão</span>
        </div>
        <div class="status-row">
          <span class="label">Ambiente:</span>
          <span>{{ isProduction ? '🚀 Produção' : '💻 Desenvolvimento' }}</span>
        </div>
        <div class="status-row">
          <span class="label">Status:</span>
          <span v-if="connectionStatus.success" class="success">✅ Online</span>
          <span v-else class="error">❌ Offline - {{ connectionStatus.error }}</span>
        </div>
        <button class="btn-test" @click="testConnection">🔄 Testar Conexão</button>
      </div>

      <!-- Alterar URL -->
      <div class="card">
        <h2>✏️ Alterar URL da API</h2>
        <div class="url-editor">
          <input
              v-model="newUrlInput"
              class="url-input"
              placeholder="http://localhost:3001"
              @keydown.enter="applyNewUrl"
          />
          <button class="btn-primary" @click="applyNewUrl">✅ Aplicar</button>
          <button class="btn-secondary" @click="resetToDefault">↩️ Resetar</button>
        </div>
        <div class="quick-urls">
          <span class="label">Rápidos:</span>
          <button
              v-for="url in quickUrls"
              :key="url"
              class="btn-quick"
              @click="setQuickUrl(url)"
          >
            {{ url }}
          </button>
        </div>
        <div v-if="urlError" class="error-message">⚠️ {{ urlError }}</div>
      </div>

      <!-- Testes -->
      <div class="card">
        <h2>🧪 Testes Rápidos</h2>
        <div class="test-buttons">
          <button class="btn-test" @click="testEndpoint('/api/parks')">
            📋 /api/parks
          </button>
          <button class="btn-test" @click="testAnalysis">
            🌡️ Análise
          </button>
        </div>
        <div v-if="testResult" class="test-result">
          <h4>Resultado:</h4>
          <pre>{{ JSON.stringify(testResult, null, 2) }}</pre>
        </div>
      </div>

      <!-- Logs -->
      <div class="card">
        <h2>📋 Logs</h2>
        <button class="btn-clear" @click="clearLogs">🗑️ Limpar</button>
        <div class="logs-container">
          <div
              v-for="(log, index) in logs"
              :key="index"
              class="log-entry"
              :class="log.type"
          >
            <span class="log-time">{{ log.time }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
          <div v-if="logs.length === 0" class="empty-logs">
            Nenhum log ainda
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useApiConfig } from '~/composables/useApiConfig'

const {
  apiUrl,
  isCustom,
  isProduction,
  setApiUrl,
  resetApiUrl,
  getApiUrl,
  testApiConnection
} = useApiConfig()

// Estado
const newUrlInput = ref('')
const urlError = ref('')
const connectionStatus = ref<{ success: boolean; error?: string; status?: number }>({
  success: false
})
const testResult = ref<any>(null)
const logs = ref<Array<{ time: string; message: string; type: string }>>([])

// URLs rápidas
const quickUrls = [
  'http://localhost:3001',
  'http://200.137.197.69:55235',
  'http://192.168.30.233:6789',
]

// Aplicar nova URL
async function applyNewUrl() {
  urlError.value = ''
  if (!newUrlInput.value || newUrlInput.value.trim() === '') {
    urlError.value = 'Digite uma URL válida'
    return
  }

  try {
    const url = newUrlInput.value.trim().replace(/\/$/, '')
    await setApiUrl(url)
    addLog(`URL alterada para: ${url}`, 'info')
    await testConnection()
  } catch (error: any) {
    urlError.value = error.message
    addLog(`Erro: ${error.message}`, 'error')
  }
}

// Resetar URL
function resetToDefault() {
  resetApiUrl()
  newUrlInput.value = getApiUrl()
  addLog('URL resetada para padrão', 'info')
  testConnection()
}

// URL rápida
function setQuickUrl(url: string) {
  newUrlInput.value = url
  applyNewUrl()
}

// Testar conexão
async function testConnection() {
  const result = await testApiConnection()
  connectionStatus.value = result
  if (result.success) {
    addLog(`Conexão OK: ${result.status} ${result.statusText}`, 'success')
  } else {
    addLog(`Conexão falhou: ${result.error}`, 'error')
  }
}

// Testar endpoint
async function testEndpoint(endpoint: string) {
  testResult.value = null
  try {
    const url = getApiUrl()
    const response = await fetch(`${url}${endpoint}`)
    const data = await response.json()
    testResult.value = {
      success: response.ok,
      status: response.status,
      statusText: response.statusText,
      data: data,
    }
    addLog(`Teste ${endpoint}: ${response.status}`, response.ok ? 'success' : 'error')
  } catch (error: any) {
    testResult.value = { success: false, error: error.message }
    addLog(`Erro em ${endpoint}: ${error.message}`, 'error')
  }
}

// Testar análise
async function testAnalysis() {
  await testEndpoint('/api/park/analyze?debug=true')
}

// Adicionar log
function addLog(message: string, type: 'info' | 'success' | 'error' = 'info') {
  const time = new Date().toLocaleTimeString()
  logs.value.unshift({ time, message, type })
  if (logs.value.length > 100) {
    logs.value.pop()
  }
}

// Limpar logs
function clearLogs() {
  logs.value = []
}

// Inicializar
onMounted(() => {
  newUrlInput.value = apiUrl.value
  testConnection()
})
</script>

<style scoped>
.debug-page {
  padding: 20px;
  max-width: 900px;
  margin: 0 auto;
  font-family: 'Titillium Web', sans-serif;
}

.container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

h1 {
  font-size: 28px;
  margin-bottom: 0;
  color: #1a1a1a;
}

h2 {
  font-size: 18px;
  margin-top: 0;
  margin-bottom: 16px;
  color: #333;
}

/* Cards */
.card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid #e5e7eb;
}

/* Status */
.status-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #f3f4f6;
}

.status-row:last-child {
  border-bottom: none;
}

.label {
  font-weight: 600;
  color: #6b7280;
  min-width: 120px;
  font-size: 14px;
}

.url {
  font-family: 'Courier New', monospace;
  background: #f3f4f6;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 14px;
  color: #1f2937;
  flex: 1;
}

.badge {
  padding: 2px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.badge.custom {
  background: #dbeafe;
  color: #1d4ed8;
}

.badge.default {
  background: #f3f4f6;
  color: #6b7280;
}

.success {
  color: #16a34a;
  font-weight: 600;
}

.error {
  color: #dc2626;
  font-weight: 600;
}

/* URL Editor */
.url-editor {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.url-input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  font-family: 'Courier New', monospace;
}

.url-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.quick-urls {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.quick-urls .label {
  min-width: auto;
  font-size: 13px;
}

/* Buttons */
.btn-primary,
.btn-secondary,
.btn-test,
.btn-clear {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background: #2563eb;
  transform: translateY(-1px);
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
}

.btn-secondary:hover {
  background: #e5e7eb;
}

.btn-test {
  background: #f0fdf4;
  color: #16a34a;
  border: 1px solid #86efac;
}

.btn-test:hover {
  background: #dcfce7;
}

.btn-clear {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fca5a5;
  padding: 6px 14px;
  font-size: 12px;
  float: right;
  margin-top: -40px;
}

.btn-quick {
  padding: 4px 12px;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  font-family: 'Courier New', monospace;
}

.btn-quick:hover {
  background: #e5e7eb;
}

.error-message {
  margin-top: 8px;
  color: #dc2626;
  font-size: 14px;
}

/* Test Result */
.test-result {
  margin-top: 12px;
  background: #f9fafb;
  border-radius: 8px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  max-height: 300px;
  overflow: auto;
}

.test-result h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #4b5563;
}

.test-result pre {
  margin: 0;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
  color: #1f2937;
}

/* Logs */
.logs-container {
  max-height: 300px;
  overflow-y: auto;
  background: #fafafa;
  border-radius: 8px;
  padding: 8px;
  border: 1px solid #e5e7eb;
}

.log-entry {
  display: flex;
  gap: 12px;
  padding: 6px 10px;
  border-bottom: 1px solid #f3f4f6;
  font-size: 13px;
}

.log-entry:last-child {
  border-bottom: none;
}

.log-time {
  color: #9ca3af;
  font-family: 'Courier New', monospace;
  min-width: 80px;
  font-size: 12px;
}

.log-message {
  color: #1f2937;
}

.log-entry.info .log-message {
  color: #2563eb;
}

.log-entry.success .log-message {
  color: #16a34a;
}

.log-entry.error .log-message {
  color: #dc2626;
}

.empty-logs {
  color: #9ca3af;
  text-align: center;
  padding: 20px;
}

/* Test buttons */
.test-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* Responsive */
@media (max-width: 600px) {
  .debug-page {
    padding: 12px;
  }

  .url-editor {
    flex-direction: column;
  }

  .status-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>