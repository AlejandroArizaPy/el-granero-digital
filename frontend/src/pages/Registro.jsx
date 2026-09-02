// Importamos React y navegación
import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';

export const Registro = () => {
  const navigate = useNavigate();

  const handleRegister = (e) => {
    e.preventDefault();
    navigate('/login');
  };

  return (
    <>
      <Header />

      <main>
        <div className="login-container">
          <div className="login-image">
            <img src="/img/Logo-Granero-Digital.jpeg" alt="Logo-registrarse" />
          </div>

          <div className="login-box">
            <h2>CREAR CUENTA</h2>
            <p>Completa la siguiente información para registrarte en Granero Digital.</p>

            <form onSubmit={handleRegister}>
              <label>Nombre completo *</label>
              <input type="text" required />

              <div className="row">
                <div>
                  <label>Tipo *</label>
                  <select>
                    <option>C.C</option>
                    <option>Pasaporte</option>
                  </select>
                </div>

                <div>
                  <label>Número de documento *</label>
                  <input type="text" required />
                </div>
              </div>

              <label>Correo electrónico *</label>
              <input type="email" required />

              <div className="row">
                <div>
                  <label>Celular *</label>
                  <input type="text" required />
                </div>

                <div>
                  <label>Rol *</label>
                  <select>
                    <option>Cliente</option>
                    <option>Vendedor</option>
                  </select>
                </div>
              </div>

              <div className="row">
                <div>
                  <label>Contraseña *</label>
                  <input type="password" required />
                </div>

                <div>
                  <label>Confirmar Contraseña *</label>
                  <input type="password" required />
                </div>
              </div>

              <button type="submit">REGISTRARSE</button>

              <div className="links">
                <span>¿Ya tienes una cuenta?</span>
                <Link to="/login">Inicia sesión</Link>
              </div>
            </form>
          </div>
        </div>
      </main>

      <Footer />
    </>
  );
};