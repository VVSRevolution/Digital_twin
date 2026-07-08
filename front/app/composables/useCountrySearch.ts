import { ref } from 'vue'
import type { CountrySuggestion } from '@/types/parkSearch'

export const COUNTRY_LIST: CountrySuggestion[] = [
  // 🌍 ÁFRICA
  { id: 'AO', name: 'Angola', code: 'AO' },
  { id: 'DZ', name: 'Argélia', code: 'DZ' },
  { id: 'BJ', name: 'Benin', code: 'BJ' },
  { id: 'BW', name: 'Botsuana', code: 'BW' },
  { id: 'BF', name: 'Burquina Faso', code: 'BF' },
  { id: 'BI', name: 'Burundi', code: 'BI' },
  { id: 'CM', name: 'Camarões', code: 'CM' },
  { id: 'CV', name: 'Cabo Verde', code: 'CV' },
  { id: 'CF', name: 'República Centro-Africana', code: 'CF' },
  { id: 'TD', name: 'Chade', code: 'TD' },
  { id: 'KM', name: 'Comores', code: 'KM' },
  { id: 'CG', name: 'Congo', code: 'CG' },
  { id: 'CD', name: 'República Democrática do Congo', code: 'CD' },
  { id: 'DJ', name: 'Djibouti', code: 'DJ' },
  { id: 'EG', name: 'Egito', code: 'EG' },
  { id: 'ER', name: 'Eritreia', code: 'ER' },
  { id: 'SZ', name: 'Essuatíni', code: 'SZ' },
  { id: 'ET', name: 'Etiópia', code: 'ET' },
  { id: 'GA', name: 'Gabão', code: 'GA' },
  { id: 'GM', name: 'Gâmbia', code: 'GM' },
  { id: 'GH', name: 'Gana', code: 'GH' },
  { id: 'GN', name: 'Guiné', code: 'GN' },
  { id: 'GW', name: 'Guiné-Bissau', code: 'GW' },
  { id: 'GQ', name: 'Guiné Equatorial', code: 'GQ' },
  { id: 'KE', name: 'Quênia', code: 'KE' },
  { id: 'LS', name: 'Lesoto', code: 'LS' },
  { id: 'LR', name: 'Libéria', code: 'LR' },
  { id: 'LY', name: 'Líbia', code: 'LY' },
  { id: 'MG', name: 'Madagáscar', code: 'MG' },
  { id: 'MW', name: 'Malawi', code: 'MW' },
  { id: 'ML', name: 'Mali', code: 'ML' },
  { id: 'MA', name: 'Marrocos', code: 'MA' },
  { id: 'MU', name: 'Maurícia', code: 'MU' },
  { id: 'MR', name: 'Mauritânia', code: 'MR' },
  { id: 'MZ', name: 'Moçambique', code: 'MZ' },
  { id: 'NA', name: 'Namíbia', code: 'NA' },
  { id: 'NE', name: 'Níger', code: 'NE' },
  { id: 'NG', name: 'Nigéria', code: 'NG' },
  { id: 'RW', name: 'Ruanda', code: 'RW' },
  { id: 'ST', name: 'São Tomé e Príncipe', code: 'ST' },
  { id: 'SN', name: 'Senegal', code: 'SN' },
  { id: 'SC', name: 'Seicheles', code: 'SC' },
  { id: 'SL', name: 'Serra Leoa', code: 'SL' },
  { id: 'SO', name: 'Somália', code: 'SO' },
  { id: 'ZA', name: 'África do Sul', code: 'ZA' },
  { id: 'SS', name: 'Sudão do Sul', code: 'SS' },
  { id: 'SD', name: 'Sudão', code: 'SD' },
  { id: 'TZ', name: 'Tanzânia', code: 'TZ' },
  { id: 'TG', name: 'Togo', code: 'TG' },
  { id: 'TN', name: 'Tunísia', code: 'TN' },
  { id: 'UG', name: 'Uganda', code: 'UG' },
  { id: 'ZM', name: 'Zâmbia', code: 'ZM' },
  { id: 'ZW', name: 'Zimbábue', code: 'ZW' },

  // 🌍 AMÉRICA DO NORTE E CENTRAL
  { id: 'AG', name: 'Antígua e Barbuda', code: 'AG' },
  { id: 'BS', name: 'Bahamas', code: 'BS' },
  { id: 'BB', name: 'Barbados', code: 'BB' },
  { id: 'BZ', name: 'Belize', code: 'BZ' },
  { id: 'CA', name: 'Canadá', code: 'CA' },
  { id: 'CR', name: 'Costa Rica', code: 'CR' },
  { id: 'CU', name: 'Cuba', code: 'CU' },
  { id: 'DM', name: 'Dominica', code: 'DM' },
  { id: 'DO', name: 'República Dominicana', code: 'DO' },
  { id: 'SV', name: 'El Salvador', code: 'SV' },
  { id: 'GD', name: 'Granada', code: 'GD' },
  { id: 'GT', name: 'Guatemala', code: 'GT' },
  { id: 'HT', name: 'Haiti', code: 'HT' },
  { id: 'HN', name: 'Honduras', code: 'HN' },
  { id: 'JM', name: 'Jamaica', code: 'JM' },
  { id: 'MX', name: 'México', code: 'MX' },
  { id: 'NI', name: 'Nicarágua', code: 'NI' },
  { id: 'PA', name: 'Panamá', code: 'PA' },
  { id: 'PR', name: 'Porto Rico', code: 'PR' },
  { id: 'KN', name: 'São Cristóvão e Neves', code: 'KN' },
  { id: 'LC', name: 'Santa Lúcia', code: 'LC' },
  { id: 'VC', name: 'São Vicente e Granadinas', code: 'VC' },
  { id: 'TT', name: 'Trinidad e Tobago', code: 'TT' },
  { id: 'US', name: 'Estados Unidos', code: 'US' },

  // 🌍 AMÉRICA DO SUL
  { id: 'AR', name: 'Argentina', code: 'AR' },
  { id: 'BO', name: 'Bolívia', code: 'BO' },
  { id: 'BR', name: 'Brasil', code: 'BR' },
  { id: 'CL', name: 'Chile', code: 'CL' },
  { id: 'CO', name: 'Colômbia', code: 'CO' },
  { id: 'EC', name: 'Equador', code: 'EC' },
  { id: 'GY', name: 'Guiana', code: 'GY' },
  { id: 'PY', name: 'Paraguai', code: 'PY' },
  { id: 'PE', name: 'Peru', code: 'PE' },
  { id: 'SR', name: 'Suriname', code: 'SR' },
  { id: 'UY', name: 'Uruguai', code: 'UY' },
  { id: 'VE', name: 'Venezuela', code: 'VE' },

  // 🌍 ÁSIA
  { id: 'AF', name: 'Afeganistão', code: 'AF' },
  { id: 'SA', name: 'Arábia Saudita', code: 'SA' },
  { id: 'AM', name: 'Armênia', code: 'AM' },
  { id: 'AZ', name: 'Azerbaijão', code: 'AZ' },
  { id: 'BH', name: 'Bahrein', code: 'BH' },
  { id: 'BD', name: 'Bangladesh', code: 'BD' },
  { id: 'BT', name: 'Butão', code: 'BT' },
  { id: 'BN', name: 'Brunei', code: 'BN' },
  { id: 'KH', name: 'Camboja', code: 'KH' },
  { id: 'KZ', name: 'Cazaquistão', code: 'KZ' },
  { id: 'CN', name: 'China', code: 'CN' },
  { id: 'CY', name: 'Chipre', code: 'CY' },
  { id: 'KR', name: 'Coreia do Sul', code: 'KR' },
  { id: 'AE', name: 'Emirados Árabes Unidos', code: 'AE' },
  { id: 'PH', name: 'Filipinas', code: 'PH' },
  { id: 'GE', name: 'Geórgia', code: 'GE' },
  { id: 'IN', name: 'Índia', code: 'IN' },
  { id: 'ID', name: 'Indonésia', code: 'ID' },
  { id: 'IR', name: 'Irã', code: 'IR' },
  { id: 'IQ', name: 'Iraque', code: 'IQ' },
  { id: 'IL', name: 'Israel', code: 'IL' },
  { id: 'JP', name: 'Japão', code: 'JP' },
  { id: 'JO', name: 'Jordânia', code: 'JO' },
  { id: 'KW', name: 'Kuwait', code: 'KW' },
  { id: 'LA', name: 'Laos', code: 'LA' },
  { id: 'LB', name: 'Líbano', code: 'LB' },
  { id: 'MY', name: 'Malásia', code: 'MY' },
  { id: 'MV', name: 'Maldivas', code: 'MV' },
  { id: 'MN', name: 'Mongólia', code: 'MN' },
  { id: 'MM', name: 'Mianmar', code: 'MM' },
  { id: 'NP', name: 'Nepal', code: 'NP' },
  { id: 'OM', name: 'Omã', code: 'OM' },
  { id: 'PK', name: 'Paquistão', code: 'PK' },
  { id: 'PS', name: 'Palestina', code: 'PS' },
  { id: 'QA', name: 'Catar', code: 'QA' },
  { id: 'SG', name: 'Singapura', code: 'SG' },
  { id: 'SY', name: 'Síria', code: 'SY' },
  { id: 'LK', name: 'Sri Lanka', code: 'LK' },
  { id: 'TH', name: 'Tailândia', code: 'TH' },
  { id: 'TW', name: 'Taiwan', code: 'TW' },
  { id: 'TJ', name: 'Tajiquistão', code: 'TJ' },
  { id: 'TL', name: 'Timor-Leste', code: 'TL' },
  { id: 'TR', name: 'Turquia', code: 'TR' },
  { id: 'TM', name: 'Turcomenistão', code: 'TM' },
  { id: 'UZ', name: 'Uzbequistão', code: 'UZ' },
  { id: 'VN', name: 'Vietnã', code: 'VN' },
  { id: 'YE', name: 'Iêmen', code: 'YE' },

  // 🌍 EUROPA
  { id: 'AL', name: 'Albânia', code: 'AL' },
  { id: 'DE', name: 'Alemanha', code: 'DE' },
  { id: 'AD', name: 'Andorra', code: 'AD' },
  { id: 'AT', name: 'Áustria', code: 'AT' },
  { id: 'BE', name: 'Bélgica', code: 'BE' },
  { id: 'BY', name: 'Bielorrússia', code: 'BY' },
  { id: 'BA', name: 'Bósnia e Herzegovina', code: 'BA' },
  { id: 'BG', name: 'Bulgária', code: 'BG' },
  { id: 'HR', name: 'Croácia', code: 'HR' },
  { id: 'DK', name: 'Dinamarca', code: 'DK' },
  { id: 'SK', name: 'Eslováquia', code: 'SK' },
  { id: 'SI', name: 'Eslovênia', code: 'SI' },
  { id: 'ES', name: 'Espanha', code: 'ES' },
  { id: 'EE', name: 'Estônia', code: 'EE' },
  { id: 'FI', name: 'Finlândia', code: 'FI' },
  { id: 'FR', name: 'França', code: 'FR' },
  { id: 'GR', name: 'Grécia', code: 'GR' },
  { id: 'HU', name: 'Hungria', code: 'HU' },
  { id: 'IE', name: 'Irlanda', code: 'IE' },
  { id: 'IS', name: 'Islândia', code: 'IS' },
  { id: 'IT', name: 'Itália', code: 'IT' },
  { id: 'LV', name: 'Letônia', code: 'LV' },
  { id: 'LI', name: 'Liechtenstein', code: 'LI' },
  { id: 'LT', name: 'Lituânia', code: 'LT' },
  { id: 'LU', name: 'Luxemburgo', code: 'LU' },
  { id: 'MT', name: 'Malta', code: 'MT' },
  { id: 'MD', name: 'Moldávia', code: 'MD' },
  { id: 'MC', name: 'Mônaco', code: 'MC' },
  { id: 'ME', name: 'Montenegro', code: 'ME' },
  { id: 'NO', name: 'Noruega', code: 'NO' },
  { id: 'NL', name: 'Países Baixos', code: 'NL' },
  { id: 'PL', name: 'Polônia', code: 'PL' },
  { id: 'PT', name: 'Portugal', code: 'PT' },
  { id: 'GB', name: 'Reino Unido', code: 'GB' },
  { id: 'CZ', name: 'República Tcheca', code: 'CZ' },
  { id: 'RO', name: 'Romênia', code: 'RO' },
  { id: 'RU', name: 'Rússia', code: 'RU' },
  { id: 'SM', name: 'San Marino', code: 'SM' },
  { id: 'RS', name: 'Sérvia', code: 'RS' },
  { id: 'SE', name: 'Suécia', code: 'SE' },
  { id: 'CH', name: 'Suíça', code: 'CH' },
  { id: 'UA', name: 'Ucrânia', code: 'UA' },
  { id: 'VA', name: 'Vaticano', code: 'VA' },

  // 🌍 OCEANIA
  { id: 'AU', name: 'Austrália', code: 'AU' },
  { id: 'FJ', name: 'Fiji', code: 'FJ' },
  { id: 'KI', name: 'Kiribati', code: 'KI' },
  { id: 'MH', name: 'Ilhas Marshall', code: 'MH' },
  { id: 'FM', name: 'Micronésia', code: 'FM' },
  { id: 'NR', name: 'Nauru', code: 'NR' },
  { id: 'NZ', name: 'Nova Zelândia', code: 'NZ' },
  { id: 'PW', name: 'Palau', code: 'PW' },
  { id: 'PG', name: 'Papua Nova Guiné', code: 'PG' },
  { id: 'SB', name: 'Ilhas Salomão', code: 'SB' },
  { id: 'WS', name: 'Samoa', code: 'WS' },
  { id: 'TO', name: 'Tonga', code: 'TO' },
  { id: 'TV', name: 'Tuvalu', code: 'TV' },
  { id: 'VU', name: 'Vanuatu', code: 'VU' },
]

