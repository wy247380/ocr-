import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

export function uploadPatentFile(file) {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/patent/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function uploadPatentFilesBatch(files) {
  const formData = new FormData()
  for (const file of files) {
    formData.append('files', file)
  }
  return api.post('/patent/upload-batch', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function getBatchStatus(batchId) {
  return api.get(`/patent/batch/${batchId}`)
}

export function getTaskStatus(taskId) {
  return api.get(`/patent/tasks/${taskId}`)
}

export function listTasks(params = {}) {
  return api.get('/patent/tasks', { params })
}

export function listPendingReviews(params = {}) {
  return api.get('/admin/reviews', { params })
}

export function approveReview(resultId, data) {
  return api.post(`/admin/reviews/${resultId}/approve`, data)
}

export function rejectReview(resultId, data) {
  return api.post(`/admin/reviews/${resultId}/reject`, data)
}

export function listAuditLogs(params = {}) {
  return api.get('/admin/audit-logs', { params })
}

export default api
