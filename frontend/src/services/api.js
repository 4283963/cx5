import axios from 'axios'

const API_BASE_URL = '/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API 请求错误:', error)
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
    })
  },

  scanWaybillBase64: (imageBase64, conveyorId = 'CONV-001') => {
    return api.post('/scan/waybill/base64', {
      image: imageBase64,
      conveyor_id: conveyorId,
    })
  },

  getScanRecords: (params = {}) => {
    return api.get('/scan/records', { params })
  },

  getScanRecord: (recordId) => {
    return api.get(`/scan/records/${recordId}`)
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
