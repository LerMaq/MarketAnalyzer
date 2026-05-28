import axios from 'axios'

const baseURL = import.meta.env.VITE_API_URL || '/api'

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