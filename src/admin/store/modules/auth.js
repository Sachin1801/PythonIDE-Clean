/**
 * Auth Module for Admin Panel
 * Handles admin authentication state
 */

import api from '../../api/auth'

const TOKEN_KEY = 'admin_token'
const USER_KEY = 'admin_user'

export default {
  namespaced: true,

  state: {
    token: localStorage.getItem(TOKEN_KEY) || null,
    user: JSON.parse(localStorage.getItem(USER_KEY) || 'null'),
    isAuthenticated: false,
    loading: false,
    error: null
  },

  mutations: {
    SET_TOKEN(state, token) {
      state.token = token
      if (token) {
        localStorage.setItem(TOKEN_KEY, token)
      } else {
        localStorage.removeItem(TOKEN_KEY)
      }
    },
    SET_USER(state, user) {
      state.user = user
      if (user) {
        localStorage.setItem(USER_KEY, JSON.stringify(user))
      } else {
        localStorage.removeItem(USER_KEY)
      }
    },
    SET_AUTHENTICATED(state, isAuthenticated) {
      state.isAuthenticated = isAuthenticated
    },
    SET_LOADING(state, loading) {
      state.loading = loading
    },
    SET_ERROR(state, error) {
      state.error = error
    },
    CLEAR_AUTH(state) {
      state.token = null
      state.user = null
      state.isAuthenticated = false
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    }
  },

  actions: {
    async login({ commit }, { username, password }) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)

      try {
        const response = await api.login(username, password)

        if (response.success) {
          commit('SET_TOKEN', response.token)
          commit('SET_USER', response.user)
          commit('SET_AUTHENTICATED', true)
          return { success: true }
        } else {
          commit('SET_ERROR', response.error || 'Login failed')
          return { success: false, error: response.error }
        }
      } catch (error) {
        const errorMessage = error.response?.data?.error || error.message || 'Login failed'
        commit('SET_ERROR', errorMessage)
        return { success: false, error: errorMessage }
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async logout({ commit, state }) {
      try {
        if (state.token) {
          await api.logout(state.token)
        }
      } catch (error) {
        console.error('Logout error:', error)
      } finally {
        commit('CLEAR_AUTH')
      }
    },

    async checkSession({ commit, state }) {
      if (!state.token) {
        commit('SET_AUTHENTICATED', false)
        return false
      }

      try {
        const response = await api.validateSession(state.token)

        if (response.valid) {
          commit('SET_USER', response.user)
          commit('SET_AUTHENTICATED', true)
          return true
        } else {
          commit('CLEAR_AUTH')
          return false
        }
      } catch (error) {
        console.error('Session validation error:', error)
        commit('CLEAR_AUTH')
        return false
      }
    },

    async renewSession({ commit, state }) {
      if (!state.token) return false

      try {
        const response = await api.renewSession(state.token)
        return response.success
      } catch (error) {
        console.error('Session renewal error:', error)
        return false
      }
    }
  },

  getters: {
    isAuthenticated: state => state.isAuthenticated,
    user: state => state.user,
    token: state => state.token,
    isLoading: state => state.loading,
    error: state => state.error,
    username: state => state.user?.username || '',
    fullName: state => state.user?.full_name || state.user?.username || ''
  }
}
