import { Link, useLocation } from 'react-router-dom';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { formatCurrency } from '../utils/format';

const estadoPedido = {
  PDT: 'Pendiente',
  ENP: 'En preparación',
  CPO: 'Completado',
  CLO: 'Cancelado',
};

function getPedido(locationState) {
  // La navegación inmediata usa route state; sessionStorage permite recargar la página.
  if (locationState?.pedido) return locationState.pedido;
  try {
    return JSON.parse(sessionStorage.getItem('granero.lastOrder') || 'null');
  } catch {
    return null;
  }
}

export const CompraConfirmada = () => {
  const location = useLocation();
  const pedido = getPedido(location.state);

  return (
    <>
      <Header />
      <main className="container-pedido">
        {pedido ? (
          <div className="card-pedido">
            <div className="icono-pedido" aria-hidden="true">✓</div>
            <h2>¡Pedido creado correctamente!</h2>
            <div className="info-pedido">
              <p>
                El pedido fue registrado y está pendiente de confirmación por el campesino.
              </p>
              <p><strong>Número de pedido:</strong> #{pedido.id}</p>
              <p><strong>Estado:</strong> {estadoPedido[pedido.estado] || pedido.estado}</p>
              {pedido.total !== undefined && (
                <p><strong>Total registrado:</strong> {formatCurrency(pedido.total)}</p>
              )}
            </div>
          </div>
        ) : (
          <div className="card-pedido">
            <h2>No hay una confirmación reciente</h2>
            <p>Los datos del pedido no están disponibles en esta sesión.</p>
          </div>
        )}

        <div className="botones-pedido">
          <Link to="/catalogo" className="btn-pedido">Volver al catálogo</Link>
          <Link to="/" className="btn-pedido">Volver al inicio</Link>
        </div>
      </main>
      <Footer />
    </>
  );
};
