import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';

export const Carrito = () => {
  // ids de los productos que se asignan al carrito, pueden incrementar o decrementar
  const [items, setItems] = useState([
    { id: 1, nombre: 'Papa pastusa', cantidad: 1, precioUnitario: 3500 },
    { id: 2, nombre: 'Tomate chonto', cantidad: 1, precioUnitario: 2000 },
    { id: 3, nombre: 'Zanahoria', cantidad: 1, precioUnitario: 2500 },
    { id: 4, nombre: 'Cebolla larga', cantidad: 1, precioUnitario: 1500 },
    { id: 5, nombre: 'Banano', cantidad: 1, precioUnitario: 800},
    { id: 6, nombre: 'fresas', cantidad: 1, precioUnitario: 1200}
  ]);

  const costoEnvio = 5000;

  // Funciones para que podamos incrementar y decrementar lo que son los items
  const incrementar = (id) => {
    setItems(items.map(item => item.id === id ? { ...item, cantidad: item.cantidad + 1 } : item));
  };

  const decrementar = (id) => {
    setItems(items.map(item => item.id === id && item.cantidad > 1 ? { ...item, cantidad: item.cantidad - 1 } : item));
  };

  const eliminar = (id) => {
    setItems(items.filter(item => item.id !== id));
  };

  // Función para poder calcular el precio completo de los items que se seleccionan en el carrito
  const subtotal = items.reduce((acc, item) => acc + (item.precioUnitario * item.cantidad), 0);
  const total = subtotal + (items.length > 0 ? costoEnvio : 0);

  return (
    <>
      <Header />

      <div className="container">
        <h2>Mi carrito de compras:</h2>

        <div className="carrito">
          <table>
            <thead>
              <tr>
                <th>Producto</th>
                <th>Cantidad</th>
                <th>Precio</th>
                <th>Subtotal</th>
                <th>Acción</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>{item.nombre}</td>
                  <td>
                    <div className="cantidad-carrito">
                      <button onClick={() => decrementar(item.id)}>-</button>
                      <span>{item.cantidad} kg</span>
                      <button onClick={() => incrementar(item.id)}>+</button>
                    </div>
                  </td>
                  <td>${item.precioUnitario.toLocaleString()}/kg</td>
                  <td>${(item.precioUnitario * item.cantidad).toLocaleString()}</td>
                  <td>
                    <button onClick={() => eliminar(item.id)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>🗑️</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="resumen">
            <h3>Resumen del pedido:</h3>
            <p>Productos: {items.length}</p>
            <p>Subtotal: ${subtotal.toLocaleString()}</p>
            <p>Envío: ${items.length > 0 ? costoEnvio.toLocaleString() : 0}</p>
            <p><strong>Total: ${total.toLocaleString()}</strong></p>

            <Link to="/confirmacion" className="btn">Continuar compra</Link>
          </div>
        </div>

        <Link to="/catalogo" className="volver">← Seguir comprando</Link>
      </div>

      <Footer />
    </>
  );
};