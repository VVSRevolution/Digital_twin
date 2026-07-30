// ~/services/index.ts

// ============================================================
// 🔥 RE-EXPORTA TIPOS
// ============================================================

export type * from '@/types'

// ============================================================
// 🔥 RE-EXPORTA FUNÇÕES (VALORES)
// ============================================================

export * from './eeService'

export * from './satelliteService'


// ============================================================
// 🔥 RE-EXPORTA FUNÇÕES AUXILIARES DE TIPOS
// ============================================================

// 🔥 IMPORTANTE: Re-exporta as funções auxiliares como VALORES
export {parkToSearchResult, osmToSearchResult} from '@/types'