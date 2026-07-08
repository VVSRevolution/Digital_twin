import { ref } from 'vue'
import { useNotifications } from '~/composables/useErrorHandler'
import { useCountrySearch } from './useCountrySearch'
import type { AddParkData } from '@/types/parkSearch'

export function useAddParkForm() {
  const { handleError, handleSuccess, handleInfo } = useNotifications()
  const { getCodeByName } = useCountrySearch()

  const isAddingPark = ref(false)
  const newParkName = ref('')
  const newParkCountry = ref('Brasil')
  const newParkCity = ref('')
  const newParkStartDate = ref('')
  const newParkEndDate = ref('')
  const selectedCountryCode = ref('BR')

  function resetForm() {
    newParkName.value = ''
    newParkCountry.value = 'Brasil'
    newParkCity.value = ''
    newParkStartDate.value = ''
    newParkEndDate.value = ''
    selectedCountryCode.value = 'BR'
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
    if (!newParkCity.value || !newParkCountry.value || !newParkName.value ||
        !newParkStartDate.value || !newParkEndDate.value) {
      handleError('Preencha todos os campos obrigatórios')
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
      endDate: newParkEndDate.value
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
