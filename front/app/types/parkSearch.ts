//types/parkSearch.ts
/**
 * Tipos e Interfaces para o sistema de busca de parques
 */
import type {ParkGeometry} from "~/types/index";

export interface ParkSuggestion {
    id: number
    osm_id?: number
    osm_type?: string
    name: string
    city: string
    country: string
    lat: number
    lon: number
    display_name: string
    geometry?: ParkGeometry
}

export interface CountrySuggestion {
    id: string
    name: string
    code: string
}

export interface CitySuggestion {
    id: number
    name: string
    state: string
    country: string
    lat: number
    lon: number
}

export interface AddParkData {
    name: string
    city: string
    country: string
    startDate: string | null
    endDate: string | null
    geometry?: ParkGeometry
    isUpToDate?: boolean
    satellites?: string[]
    numBuffers?: number
    bufferDistance?: number
}