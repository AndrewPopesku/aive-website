"use client"

import React, { createContext, useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { 
  loginApiV1AuthLoginPost, 
  registerApiV1AuthRegisterPost,
  getCurrentUserInfoApiV1AuthMeGet,
  type UserResponse
} from '@/client'
import { apiClient } from '@/lib/api-client'
import { extractErrorMessage } from '@/lib/error-handler'

interface AuthContextType {
  user: UserResponse | null
  token: string | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  // Load token and user from localStorage on mount
  useEffect(() => {
    const loadAuth = async () => {
      try {
        const storedToken = localStorage.getItem('auth_token')
        if (storedToken) {
          setToken(storedToken)
          
          // Fetch user info with the stored token
          const response = await getCurrentUserInfoApiV1AuthMeGet({
            client: apiClient,
          })
          
          if (response.data) {
            setUser(response.data)
          } else {
            // Token is invalid, clear it
            localStorage.removeItem('auth_token')
            setToken(null)
          }
        }
      } catch (error) {
        console.error('Failed to load auth:', error)
        localStorage.removeItem('auth_token')
        setToken(null)
      } finally {
        setLoading(false)
      }
    }

    loadAuth()
  }, [])

  // Note: Authorization header is automatically set by the API client's auth callback
  // which reads the token from localStorage

  const login = useCallback(async (username: string, password: string) => {
    try {
      const response = await loginApiV1AuthLoginPost({
        client: apiClient,
        body: {
          username,
          password,
        },
      })

      if (response.error) {
        const errorMessage = extractErrorMessage(response.error, 'Login failed')
        throw new Error(errorMessage)
      }

      if (response.data) {
        const { access_token } = response.data
        
        // Store token
        localStorage.setItem('auth_token', access_token)
        setToken(access_token)

        // Fetch user info
        const userResponse = await getCurrentUserInfoApiV1AuthMeGet({
          client: apiClient,
        })

        if (userResponse.data) {
          setUser(userResponse.data)
        }
      }
    } catch (error: any) {
      console.error('Login failed:', error)
      const message = extractErrorMessage(error, 'Login failed')
      throw new Error(message)
    }
  }, [])

  const register = useCallback(async (email: string, username: string, password: string) => {
    try {
      const response = await registerApiV1AuthRegisterPost({
        client: apiClient,
        body: {
          email,
          username,
          password,
        },
      })

      if (response.error) {
        const errorMessage = extractErrorMessage(response.error, 'Registration failed')
        throw new Error(errorMessage)
      }

      // After successful registration, log the user in
      await login(username, password)
    } catch (error: any) {
      console.error('Registration failed:', error)
      const message = extractErrorMessage(error, 'Registration failed')
      throw new Error(message)
    }
  }, [login])

  const logout = useCallback(() => {
    localStorage.removeItem('auth_token')
    setToken(null)
    setUser(null)
    router.push('/login')
  }, [router])

  const value: AuthContextType = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!token && !!user,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
