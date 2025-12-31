/**
 * Users Module for Admin Panel
 * Handles user management state
 */

import usersApi from '../../api/users'

export default {
  namespaced: true,

  state: {
    users: [],
    currentUser: null,
    total: 0,
    page: 1,
    limit: 20,
    loading: false,
    error: null,
    filters: {
      search: '',
      role: '',
      status: ''
    },
    sortBy: 'username',
    sortOrder: 'asc'
  },

  mutations: {
    SET_USERS(state, users) {
      state.users = users
    },
    SET_CURRENT_USER(state, user) {
      state.currentUser = user
    },
    SET_TOTAL(state, total) {
      state.total = total
    },
    SET_PAGE(state, page) {
      state.page = page
    },
    SET_LIMIT(state, limit) {
      state.limit = limit
    },
    SET_LOADING(state, loading) {
      state.loading = loading
    },
    SET_ERROR(state, error) {
      state.error = error
    },
    SET_FILTERS(state, filters) {
      state.filters = { ...state.filters, ...filters }
    },
    SET_SORT(state, { sortBy, sortOrder }) {
      if (sortBy) state.sortBy = sortBy
      if (sortOrder) state.sortOrder = sortOrder
    },
    RESET_FILTERS(state) {
      state.filters = { search: '', role: '', status: '' }
      state.page = 1
    },
    UPDATE_USER_IN_LIST(state, updatedUser) {
      const index = state.users.findIndex(u => u.id === updatedUser.id)
      if (index !== -1) {
        state.users.splice(index, 1, { ...state.users[index], ...updatedUser })
      }
    },
    REMOVE_USER_FROM_LIST(state, userId) {
      state.users = state.users.filter(u => u.id !== userId)
      state.total = Math.max(0, state.total - 1)
    }
  },

  actions: {
    async fetchUsers({ commit, state, rootState }) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)

      try {
        const token = rootState.auth.token
        const response = await usersApi.getUsers(token, {
          page: state.page,
          limit: state.limit,
          search: state.filters.search,
          role: state.filters.role,
          status: state.filters.status,
          sort_by: state.sortBy,
          sort_order: state.sortOrder
        })

        if (response.success) {
          commit('SET_USERS', response.users)
          commit('SET_TOTAL', response.total)
          return { success: true }
        } else {
          commit('SET_ERROR', response.error)
          return { success: false, error: response.error }
        }
      } catch (error) {
        const errorMessage = error.response?.data?.error || error.message || 'Failed to fetch users'
        commit('SET_ERROR', errorMessage)
        return { success: false, error: errorMessage }
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async fetchUser({ commit, rootState }, userId) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)

      try {
        const token = rootState.auth.token
        const response = await usersApi.getUser(token, userId)

        if (response.success) {
          commit('SET_CURRENT_USER', response.user)
          return { success: true, user: response.user }
        } else {
          commit('SET_ERROR', response.error)
          return { success: false, error: response.error }
        }
      } catch (error) {
        const errorMessage = error.response?.data?.error || error.message || 'Failed to fetch user'
        commit('SET_ERROR', errorMessage)
        return { success: false, error: errorMessage }
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async createUser({ commit, dispatch, rootState }, userData) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)

      try {
        const token = rootState.auth.token
        const response = await usersApi.createUser(token, userData)

        if (response.success) {
          // Refresh user list
          await dispatch('fetchUsers')
          return { success: true, user: response.user }
        } else {
          commit('SET_ERROR', response.error)
          return { success: false, error: response.error }
        }
      } catch (error) {
        const errorMessage = error.response?.data?.error || error.message || 'Failed to create user'
        commit('SET_ERROR', errorMessage)
        return { success: false, error: errorMessage }
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async updateUser({ commit, rootState }, { userId, userData }) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)

      try {
        const token = rootState.auth.token
        const response = await usersApi.updateUser(token, userId, userData)

        if (response.success) {
          commit('UPDATE_USER_IN_LIST', { id: userId, ...userData })
          return { success: true }
        } else {
          commit('SET_ERROR', response.error)
          return { success: false, error: response.error }
        }
      } catch (error) {
        const errorMessage = error.response?.data?.error || error.message || 'Failed to update user'
        commit('SET_ERROR', errorMessage)
        return { success: false, error: errorMessage }
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async deleteUser({ commit, rootState }, userId) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)

      try {
        const token = rootState.auth.token
        const response = await usersApi.deleteUser(token, userId)

        if (response.success) {
          commit('REMOVE_USER_FROM_LIST', userId)
          return { success: true }
        } else {
          commit('SET_ERROR', response.error)
          return { success: false, error: response.error }
        }
      } catch (error) {
        const errorMessage = error.response?.data?.error || error.message || 'Failed to delete user'
        commit('SET_ERROR', errorMessage)
        return { success: false, error: errorMessage }
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async resetPassword({ commit, rootState }, { userId, newPassword }) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)

      try {
        const token = rootState.auth.token
        const response = await usersApi.resetPassword(token, userId, newPassword)

        if (response.success) {
          return { success: true, newPassword: response.new_password }
        } else {
          commit('SET_ERROR', response.error)
          return { success: false, error: response.error }
        }
      } catch (error) {
        const errorMessage = error.response?.data?.error || error.message || 'Failed to reset password'
        commit('SET_ERROR', errorMessage)
        return { success: false, error: errorMessage }
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async bulkImport({ commit, dispatch, rootState }, file) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)

      try {
        const token = rootState.auth.token
        const response = await usersApi.bulkImport(token, file)

        if (response.success) {
          // Refresh user list
          await dispatch('fetchUsers')
          return {
            success: true,
            created: response.created,
            failed: response.failed,
            errors: response.errors
          }
        } else {
          commit('SET_ERROR', response.error)
          return { success: false, error: response.error }
        }
      } catch (error) {
        const errorMessage = error.response?.data?.error || error.message || 'Failed to import users'
        commit('SET_ERROR', errorMessage)
        return { success: false, error: errorMessage }
      } finally {
        commit('SET_LOADING', false)
      }
    },

    setPage({ commit, dispatch }, page) {
      commit('SET_PAGE', page)
      dispatch('fetchUsers')
    },

    setFilters({ commit, dispatch }, filters) {
      commit('SET_FILTERS', filters)
      commit('SET_PAGE', 1)
      dispatch('fetchUsers')
    },

    setSort({ commit, dispatch }, { sortBy, sortOrder }) {
      commit('SET_SORT', { sortBy, sortOrder })
      dispatch('fetchUsers')
    },

    resetFilters({ commit, dispatch }) {
      commit('RESET_FILTERS')
      dispatch('fetchUsers')
    }
  },

  getters: {
    users: state => state.users,
    currentUser: state => state.currentUser,
    total: state => state.total,
    page: state => state.page,
    limit: state => state.limit,
    pages: state => Math.ceil(state.total / state.limit),
    isLoading: state => state.loading,
    error: state => state.error,
    filters: state => state.filters,
    sortBy: state => state.sortBy,
    sortOrder: state => state.sortOrder
  }
}
