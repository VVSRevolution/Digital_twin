<script lang="ts" setup>
import {useNotifications} from '~/composables/useErrorHandler'

const {notifications, removeNotification} = useNotifications()
</script>

<template>
  <div class="notifications-container">
    <transition-group name="notification" tag="div">
      <div
          v-for="notification in notifications"
          :key="notification.id"
          :class="['notification', `notification-${notification.type}`]"
      >
        <div class="notification-content">
          {{ notification.message }}
        </div>
        <button
            aria-label="Fechar notificação"
            class="notification-close"
            @click="removeNotification(notification.id)"
        >
          ✕
        </button>
      </div>
    </transition-group>
  </div>
</template>

<style scoped>
.notifications-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none;
}

.notification {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  font-size: 14px;
  pointer-events: auto;
  animation: slideIn 0.3s ease-out;
  min-width: 300px;
  max-width: 500px;
}

.notification-error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.notification-success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.notification-info {
  background-color: #d1ecf1;
  color: #0c5460;
  border: 1px solid #bee5eb;
}

.notification-content {
  flex: 1;
  margin-right: 12px;
  line-height: 1.5;
}

.notification-close {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 18px;
  padding: 0;
  color: inherit;
  opacity: 0.7;
  transition: opacity 0.2s;
  flex-shrink: 0;
}

.notification-close:hover {
  opacity: 1;
}

.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.notification-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
</style>
