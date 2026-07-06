// nuxt.config.ts
import { defineNuxtConfig } from 'nuxt/config'
import Aura from '@primeuix/themes/aura'

export default defineNuxtConfig({
    modules: [
        '@primevue/nuxt-module'
    ],
    primevue: {
        options: {
            theme: {
                preset: Aura,
                options: {
                    prefix: 'p',
                    darkModeSelector: 'none',
                    cssLayer: false
                }
            }
        }
    },
    css: [
        'primeicons/primeicons.css'
    ],
    runtimeConfig: {
        public: {
            apiUrl: process.env.NODE_ENV === 'production'
                ? 'http://200.137.197.69:55235'
                : 'http://localhost:3001'
        }
    }
})