export function useCountrySearch() {
  const countrySuggestions = ref<CountrySuggestion[]>([])
  const showCountrySuggestions = ref(false)
  const countryCache = new Map<string, CountrySuggestion[]>()

  function searchCountries(query: string): CountrySuggestion[] {
    if (!query || query.length < 1) return []

    const cacheKey = query.toLowerCase()
    if (countryCache.has(cacheKey)) return countryCache.get(cacheKey) || []

    const results = COUNTRY_LIST
        .filter(c => c.name.toLowerCase().includes(query.toLowerCase()) ||
            c.code.toLowerCase().includes(query.toLowerCase()))
        .slice(0, 8)

    if (results.length > 0) countryCache.set(cacheKey, results)
    return results
  }

  function hideSuggestions() {
    setTimeout(() => { showCountrySuggestions.value = false }, 300)
  }

  function getCountryList() {
    return COUNTRY_LIST
  }

  function getCountryByCode(code: string): CountrySuggestion | undefined {
    return COUNTRY_LIST.find(c => c.code === code)
  }

  function getCodeByName(name: string): string | undefined {
    return COUNTRY_LIST.find(c => c.name.toLowerCase() === name.toLowerCase())?.code
  }

  return {
    countrySuggestions,
    showCountrySuggestions,
    searchCountries,
    hideSuggestions,
    getCountryList,
    getCountryByCode,
    getCodeByName
  }
}
