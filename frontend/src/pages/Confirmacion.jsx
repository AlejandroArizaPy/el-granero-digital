// Importamos React y el hook de navegación
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';

export const Confirmacion = () => {
  const navigate = useNavigate();

  // Envío del formulario de checkout
  const handleConfirm = (e) => {
    e.preventDefault();
    navigate('/compra-exitosa');
  };

  return (
    <>
      <Header />

      <div className="container-checkout">
        <h2>Confirmar pedido</h2>

        <div className="contenido-checkout">
          <form className="formulario-checkout" onSubmit={handleConfirm}>
            <h3>Datos de entrega:</h3>

            <label>Nombre completo:</label>
            <input type="text" required />

            <label>Dirección de entrega:</label>
            <input type="text" required />

            <div className="fila-checkout">
              <div>
                <label>Departamento:</label>
                <select>
                  <option>Seleccionar</option>
                  <option>Antioquia</option>
                  <option>Cundinamarca</option>
                </select>
              </div>

              <div>
                <label>Ciudad:</label>
                <input type="text" required />
              </div>
            </div>

            <label>Teléfono:</label>
            <input type="text" required />

            <label>Observaciones:</label>
            <textarea></textarea>

            <button type="submit" className="btn-checkout" style={{ width: '100%', border: 'none', cursor: 'pointer' }}>
              Confirmar compra
            </button>
          </form>

          <div className="resumen-checkout">
            <h3>Resumen del pedido</h3>

            <p>Papa Pastusa x2 kg</p>
            <p>Banano x1 kg</p>
            <p>Fresas x3 kg</p>

            <p className="total-checkout">Total: $16.400</p>
          </div>
        </div>
      </div>

      <Footer />
    </>
  );
};