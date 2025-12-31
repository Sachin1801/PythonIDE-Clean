/**
 * Admin Users API
 * API calls for user management
 */

const BASE_URL = '/api/admin/users'

function buildQueryString(params) {
  const searchParams = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== '') {
      searchParams.append(key, value)
    }
  }
  return searchParams.toString()
}

export default {
  async getUsers(token, params = {}) {
    const queryString = buildQueryString(params)
    const url = queryString ? `${BASE_URL}?${queryString}` : BASE_URL

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    return response.json()
  },

  async getUser(token, userId) {
    const response = await fetch(`${BASE_URL}/${userId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    return response.json()
  },

  async createUser(token, userData) {
    const response = await fetch(BASE_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(userData)
    })

    return response.json()
  },

  async updateUser(token, userId, userData) {
    const response = await fetch(`${BASE_URL}/${userId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(userData)
    })

    return response.json()
  },

  async deleteUser(token, userId) {
    const response = await fetch(`${BASE_URL}/${userId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    return response.json()
  },

  async resetPassword(token, userId, newPassword = null) {
    const body = newPassword ? { new_password: newPassword } : {}

    const response = await fetch(`${BASE_URL}/${userId}/reset-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(body)
    })

    return response.json()
  },

  async bulkImport(token, file) {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${BASE_URL}/bulk-import`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    })

    return response.json()
  },

  async exportUsers(token, params = {}) {
    const queryString = buildQueryString({ ...params, export: 'true' })
    const url = `${BASE_URL}?${queryString}`

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    // Return blob for file download
    return response.blob()
  },

  async downloadTemplate(token) {
    const response = await fetch(`${BASE_URL}/bulk-import`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    return response.blob()
  }
}
