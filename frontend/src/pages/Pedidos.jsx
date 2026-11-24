import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { Footer } from '../components/Footer'
import { Header } from '../components/Header'
import { useAuth } from '../context/AuthContext'
import { apiRequest, getApiErrorMessage } from '../services/api'
import { formatCurrency } from '../utils/format'
import {
  formatOrderDate,
  getAvailableOrderActions,
  getOrderStatusLabel,
  getPaymentMethodLabel,
  ORDER_ACTION_LABELS,
} from './orderUtils'

function PedidoDetalles({ pedido }) {
  return (
    <ul className="detalles-pedido">
      {pedido.detalles?.map((detalle) => (
        <li key={detalle.producto}>
          <span>
            {detalle.producto_nombre || `Producto #${detalle.producto}`} × {detalle.cantidad}
          </span>
          {detalle.subtotal !== undefined && (
            <span>{formatCurrency(detalle.subtotal)}</span>
          )}
        </li>
      ))}
    </ul>
  )
}

export function ListaPedidos({ tipo }) {
  const esCampesino = tipo === 'campesino'
  const [pedidos, setPedidos] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const cargarPedidos = useCallback(async (signal) => {
    try {
      // El backend filtra esta lista por comprador o vendedor según el JWT.
      const { data } = await apiRequest('/ordenes/api/', { signal })
      setPedidos(Array.isArray(data) ? data : [])
    } catch (requestError) {
      if (requestError.name !== 'AbortError') {
        setError(getApiErrorMessage(requestError))
      }
    } finally {
      if (!signal?.aborted) setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    // Inicia la carga de datos de la vista al montarla.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    cargarPedidos(controller.signal)
    return () => controller.abort()
  }, [cargarPedidos])

  const actualizar = () => {
    setIsLoading(true)
    setError('')
    cargarPedidos()
  }

  return (
    <>
      <Header />
      <main className="container-checkout pedidos-page">
        <h2>{esCampesino ? 'Pedidos recibidos' : 'Mis pedidos'}</h2>
        <div className="pedidos-acciones-cabecera">
          <button type="button" onClick={actualizar} disabled={isLoading}>
            Actualizar
          </button>
        </div>
        {isLoading && <p role="status">Cargando pedidos…</p>}
        {error && <p className="form-error" role="alert">{error}</p>}
        {!isLoading && !error && pedidos.length === 0 && (
          <p role="status">
            {esCampesino ? 'Todavía no has recibido pedidos.' : 'Todavía no tienes pedidos.'}
          </p>
        )}
        <section className="lista-pedidos" aria-label="Pedidos">
          {pedidos.map((pedido) => (
            <article className="pedido-resumen" key={pedido.id}>
              <h3>Pedido #{pedido.id}</h3>
              <p><strong>Fecha:</strong> {formatOrderDate(pedido.fecha)}</p>
              <p>
                <strong>Estado:</strong>{' '}
                <span className={`estado-pedido estado-${pedido.estado}`}>
                  {getOrderStatusLabel(pedido.estado)}
                </span>
              </p>
              {esCampesino && (
                <p><strong>Comprador:</strong> {pedido.comprador_nombre || `Comprador #${pedido.comprador}`}</p>
              )}
              <PedidoDetalles pedido={pedido} />
              <p><strong>Total:</strong> {formatCurrency(pedido.total)}</p>
              <Link className="btn" to={`/pedidos/${pedido.id}`}>Ver pedido</Link>
            </article>
          ))}
        </section>
      </main>
      <Footer />
    </>
  )
}

export function DetallePedido() {
  const { id } = useParams()
  const { user } = useAuth()
  const [pedido, setPedido] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [busyAction, setBusyAction] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const actionInProgress = useRef(false)

  const cargarPedido = useCallback(async (signal) => {
    setError('')
    try {
      const { data } = await apiRequest(`/ordenes/api/${id}/`, { signal })
      setPedido(data)
    } catch (requestError) {
      if (requestError.name !== 'AbortError') {
        setError(getApiErrorMessage(requestError))
      }
    } finally {
      if (!signal?.aborted) setIsLoading(false)
    }
  }, [id])

  useEffect(() => {
    const controller = new AbortController()
    // Carga el identificador actual al navegar entre pedidos.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIsLoading(true)
    setPedido(null)
    cargarPedido(controller.signal)
    return () => controller.abort()
  }, [cargarPedido])

  const ejecutarAccion = async (accion) => {
    // El bloqueo local evita dos clics; el backend vuelve a validar propietario y estado.
    if (actionInProgress.current || !pedido) return
    actionInProgress.current = true
    setBusyAction(accion)
    setError('')
    setMessage('')

    try {
      const { data } = await apiRequest(`/ordenes/api/${pedido.id}/${accion}/`, {
        method: 'POST',
      })
      setPedido(data)
      setMessage(`Pedido actualizado: ${getOrderStatusLabel(data.estado)}.`)
    } catch (requestError) {
      setError(getApiErrorMessage(requestError))
    } finally {
      actionInProgress.current = false
      setBusyAction('')
    }
  }

  const acciones = getAvailableOrderActions(user?.rol, pedido?.estado)
  const volverA = user?.rol === 'campesino' ? '/pedidos-recibidos' : '/mis-pedidos'

  return (
    <>
      <Header />
      <main className="container-checkout pedidos-page">
        <h2>Detalle del pedido</h2>
        {isLoading && <p role="status">Cargando pedido…</p>}
        {error && <p className="form-error" role="alert">{error}</p>}
        {!isLoading && !error && pedido && (
          <article className="pedido-detalle">
            <h3>Pedido #{pedido.id}</h3>
            <p><strong>Fecha:</strong> {formatOrderDate(pedido.fecha)}</p>
            <p><strong>Estado:</strong> {getOrderStatusLabel(pedido.estado)}</p>
            {user?.rol === 'campesino' && (
              <p><strong>Comprador:</strong> {pedido.comprador_nombre || `Comprador #${pedido.comprador}`}</p>
            )}
            <p><strong>Dirección:</strong> {pedido.direccion_entrega}</p>
            <p><strong>Ciudad:</strong> {pedido.ciudad}</p>
            <p><strong>Método de pago:</strong> {getPaymentMethodLabel(pedido.metodo_pago)}</p>
            <h4>Productos</h4>
            <PedidoDetalles pedido={pedido} />
            <p><strong>Total:</strong> {formatCurrency(pedido.total)}</p>
            {message && <p role="status">{message}</p>}
            {acciones.length > 0 && (
              <div className="acciones-pedido">
                {acciones.map((accion) => (
                  <button
                    key={accion}
                    type="button"
                    className={accion === 'cancelar' ? 'accion-secundaria' : ''}
                    onClick={() => ejecutarAccion(accion)}
                    disabled={Boolean(busyAction)}
                  >
                    {busyAction === accion ? 'Actualizando…' : ORDER_ACTION_LABELS[accion]}
                  </button>
                ))}
              </div>
            )}
          </article>
        )}
        <div className="pedidos-acciones-cabecera">
          <Link className="volver" to={volverA}>Volver a pedidos</Link>
          <button type="button" onClick={() => cargarPedido()} disabled={isLoading || Boolean(busyAction)}>
            Actualizar detalle
          </button>
        </div>
      </main>
      <Footer />
    </>
  )
}
