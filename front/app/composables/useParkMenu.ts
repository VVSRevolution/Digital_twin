import { ref, watch } from 'vue'
import type { SearchResult } from '@/types/parkSearch'

export function useParkMenu() {
  const isMenuOpen = ref(false)
  const selectedPark = ref<SearchResult | null>(null)
  const menuCardRef = ref<HTMLElement | null>(null)

  function toggleMenu() {
    isMenuOpen.value = !isMenuOpen.value
  }

  function closeMenu() {
    isMenuOpen.value = false
  }

  function handleClickOutside(event: MouseEvent) {
    if (menuCardRef.value && !menuCardRef.value.contains(event.target as Node)) {
      isMenuOpen.value = false
    }
  }

  watch(isMenuOpen, (newVal) => {
    if (newVal) {
      document.addEventListener('click', handleClickOutside)
    } else {
      document.removeEventListener('click', handleClickOutside)
    }
  })

  return {
    isMenuOpen,
    selectedPark,
    menuCardRef,
    toggleMenu,
    closeMenu,
    handleClickOutside
  }
}
