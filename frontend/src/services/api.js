const ACCESS_TOKEN_KEY = 'granero.access'
const REFRESH_TOKEN_KEY = 'granero.refresh'

// Accede a localStorage con protección para SSR o navegadores que lo bloqueen.
function getStorage() {
  if (typeof window === 'undefined') return null

  try {
    return window.localStorage
  } catch {
    return null
  }
}

export function getAccessToken() {
  return getStorage()?.getItem(ACCESS_TOKEN_KEY) ?? null
}

export function saveTokens(tokens) {
  const storage = getStorage()
  if (!storage) return

  if (tokens.access) storage.setItem(ACCESS_TOKEN_KEY, tokens.access)
  if (tokens.refresh) storage.setItem(REFRESH_TOKEN_KEY, tokens.refresh)
}

export function clearTokens() {
  const storage = getStorage()
  storage?.removeItem(ACCESS_TOKEN_KEY)
  storage?.removeItem(REFRESH_TOKEN_KEY)
}

function notifySessionExpired() {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event('granero:session-expired'))
  }
}

function describeErrorContent(data) {
  if (typeof data === 'string' && data) return data
  if (Array.isArray(data)) return data.map(describeErrorContent).filter(Boolean).join(' ')
  if (!data || typeof data !== 'object') return ''

  const detail = data.detail ?? data.message
  if (detail) return describeErrorContent(detail)

  return Object.entries(data)
    .map(([field, errors]) => {
      const description = describeErrorContent(errors)
      return description ? `${field}: ${description}` : ''
    })
    .filter(Boolean)
    .join(' ')
}

async function readResponse(response) {
  // Algunas respuestas correctas, como DELETE, no incluyen cuerpo.
  if (response.status === 204 || response.status === 205) return null

  const content = await response.text()
  if (!content) return null

  const contentType = response.headers.get('Content-Type') || ''
  if (contentType.includes('json')) {
    try {
      return JSON.parse(content)
    } catch {
      return content
    }
  }

  return content
}

/** Error HTTP que conserva el estado y el contenido devuelto por el backend. */
export class ApiError extends Error {
  constructor(status, data, statusText) {
    const message = describeErrorContent(data)
      || statusText
      || `Error HTTP ${status}`

    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

export function getApiErrorMessage(error) {
  if (error instanceof ApiError) return error.message
  if (error instanceof TypeError) {
    return 'No fue posible conectar con el servidor. Verifica que Django esté en ejecución.'
  }
  return error?.message || 'Ocurrió un error inesperado.'
}

let refreshRequest = null

async function refreshAccessToken() {
  // Las solicitudes simultáneas comparten una sola renovación del token.
  if (refreshRequest) return refreshRequest

  const refresh = getStorage()?.getItem(REFRESH_TOKEN_KEY)
  if (!refresh) return null

  refreshRequest = (async () => {
    const response = await fetch('/api/token/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    })
    const data = await readResponse(response)

    if (!response.ok || !data?.access) {
      if (response.status === 401 || response.status === 400) {
        clearTokens()
        notifySessionExpired()
      }
      throw new ApiError(response.status, data, response.statusText)
    }

    saveTokens(data)
    return data.access
  })()

  try {
    return await refreshRequest
  } finally {
    refreshRequest = null
  }
}

/**
 * Realiza una solicitud al backend y devuelve el estado HTTP junto con su contenido.
 * Los objetos y arreglos se envían como JSON; FormData se conserva para cargas de archivos.
 */
export async function apiRequest(path, options = {}) {
  const {
    method = 'GET',
    headers = {},
    body,
    auth = true,
    ...fetchOptions
  } = options

  const requestHeaders = new Headers(headers)
  let requestBody = body

  const isFormData = typeof FormData !== 'undefined' && body instanceof FormData
  const isUrlSearchParams = typeof URLSearchParams !== 'undefined'
    && body instanceof URLSearchParams
  const isBlob = typeof Blob !== 'undefined' && body instanceof Blob
  const isArrayBuffer = typeof ArrayBuffer !== 'undefined'
    && (body instanceof ArrayBuffer || ArrayBuffer.isView(body))
  const isNativeBody = isFormData || isUrlSearchParams || isBlob || isArrayBuffer

  // Los objetos se serializan como JSON; FormData conserva el boundary del navegador.
  if (body !== undefined && body !== null && typeof body === 'object' && !isNativeBody) {
    if (!requestHeaders.has('Content-Type')) {
      requestHeaders.set('Content-Type', 'application/json')
    }
    requestBody = JSON.stringify(body)
  }

  const requestOptions = {
    ...fetchOptions,
    method,
    headers: requestHeaders,
    ...(requestBody === undefined || requestBody === null ? {} : { body: requestBody }),
  }

  const accessToken = auth ? getAccessToken() : null
  // El header solo se agrega si la solicitud no lo especificó explícitamente.
  if (accessToken && !requestHeaders.has('Authorization')) {
    requestHeaders.set('Authorization', `Bearer ${accessToken}`)
  }

  let response = await fetch(path, requestOptions)
  const isRefreshRequest = path.split('?')[0].endsWith('/api/token/refresh/')

  if (response.status === 401 && auth && !isRefreshRequest) {
    // Ante un access vencido, renueva y repite la solicitud una sola vez.
    const hasRefreshToken = Boolean(getStorage()?.getItem(REFRESH_TOKEN_KEY))
    const refreshedAccessToken = await refreshAccessToken()
    if (refreshedAccessToken) {
      requestHeaders.set('Authorization', `Bearer ${refreshedAccessToken}`)
      response = await fetch(path, requestOptions)
      if (response.status === 401) {
        clearTokens()
        notifySessionExpired()
      }
    } else if (!hasRefreshToken) {
      clearTokens()
      notifySessionExpired()
    }
  }

  const data = await readResponse(response)

  if (!response.ok) {
    throw new ApiError(response.status, data, response.statusText)
  }

  return { status: response.status, data }
}
