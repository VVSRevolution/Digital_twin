// app/composables/useApiConfig.ts
import {readonly, ref} from 'vue'
import {useCookie} from '#app'

export const useApiConfig = () => {
    // 🔥 Estado reativo
    const apiUrl = ref<string>('')
    const isCustom = ref(false)
    const isProduction = ref(false)

    // 🔥 Cookie para persistir URL personalizada (30 dias)
    const customApiCookie = useCookie<string>('custom_api_url', {
        default: () => '',
        maxAge: 60 * 60 * 24 * 30,
        secure: process.env.NODE_ENV === 'production',
    })

    // 🔥 Carregar configuração
    function loadConfig() {
        const config = useRuntimeConfig()
        const defaultUrl = config.public.apiUrl || 'http://localhost:3001'

        if (customApiCookie.value && customApiCookie.value.trim() !== '') {
            apiUrl.value = customApiCookie.value
            isCustom.value = true
        } else {
            apiUrl.value = defaultUrl
            isCustom.value = false
        }

        isProduction.value = process.env.NODE_ENV === 'production'
        console.log(`🔧 API URL: ${apiUrl.value} (${isCustom.value ? 'personalizada' : 'padrão'})`)
    }

    // 🔥 Definir nova URL
    function setApiUrl(url: string) {
        if (!url || url.trim() === '') {
            const config = useRuntimeConfig()
            apiUrl.value = config.public.apiUrl || 'http://localhost:3001'
            isCustom.value = false
            customApiCookie.value = ''
            return
        }

        const cleanUrl = url.trim().replace(/\/$/, '')

        try {
            new URL(cleanUrl) // Valida se é URL válida
            apiUrl.value = cleanUrl
            isCustom.value = true
            customApiCookie.value = cleanUrl
        } catch (error) {
            throw new Error('URL inválida! Use o formato: http://localhost:3001')
        }
    }

    // 🔥 Resetar para URL padrão
    function resetApiUrl() {
        const config = useRuntimeConfig()
        apiUrl.value = config.public.apiUrl || 'http://localhost:3001'
        isCustom.value = false
        customApiCookie.value = ''
    }

    // 🔥 Obter URL atual
    function getApiUrl(): string {
        if (!apiUrl.value) {
            loadConfig()
        }
        return apiUrl.value
    }

    // 🔥 Testar conexão com a API
    async function testApiConnection(url?: string) {
        const testUrl = url || apiUrl.value
        try {
            const response = await fetch(`${testUrl}/api/parks`, {
                method: 'HEAD',
                signal: AbortSignal.timeout(5000),
            })
            return {
                success: response.ok,
                status: response.status,
                statusText: response.statusText,
                url: testUrl,
                time: new Date().toISOString()
            }
        } catch (error: any) {
            return {
                success: false,
                error: error.message || 'Erro de conexão',
                url: testUrl,
            }
        }
    }

    // Inicializar
    if (import.meta.client) {
        loadConfig()
    }

    return {
        apiUrl: readonly(apiUrl),
        isCustom: readonly(isCustom),
        isProduction: readonly(isProduction),
        loadConfig,
        setApiUrl,
        resetApiUrl,
        getApiUrl,
        testApiConnection,
    }
}