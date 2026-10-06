"""Punto de entrada del gestor de tienda (menu interactivo en consola)."""

import gestor
import almacen
import reportes

ARCHIVO = "datos_ejemplo.json"


def pedir_numero(mensaje):
    # pide un numero al usuario hasta que escriba algo valido
    while True:
        respuesta = input(mensaje)
        try:
            return float(respuesta)
        except ValueError:
            print("Eso no es un numero, intenta de nuevo.")


def menu():
    print("Bienvenido al gestor de la tienda La Esquina")
    if almacen.existe_archivo(ARCHIVO):
        almacen.cargar_datos(ARCHIVO)
        print("Datos cargados de", ARCHIVO)
    while True:
        print("")
        print("1) Agregar producto")
        print("2) Registrar venta")
        print("3) Cotizar")
        print("4) Reporte de inventario")
        print("5) Resumen de ventas")
        print("6) Mas vendidos")
        print("7) Alertas de stock bajo")
        print("8) Guardar y salir")
        opcion = input("Opcion: ")
        if opcion == "1":
            codigo = input("Codigo: ")
            nombre = input("Nombre: ")
            precio = pedir_numero("Precio: ")
            stock = int(pedir_numero("Stock inicial: "))
            if gestor.agregarProducto(codigo, nombre, precio, stock):
                print("Producto agregado.")
            else:
                print("Error:", gestor.ultimo_error)
        elif opcion == "2":
            codigo = input("Codigo del producto: ")
            cantidad = int(pedir_numero("Cantidad: "))
            cliente = input("Codigo de cliente (enter si no tiene): ")
            venta = gestor.registrar_venta(codigo, cantidad, cliente)
            if venta is not None:
                print(venta["ticket"])
            else:
                print("Error:", gestor.ultimo_error)
        elif opcion == "3":
            codigo = input("Codigo del producto: ")
            cantidad = int(pedir_numero("Cantidad: "))
            total = gestor.cotizar(codigo, cantidad)
            if total is not None:
                print("Total estimado (con IVA): $" + str(total))
            else:
                print("Error:", gestor.ultimo_error)
        elif opcion == "4":
            reportes.reporte_inventario()
        elif opcion == "5":
            reportes.resumen_ventas()
        elif opcion == "6":
            for codigo, unidades in reportes.mas_vendidos():
                print(codigo, "->", unidades, "unidades")
        elif opcion == "7":
            productos_bajos = reportes.productos_stock_bajo()
            if len(productos_bajos) == 0:
                print("No hay productos con stock bajo.")
            else:
                for producto in productos_bajos:
                    print("OJO:", producto["nombre"], "solo tiene",
                          producto["stock"], "unidades")
        elif opcion == "8":
            almacen.guardar_datos(ARCHIVO)
            print("Datos guardados. Hasta luego.")
            break
        else:
            print("Opcion no valida.")


if __name__ == "__main__":
    menu()
