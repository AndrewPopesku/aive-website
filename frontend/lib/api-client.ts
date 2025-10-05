import { createClient } from '@hey-api/client-axios'
import { createConfig } from '@hey-api/client-axios'

// Create the API client with the backend URL
export const apiClient = createClient(createConfig({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    // Don't set default Content-Type as it will be overridden for form data
  },
  withCredentials: true, // Required to send Authorization header with credentials
  responseType: 'json',
  // Configure authentication to read token from localStorage
  auth: () => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('auth_token')
      return token || undefined
    }
    return undefined
  },
}))

// Export the client for use in hooks and components
export default apiClient

