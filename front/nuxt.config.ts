export default defineNuxtConfig({
    runtimeConfig: {
        public: {
            apiUrl: process.env.NODE_ENV === 'production'
                ? 'http://200.137.197.69:55235'
                : 'http://localhost:3001'
        }
    }
})