// Importamos React Router para definir las rutas globales de la SPA
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
import { CrearProducto } from './pages/CrearProducto';
import { ListaPedidos, DetallePedido } from './pages/Pedidos';
import { AdminPanel } from './pages/AdminPanel';
import { RequireAuth } from './components/RequireAuth';

export function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Inicio />} />
        {/* El catálogo y el detalle requieren una sesión; cada rol tiene rutas de gestión propias. */}
        <Route path="/catalogo" element={<RequireAuth><Catalogo /></RequireAuth>} />
        <Route path="/producto/:id" element={<RequireAuth><DetalleProducto /></RequireAuth>} />
        <Route path="/productos/nuevo" element={<RequireAuth roles={['campesino']}><CrearProducto /></RequireAuth>} />
        <Route path="/mis-pedidos" element={<RequireAuth roles={['comprador']}><ListaPedidos tipo="comprador" /></RequireAuth>} />
        <Route path="/pedidos-recibidos" element={<RequireAuth roles={['campesino']}><ListaPedidos tipo="campesino" /></RequireAuth>} />
        <Route path="/pedidos/:id" element={<RequireAuth roles={['comprador', 'campesino']}><DetallePedido /></RequireAuth>} />
        <Route path="/administracion" element={<RequireAuth roles={['admin']}><AdminPanel /></RequireAuth>} />
        <Route path="/carrito" element={<RequireAuth roles={['comprador']}><Carrito /></RequireAuth>} />
        <Route path="/confirmacion" element={<RequireAuth roles={['comprador']}><Confirmacion /></RequireAuth>} />
        <Route path="/compra-exitosa" element={<RequireAuth roles={['comprador']}><CompraConfirmada /></RequireAuth>} />
        <Route path="/login" element={<Login />} />
        <Route path="/registro" element={<Registro />} />
      </Routes>
    </Router>
  );
}

export default App;
