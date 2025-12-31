/**
 * Admin Audit Log API
 * API calls for audit log viewing and export
 */

const BASE_URL = '/api/admin/audit'

export default {
  /**
   * Get paginated audit logs with filters
   */
  async getLogs(token, params = {}) {
    const queryParams = new URLSearchParams()

    if (params.page) queryParams.append('page', params.page)
    if (params.limit) queryParams.append('limit', params.limit)
    if (params.action_type) queryParams.append('action_type', params.action_type)
    if (params.admin_id) queryParams.append('admin_id', params.admin_id)
    if (params.from_date) queryParams.append('from_date', params.from_date)
    if (params.to_date) queryParams.append('to_date', params.to_date)
    if (params.search) queryParams.append('search', params.search)

    const url = `${BASE_URL}?${queryParams.toString()}`

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    return response.json()
  },

  /**
   * Export audit logs to CSV
   */
  async exportLogs(token, params = {}) {
    const queryParams = new URLSearchParams()

    if (params.action_type) queryParams.append('action_type', params.action_type)
    if (params.admin_id) queryParams.append('admin_id', params.admin_id)
    if (params.from_date) queryParams.append('from_date', params.from_date)
    if (params.to_date) queryParams.append('to_date', params.to_date)
    if (params.search) queryParams.append('search', params.search)

    const url = `${BASE_URL}/export?${queryParams.toString()}`

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    return response.blob()
  },

  /**
   * Get list of distinct action types
   */
  async getActionTypes(token) {
    const response = await fetch(`${BASE_URL}/action-types`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    return response.json()
  },

  /**
   * Get list of admin users with audit entries
   */
  async getAdmins(token) {
    const response = await fetch(`${BASE_URL}/admins`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    return response.json()
  }
}
