import { useState, useCallback } from 'react'

/**
 * Custom hook for handling async operations with loading and error states
 * @param {Function} asyncFunction - The async function to execute
 * @returns {Object} - { execute, loading, error, data }
 */
export function useAsync(asyncFunction) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [data, setData] = useState(null)

  const execute = useCallback(
    async (...args) => {
      try {
        setLoading(true)
        setError(null)
        const result = await asyncFunction(...args)
        setData(result)
        return result
      } catch (err) {
        setError(err)
        throw err
      } finally {
        setLoading(false)
      }
    },
    [asyncFunction]
  )

  return { execute, loading, error, data, reset: () => { setError(null); setData(null) } }
}

/**
 * Custom hook for handling API calls with automatic error handling
 * @param {Function} apiCall - The API function to call
 * @param {Object} options - { onSuccess, onError, immediate }
 */
export function useApiCall(apiCall, options = {}) {
  const { onSuccess, onError } = options
  // Note: immediate option is reserved for future use
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [data, setData] = useState(null)

  const execute = useCallback(
    async (...args) => {
      try {
        setLoading(true)
        setError(null)
        const result = await apiCall(...args)
        setData(result)
        if (onSuccess) onSuccess(result)
        return result
      } catch (err) {
        setError(err)
        if (onError) onError(err)
        else console.error('API call failed:', err)
        throw err
      } finally {
        setLoading(false)
      }
    },
    [apiCall, onSuccess, onError]
  )

  return { execute, loading, error, data, reset: () => { setError(null); setData(null) } }
}


