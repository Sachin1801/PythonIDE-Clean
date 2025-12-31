/**
 * Admin Panel Vuex Store
 * Central state management for the admin panel
 */

import { createStore } from 'vuex'
import auth from './modules/auth'
import users from './modules/users'

export default createStore({
  modules: {
    auth,
    users
  },
  state: {
    loading: false,
    error: null
  },
  mutations: {
    SET_LOADING(state, loading) {
      state.loading = loading
    },
    SET_ERROR(state, error) {
      state.error = error
    },
    CLEAR_ERROR(state) {
      state.error = null
    }
  },
  actions: {
    setLoading({ commit }, loading) {
      commit('SET_LOADING', loading)
    },
    setError({ commit }, error) {
      commit('SET_ERROR', error)
    },
    clearError({ commit }) {
      commit('CLEAR_ERROR')
    }
  },
  getters: {
    isLoading: state => state.loading,
    error: state => state.error
  }
})
