export const ROLE_LABELS = Object.freeze({
  admin: 'Administrador',
  comprador: 'Comprador',
  campesino: 'Campesino',
})

export function getRoleLabel(role) {
  return ROLE_LABELS[role] || role || 'Rol no disponible'
}

export function getAdminMetrics(users, products, orders) {
  return {
    users: users.length,
    products: products.length,
    orders: orders.length,
    pendingOrders: orders.filter((order) => order.estado === 'PDT').length,
  }
}

export function getProductOwnerName(product) {
  const name = [product?.usuario?.first_name, product?.usuario?.last_name]
    .filter(Boolean)
    .join(' ')

  return name || `Campesino #${product?.usuario?.id ?? '—'}`
}

export function buildProductIndex(products) {
  return new Map(products.map((product) => [String(product.id), product]))
}

export function getOrderSellerName(order, productsById) {
  const product = order?.detalles
    ?.map((detail) => productsById.get(String(detail.producto)))
    .find(Boolean)

  return product
    ? getProductOwnerName(product)
    : `Campesino #${order?.vendedor ?? '—'}`
}
