/**
 * Extract error message from backend or detect connection issues
 * Backend sends error messages in the "detail" field with appropriate status codes
 */
export function extractErrorMessage(error: any, fallbackMessage: string = 'An error occurred'): string {
  if (!error) {
    return fallbackMessage
  }

  // Check for connection/network errors
  if (error.code === 'ERR_NETWORK' || 
      error.name === 'TypeError' && error.message?.includes('fetch') ||
      error.code === 'ECONNREFUSED' ||
      error.message?.includes('Failed to fetch') ||
      error.message?.includes('Network Error')) {
    return 'Lost connection to server. Please check your internet connection.'
  }

  // Extract backend error message from detail field
  if (error?.detail) {
    if (typeof error.detail === 'string') {
      return error.detail
    }
    // If detail is an array (validation errors), join them
    if (Array.isArray(error.detail)) {
      return error.detail.map((err: any) => {
        if (typeof err === 'string') return err
        return err.msg || err.message || JSON.stringify(err)
      }).join(', ')
    }
  }

  // Try response.data.detail (axios/fetch wrapper format)
  if (error?.response?.data?.detail) {
    return extractErrorMessage(error.response.data, fallbackMessage)
  }

  // If error has message property, use it
  if (error?.message && typeof error.message === 'string') {
    return error.message
  }

  return fallbackMessage
}
