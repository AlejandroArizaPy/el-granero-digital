export function addProductToCart(items, product, quantity = 1) {
  // El pedido acepta un solo vendedor; su ID viene del producto del backend.
  const sellerId = product.usuario?.id
  if (sellerId === undefined || sellerId === null) {
    return { items, error: 'No se pudo identificar al vendedor del producto.' }
  }

  if (items.length && items[0].sellerId !== sellerId) {
    return {
      items,
      error: 'El pedido solo puede incluir productos de un mismo campesino. Vacía el carrito para cambiar de vendedor.',
    }
  }

  const existingItem = items.find((item) => item.id === product.id)
  const nextQuantity = (existingItem?.cantidad || 0) + quantity
  // Se evita superar el stock conocido antes de enviar el pedido al servidor.
  if (!Number.isInteger(quantity) || quantity < 1 || nextQuantity > Number(product.stock)) {
    return { items, error: 'La cantidad supera el stock disponible.' }
  }

  if (existingItem) {
    return {
      items: items.map((item) => (
        item.id === product.id
          ? { ...item, cantidad: nextQuantity }
          : item
      )),
      error: null,
    }
  }

  return {
    items: [...items, {
      id: product.id,
      nombre: product.nombre,
      precioUnitario: product.precio,
      imagen: product.imagen,
      stock: Number(product.stock),
      sellerId,
      sellerName: [product.usuario.first_name, product.usuario.last_name]
        .filter(Boolean)
        .join(' '),
      cantidad: quantity,
    }],
    error: null,
  }
}

export function updateCartQuantity(items, id, quantity) {
  return items.map((item) => {
    if (item.id !== id || item.stock < 1) return item
    const parsedQuantity = Number(quantity) || 1
    const cantidad = Math.min(item.stock, Math.max(1, Math.floor(parsedQuantity)))
    return { ...item, cantidad }
  })
}

export function removeCartItem(items, id) {
  return items.filter((item) => item.id !== id)
}

export function calculateCartSubtotal(items) {
  // Se redondea a centavos antes de sumar para reducir errores de punto flotante.
  const cents = items.reduce((sum, item) => (
    sum + Math.round(Number(item.precioUnitario) * 100) * item.cantidad
  ), 0)
  return cents / 100
}

export function calculateCartItemCount(items) {
  return items.reduce((total, item) => total + Number(item.cantidad || 0), 0)
}

export function readCart(storage) {
  try {
    const savedCart = JSON.parse(storage?.getItem('granero.cart') || '[]')
    return Array.isArray(savedCart) ? savedCart : []
  } catch {
    return []
  }
}

export function writeCart(storage, items) {
  try {
    storage?.setItem('granero.cart', JSON.stringify(items))
  } catch {
    // El flujo sigue disponible en memoria si el navegador bloquea el almacenamiento local.
  }
}
