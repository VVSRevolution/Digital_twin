import {computed, ref} from 'vue'
import type {Notification} from '~/types'

const notifications = ref<Notification[]>([])

export const useNotifications = () => {
    const addNotification = (
        message: string,
        type: 'error' | 'success' | 'info' = 'info',
        duration = 10000,
        closable = true
    ) => {
        const id = `notify-${Date.now()}-${Math.random()}`

        notifications.value.push({
            id,
            message,
            type,
            duration,
            closable,
        })

        if (duration > 0 && closable) {
            setTimeout(() => {
                removeNotification(id)
            }, duration)
        }
    }

    const removeNotification = (id: string) => {
        notifications.value = notifications.value.filter(n => n.id !== id)
    }

    const handleError = (error: unknown, defaultMessage = 'Erro ao processar requisição', closable: boolean = true) => {
        let message = defaultMessage

        if (error instanceof Error) {
            message = error.message
        } else if (typeof error === 'string') {
            message = error
        }

        const formattedMessage = message.replace(/\n/g, '<br>')

        console.error('❌ Erro:', error)
        addNotification(`❌ ${formattedMessage}`, 'error', 10000, closable)
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

