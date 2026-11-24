import { useCallback, useEffect, useMemo, useState } from 'react'

import { Footer } from '../components/Footer'
import { Header } from '../components/Header'
import { useAuth } from '../context/AuthContext'
import { formatCurrency } from '../utils/format'
import { apiRequest, getApiErrorMessage } from '../services/api'
import { formatOrderDate, getOrderStatusLabel, getPaymentMethodLabel } from './orderUtils'
import {
  buildProductIndex,
  getAdminMetrics,
  getOrderSellerName,
  getProductOwnerName,
  getRoleLabel,
} from './adminUtils'

const TABS = [
  { id: 'resumen', label: 'Resumen' },
  { id: 'usuarios', label: 'Usuarios' },
  { id: 'productos', label: 'Productos' },
  { id: 'pedidos', label: 'Pedidos' },
]

const EMPTY_DATA = { users: [], products: [], orders: [] }

function StatusBadge({ active }) {
  return (
    <span className={'admin-status ' + (active ? 'admin-status--active' : 'admin-status--inactive')}>
      {active ? 'Activo' : 'Inactivo'}
    </span>
  )
}

function OrderDetailsDialog({ order, sellerName, isLoading, error, onClose }) {
  useEffect(() => {
    if (!order) return undefined

    const closeOnEscape = (event) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [order, onClose])

  if (!order) return null

  return (
    <div
      className="admin-dialog-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <section
        className="admin-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="admin-order-dialog-title"
      >
        <div className="admin-dialog-heading">
          <div>
            <p className="admin-eyebrow">Consulta de pedido</p>
            <h2 id="admin-order-dialog-title">Pedido #{order.id}</h2>
          </div>
          <button className="admin-icon-button" type="button" onClick={onClose} aria-label="Cerrar detalle">
            <span aria-hidden="true">×</span>
          </button>
        </div>

        <div className="admin-order-meta">
          <p><strong>Comprador:</strong> {order.comprador_nombre || 'Comprador #' + order.comprador}</p>
          <p><strong>Campesino:</strong> {sellerName}</p>
          <p><strong>Fecha:</strong> {formatOrderDate(order.fecha)}</p>
          <p>
            <strong>Estado:</strong>{' '}
            <span className={'estado-pedido estado-' + order.estado}>
              {getOrderStatusLabel(order.estado)}
            </span>
          </p>
          <p><strong>Entrega:</strong> {order.direccion_entrega}, {order.ciudad}</p>
          <p><strong>Pago:</strong> {getPaymentMethodLabel(order.metodo_pago)}</p>
        </div>

        {isLoading && <p className="admin-loading" role="status">Actualizando detalle del pedido…</p>}
        {error && <p className="admin-alert" role="alert">{error}</p>}

        <h3>Productos del pedido</h3>
        <div className="admin-table-wrap">
          <table className="admin-table admin-detail-table">
            <thead>
              <tr><th>Producto</th><th>Cantidad</th><th>Precio histórico</th><th>Subtotal</th></tr>
            </thead>
            <tbody>
              {order.detalles?.map((detail) => (
                <tr key={detail.producto}>
                  <td>{detail.producto_nombre || 'Producto #' + detail.producto}</td>
                  <td>{detail.cantidad}</td>
                  <td>{formatCurrency(detail.precio_unitario)}</td>
                  <td>{formatCurrency(detail.subtotal)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="admin-order-total"><strong>Total:</strong> {formatCurrency(order.total)}</p>
        <p className="admin-readonly-note">Este panel permite consultar pedidos; su estado e inventario se gestionan en el flujo del campesino.</p>
      </section>
    </div>
  )
}

export function AdminPanel() {
  const { user } = useAuth()
  const [data, setData] = useState(EMPTY_DATA)
  const [activeTab, setActiveTab] = useState('resumen')
  const [isLoading, setIsLoading] = useState(true)
  const [hasLoaded, setHasLoaded] = useState(false)
  const [error, setError] = useState('')
  const [operationError, setOperationError] = useState('')
  const [pendingActions, setPendingActions] = useState({})
  const [selectedOrder, setSelectedOrder] = useState(null)
  const [orderDetailLoading, setOrderDetailLoading] = useState(false)
  const [orderDetailError, setOrderDetailError] = useState('')
  const selectedOrderId = selectedOrder?.id

  const loadData = useCallback(async (signal) => {
    setError('')
    try {
      // Tres lecturas reúnen los datos para el resumen y las secciones del panel.
      const [usersResponse, productsResponse, ordersResponse] = await Promise.all([
        apiRequest('/usuarios/api/', { signal }),
        apiRequest('/productos/api/administracion/', { signal }),
        apiRequest('/ordenes/api/', { signal }),
      ])

      if (![usersResponse.data, productsResponse.data, ordersResponse.data].every(Array.isArray)) {
        throw new Error('El servidor devolvió un formato de lista inesperado.')
      }
      if (signal?.aborted) return

      setData({
        users: usersResponse.data,
        products: productsResponse.data,
        orders: ordersResponse.data,
      })
      setHasLoaded(true)
    } catch (requestError) {
      if (requestError.name !== 'AbortError' && !signal?.aborted) {
        setError(getApiErrorMessage(requestError))
      }
    } finally {
      if (!signal?.aborted) setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    Promise.resolve().then(() => loadData(controller.signal))
    return () => controller.abort()
  }, [loadData])

  useEffect(() => {
    if (!selectedOrderId) return undefined

    const controller = new AbortController()
    apiRequest('/ordenes/api/' + selectedOrderId + '/', { signal: controller.signal })
      .then((response) => {
        setSelectedOrder((current) => (
          current?.id === selectedOrderId ? response.data : current
        ))
      })
      .catch((requestError) => {
        if (!controller.signal.aborted) setOrderDetailError(getApiErrorMessage(requestError))
      })
      .finally(() => {
        if (!controller.signal.aborted) setOrderDetailLoading(false)
      })

    return () => controller.abort()
  }, [selectedOrderId])

  const productsById = useMemo(() => buildProductIndex(data.products), [data.products])
  const metrics = useMemo(
    () => getAdminMetrics(data.users, data.products, data.orders),
    [data],
  )

  const refreshData = () => {
    setIsLoading(true)
    setOperationError('')
    loadData()
  }

  const runAccountAction = async (account, activate) => {
    const key = 'user-' + account.id
    if (pendingActions[key]) return
    if (!activate && !window.confirm('¿Desactivar la cuenta de ' + account.username + '?')) return

    const action = activate ? 'activar' : 'desactivar'
    setPendingActions((current) => ({ ...current, [key]: true }))
    setOperationError('')
    try {
      const response = await apiRequest(
        '/usuarios/api/' + account.id + '/' + action + '/',
        { method: 'POST' },
      )
      const updatedAccount = response.data
      setData((current) => ({
        ...current,
        users: current.users.map((user) => (
          user.id === updatedAccount.id ? updatedAccount : user
        )),
      }))
    } catch (requestError) {
      setOperationError(getApiErrorMessage(requestError))
    } finally {
      setPendingActions((current) => ({ ...current, [key]: false }))
    }
  }

  const runProductAction = async (product, activate) => {
    const key = 'product-' + product.id
    if (pendingActions[key]) return
    if (!activate && !window.confirm('¿Desactivar la publicación “' + product.nombre + '”?')) return

    const action = activate ? 'activar' : 'desactivar'
    setPendingActions((current) => ({ ...current, [key]: true }))
    setOperationError('')
    try {
      const response = await apiRequest(
        '/productos/api/' + product.id + '/' + action + '/',
        { method: 'POST' },
      )
      const updatedProduct = response.data
      setData((current) => ({
        ...current,
        products: current.products.map((item) => (
          item.id === updatedProduct.id ? updatedProduct : item
        )),
      }))
    } catch (requestError) {
      setOperationError(getApiErrorMessage(requestError))
    } finally {
      setPendingActions((current) => ({ ...current, [key]: false }))
    }
  }

  const openOrderDetail = (order) => {
    setSelectedOrder(order)
    setOrderDetailLoading(true)
    setOrderDetailError('')
  }

  const closeOrderDetail = () => {
    setSelectedOrder(null)
    setOrderDetailLoading(false)
    setOrderDetailError('')
  }

  const renderUsers = () => (
    <section className="admin-section" aria-labelledby="admin-users-title">
      <div className="admin-section-heading">
        <div>
          <p className="admin-eyebrow">Cuentas de la plataforma</p>
          <h2 id="admin-users-title">Usuarios</h2>
        </div>
        <span className="admin-section-count">{data.users.length} cuentas</span>
      </div>
      {data.users.length === 0 ? (
        <p className="admin-empty">No hay usuarios para mostrar.</p>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr><th>Usuario</th><th>Nombre</th><th>Rol</th><th>Estado</th><th>Acción</th></tr>
            </thead>
            <tbody>
              {data.users.map((account) => {
                const isSelf = Number(account.id) === Number(user?.id)
                const busy = Boolean(pendingActions['user-' + account.id])
                return (
                  <tr key={account.id}>
                    <td className="admin-username">{account.username}</td>
                    <td>{[account.first_name, account.last_name].filter(Boolean).join(' ') || '—'}</td>
                    <td><span className={'admin-role admin-role--' + account.rol}>{getRoleLabel(account.rol)}</span></td>
                    <td><StatusBadge active={account.is_active} /></td>
                    <td>
                      {isSelf ? (
                        <span className="admin-self-note" title="No puedes desactivar tu propia cuenta.">Tu cuenta</span>
                      ) : (
                        <button
                          className={'admin-action-button ' + (account.is_active ? 'admin-action-button--danger' : '')}
                          type="button"
                          disabled={busy}
                          onClick={() => runAccountAction(account, !account.is_active)}
                        >
                          {busy ? 'Guardando…' : account.is_active ? 'Desactivar' : 'Activar'}
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )

  const renderProducts = () => (
    <section className="admin-section" aria-labelledby="admin-products-title">
      <div className="admin-section-heading">
        <div>
          <p className="admin-eyebrow">Publicaciones de campesinos</p>
          <h2 id="admin-products-title">Productos</h2>
        </div>
        <span className="admin-section-count">{data.products.length} publicaciones</span>
      </div>
      {data.products.length === 0 ? (
        <p className="admin-empty">No hay productos para mostrar.</p>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr><th>Producto</th><th>Precio</th><th>Stock</th><th>Campesino</th><th>Categoría</th><th>Estado</th><th>Acción</th></tr>
            </thead>
            <tbody>
              {data.products.map((product) => {
                const busy = Boolean(pendingActions['product-' + product.id])
                return (
                  <tr key={product.id}>
                    <td className="admin-product-name">{product.nombre}</td>
                    <td>{formatCurrency(product.precio)}</td>
                    <td>{product.stock}</td>
                    <td>{getProductOwnerName(product)}</td>
                    <td>{product.categoria_nombre || 'Categoría #' + product.categoria}</td>
                    <td><StatusBadge active={product.activo} /></td>
                    <td>
                      <button
                        className={'admin-action-button ' + (product.activo ? 'admin-action-button--danger' : '')}
                        type="button"
                        disabled={busy}
                        onClick={() => runProductAction(product, !product.activo)}
                      >
                        {busy ? 'Guardando…' : product.activo ? 'Desactivar' : 'Activar'}
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
      <p className="admin-readonly-note">El panel solo cambia el estado de publicación; no edita precio, stock, propietario ni contenido.</p>
    </section>
  )

  const renderOrders = () => (
    <section className="admin-section" aria-labelledby="admin-orders-title">
      <div className="admin-section-heading">
        <div>
          <p className="admin-eyebrow">Actividad comercial</p>
          <h2 id="admin-orders-title">Pedidos</h2>
        </div>
        <span className="admin-section-count">{data.orders.length} pedidos</span>
      </div>
      {data.orders.length === 0 ? (
        <p className="admin-empty">Todavía no hay pedidos.</p>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr><th>Número</th><th>Comprador</th><th>Campesino</th><th>Fecha</th><th>Estado</th><th>Total</th><th>Detalle</th></tr>
            </thead>
            <tbody>
              {data.orders.map((order) => {
                const units = order.detalles?.reduce((total, detail) => total + Number(detail.cantidad), 0) || 0
                return (
                  <tr key={order.id}>
                    <td className="admin-username">#{order.id}</td>
                    <td>{order.comprador_nombre || 'Comprador #' + order.comprador}</td>
                    <td>{getOrderSellerName(order, productsById)}</td>
                    <td>{formatOrderDate(order.fecha)}</td>
                    <td><span className={'estado-pedido estado-' + order.estado}>{getOrderStatusLabel(order.estado)}</span></td>
                    <td>{formatCurrency(order.total)}</td>
                    <td>
                      <button className="admin-action-button" type="button" onClick={() => openOrderDetail(order)}>
                        Ver {units} {units === 1 ? 'unidad' : 'unidades'}
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
      <p className="admin-readonly-note">Consulta de solo lectura: no se muestran acciones para cambiar estados.</p>
    </section>
  )

  const tabContent = {
    resumen: (
      <>
        <section className="admin-metrics" aria-label="Indicadores del sistema">
          <article className="admin-metric-card">
            <span className="admin-metric-icon" aria-hidden="true">♙</span>
            <div><p>Usuarios</p><strong>{metrics.users}</strong></div>
          </article>
          <article className="admin-metric-card">
            <span className="admin-metric-icon" aria-hidden="true">▧</span>
            <div><p>Productos</p><strong>{metrics.products}</strong></div>
          </article>
          <article className="admin-metric-card">
            <span className="admin-metric-icon" aria-hidden="true">▤</span>
            <div><p>Pedidos</p><strong>{metrics.orders}</strong></div>
          </article>
          <article className="admin-metric-card admin-metric-card--pending">
            <span className="admin-metric-icon" aria-hidden="true">◷</span>
            <div><p>Pendientes</p><strong>{metrics.pendingOrders}</strong></div>
          </article>
        </section>
        <section className="admin-welcome-card">
          <p className="admin-eyebrow">Gestión de la plataforma</p>
          <h2>Bienvenido al panel administrativo</h2>
          <p>Consulta usuarios, publicaciones y pedidos. Las acciones disponibles respetan los permisos y flujos existentes.</p>
          <div className="admin-shortcuts">
            {TABS.slice(1).map((tab) => (
              <button type="button" key={tab.id} onClick={() => setActiveTab(tab.id)}>
                Ver {tab.label.toLowerCase()} <span aria-hidden="true">→</span>
              </button>
            ))}
          </div>
        </section>
      </>
    ),
    usuarios: renderUsers(),
    productos: renderProducts(),
    pedidos: renderOrders(),
  }

  return (
    <>
      <Header />
      <main className="admin-page">
        <header className="admin-page-heading">
          <div>
            <p className="admin-eyebrow">El Granero Digital · Administración</p>
            <h1>Panel de control</h1>
            <p>Supervisa cuentas, publicaciones y pedidos de la plataforma.</p>
          </div>
          <button className="admin-refresh-button" type="button" onClick={refreshData} disabled={isLoading}>
            <span aria-hidden="true">↻</span> Actualizar datos
          </button>
        </header>

        {error && <p className="admin-alert" role="alert">{error}</p>}
        {operationError && <p className="admin-alert" role="alert">{operationError}</p>}
        {isLoading && <p className="admin-loading" role="status">Cargando información administrativa…</p>}

        {hasLoaded && (
          <>
            <nav className="admin-tabs" aria-label="Secciones administrativas">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  aria-pressed={activeTab === tab.id}
                  className={activeTab === tab.id ? 'admin-tab admin-tab--active' : 'admin-tab'}
                  onClick={() => {
                    setActiveTab(tab.id)
                    setOperationError('')
                  }}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
            {tabContent[activeTab]}
          </>
        )}

        {!isLoading && !hasLoaded && !error && (
          <p className="admin-empty" role="status">No fue posible cargar la información.</p>
        )}
      </main>
      <Footer />
      <OrderDetailsDialog
        order={selectedOrder}
        sellerName={selectedOrder ? getOrderSellerName(selectedOrder, productsById) : ''}
        isLoading={orderDetailLoading}
        error={orderDetailError}
        onClose={closeOrderDetail}
      />
    </>
  )
}
