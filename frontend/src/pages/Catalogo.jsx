// Importamos Hooks de React para el manejo del estado local de la búsqueda
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';

export const Catalogo = () => {
  const navigate = useNavigate();

  // Estado con el catálogo de productos extraído de tu HTML original[cite: 2]
  const [productos] = useState([
    { id: 1, nombre: 'Papa pastusa', categoria: 'Tubérculos', precio: 3500, img: '/img/papa-pastusa.jpg' },
    { id: 2, nombre: 'Tomate chonto', categoria: 'Verduras', precio: 2000, img: '/img/tomate-chonto.jpg' },
    { id: 3, nombre: 'Zanahoria', categoria: 'Hortalizas', precio: 2500, img: '/img/zanahoria.jpg' },
    { id: 4, nombre: 'Cebolla larga', categoria: 'Hortalizas', precio: 1500, img: '/img/cebolla.jpg' },
    { id: 5, nombre: 'Banano', categoria: 'Frutas', precio: 800, img: '/img/banano.avif' },
    { id: 6, nombre: 'Fresas', categoria: 'Frutas', precio: 1200, img: '/img/fresas.avif' }
  ]);

  // Estado que captura el texto del buscador
  const [busqueda, setBusqueda] = useState('');

  return (
    <>
      <Header />

      {/* Barra de filtrado */}
      <section className="filtros">
        <input 
          type="text" 
          placeholder="Buscar Productos..." 
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
        />

        <select>
          <option>Categoría</option>
          <option>Frutas</option>
          <option>Verduras</option>
          <option>Tubérculos</option>
        </select>

        <select>
          <option>Precio</option>
          <option>Ascendente</option>
          <option>Descendente</option>
        </select>

        <select>
          <option>Ordenar por</option>
          <option>Peso</option>
          <option>Calificación</option>
        </select>
      </section>

      {/* Grid dinámico de productos filtrados */}
      <section className="productos">
        {productos
          .filter(p => p.nombre.toLowerCase().includes(busqueda.toLowerCase()))
          .map((producto) => (
            <div className="card" key={producto.id}>
              <h3>{producto.nombre}</h3>
              <img src={producto.img} alt={producto.nombre} />
              <p>Categoría: {producto.categoria}</p>
              <p>Precio: ${producto.precio.toLocaleString()} / kg</p>
              <div className="estrellas">★★★★★</div>
              <button onClick={() => navigate('/producto')}>Ver Detalle</button>
            </div>
          ))}
      </section>

      <Footer />
    </>
  );
};