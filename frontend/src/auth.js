import { ref } from 'vue'
import api from './api/client'

const user = ref(null)

async function loadUser() {
  try {
    const res = await api.get('/user/me')
    user.value = res.data
  } catch (e) {
    user.value = null
  }
}

async function getCurrentUser() {
  return user.value
}

async function login(email, password) {
  const res = await api.post('/auth/login', { email, password })
  await loadUser()
  return res
}

async function register(email, password, name) {
  const res = await api.post('/auth/register', { email, password, name })
  await loadUser()
  return res
}

async function logout() {
  await api.post('/auth/logout')
  user.value = null
}

export default {
  user,
  loadUser,
  getCurrentUser,
  login,
  register,
  logout
}
