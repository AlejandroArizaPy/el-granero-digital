// Los códigos cortos son los valores guardados y devueltos por Django.
export const ORDER_STATUS_LABELS = Object.freeze({
  PDT: 'Pendiente',
  ENP: 'En preparación',
  CPO: 'Completado',
  CLO: 'Cancelado',
})

const ORDER_ACTIONS_BY_STATUS = Object.freeze({
  // La interfaz oculta acciones inválidas; el backend vuelve a validar cada transición.
  PDT: ['confirmar', 'cancelar'],
  ENP: ['completar', 'cancelar'],
})

export const ORDER_ACTION_LABELS = Object.freeze({
  confirmar: 'Confirmar pedido',
  cancelar: 'Cancelar pedido',
  completar: 'Marcar como completado',
})

export function getOrderStatusLabel(status) {
  return ORDER_STATUS_LABELS[status] || status || 'Estado no disponible'
}

export function getAvailableOrderActions(role, status) {
  if (role !== 'campesino') return []
  return ORDER_ACTIONS_BY_STATUS[status] || []
}

export function getPaymentMethodLabel(method) {
  if (method === 'EFO') return 'Efectivo contraentrega'
  if (method === 'TRF') return 'Transferencia bancaria'
  return method || 'No disponible'
}

export function formatOrderDate(value) {
  if (!value) return 'Fecha no disponible'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return new Intl.DateTimeFormat('es-CO', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}
