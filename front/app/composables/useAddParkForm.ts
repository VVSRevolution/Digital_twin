// composables/useAddParkForm.ts
import {ref} from 'vue'
import {useNotifications} from '~/composables/useErrorHandler'
import {useCountrySearch} from './useCountrySearch'

// ============================================================
// 🔥 INTERFACE FORA DA FUNÇÃO
// ============================================================
export interface AddParkData {
    name: string
    city: string
    country: string
    startDate: string | null
    endDate: string | null
    isUpToDate?: boolean
    satellites?: string[]
    numBuffers?: number
    bufferDistance?: number
}

// ============================================================
// 🔥 COMPOSABLE
// ============================================================
export function useAddParkForm() {
    const {handleError, handleSuccess, handleInfo} = useNotifications()
    const {getCodeByName} = useCountrySearch()

    const isAddingPark = ref(false)
    const newParkName = ref('')
    const newParkCountry = ref('Brasil')
    const newParkCity = ref('')
    const newParkStartDate = ref('')
    const newParkEndDate = ref('')
    const selectedCountryCode = ref('BR')

    const isUpToDate = ref(true)
    const selectedSatellites = ref<string[]>(['LANDSAT_8', 'LANDSAT_9'])
    const newNumBuffers = ref(11)
    const newBufferDistance = ref(90)

    function resetForm() {
        newParkName.value = ''
        newParkCountry.value = 'Brasil'
        newParkCity.value = ''
        newParkStartDate.value = ''
        newParkEndDate.value = ''
        selectedCountryCode.value = 'BR'
        isUpToDate.value = true
        selectedSatellites.value = ['LANDSAT_8', 'LANDSAT_9']
        newNumBuffers.value = 11
        newBufferDistance.value = 90
    }

    function startAddPark() {
        isAddingPark.value = true
        resetForm()
    }

    function cancelAddPark() {
        isAddingPark.value = false
        handleInfo('Cadastro cancelado')
    }

    function validateForm(): boolean {
        // Campos obrigatórios
        if (!newParkCity.value || !newParkCountry.value || !newParkName.value) {
            handleError('Preencha todos os campos obrigatórios')
            return false
        }

        // DATA DE INÍCIO É SEMPRE OBRIGATÓRIA
        if (!newParkStartDate.value) {
            handleError('Selecione uma data de início')
            return false
        }

        // Só valida data fim se NÃO estiver mantendo atualizado
        if (!isUpToDate.value && newParkEndDate.value && newParkEndDate.value < newParkStartDate.value) {
            handleError('Data de fim não pode ser anterior à data de início')
            return false
        }

        return true
    }

    function getFormData(): AddParkData {
        return {
            city: newParkCity.value,
            country: newParkCountry.value,
            name: newParkName.value,
            startDate: newParkStartDate.value,
            endDate: isUpToDate.value ? null : newParkEndDate.value, // Só tem fim se for manual
            isUpToDate: isUpToDate.value,
            satellites: selectedSatellites.value,
            numBuffers: newNumBuffers.value,
            bufferDistance: newBufferDistance.value
        }
    }

    function confirmAddPark(): AddParkData | null {
        if (!validateForm()) return null

        const data = getFormData()
        isAddingPark.value = false
        handleSuccess(`Parque "${newParkName.value}" cadastrado com sucesso!`)

        return data
    }

    function selectCountry(countryName: string) {
        const code = getCodeByName(countryName)
        if (code) {
            selectedCountryCode.value = code
            newParkCity.value = ''
        }
    }

    return {
        // States
        isAddingPark,
        newParkName,
        newParkCountry,
        newParkCity,
        newParkStartDate,
        newParkEndDate,
        selectedCountryCode,
        isUpToDate,
        selectedSatellites,
        newNumBuffers,
        newBufferDistance,

        // Methods
        startAddPark,
        cancelAddPark,
        confirmAddPark,
        selectCountry,
        validateForm,
        getFormData,
        resetForm
    }
}