import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import {
  addProductToCart,
  calculateCartItemCount,
  calculateCartSubtotal,
  readCart,
  removeCartItem,
  updateCartQuantity,
  writeCart,
} from './cartUtils'

const CartContext = createContext(null)

function loadCart() {
  // El carrito se restaura al abrir la aplicación y se tolera almacenamiento bloqueado.
  try {
    return readCart(typeof window === 'undefined' ? null : window.localStorage)
  } catch {
    return []
  }
}

export function CartProvider({ children }) {
  const [items, setItems] = useState(loadCart)

  useEffect(() => {
    // Mantiene la copia local sincronizada cada vez que cambian los productos o cantidades.
    try {
      writeCart(typeof window === 'undefined' ? null : window.localStorage, items)
    } catch {
      // El carrito permanece disponible en memoria si localStorage no está accesible.
    }
  }, [items])

  const addItem = useCallback((product, quantity = 1) => {
    // La utilidad también comprueba stock y que todos los productos sean del mismo vendedor.
    const result = addProductToCart(items, product, quantity)
    if (result.error) return { ok: false, message: result.error }
    setItems(result.items)
    return { ok: true }
  }, [items])

  const updateQuantity = useCallback((id, quantity) => {
    setItems((currentItems) => updateCartQuantity(currentItems, id, quantity))
  }, [])

  const removeItem = useCallback((id) => {
    setItems((currentItems) => removeCartItem(currentItems, id))
  }, [])

  const clearCart = useCallback(() => setItems([]), [])
  // Se deriva de items para que el contador nunca quede desincronizado.
  const itemCount = useMemo(() => calculateCartItemCount(items), [items])
  const subtotal = useMemo(() => calculateCartSubtotal(items), [items])
  const value = useMemo(() => ({
    items,
    itemCount,
    subtotal,
    addItem,
    updateQuantity,
    removeItem,
    clearCart,
  }), [items, itemCount, subtotal, addItem, updateQuantity, removeItem, clearCart])

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useCart() {
  const context = useContext(CartContext)
  if (!context) throw new Error('useCart debe usarse dentro de CartProvider.')
  return context
}
