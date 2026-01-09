import { useState, useCallback } from 'react'
import { getErrorMessage, handleApiError } from '../utils/errorHandler'
import { toast } from '../components/ui/toast'

/**
 * Custom hook for API calls with automatic error handling and loading states
 * @param {Function} apiCall - The API function to call
 * @param {Object} options - Configuration options
 * @param {boolean} options.showErrorToast - Show error toast on failure (default: true)
 * @param {boolean} options.showSuccessToast - Show success toast on success (default: false)
 * @param {string} options.successMessage - Success message for toast
 * @param {Function} options.onSuccess - Callback on success
 * @param {Function} options.onError - Callback on error
 * @param {Function} options.onAuthError - Custom auth error handler
 * @returns {Object} - { execute, loading, error, data, reset }
 */
export function useApi(apiCall, options = {}) {
  const {
    showErrorToast = true,
    showSuccessToast = false,
    successMessage,
    onSuccess,
    onError,
    onAuthError,
  } = options

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
        
        if (showSuccessToast && successMessage) {
          toast.success(successMessage)
        }
        
        if (onSuccess) {
          onSuccess(result)
        }
        
        return result
      } catch (err) {
        setError(err)
        
        // Handle error
        handleApiError(err, {
          onAuthError: onAuthError || (() => {
            // Default auth error handling is done by interceptor
          }),
          onOtherError: (error) => {
            if (showErrorToast) {
              toast.error(getErrorMessage(error))
            }
            if (onError) {
              onError(error)
            } else {
            }
          },
        })
        
        throw err
      } finally {
        setLoading(false)
      }
    },
    [apiCall, showErrorToast, showSuccessToast, successMessage, onSuccess, onError, onAuthError]
  )

  const reset = useCallback(() => {
    setError(null)
    setData(null)
  }, [])

  return { execute, loading, error, data, reset }
}

/**
 * Hook for API calls that should show success toast by default
 */
export function useApiWithToast(apiCall, successMessage, options = {}) {
  return useApi(apiCall, {
    ...options,
    showSuccessToast: true,
    successMessage,
  })
}



