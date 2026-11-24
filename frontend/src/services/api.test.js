wimport assert from 'node:assert/strict'
import test from 'node:test'

import { ApiError, apiRequest } from './api.js'

function mockFetch(t, implementation) {
  const originalFetch = globalThis.fetch
  globalThis.fetch = implementation
  t.after(() => {
    globalThis.fetch = originalFetch
  })
}

function mockBrowserStorage(t, initialValues = {}) {
  const previousWindow = globalThis.window
  const values = new Map(Object.entries(initialValues))
  globalThis.window = {
    localStorage: {
      getItem: (key) => values.get(key) ?? null,
      setItem: (key, value) => values.set(key, String(value)),
      removeItem: (key) => values.delete(key),
    },
    dispatchEvent: () => true,
  }
  t.after(() => {
    if (previousWindow === undefined) delete globalThis.window
    else globalThis.window = previousWindow
  })
}

test('GET exitoso convierte la respuesta JSON y conserva el estado', async (t) => {
  mockFetch(t, async (path, options) => {
    assert.equal(path, '/productos/api/')
    assert.equal(options.method, 'GET')
    assert.equal('body' in options, false)

    return new Response(JSON.stringify([{ id: 1, nombre: 'Papa' }]), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    })
  })

  const result = await apiRequest('/productos/api/')

  assert.equal(result.status, 200)
  assert.deepEqual(result.data, [{ id: 1, nombre: 'Papa' }])
})

test('POST serializa el cuerpo JSON y configura Content-Type', async (t) => {
  const payload = { username: 'comprador', password: 'secreto' }

  mockFetch(t, async (_path, options) => {
    assert.equal(options.method, 'POST')
    assert.equal(new Headers(options.headers).get('Content-Type'), 'application/json')
    assert.equal(options.body, JSON.stringify(payload))

    return new Response(JSON.stringify({ id: 7 }), {
      status: 201,
      headers: { 'Content-Type': 'application/json' },
    })
  })

  const result = await apiRequest('/usuarios/api/', {
    method: 'POST',
    body: payload,
  })

  assert.equal(result.status, 201)
  assert.deepEqual(result.data, { id: 7 })
})

test('POST multipart conserva FormData y deja que fetch genere el boundary', async (t) => {
  mockBrowserStorage(t, { 'granero.access': 'token-campesino' })
  const formData = new FormData()
  formData.append('nombre', 'Papa')
  formData.append('imagen', new Blob(['imagen']), 'papa.png')

  mockFetch(t, async (_path, options) => {
    assert.equal(options.method, 'POST')
    assert.equal(options.body, formData)
    assert.equal(new Headers(options.headers).has('Content-Type'), false)
    assert.equal(
      new Headers(options.headers).get('Authorization'),
      'Bearer token-campesino',
    )

    return new Response(JSON.stringify({ id: 12 }), {
      status: 201,
      headers: { 'Content-Type': 'application/json' },
    })
  })

  const result = await apiRequest('/productos/api/', {
    method: 'POST',
    body: formData,
  })

  assert.equal(result.status, 201)
  assert.deepEqual(result.data, { id: 12 })
})

test('respuesta HTTP 401 expone estado y contenido de Django en ApiError', async (t) => {
  const errorBody = { detail: 'Credenciales no válidas.' }

  mockFetch(t, async () => new Response(JSON.stringify(errorBody), {
    status: 401,
    headers: { 'Content-Type': 'application/json' },
  }))

  await assert.rejects(
    apiRequest('/api/token/', { method: 'POST', body: {} }),
    (error) => {
      assert.ok(error instanceof ApiError)
      assert.equal(error.status, 401)
      assert.equal(error.message, errorBody.detail)
      assert.deepEqual(error.data, errorBody)
      return true
    },
  )
})

test('respuesta HTTP 400 conserva errores de validación de Django', async (t) => {
  const errorBody = { username: ['Este campo es obligatorio.'] }
  mockFetch(t, async () => new Response(JSON.stringify(errorBody), {
    status: 400,
    headers: { 'Content-Type': 'application/json' },
  }))

  await assert.rejects(
    apiRequest('/usuarios/api/', { method: 'POST', body: {} }),
    (error) => {
      assert.ok(error instanceof ApiError)
      assert.equal(error.status, 400)
      assert.deepEqual(error.data, errorBody)
      assert.match(error.message, /username/)
      return true
    },
  )
})

test('envía Bearer automáticamente y renueva el access token tras 401', async (t) => {
  mockBrowserStorage(t, {
    'granero.access': 'access-expirado',
    'granero.refresh': 'refresh-valido',
  })
  const authorizationHeaders = []
  let productRequestCount = 0

  mockFetch(t, async (path, options) => {
    if (path === '/productos/api/') {
      authorizationHeaders.push(options.headers.get('Authorization'))
      productRequestCount += 1
      if (productRequestCount === 1) {
        return new Response(JSON.stringify({ detail: 'Token expirado.' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        })
      }
      return new Response('[]', {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    }

    assert.equal(path, '/api/token/refresh/')
    assert.equal(new Headers(options.headers).get('Content-Type'), 'application/json')
    assert.deepEqual(JSON.parse(options.body), { refresh: 'refresh-valido' })
    return new Response(JSON.stringify({ access: 'access-nuevo' }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    })
  })

  const result = await apiRequest('/productos/api/')

  assert.equal(result.status, 200)
  assert.deepEqual(result.data, [])
  assert.deepEqual(authorizationHeaders, [
    'Bearer access-expirado',
    'Bearer access-nuevo',
  ])
})

test('respuesta vacía HTTP 204 devuelve contenido null', async (t) => {
  mockFetch(t, async () => new Response(null, { status: 204 }))

  const result = await apiRequest('/ordenes/api/1/', { method: 'DELETE' })

  assert.equal(result.status, 204)
  assert.equal(result.data, null)
})

test('error de conexión se propaga para que la página pueda manejarlo', async (t) => {
  const connectionError = new TypeError('Failed to fetch')
  mockFetch(t, async () => {
    throw connectionError
  })

  await assert.rejects(
    apiRequest('/productos/api/'),
    (error) => error === connectionError,
  )
})
