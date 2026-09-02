import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';

export const Inicio = () => {
  // Funcioón para gestionar la navegación mediante eventos click
  const navigate = useNavigate();

  return (
    <>
      <Header />
      
      {/* Contenedor principal de la página Inicio */}
      <main className="contenedor">
        <h2>Conectamos el campo con tu hogar</h2>

        <p className="descripcion">
          Granero Digital es una plataforma que conecta directamente a los campesinos con los consumidores,
          facilitando la compra de productos agrícolas frescos, de calidad y a precios justos desde cualquier lugar.
        </p>

        <div className="contenido">
          <div className="opciones">
            {/* Redirección al catálogo interactivo */}
            <div className="opcion" onClick={() => navigate('/catalogo')}>
              <img src="/img/icono-maiz.png" alt="icono maiz" />
              <p>Explorar productos</p>
            </div>

            {/* Redirección al formulario de registro */}
            <div className="opcion" onClick={() => navigate('/registro')}>
              <img src="/img/icono-usuario.png" alt="icono usuario-registrarse" />
              <p>Registrarse</p>
            </div>
          </div>

          <div className="imagen">
            <img src="/img/campesino.jpg" alt="campesino" />
          </div>
        </div>
      </main>

      <Footer />
    </>
  );
};