import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { getApiErrorMessage } from '../services/api';
import { useAuth } from '../context/AuthContext';

export const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const successMessage = location.state?.message;
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      // login obtiene los tokens y carga el perfil antes de navegar.
      await login(username.trim(), password);
      navigate(location.state?.from?.pathname || '/catalogo', { replace: true });
    } catch (requestError) {
      setError(getApiErrorMessage(requestError));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <Header />
      <main>
        <section className="login-container">
          <div className="login-box">
            <h2>INICIAR SESIÓN</h2>
            {successMessage && <p role="status">{successMessage}</p>}
            <form onSubmit={handleSubmit}>
              <label htmlFor="username">Nombre de usuario *</label>
              <input
                id="username"
                name="username"
                type="text"
                autoComplete="username"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                required
              />

              <label htmlFor="password">Contraseña *</label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />

              {error && <p className="form-error" role="alert">{error}</p>}
              <button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Ingresando…' : 'INICIAR SESIÓN'}
              </button>
            </form>

            <div className="links">
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
