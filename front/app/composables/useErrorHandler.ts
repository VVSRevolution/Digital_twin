import {computed, ref} from 'vue'

export interface Notification {
    id: string
    message: string
    type: 'error' | 'success' | 'info'
    duration?: number
}

const notifications = ref<Notification[]>([])

export const useNotifications = () => {
    const addNotification = (
        message: string,
        type: 'error' | 'success' | 'info' = 'info',
        duration = 10000
    ) => {
        const id = `notify-${Date.now()}-${Math.random()}`

        notifications.value.push({
            id,
            message,
            type,
            duration,
        })

        if (duration > 0) {
            setTimeout(() => {
                removeNotification(id)
            }, duration)
        }
    }

    const removeNotification = (id: string) => {
        notifications.value = notifications.value.filter(n => n.id !== id)
    }

    const handleError = (error: unknown, defaultMessage = 'Erro ao processar requisição') => {
        let message = defaultMessage

        if (error instanceof Error) {
            message = error.message
        } else if (typeof error === 'string') {
            message = error
        }

        console.error('❌ Erro:', error)
        addNotification(`❌ ${message}`, 'error')
    }

    const handleSuccess = (message = 'Operação realizada com sucesso!') => {
        console.log('✅ Sucesso:', message)
        addNotification(`✅ ${message}`, 'success')
    }

    const handleInfo = (message: string) => {
        console.log('ℹ️ Info:', message)
        addNotification(`ℹ️ ${message}`, 'info')
    }

    return {
        notifications: computed(() => notifications.value),
        addNotification,
        removeNotification,
        handleError,
        handleSuccess,
        handleInfo,
    }
}

