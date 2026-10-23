import api from './client'

export const authApi = {
  signup: (data) => api.post('/auth/signup', data),
  login:  (data) => api.post('/auth/login', data),
  logout: ()     => api.post('/auth/logout'),
  me:     ()     => api.get('/auth/me'),
}

export const uploadsApi = {
  preview: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post('/uploads/preview', fd)
  },
  confirm: (file, mappingObj) => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('mapping_json', JSON.stringify(mappingObj))
    return api.post('/uploads', fd)
  },
  list:   ()         => api.get('/uploads'),
  get:    (id)       => api.get(`/uploads/${id}`),
  delete: (id)       => api.delete(`/uploads/${id}`),
}

export const analyticsApi = {
  summary:    (id) => api.get(`/analytics/${id}/summary`),
  products:   (id) => api.get(`/analytics/${id}/products`),
  monthly:    (id) => api.get(`/analytics/${id}/monthly`),
  dayOfMonth: (id) => api.get(`/analytics/${id}/day-of-month`),
  reprocess:  (id) => api.post(`/analytics/${id}/process`),
}

export const exportsApi = {
  products:   (id) => `/api/exports/${id}/products.csv`,
  monthly:    (id) => `/api/exports/${id}/monthly.csv`,
  dayOfMonth: (id) => `/api/exports/${id}/day-of-month.csv`,
}
