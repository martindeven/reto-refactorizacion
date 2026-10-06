"""Reportes de la tienda: inventario, ventas y mas vendidos."""

import gestor


def formatear_moneda(valor):
    # le da formato de dinero al numero
    return "$" + str(round(valor, 2))


def productos_stock_bajo():
    """Regresa la lista de productos con stock por debajo del minimo."""
    return [producto for producto in gestor.INVENTARIO.values()
            if producto["stock"] < gestor.STOCK_MINIMO]


def reporte_inventario():
    """Arma el reporte del inventario, lo imprime y lo regresa como texto."""
    lineas = ["===== INVENTARIO ====="]
    valor_total = 0  # entero: sin productos el reporte dice "$0", no "$0.0"
    for producto in gestor.INVENTARIO.values():
        linea = (f"{producto['codigo']} | {producto['nombre']} | "
                 f"{formatear_moneda(producto['precio'])} | "
                 f"stock: {producto['stock']}")
        if producto["stock"] < gestor.STOCK_MINIMO:
            linea += "  <-- STOCK BAJO"
        lineas.append(linea)
        valor_total = valor_total + producto["precio"] * producto["stock"]
    lineas.append(f"Valor total del inventario: {formatear_moneda(valor_total)}")
    texto = "\n".join(lineas) + "\n"
    print(texto)
    return texto


def total_vendido():
    """Suma el total (con IVA) de todas las ventas registradas."""
    total = 0
    for venta in gestor.VENTAS:
        total = total + venta["total"]
    return round(total, 2)


def mas_vendidos(n=3):
    """Regresa los n productos mas vendidos como lista de (codigo, unidades)."""
    unidades_por_codigo = {}
    for venta in gestor.VENTAS:
        codigo = venta["codigo"]
        unidades_por_codigo[codigo] = (unidades_por_codigo.get(codigo, 0)
                                       + venta["cantidad"])
    # sorted es estable (tambien con reverse=True): en empates queda primero
    # el producto que se vendio primero, igual que con el metodo anterior
    ranking = sorted(unidades_por_codigo.items(),
                     key=lambda par: par[1], reverse=True)
    return ranking[:n]


def resumen_ventas():
    """Arma el resumen de ventas del dia, lo imprime y lo regresa."""
    lineas = ["===== RESUMEN DE VENTAS ====="]
    total = 0  # entero: sin ventas el resumen dice "$0", no "$0.0"
    for venta in gestor.VENTAS:
        lineas.append(f"Folio {venta['folio']}: {venta['nombre']} "
                      f"x{venta['cantidad']} = {formatear_moneda(venta['total'])}")
        total = total + venta["total"]
    lineas.append(f"Numero de ventas: {len(gestor.VENTAS)}")
    lineas.append(f"Total del dia: {formatear_moneda(total)}")
    texto = "\n".join(lineas) + "\n"
    print(texto)
    return texto
