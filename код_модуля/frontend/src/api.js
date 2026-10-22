import axios from 'axios'

// Клиент REST API модуля. Токен сеанса хранится в sessionStorage.
const api = axios.create({ baseURL: '/api/' })

api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('token')
  if (token) config.headers.Authorization = `Token ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) {
      sessionStorage.clear()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export function errorText(error) {
  const data = error.response?.data
  if (!data) return 'Сервер недоступен. Повторите попытку.'
  if (data.detail) return data.detail
  return Object.values(data).flat().join(' ')
}

export const fmtDate = (d) => (d ? d.split('-').reverse().join('.') : '')
export const fmtTime = (t) => (t ? t.slice(0, 5) : '')

export default api
