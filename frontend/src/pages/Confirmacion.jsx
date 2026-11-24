import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { useCart } from '../context/CartContext';
import { apiRequest, getApiErrorMessage } from '../services/api';
import { formatCurrency } from '../utils/format';

export const Confirmacion = () => {
  const navigate = useNavigate();
  const { items, subtotal, clearCart } = useCart();
  const [direccionEntrega, setDireccionEntrega] = useState('');
  const [ciudad, setCiudad] = useState('');
  const [metodoPago, setMetodoPago] = useState('EFO');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleConfirm = async (event) => {
    event.preventDefault();
    if (items.length === 0) {
      setError('Agrega al menos un producto antes de crear el pedido.');
      return;
    }

    setError('');
    setIsSubmitting(true);
    try {
      // Solo se envían datos de entrega y cantidades; Django fija precios y total.
      const { data: pedido } = await apiRequest('/ordenes/api/', {
        method: 'POST',
        body: {
          direccion_entrega: direccionEntrega.trim(),
          ciudad: ciudad.trim(),
          metodo_pago: metodoPago,
          detalles: items.map((item) => ({
            producto: item.id,
            cantidad: item.cantidad,
          })),
        },
      });

      try {
        sessionStorage.setItem('granero.lastOrder', JSON.stringify(pedido));
      } catch {
        // La navegación conserva el pedido en route state si sessionStorage no está disponible.
      }
      // El carrito se vacía únicamente después de recibir una creación exitosa.
      clearCart();
      navigate('/compra-exitosa', { replace: true, state: { pedido } });
    } catch (requestError) {
      setError(getApiErrorMessage(requestError));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <Header />
      <main className="container-checkout">
        <h2>Confirmar pedido</h2>
        {items.length === 0 ? (
          <div>
            <p>Tu carrito está vacío.</p>
            <Link to="/catalogo" className="btn">Volver al catálogo</Link>
          </div>
        ) : (
          <div className="contenido-checkout">
            <form className="formulario-checkout" onSubmit={handleConfirm}>
              <h3>Datos de entrega</h3>
              <label htmlFor="direccion-entrega">Dirección de entrega *</label>
              <input
                id="direccion-entrega"
                name="direccion_entrega"
                type="text"
                value={direccionEntrega}
                onChange={(event) => setDireccionEntrega(event.target.value)}
                required
              />

              <label htmlFor="ciudad">Ciudad *</label>
              <input
                id="ciudad"
                name="ciudad"
                type="text"
                value={ciudad}
                onChange={(event) => setCiudad(event.target.value)}
                required
              />

              <label htmlFor="metodo-pago">Método de pago *</label>
              <select
                id="metodo-pago"
                name="metodo_pago"
                value={metodoPago}
                onChange={(event) => setMetodoPago(event.target.value)}
                required
              >
                <option value="EFO">Efectivo contraentrega</option>
                <option value="TRF">Transferencia bancaria</option>
              </select>

              {error && <p className="form-error" role="alert">{error}</p>}
              <button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Creando pedido…' : 'Crear pedido'}
              </button>
            </form>

            <section className="resumen-checkout" aria-label="Resumen del pedido">
              <h3>Resumen del pedido</h3>
              {items.map((item) => (
                <p key={item.id}>{item.nombre} × {item.cantidad}</p>
              ))}
              <p className="total-checkout">Subtotal: {formatCurrency(subtotal)}</p>
              <p>El total se calculará con los precios vigentes al crear el pedido.</p>
            </section>
          </div>
        )}
      </main>
      <Footer />
    </>
  );
};
