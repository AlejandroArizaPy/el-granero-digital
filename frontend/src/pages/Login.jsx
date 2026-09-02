// Importamos React y enrutamiento
import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';

export const Login = () => {
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    navigate('/catalogo');
  };

  return (
    <>
      <Header />

      <main>
        <section className="login-container">
          <div className="login-box">
            <h2>INICIAR SESIÓN</h2>

            <form onSubmit={handleSubmit}>
              <label>Nombre de usuario o correo electrónico *</label>
              <input type="text" required />

              <label>Contraseña *</label>
              <input type="password" required />

              <div className="remember">
                <input type="checkbox" id="check" />
                <label htmlFor="check">Recuérdame</label>
              </div>

              <button type="submit">INICIAR SESIÓN</button>
            </form>

            <div className="links">
              <a href="#">¿Olvidaste la contraseña?</a>
              <Link to="/registro">Regístrate</Link>
            </div>
          </div>

          <div className="login-imagen">
            <img src="/img/Logo-Granero-Digital.jpeg" alt="Granero Digital" />
          </div>
        </section>
      </main>

      <Footer />
    </>
  );
};