// Importamos React y componentes de navegación
import React from 'react';
import { Link } from 'react-router-dom';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';

export const CompraConfirmada = () => {
  return (
    <>
      <Header />

      <div className="container-pedido">
        <div className="card-pedido">
          <div className="icono-pedido">✔</div>

          <h2>¡Compra realizada con éxito!</h2>

          <div className="info-pedido">
            <div className="col-pedido">
              <p>
                Gracias por comprar en Granero Digital. Tu pedido ha sido registrado correctamente y pronto será preparado por nuestros productores.
              </p>
            </div>

            <div className="col-pedido">
              <p><strong>Número de pedido:</strong><br />#PED-00001</p>
              <p><strong>Estado:</strong> En preparación</p>
            </div>
          </div>
        </div>

        <div className="botones-pedido">
          <Link to="#" className="btn-pedido">Ver mis pedidos</Link>
          <Link to="/" className="btn-pedido">Volver al inicio</Link>
        </div>
      </div>

      <Footer />
    </>
  );
};