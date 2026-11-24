import assert from 'node:assert/strict'
import test from 'node:test'

import {
  formatOrderDate,
  getAvailableOrderActions,
  getOrderStatusLabel,
  getPaymentMethodLabel,
} from './orderUtils.js'

test('muestra etiquetas para los estados y métodos de pago del backend', () => {
  assert.equal(getOrderStatusLabel('PDT'), 'Pendiente')
  assert.equal(getOrderStatusLabel('ENP'), 'En preparación')
  assert.equal(getOrderStatusLabel('CPO'), 'Completado')
  assert.equal(getOrderStatusLabel('CLO'), 'Cancelado')
  assert.equal(getPaymentMethodLabel('EFO'), 'Efectivo contraentrega')
  assert.equal(getPaymentMethodLabel('TRF'), 'Transferencia bancaria')
})

test('solo muestra al campesino acciones válidas para el estado actual', () => {
  assert.deepEqual(getAvailableOrderActions('comprador', 'PDT'), [])
  assert.deepEqual(getAvailableOrderActions('campesino', 'PDT'), ['confirmar', 'cancelar'])
  assert.deepEqual(getAvailableOrderActions('campesino', 'ENP'), ['completar', 'cancelar'])
  assert.deepEqual(getAvailableOrderActions('campesino', 'CPO'), [])
  assert.deepEqual(getAvailableOrderActions('campesino', 'CLO'), [])
})

test('formatea fecha disponible y tolera fecha ausente o inválida', () => {
  assert.match(formatOrderDate('2026-11-23T12:00:00Z'), /2026/)
  assert.equal(formatOrderDate(null), 'Fecha no disponible')
  assert.equal(formatOrderDate('fecha-invalida'), 'fecha-invalida')
})
