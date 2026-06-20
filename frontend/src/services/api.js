import axios from 'axios'

const API_BASE_URL = '/api/v1'

const DEFAULT_TIMEOUT = 60000
const SCAN_TIMEOUT = 90000

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: DEFAULT_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use(
  (config) => {
    config.metadata = { startTime: Date.now() }
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  (response) => {
    const duration = Date.now() - (response.config.metadata?.startTime || Date.now())
    if (duration > 3000) {
      console.warn(`[慢请求] ${response.config.method?.toUpperCase()} ${response.config.url} | ${duration}ms`)
    }
    return response.data
  },
  (error) => {
    if (error.code === 'ECONNABORTED' || error.response?.status === 504) {
      console.error('[请求超时] 服务器处理时间过长:', error.config?.url)
      error.userMessage = '服务器处理超时，请减少并发扫描量或稍后重试'
    } else if (!error.response) {
      console.error('[网络错误] 无法连接到后端服务器')
      error.userMessage = '网络连接失败，请检查后端服务是否启动'
    } else {
      console.error('API 请求错误:', error.response?.status, error.config?.url)
      error.userMessage = error.response?.data?.detail || '请求失败'
    }
    return Promise.reject(error)
  }
)

export const scanApi = {
  scanWaybill: (imageFile, conveyorId = 'CONV-001') => {
    const formData = new FormData()
    formData.append('image', imageFile)
    formData.append('conveyor_id', conveyorId)
    return api.post('/scan/waybill', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: SCAN_TIMEOUT,
    })
  },

  scanWaybillBase64: (imageBase64, conveyorId = 'CONV-001') => {
    return api.post(
      '/scan/waybill/base64',
      {
        image: imageBase64,
        conveyor_id: conveyorId,
      },
      { timeout: SCAN_TIMEOUT }
    )
  },

  getScanRecords: (params = {}) => {
    return api.get('/scan/records', { params })
  },

  getScanRecord: (recordId) => {
    return api.get(`/scan/records/${recordId}`)
  },

  getOcrPerformance: () => {
    return api.get('/scan/performance')
  },
}

export const interceptApi = {
  getActiveIntercepts: () => {
    return api.get('/intercept/active')
  },

  getInterceptHistory: (params = {}) => {
    return api.get('/intercept/history', { params })
  },

  checkIntercept: (trackingNumber) => {
    return api.post(`/intercept/check/${trackingNumber}`)
  },

  handleIntercept: (trackingNumber, handledBy, remark = '') => {
    return api.post(`/intercept/handle/${trackingNumber}`, null, {
      params: { handled_by: handledBy, remark },
    })
  },

  clearActiveIntercept: (trackingNumber) => {
    return api.post(`/intercept/clear/${trackingNumber}`)
  },

  getAllValves: () => {
    return api.get('/intercept/valves')
  },

  getValveStatus: (valveId) => {
    return api.get(`/intercept/valves/${valveId}`)
  },

  controlValve: (valveId, action, duration = null) => {
    return api.post('/intercept/valves/control', {
      valve_id: valveId,
      action,
      duration,
    })
  },

  triggerValve: (valveId, duration = null) => {
    return api.post(`/intercept/valves/${valveId}/trigger`, null, {
      params: duration ? { duration } : {},
    })
  },

  getPackageStatus: (trackingNumber) => {
    return api.get(`/intercept/packages/status/${trackingNumber}`)
  },
}

export default api
