import { ref } from 'vue'
import api from './api/client'

const STORAGE_KEY = 'analysis_tasks'

const tasks = ref([])
const notifications = ref([])

let pollTimer = null
let pollingInProgress = false

const loadTasks = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return
    const parsed = JSON.parse(raw)
    if (Array.isArray(parsed)) {
      tasks.value = parsed
    }
  } catch (e) {
    console.error('Ошибка чтения списка анализов из localStorage:', e)
  }
}

const saveTasks = () => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks.value))
  } catch (e) {
    console.error('Ошибка сохранения списка анализов в localStorage:', e)
  }
}

const pushNotification = (payload) => {
  const id = `${Date.now()}_${Math.random().toString(16).slice(2)}`
  notifications.value.push({ id, ...payload })
}

const removeTask = (taskId) => {
  tasks.value = tasks.value.filter(t => t.id !== taskId)
  saveTasks()
  if (tasks.value.length === 0) {
    stopPolling()
  }
}

const updateTask = (taskId, patch) => {
  const existing = tasks.value.find(t => t.id === taskId)
  if (existing) {
    Object.assign(existing, patch)
    saveTasks()
  }
}

const pollOnce = async () => {
  if (pollingInProgress) return
  if (tasks.value.length === 0) return
  pollingInProgress = true

  try {
    const snapshot = [...tasks.value]
    await Promise.all(snapshot.map(async (task) => {
      try {
        const res = await api.get(`/tasks/status/${task.id}`)
        const data = res.data

        updateTask(task.id, {
          status: data.status,
          retry_count: data.retry_count ?? 0,
          ozon_id: data.ozon_id,
          product_id: data.product_id
        })

        if (data.status === 'completed') {
          if (data.ozon_id && data.product_id) {
            pushNotification({
              type: 'success',
              title: 'Анализ завершён',
              message: 'Отчёт готов. Можно открыть результат.',
              actionLabel: 'Открыть отчёт',
              actionPath: `/product/${data.ozon_id}/${data.product_id}`
            })
          } else {
            pushNotification({
              type: 'success',
              title: 'Анализ завершён',
              message: 'Отчёт готов, но данные для открытия не получены.'
            })
          }
          removeTask(task.id)
        } else if (data.status === 'failed') {
          pushNotification({
            type: 'error',
            title: 'Анализ не завершён',
            message: 'Не удалось завершить анализ. Попробуйте повторить позже.'
          })
          removeTask(task.id)
        }
      } catch (e) {
        const status = e.response?.status
        if (status === 404) {
          removeTask(task.id)
        } else {
          console.error('Ошибка опроса статуса анализа:', e)
        }
      }
    }))
  } finally {
    pollingInProgress = false
  }
}

const startPolling = () => {
  if (pollTimer) return
  pollOnce()
  pollTimer = setInterval(pollOnce, 2500)
}

const stopPolling = () => {
  if (!pollTimer) return
  clearInterval(pollTimer)
  pollTimer = null
}

const addTask = (taskId) => {
  if (!taskId) return
  const existing = tasks.value.find(t => t.id === taskId)
  if (!existing) {
    tasks.value.push({
      id: taskId,
      status: 'pending',
      retry_count: 0,
      created_at: Date.now()
    })
    saveTasks()
  }
  startPolling()
}

const initTracker = () => {
  loadTasks()
  if (tasks.value.length > 0) {
    startPolling()
  }
}

const dismissNotification = (id) => {
  notifications.value = notifications.value.filter(n => n.id !== id)
}

export {
  tasks,
  notifications,
  addTask,
  initTracker,
  dismissNotification
}
