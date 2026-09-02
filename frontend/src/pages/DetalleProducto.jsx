// Importamos React y hooks para actualizar la cantidad seleccionada
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';

export const DetalleProducto = () => {
  // Estado para controlar la cantidad de kg a comprar
  const [cantidad, setCantidad] = useState(1);
  const navigate = useNavigate();

  return (
    <>
      <Header />

      <section className="detalle-container">
        <div className="detalle-card">
          <div className="detalle-img">
            <p><strong>Productor:</strong> Finca El Roble</p>
            <img src="/img/papa-pastusa.jpg" alt="Papa pastusa" />
          </div>

          <div className="detalle-info">
            <h2>Papa pastusa</h2>

            <p><strong>Categoría:</strong> Tubérculos</p>
            <p><strong>Precio:</strong> $3.500 / kg</p>
            <p><strong>Stock disponible:</strong> 120 kg</p>

            <p className="descripcion-producto">
              <strong>Descripción del producto:</strong>
              Papa fresca cultivada por productores locales, ideal para consumo diario.
            </p>

            <p className="calificacion">
              <strong>Calificación:</strong>
              <span>★★★★★</span>
            </p>

            {/* Contador reactivo de cantidad */}
            <div className="cantidad">
              <label>Cantidad:</label>
              <button onClick={() => setCantidad(prev => Math.max(1, prev - 1))}>-</button>
              <span>{cantidad}</span>
              <button onClick={() => setCantidad(prev => prev + 1)}>+</button>
            </div>

            <button className="btn-carrito" onClick={() => navigate('/carrito')}>Agregar al carrito</button>

            <Link to="/catalogo" className="volver">Volver al catálogo</Link>
          </div>
        </div>
      </section>

      {/* Sección de productos recomendados */}
      <section className="relacionados">
        <h3>Productos relacionados:</h3>

        <div className="productos">
          <div className="card">
            <h4>Cebolla larga</h4>
            <img src="/img/cebolla.jpg" alt="cebolla" />
            <p>Categoría: Hortalizas</p>
            <p>Precio: $1.500 / kg</p>
            <div className="estrellas">★★★★★</div>
            <button onClick={() => navigate('/producto')}>Ver Detalle</button>
          </div>

          <div className="card">
            <h4>Banano</h4>
            <img src="/img/banano.avif" alt="banano" />
            <p>Categoría: Frutas</p>
            <p>Precio: $800 / kg</p>
            <div className="estrellas">★★★★★</div>
            <button onClick={() => navigate('/producto')}>Ver Detalle</button>
          </div>

          <div className="card">
            <h4>Fresas</h4>
            <img src="/img/fresas.avif" alt="fresas" />
            <p>Categoría: Frutas</p>
            <p>Precio: $1.200 / kg</p>
            <div className="estrellas">★★★★★</div>
            <button onClick={() => navigate('/producto')}>Ver Detalle</button>
          </div>
        </div>
      </section>

      <Footer />
    </>
  );
};