import axios from 'axios'

// Vite требует, чтобы переменные начинались с префикса VITE_
const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: baseURL,
  withCredentials: true
})

// Обработка ошибок (например, 401 для редиректа на логин в будущем)
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      console.warn('Требуется авторизация')
    }
    return Promise.reject(error)
  }
)

export default api