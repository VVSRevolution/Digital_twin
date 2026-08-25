// app/composables/useApiConfig.ts
import {computed, readonly, ref} from 'vue'

// 🔥 CHAVE PARA LOCALSTORAGE
const STORAGE_KEY = 'api_custom_url'

// 🔥 Estado GLOBAL (persiste entre páginas)
const customUrl = ref<string | null>(null)

// 🔥 Carregar do localStorage apenas no cliente
if (typeof window !== 'undefined') {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
        customUrl.value = saved
    }
}

export const useApiConfig = () => {
    const config = useRuntimeConfig()
    const defaultUrl = config.public.apiUrl || 'http://localhost:3001'

    // URL atual
    const apiUrl = computed(() => {
        return customUrl.value || defaultUrl
    })

    const isCustom = computed(() => {
        return customUrl.value !== null && customUrl.value !== defaultUrl
    })

    const isProduction = computed(() => {
        return process.env.NODE_ENV === 'production'
    })

    // 🔥 SALVAR no localStorage
    function setApiUrl(url: string) {
        if (!url || url.trim() === '') {
            customUrl.value = null
            if (typeof window !== 'undefined') {
                localStorage.removeItem(STORAGE_KEY)
            }
            return
        }

        const cleanUrl = url.trim().replace(/\/$/, '')

        try {
            new URL(cleanUrl) // Valida URL
            customUrl.value = cleanUrl
            if (typeof window !== 'undefined') {
                localStorage.setItem(STORAGE_KEY, cleanUrl)
            }
        } catch (error) {
            throw new Error('URL inválida! Use o formato: http://localhost:3001')
        }
    }

    function resetApiUrl() {
        customUrl.value = null
        if (typeof window !== 'undefined') {
            localStorage.removeItem(STORAGE_KEY)
        }
    }

    function getApiUrl(): string {
        return apiUrl.value
    }

    async function testApiConnection() {
        try {
            const url = getApiUrl()
            const response = await fetch(`${url}/health`, {
                signal: AbortSignal.timeout(5000)
            })
            return {
                success: response.ok,
                status: response.status,
                statusText: response.statusText,
                error: undefined
            }
        } catch (error: any) {
            return {
                success: false,
                error: error.message || 'Falha na conexão',
                status: undefined,
                statusText: undefined
            }
        }
    }

    return {
        apiUrl: readonly(apiUrl),
        isCustom: readonly(isCustom),
        isProduction: readonly(isProduction),
        setApiUrl,
        resetApiUrl,
        getApiUrl,
        testApiConnection
    }
}