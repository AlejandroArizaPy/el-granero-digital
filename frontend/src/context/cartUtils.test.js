import assert from 'node:assert/strict'
import test from 'node:test'

import {
  addProductToCart,
  calculateCartItemCount,
  calculateCartSubtotal,
  readCart,
  removeCartItem,
  updateCartQuantity,
  writeCart,
} from './cartUtils.js'

const producto = (id, vendedor, precio = '2.35', stock = 5) => ({
  id,
  nombre: `Producto ${id}`,
  precio,
  imagen: `/media/${id}.png`,
  stock,
  usuario: { id: vendedor, first_name: 'Ana', last_name: 'Campesina' },
})

test('agrega producto real conservando ID, vendedor, precio e imagen', () => {
  const result = addProductToCart([], producto(7, 20), 2)

  assert.equal(result.error, null)
  assert.deepEqual(result.items[0], {
    id: 7,
    nombre: 'Producto 7',
    precioUnitario: '2.35',
    imagen: '/media/7.png',
    stock: 5,
    sellerId: 20,
    sellerName: 'Ana Campesina',
    cantidad: 2,
  })
})

test('rechaza mezclar vendedores y conserva el contenido actual', () => {
  const original = addProductToCart([], producto(1, 20)).items
  const result = addProductToCart(original, producto(2, 21))

  assert.match(result.error, /mismo campesino/)
  assert.deepEqual(result.items, original)
})

test('limita cantidades al stock, calcula subtotal y permite eliminar', () => {
  const first = addProductToCart([], producto(1, 20, '2.35', 3), 2)
  const second = addProductToCart(first.items, producto(1, 20, '2.35', 3), 1)
  const overStock = addProductToCart(second.items, producto(1, 20, '2.35', 3), 1)
  const adjusted = updateCartQuantity(second.items, 1, 20)

  assert.match(overStock.error, /stock disponible/)
  assert.equal(adjusted[0].cantidad, 3)
  assert.equal(calculateCartSubtotal(adjusted), 7.05)
  assert.equal(calculateCartItemCount(adjusted), 3)
  assert.equal(calculateCartItemCount(removeCartItem(adjusted, 1)), 0)
  assert.deepEqual(removeCartItem(adjusted, 1), [])
})

test('persiste y restaura el carrito usando almacenamiento local', () => {
  const values = new Map()
  const storage = {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
  }
  const items = addProductToCart([], producto(9, 20), 2).items

  writeCart(storage, items)

  assert.deepEqual(readCart(storage), items)
  assert.deepEqual(readCart({ getItem: () => '{malformed' }), [])
})
