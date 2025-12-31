/**
 * Admin File Browser API
 * API calls for browsing and downloading student files
 */

const BASE_URL = '/api/admin/files'

export default {
  /**
   * Get list of all student directories
   */
  async getStudents(token) {
    const response = await fetch(`${BASE_URL}/students`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    return response.json()
  },

  /**
   * Browse directory contents
   */
  async browse(token, path = '') {
    const params = new URLSearchParams()
    if (path) params.append('path', path)

    const response = await fetch(`${BASE_URL}/browse?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    return response.json()
  },

  /**
   * Get file content for preview
   */
  async getContent(token, path) {
    const params = new URLSearchParams({ path })

    const response = await fetch(`${BASE_URL}/content?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    return response.json()
  },

  /**
   * Download file or directory
   */
  async download(token, path) {
    const params = new URLSearchParams({ path })

    const response = await fetch(`${BASE_URL}/download?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    return response.blob()
  },

  /**
   * Get download URL (for opening in new tab)
   */
  getDownloadUrl(path) {
    const params = new URLSearchParams({ path })
    return `${BASE_URL}/download?${params.toString()}`
  },

  /**
   * Search files
   */
  async search(token, query, student = '') {
    const params = new URLSearchParams({ q: query })
    if (student) params.append('student', student)

    const response = await fetch(`${BASE_URL}/search?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    return response.json()
  }
}
