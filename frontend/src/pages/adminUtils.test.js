import test from 'node:test'
import assert from 'node:assert/strict'

import {
  buildProductIndex,
  getAdminMetrics,
  getOrderSellerName,
  getProductOwnerName,
  getRoleLabel,
} from './adminUtils.js'

test('resume totales reales y pedidos pendientes PDT', () => {
  const metrics = getAdminMetrics(
    [{ id: 1 }, { id: 2 }],
    [{ id: 3 }],
    [{ id: 4, estado: 'PDT' }, { id: 5, estado: 'ENP' }, { id: 6, estado: 'PDT' }],
  )

  assert.deepEqual(metrics, {
    users: 2,
    products: 1,
    orders: 3,
    pendingOrders: 2,
  })
})

test('presenta roles conocidos y conserva un rol inesperado', () => {
  assert.equal(getRoleLabel('admin'), 'Administrador')
  assert.equal(getRoleLabel('comprador'), 'Comprador')
  assert.equal(getRoleLabel('campesino'), 'Campesino')
  assert.equal(getRoleLabel('otro'), 'otro')
})

test('obtiene el campesino desde los productos de un pedido', () => {
  const products = buildProductIndex([{
    id: 12,
    usuario: { id: 8, first_name: 'Duván', last_name: 'Guerra' },
  }])

  assert.equal(getOrderSellerName({ vendedor: 8, detalles: [{ producto: 12 }] }, products), 'Duván Guerra')
  assert.equal(getProductOwnerName({ usuario: { id: 8 } }), 'Campesino #8')
  assert.equal(getOrderSellerName({ vendedor: 8, detalles: [] }, products), 'Campesino #8')
})
