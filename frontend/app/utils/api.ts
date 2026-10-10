export interface ApiTokens {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
  expires_in: number
}

const accessKey = 'vu_api_access_token'
const refreshKey = 'vu_api_refresh_token'
let refreshInFlight: Promise<ApiTokens | null> | null = null

function storage(): Storage | null {
  return import.meta.client ? sessionStorage : null
}

export function getApiTokens(): ApiTokens | null {
  const store = storage()
  if (!store) return null
  const access = store.getItem(accessKey)
  const refresh = store.getItem(refreshKey)
  return access && refresh
    ? { access_token: access, refresh_token: refresh, token_type: 'bearer', expires_in: 0 }
    : null
}

export function saveApiTokens(tokens: ApiTokens | null) {
  const store = storage()
  if (!store) return
  if (!tokens) {
    store.removeItem(accessKey)
    store.removeItem(refreshKey)
    return
  }
  store.setItem(accessKey, tokens.access_token)
  store.setItem(refreshKey, tokens.refresh_token)
}

function apiBase(): string {
  const runtime =
    typeof useRuntimeConfig === 'function' ? useRuntimeConfig() : { public: { apiBase: '' } }
  return String(runtime.public.apiBase || '').replace(/\/$/, '')
}

export function isApiEnabled() {
  return Boolean(apiBase())
}

async function parseError(response: Response): Promise<Error> {
  let message = `API request failed (${response.status})`
  try {
    const body = await response.json()
    message = body?.error?.message || body?.detail || message
    if (Array.isArray(body?.detail))
      message = body.detail.map((item: { msg?: string }) => item.msg || '').join(', ')
  } catch {
    // Keep the status based message when the server did not return JSON.
  }
  return new Error(message)
}

async function refreshTokens(): Promise<ApiTokens | null> {
  if (refreshInFlight) return refreshInFlight
  const current = getApiTokens()
  if (!current) return null
  refreshInFlight = fetch(`${apiBase()}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: current.refresh_token }),
  })
    .then(async (response) => {
      if (!response.ok) return null
      const tokens = (await response.json()) as ApiTokens
      saveApiTokens(tokens)
      return tokens
    })
    .catch(() => null)
    .finally(() => {
      refreshInFlight = null
    })
  const tokens = await refreshInFlight
  if (!tokens) saveApiTokens(null)
  return tokens
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
  retry = true,
): Promise<T> {
  if (!isApiEnabled()) throw new Error('Backend API chưa được cấu hình.')
  const headers = new Headers(init.headers)
  if (init.body && !(init.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  const tokens = getApiTokens()
  if (tokens?.access_token) headers.set('Authorization', `Bearer ${tokens.access_token}`)
  const response = await fetch(`${apiBase()}${path}`, { ...init, headers })
  if (response.status === 401 && retry && tokens?.refresh_token) {
    const refreshed = await refreshTokens()
    if (refreshed) return apiRequest<T>(path, init, false)
  }
  if (!response.ok) throw await parseError(response)
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export async function loginApi<T = unknown>(username: string, password: string) {
  const body = new URLSearchParams({ username, password })
  const tokens = await apiRequest<ApiTokens>('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  })
  saveApiTokens(tokens)
  return apiRequest<T>('/auth/me')
}

export async function registerApi<T = unknown>(
  username: string,
  password: string,
  fullName: string,
) {
  await apiRequest('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username, password, full_name: fullName }),
  })
  // Registration creates the account but deliberately does not issue tokens.
  // Sign in immediately so the newly registered user has a usable session.
  return loginApi<T>(username, password)
}

export function clearApiSession() {
  saveApiTokens(null)
}
