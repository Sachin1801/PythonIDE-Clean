/**
 * Admin Auth API
 * API calls for admin authentication
 */

const BASE_URL = '/api/admin/auth'

export default {
  async login(username, password) {
    const response = await fetch(`${BASE_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ username, password })
    })

    return response.json()
  },

  async logout(token) {
    const response = await fetch(`${BASE_URL}/logout`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    })

    return response.json()
  },

  async validateSession(token) {
    const response = await fetch(`${BASE_URL}/session`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    return response.json()
  },

  async renewSession(token) {
    const response = await fetch(`${BASE_URL}/session`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    })

    return response.json()
  }
}
