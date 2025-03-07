import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { useState } from "react"

import { AxiosError } from "axios"
import {
  type Body_login_login_access_token as AccessToken,
  type ApiError,
  LoginService,
  type UserPublic,
  type UserRegister,
  UsersService,
} from "../client"
import useCustomToast from "./useCustomToast"

const isLoggedIn = () => {
  return localStorage.getItem("access_token") !== null
}

// Função para lidar com erros de autenticação
const handleAuthError = (err: ApiError | AxiosError) => {
  // Se for um erro de cliente (4xx), limpa as credenciais e redireciona
  if ('status' in err && err.status && err.status >= 400 && err.status < 500) {
    localStorage.removeItem("access_token")
    window.location.href = "/login"
    return true
  }
  
  // Se for um AxiosError com status 4xx
  if (err instanceof AxiosError && err.response && err.response.status >= 400 && err.response.status < 500) {
    localStorage.removeItem("access_token")
    window.location.href = "/login"
    return true
  }
  
  return false
}

const useAuth = () => {
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const showToast = useCustomToast()
  const queryClient = useQueryClient()
  const { data: user, isLoading } = useQuery<UserPublic | null, Error>({
    queryKey: ["currentUser"],
    queryFn: async () => {
      try {
        return await UsersService.readUserMe()
      } catch (err) {
        // Se for erro de cliente (4xx), trata adequadamente
        if (err instanceof AxiosError || 'status' in (err as any)) {
          const handled = handleAuthError(err as ApiError | AxiosError)
          if (handled) {
            showToast(
              "Session expired",
              "Your session has expired. Please login again.",
              "error",
            )
          }
        }
        throw err
      }
    },
    enabled: isLoggedIn(),
  })

  const signUpMutation = useMutation({
    mutationFn: (data: UserRegister) =>
      UsersService.registerUser({ requestBody: data }),

    onSuccess: () => {
      navigate({ to: "/login" })
      showToast(
        "Account created.",
        "Your account has been created successfully.",
        "success",
      )
    },
    onError: (err: ApiError) => {
      let errDetail = (err.body as any)?.detail

      if (err instanceof AxiosError) {
        errDetail = err.message
      }

      showToast("Something went wrong.", errDetail, "error")
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const login = async (data: AccessToken) => {
    const response = await LoginService.accessToken({
      formData: data,
    })
    localStorage.setItem("access_token", response.access_token)
  }

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      navigate({ to: "/" })
    },
    onError: (err: ApiError) => {
      let errDetail = (err.body as any)?.detail

      if (err instanceof AxiosError) {
        errDetail = err.message
      }

      if (Array.isArray(errDetail)) {
        errDetail = "Something went wrong"
      }

      setError(errDetail)
    },
  })

  const logout = () => {
    localStorage.removeItem("access_token")
    navigate({ to: "/" })
    window.location.reload()
  }

  return {
    signUpMutation,
    loginMutation,
    logout,
    user,
    isLoading,
    error,
    resetError: () => setError(null),
    isLoggedIn,
  }
}

export { isLoggedIn }
export default useAuth
