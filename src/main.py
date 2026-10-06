"""Punto de entrada del gestor de tienda (menu interactivo en consola)."""

from collections.abc import Callable

import almacen
import gestor
import reportes

ARCHIVO = "datos_ejemplo.json"


def pedir_numero(mensaje: str) -> float:
    """Pide un numero al usuario hasta que escriba algo valido."""
    while True:
        respuesta = input(mensaje)
        try:
            return float(respuesta)
        except ValueError:
            print("Eso no es un numero, intenta de nuevo.")


def _mostrar_opciones() -> None:
    """Imprime las opciones del menu."""
    print("")
    print("1) Agregar producto")
    print("2) Registrar venta")
    print("3) Cotizar")
    print("4) Reporte de inventario")
    print("5) Resumen de ventas")
    print("6) Mas vendidos")
    print("7) Alertas de stock bajo")
    print("8) Guardar y salir")


def _opcion_agregar_producto() -> None:
    """Pide codigo, nombre, precio y stock, y da de alta el producto."""
    codigo = input("Codigo: ")
    nombre = input("Nombre: ")
    precio = pedir_numero("Precio: ")
    stock = int(pedir_numero("Stock inicial: "))
    if gestor.agregarProducto(codigo, nombre, precio, stock):
        print("Producto agregado.")
    else:
        print("Error:", gestor.ultimo_error)


def _opcion_registrar_venta() -> None:
    """Pide codigo, cantidad y cliente, y muestra el ticket o el error."""
    codigo = input("Codigo del producto: ")
    cantidad = int(pedir_numero("Cantidad: "))
    cliente = input("Codigo de cliente (enter si no tiene): ")
    venta = gestor.registrar_venta(codigo, cantidad, cliente)
    if venta is not None:
        print(venta["ticket"])
    else:
        print("Error:", gestor.ultimo_error)


def _opcion_cotizar() -> None:
    """Pide codigo y cantidad, y muestra el total estimado o el error."""
    codigo = input("Codigo del producto: ")
    cantidad = int(pedir_numero("Cantidad: "))
    total = gestor.cotizar(codigo, cantidad)
    if total is not None:
        print("Total estimado (con IVA): $" + str(total))
    else:
        print("Error:", gestor.ultimo_error)


def _opcion_reporte_inventario() -> None:
    """Muestra el reporte de inventario."""
    reportes.reporte_inventario()


def _opcion_resumen_ventas() -> None:
    """Muestra el resumen de ventas."""
    reportes.resumen_ventas()


def _opcion_mas_vendidos() -> None:
    """Muestra los productos mas vendidos."""
    for codigo, unidades in reportes.mas_vendidos():
        print(codigo, "->", unidades, "unidades")


def _opcion_stock_bajo() -> None:
    """Muestra las alertas de stock bajo, o avisa que no hay."""
    productos_bajos = reportes.productos_stock_bajo()
    if len(productos_bajos) == 0:
        print("No hay productos con stock bajo.")
    else:
        for producto in productos_bajos:
            print("OJO:", producto["nombre"], "solo tiene",
                  producto["stock"], "unidades")


def _opcion_guardar_y_salir() -> bool:
    """Guarda los datos y regresa True para terminar el menu."""
    almacen.guardar_datos(ARCHIVO)
    print("Datos guardados. Hasta luego.")
    return True


# Cada opcion apunta a su funcion; solo "guardar y salir" regresa True
# para terminar el menu (las demas regresan None y el menu continua).
OPCIONES: dict[str, Callable[[], bool | None]] = {
    "1": _opcion_agregar_producto,
    "2": _opcion_registrar_venta,
    "3": _opcion_cotizar,
    "4": _opcion_reporte_inventario,
    "5": _opcion_resumen_ventas,
    "6": _opcion_mas_vendidos,
    "7": _opcion_stock_bajo,
    "8": _opcion_guardar_y_salir,
}


def menu() -> None:
    """Muestra el menu y atiende opciones hasta que se elige guardar y salir."""
    print("Bienvenido al gestor de la tienda La Esquina")
    if almacen.existe_archivo(ARCHIVO):
        almacen.cargar_datos(ARCHIVO)
        print("Datos cargados de", ARCHIVO)
    while True:
        _mostrar_opciones()
        accion = OPCIONES.get(input("Opcion: "))
        if accion is None:
            print("Opcion no valida.")
        elif accion():
            break


if __name__ == "__main__":
    menu()
