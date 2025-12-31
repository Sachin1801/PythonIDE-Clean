/**
 * Admin Analytics API
 * API calls for dashboard statistics and analytics
 */

const BASE_URL = '/api/admin/analytics'

export default {
  /**
   * Get dashboard statistics
   * Returns user counts, active sessions, and system stats
   */
  async getDashboardStats(token) {
    const response = await fetch(`${BASE_URL}/dashboard`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    return response.json()
  },

  /**
   * Get recent activity feed
   * Returns list of recent admin actions
   */
  async getRecentActivity(token, limit = 10) {
    const response = await fetch(`${BASE_URL}/activity?limit=${limit}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    return response.json()
  },

  /**
   * Get analytics summary
   */
  async getSummary(token, days = 30) {
    const response = await fetch(`${BASE_URL}/summary?days=${days}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    return response.json()
  },

  /**
   * Get login trends
   */
  async getLoginTrends(token, days = 30) {
    const response = await fetch(`${BASE_URL}/login-trends?days=${days}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    return response.json()
  },

  /**
   * Get execution trends
   */
  async getExecutionTrends(token, days = 30) {
    const response = await fetch(`${BASE_URL}/execution-trends?days=${days}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    return response.json()
  },

  /**
   * Get top users
   */
  async getTopUsers(token, metric = 'logins', limit = 10, days = 30) {
    const response = await fetch(`${BASE_URL}/top-users?metric=${metric}&limit=${limit}&days=${days}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    return response.json()
  }
}
