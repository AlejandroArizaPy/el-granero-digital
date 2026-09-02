// Importamos React Router para definir las rutas globales de la SPA
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Importación unificada usando llaves { } correspondientes a las exportaciones nombradas
import { Inicio } from './pages/Inicio';
import { Catalogo } from './pages/Catalogo';
import { DetalleProducto } from './pages/DetalleProducto';
import { Carrito } from './pages/Carrito';
import { Confirmacion } from './pages/Confirmacion';
import { CompraConfirmada } from './pages/CompraConfirmada';
import { Login } from './pages/Login';
import { Registro } from './pages/Registro';

export function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Inicio />} />
        <Route path="/catalogo" element={<Catalogo />} />
        <Route path="/producto" element={<DetalleProducto />} />
        <Route path="/carrito" element={<Carrito />} />
        <Route path="/confirmacion" element={<Confirmacion />} />
        <Route path="/compra-exitosa" element={<CompraConfirmada />} />
        <Route path="/login" element={<Login />} />
        <Route path="/registro" element={<Registro />} />
      </Routes>
    </Router>
  );
}

export default App;
