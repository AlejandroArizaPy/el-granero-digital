// Importamos React para definir el componente funcional
import React from 'react';
// Importamos Link de React Router para cambiar de ruta sin recargar la página
import { Link } from 'react-router-dom';

// Exportación nombrada directa para evitar errores de sintaxis
export const Header = () => {
  return (
    // Conservamos la clase 'header' definida en el CSS global[cite: 9]
    <header className="header">
      {/* Logotipo y título oficial de la plataforma */}
      <div className="logo">
        <img src="/img/Logo-Granero-Digital.jpeg" alt="logo" />
        <h1>El Granero Digital</h1>
      </div>

      {/* Menú de navegación migrado a etiquetas Link */}
      <nav>
        <Link to="/">Inicio</Link>
        <Link to="/catalogo">Productos</Link>
        <Link to="#">Nosotros</Link>
        <Link to="#">Contacto</Link>
        <Link to="/login">Iniciar sesión</Link>
      </nav>
    </header>
  );
};