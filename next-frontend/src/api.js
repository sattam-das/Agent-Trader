import axios from 'axios'

export const api = axios.create({
  baseURL: 'http://127.0.0.1:8001',
  timeout: 60000,
})

export const fetchAnalysis = async (ticker) => {
  const { data } = await api.post('/analyze', { ticker })
  return data
}
