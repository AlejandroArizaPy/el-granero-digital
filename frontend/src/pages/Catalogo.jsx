import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { useCart } from '../context/CartContext';
import { apiRequest, getApiErrorMessage } from '../services/api';
import { formatCurrency } from '../utils/format';

export const Catalogo = () => {
  const { addItem } = useCart();
  const [productos, setProductos] = useState([]);
  const [busqueda, setBusqueda] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    // La API solo lista productos activos y exige el token de la sesión.
    apiRequest('/productos/api/', { signal: controller.signal })
      .then(({ data }) => setProductos(Array.isArray(data) ? data : []))
      .catch((requestError) => {
        if (requestError.name !== 'AbortError') setError(getApiErrorMessage(requestError));
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoading(false);
      });

    return () => controller.abort();
  }, []);

  const agregarProducto = (producto) => {
    setError('');
    setMessage('');
    const result = addItem(producto);
    if (result.ok) setMessage(`${producto.nombre} se agregó al carrito.`);
    else setError(result.message);
  };

  // La búsqueda se aplica en memoria al catálogo ya recibido del servidor.
  const productosFiltrados = productos.filter((producto) => (
    producto.nombre.toLowerCase().includes(busqueda.trim().toLowerCase())
  ));

  return (
    <>
      <Header />
      <section className="filtros">
        <label htmlFor="buscar-productos">Buscar productos</label>
        <input
          id="buscar-productos"
          type="search"
          placeholder="Buscar productos…"
          value={busqueda}
          onChange={(event) => setBusqueda(event.target.value)}
        />
      </section>

      <main>
        {message && <p role="status">{message}</p>}
        {error && <p className="form-error" role="alert">{error}</p>}
        {isLoading && <p role="status">Cargando productos…</p>}
        {!isLoading && !error && productosFiltrados.length === 0 && (
          <p role="status">
            {productos.length === 0
              ? 'Todavía no hay productos activos en el catálogo.'
              : 'No hay productos que coincidan con la búsqueda.'}
          </p>
        )}

        <section className="productos" aria-label="Catálogo de productos">
          {productosFiltrados.map((producto) => (
            <article className="card" key={producto.id}>
              <h3>{producto.nombre}</h3>
              {producto.imagen && <img src={producto.imagen} alt={producto.nombre} />}
              <p>Categoría: {producto.categoria_nombre || producto.categoria}</p>
              <p>Precio: {formatCurrency(producto.precio)} / kg</p>
              <p>Disponible: {producto.stock}</p>
              <Link to={`/producto/${producto.id}`} className="btn">Ver detalle</Link>
              <button type="button" onClick={() => agregarProducto(producto)}>
                Agregar al carrito
              </button>
            </article>
          ))}
        </section>
      </main>
      <Footer />
    </>
  );
};
