/**
 * Tipos e Interfaces para o sistema de busca de parques
 */

export interface SearchResult {
  id: number
  lat: number
  lon: number
  tags?: { name?: string; [key: string]: unknown }
}

export interface ParkSuggestion {
  id: number
  name: string
  city: string
  country: string
  lat: number
  lon: number
  display_name: string
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
  city: string
  country: string
  name: string
  startDate: string
  endDate: string
}
