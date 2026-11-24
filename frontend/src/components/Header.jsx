// Importamos React para definir el componente funcional
// Importamos Link de React Router para cambiar de ruta sin recargar la página
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';

// Exportación nombrada directa para evitar errores de sintaxis
export const Header = () => {
  const { user, logout } = useAuth();
  const { clearCart, itemCount } = useCart();
  const navigate = useNavigate();

  const handleLogout = () => {
    // Se limpia el carrito para que no quede asociado a la siguiente sesión.
    clearCart();
    logout();
    navigate('/', { replace: true });
  };

  return (
    // Conservamos la clase 'header' definida en el CSS global[cite: 9]
    <header className="header">
      {/* Logotipo y título oficial de la plataforma */}
      <div className="logo">
        <img src="/img/Logo-Granero-Digital.jpeg" alt="logo" />
        <h1>El Granero Digital</h1>
      </div>

      {/* Menú de navegación migrado a etiquetas Link */}
      <nav>
        <Link to="/">Inicio</Link>
        <Link to="/catalogo">Productos</Link>
        <Link to="#">Nosotros</Link>
        <Link to="#">Contacto</Link>
        {/* Las opciones de gestión dependen del rol cargado desde el perfil. */}
        {user?.rol === 'comprador' && (
          <Link
            to="/carrito"
            className="header-cart-link"
            aria-label={itemCount ? `Carrito, ${itemCount} unidades` : 'Carrito vacío'}
            title="Carrito"
          >
            <svg viewBox="0 0 24 24" aria-hidden="true" className="header-cart-icon">
              <path d="M3 4h2l2.1 10.1a2 2 0 0 0 2 1.6h7.7a2 2 0 0 0 1.9-1.4L21 8H6" />
              <circle cx="10" cy="20" r="1.3" />
              <circle cx="18" cy="20" r="1.3" />
            </svg>
            {itemCount > 0 && <span className="header-cart-count">{itemCount}</span>}
          </Link>
        )}
        {user?.rol === 'comprador' && <Link to="/mis-pedidos">Mis pedidos</Link>}
        {user?.rol === 'campesino' && <Link to="/productos/nuevo">Publicar producto</Link>}
        {user?.rol === 'campesino' && <Link to="/pedidos-recibidos">Pedidos recibidos</Link>}
        {user?.rol === 'admin' && <Link to="/administracion">Panel administrativo</Link>}
        {user ? (
          <>
            <span className="header-greeting">
              <span>Hola,</span>
              <strong>{user.first_name || user.email || 'usuario'}</strong>
            </span>
            <button
              className="header-logout"
              type="button"
              onClick={handleLogout}
              aria-label="Cerrar sesión"
              title="Cerrar sesión"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M10 17l5-5-5-5M15 12H3" />
                <path d="M12 3h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-6" />
              </svg>
            </button>
          </>
        ) : (
          <>
            <Link to="/login">Iniciar sesión</Link>
            <Link to="/registro">Registrarse</Link>
          </>
        )}
      </nav>
    </header>
  );
};
