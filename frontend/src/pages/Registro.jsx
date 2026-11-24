import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { apiRequest, getApiErrorMessage } from '../services/api';

export const Registro = () => {
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleRegister = async (event) => {
    event.preventDefault();
    setError('');

    const form = new FormData(event.currentTarget);
    const fullName = String(form.get('nombre_completo') || '').trim();
    // Django recibe nombre y apellido por separado, aunque el formulario los agrupe.
    const [firstName, ...lastNameParts] = fullName.split(/\s+/);
    const password = String(form.get('password') || '');
    const passwordConfirmation = String(form.get('password_confirmation') || '');

    if (password !== passwordConfirmation) {
      setError('Las contraseñas no coinciden.');
      return;
    }

    setIsSubmitting(true);
    try {
      // Se envían únicamente los campos que acepta RegistroUsuarioSerializer.
      await apiRequest('/usuarios/api/', {
        method: 'POST',
        auth: false,
        body: {
          username: String(form.get('username') || '').trim(),
          password,
          first_name: firstName,
          last_name: lastNameParts.join(' '),
          email: String(form.get('email') || '').trim(),
          documento: String(form.get('documento') || '').trim(),
          celular: String(form.get('celular') || '').trim(),
          tipo_registro: String(form.get('tipo_registro') || ''),
        },
      });

      navigate('/login', {
        replace: true,
        state: { message: 'Cuenta creada. Inicia sesión para continuar.' },
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
      <main>
        <div className="login-container">
          <div className="login-image">
            <img src="/img/Logo-Granero-Digital.jpeg" alt="Logo Granero Digital" />
          </div>

          <div className="login-box">
            <h2>CREAR CUENTA</h2>
            <p>Completa la siguiente información para registrarte en Granero Digital.</p>

            <form onSubmit={handleRegister}>
              <label htmlFor="nombre_completo">Nombre completo *</label>
              <input id="nombre_completo" name="nombre_completo" type="text" required />

              <label htmlFor="username">Nombre de usuario *</label>
              <input id="username" name="username" type="text" autoComplete="username" required />

              <label htmlFor="documento">Número de documento *</label>
              <input id="documento" name="documento" type="text" required />

              <label htmlFor="email">Correo electrónico *</label>
              <input id="email" name="email" type="email" autoComplete="email" required />

              <div className="row">
                <div>
                  <label htmlFor="celular">Celular *</label>
                  <input id="celular" name="celular" type="tel" required />
                </div>
                <div>
                  <label htmlFor="tipo_registro">Rol *</label>
                  <select id="tipo_registro" name="tipo_registro" defaultValue="comprador" required>
                    <option value="comprador">Comprador</option>
                    <option value="campesino">Campesino</option>
                  </select>
                </div>
              </div>

              <div className="row">
                <div>
                  <label htmlFor="password">Contraseña *</label>
                  <input id="password" name="password" type="password" autoComplete="new-password" required />
                </div>
                <div>
                  <label htmlFor="password_confirmation">Confirmar contraseña *</label>
                  <input id="password_confirmation" name="password_confirmation" type="password" autoComplete="new-password" required />
                </div>
              </div>

              {error && <p className="form-error" role="alert">{error}</p>}
              <button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Registrando…' : 'REGISTRARSE'}
              </button>

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
