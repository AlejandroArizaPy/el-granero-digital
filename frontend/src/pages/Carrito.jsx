import { Link } from 'react-router-dom';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { useCart } from '../context/CartContext';
import { formatCurrency } from '../utils/format';

export const Carrito = () => {
  // El estado compartido mantiene cantidades y productos al cambiar de página.
  const { items, subtotal, updateQuantity, removeItem } = useCart();

  return (
    <>
      <Header />
      <main className="container">
        <h2>Mi carrito de compras</h2>
        {items.length === 0 ? (
          <div className="carrito-vacio">
            <p>Tu carrito está vacío.</p>
            <Link to="/catalogo" className="btn">Explorar productos</Link>
          </div>
        ) : (
          <div className="carrito">
            <p>Vendedor: {items[0].sellerName || 'Campesino'}</p>
            <table>
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>Cantidad</th>
                  <th>Precio unitario</th>
                  <th>Subtotal</th>
                  <th>Acción</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td>
                      {item.imagen && <img src={item.imagen} alt="" width="48" />}
                      {item.nombre}
                    </td>
                    <td>
                      <div className="cantidad-carrito">
                        <button
                          type="button"
                          onClick={() => updateQuantity(item.id, item.cantidad - 1)}
                          disabled={item.cantidad <= 1}
                          aria-label={`Disminuir ${item.nombre}`}
                        >-</button>
                        <span>{item.cantidad}</span>
                        <button
                          type="button"
                          onClick={() => updateQuantity(item.id, item.cantidad + 1)}
                          disabled={item.cantidad >= item.stock}
                          aria-label={`Aumentar ${item.nombre}`}
                        >+</button>
                      </div>
                    </td>
                    <td>{formatCurrency(item.precioUnitario)}</td>
                    <td>{formatCurrency(Number(item.precioUnitario) * item.cantidad)}</td>
                    <td>
                      <button type="button" onClick={() => removeItem(item.id)}>
                        Eliminar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="resumen">
              <h3>Resumen del pedido</h3>
              <p>Productos: {items.reduce((count, item) => count + item.cantidad, 0)}</p>
              <p><strong>Subtotal: {formatCurrency(subtotal)}</strong></p>
              <p>El total definitivo será calculado por el servidor al crear el pedido.</p>
              <Link to="/confirmacion" className="btn">Continuar compra</Link>
            </div>
          </div>
        )}
        <Link to="/catalogo" className="volver">Seguir comprando</Link>
      </main>
      <Footer />
    </>
  );
};
