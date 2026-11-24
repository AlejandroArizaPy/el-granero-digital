import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { useCart } from '../context/CartContext';
import { apiRequest, getApiErrorMessage } from '../services/api';
import { formatCurrency } from '../utils/format';

export const DetalleProducto = () => {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { addItem } = useCart();
  const [producto, setProducto] = useState(null);
  const [relacionados, setRelacionados] = useState([]);
  const [cantidad, setCantidad] = useState(1);
  const [error, setError] = useState('');
  const [message, setMessage] = useState(() => location.state?.message || '');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    // Se reinicia la vista mientras se solicita el ID nuevo de la ruta.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIsLoading(true);
    setError('');
    setProducto(null);
    setRelacionados([]);

    // Primero se carga el producto solicitado; después se buscan relacionados.
    apiRequest(`/productos/api/${id}/`, { signal: controller.signal })
      .then(({ data }) => {
        setProducto(data);
        apiRequest('/productos/api/', { signal: controller.signal })
          .then(({ data: catalogo }) => {
            if (Array.isArray(catalogo)) {
              setRelacionados(catalogo.filter((item) => (
                item.id !== Number(id) && item.categoria === data.categoria
              )).slice(0, 3));
            }
          })
          .catch(() => {});
      })
      .catch((requestError) => {
        if (requestError.name !== 'AbortError') setError(getApiErrorMessage(requestError));
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoading(false);
      });

    return () => controller.abort();
  }, [id]);

  const agregarAlCarrito = () => {
    if (!producto) return;
    // El contexto comprueba vendedor y stock antes de guardar el producto.
    const result = addItem(producto, cantidad);
    if (!result.ok) {
      setError(result.message);
      return;
    }
    setError('');
    setMessage('Producto agregado al carrito.');
  };

  return (
    <>
      <Header />
      <main>
        {isLoading && <p role="status">Cargando producto…</p>}
        {!isLoading && error && <p className="form-error" role="alert">{error}</p>}
        {!isLoading && !error && !producto && <p>Producto no encontrado.</p>}

        {producto && (
          <section className="detalle-container">
            <div className="detalle-card">
              <div className="detalle-img">
                <p>
                  <strong>Productor:</strong>{' '}
                  {[producto.usuario?.first_name, producto.usuario?.last_name].filter(Boolean).join(' ') || 'Campesino'}
                </p>
                {producto.imagen && <img src={producto.imagen} alt={producto.nombre} />}
              </div>

              <div className="detalle-info">
                <h2>{producto.nombre}</h2>
                <p><strong>Categoría:</strong> {producto.categoria_nombre || producto.categoria}</p>
                <p><strong>Precio:</strong> {formatCurrency(producto.precio)} / kg</p>
                <p><strong>Stock disponible:</strong> {producto.stock}</p>
                <p className="descripcion-producto">
                  <strong>Descripción del producto:</strong> {producto.detalle}
                </p>

                <div className="cantidad">
                  <label htmlFor="cantidad-producto">Cantidad:</label>
                  <button
                    type="button"
                    onClick={() => setCantidad((actual) => Math.max(1, actual - 1))}
                    disabled={cantidad <= 1}
                    aria-label="Disminuir cantidad"
                  >-</button>
                  <input
                    id="cantidad-producto"
                    type="number"
                    min="1"
                    max={producto.stock}
                    value={cantidad}
                    onChange={(event) => {
                      const valor = Number(event.target.value);
                      setCantidad(Math.min(producto.stock, Math.max(1, valor || 1)));
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setCantidad((actual) => Math.min(producto.stock, actual + 1))}
                    disabled={cantidad >= producto.stock}
                    aria-label="Aumentar cantidad"
                  >+</button>
                </div>

                {message && <p role="status">{message}</p>}
                {error && <p className="form-error" role="alert">{error}</p>}
                <button
                  type="button"
                  className="btn-carrito"
                  onClick={agregarAlCarrito}
                  disabled={producto.stock < 1}
                >Agregar al carrito</button>
                <button type="button" onClick={() => navigate('/carrito')}>Ir al carrito</button>
                <Link to="/catalogo" className="volver">Volver al catálogo</Link>
              </div>
            </div>
          </section>
        )}

        {producto && relacionados.length > 0 && (
          <section className="relacionados">
            <h3>Productos relacionados</h3>
            <div className="productos">
              {relacionados.map((item) => (
                <article className="card" key={item.id}>
                  <h4>{item.nombre}</h4>
                  {item.imagen && <img src={item.imagen} alt={item.nombre} />}
                  <p>Precio: {formatCurrency(item.precio)} / kg</p>
                  <Link to={`/producto/${item.id}`} className="btn">Ver detalle</Link>
                </article>
              ))}
            </div>
          </section>
        )}
      </main>
      <Footer />
    </>
  );
};
