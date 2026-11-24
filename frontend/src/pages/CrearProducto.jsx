import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { apiRequest, getApiErrorMessage } from '../services/api';

export function CrearProducto() {
  const navigate = useNavigate();
  const [categorias, setCategorias] = useState([]);
  const [isLoadingCategories, setIsLoadingCategories] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const controller = new AbortController();

    // Las opciones vienen de la base de datos; no se codifican IDs en la interfaz.
    apiRequest('/productos/api/categorias/', { signal: controller.signal })
      .then(({ data }) => {
        setCategorias(Array.isArray(data) ? data : []);
      })
      .catch((requestError) => {
        if (requestError.name !== 'AbortError') {
          setError(getApiErrorMessage(requestError));
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoadingCategories(false);
      });

    return () => controller.abort();
  }, []);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');

    // FormData permite incluir la imagen junto a los campos del producto.
    const fields = new FormData(event.currentTarget);
    const precio = Number(fields.get('precio'));
    const peso = Number(fields.get('peso'));
    const stock = Number(fields.get('stock'));
    const imagen = fields.get('imagen');
    const categoria = String(fields.get('categoria') || '');

    if (!Number.isFinite(precio) || precio <= 0) {
      setError('El precio debe ser mayor que cero.');
      return;
    }
    if (!Number.isFinite(peso) || peso <= 0) {
      setError('El peso debe ser mayor que cero.');
      return;
    }
    if (!Number.isInteger(stock) || stock < 1) {
      setError('El stock debe ser un número entero mayor que cero.');
      return;
    }
    if (!(imagen instanceof File) || imagen.size === 0) {
      setError('Selecciona una imagen del producto.');
      return;
    }
    if (!imagen.type.startsWith('image/')) {
      setError('El archivo debe tener un formato de imagen compatible.');
      return;
    }
    if (!categorias.some((item) => String(item.id) === categoria)) {
      setError('Selecciona una categoría existente.');
      return;
    }

    setIsSubmitting(true);
    try {
      const body = new FormData();
      body.append('nombre', String(fields.get('nombre') || '').trim());
      body.append('detalle', String(fields.get('detalle') || '').trim());
      body.append('precio', String(fields.get('precio')));
      body.append('stock', String(fields.get('stock')));
      body.append('peso', String(fields.get('peso')));
      body.append('categoria', categoria);
      body.append('imagen', imagen);

      // apiRequest no fija Content-Type para FormData; el navegador añade el boundary.
      const { data: producto } = await apiRequest('/productos/api/', {
        method: 'POST',
        body,
      });

      // Se abre el ID real devuelto por Django para confirmar la publicación.
      navigate(`/producto/${producto.id}`, {
        replace: true,
        state: { message: 'Producto publicado correctamente.' },
      });
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
        <h2>Publicar producto</h2>
        <form className="formulario-checkout" onSubmit={handleSubmit}>
          <label htmlFor="nombre-producto">Nombre *</label>
          <input id="nombre-producto" name="nombre" type="text" maxLength="100" required />

          <label htmlFor="detalle-producto">Descripción *</label>
          <textarea id="detalle-producto" name="detalle" required />

          <label htmlFor="precio-producto">Precio por kg *</label>
          <input
            id="precio-producto"
            name="precio"
            type="number"
            min="0.01"
            step="0.01"
            required
          />

          <label htmlFor="stock-producto">Stock *</label>
          <input id="stock-producto" name="stock" type="number" min="1" step="1" required />

          <label htmlFor="peso-producto">Peso en kilogramos *</label>
          <input
            id="peso-producto"
            name="peso"
            type="number"
            min="0.001"
            step="0.001"
            required
          />

          <label htmlFor="categoria-producto">Categoría *</label>
          <select
            id="categoria-producto"
            name="categoria"
            defaultValue=""
            required
            disabled={isLoadingCategories || categorias.length === 0}
          >
            <option value="" disabled>
              {isLoadingCategories ? 'Cargando categorías…' : 'Selecciona una categoría'}
            </option>
            {categorias.map((categoria) => (
              <option key={categoria.id} value={categoria.id}>
                {categoria.nombre_display}
              </option>
            ))}
          </select>
          {!isLoadingCategories && categorias.length === 0 && !error && (
            <p role="status">No hay categorías disponibles para publicar.</p>
          )}

          <label htmlFor="imagen-producto">Imagen *</label>
          <input
            id="imagen-producto"
            name="imagen"
            type="file"
            accept="image/*"
            required
          />

          {error && <p className="form-error" role="alert">{error}</p>}
          <button
            className="btn-carrito"
            type="submit"
            disabled={isSubmitting || isLoadingCategories || categorias.length === 0}
          >
            {isSubmitting ? 'Publicando…' : 'Publicar producto'}
          </button>
          <Link to="/catalogo" className="volver">Volver al catálogo</Link>
        </form>
      </main>
      <Footer />
    </>
  );
}
