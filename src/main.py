# -*- coding: utf-8 -*-
"""Punto de entrada del gestor de tienda (menu interactivo en consola)."""

import gestor
import almacen
import reportes

ARCHIVO = "datos_ejemplo.json"


def pedir_numero(mensaje):
    # pide un numero al usuario hasta que escriba algo valido
    while True:
        temp2 = input(mensaje)
        try:
            return float(temp2)
        except ValueError:
            print("Eso no es un numero, intenta de nuevo.")


def menu():
    print("Bienvenido al gestor de la tienda La Esquina")
    if almacen.hayArchivo(ARCHIVO):
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
        op = input("Opcion: ")
        if op == "1":
            c = input("Codigo: ")
            n = input("Nombre: ")
            p = pedir_numero("Precio: ")
            s = int(pedir_numero("Stock inicial: "))
            if gestor.agregarProducto(c, n, p, s):
                print("Producto agregado.")
            else:
                print("Error:", gestor.ultimo_error)
        elif op == "2":
            c = input("Codigo del producto: ")
            cant = int(pedir_numero("Cantidad: "))
            cli = input("Codigo de cliente (enter si no tiene): ")
            v = gestor.registrar_venta(c, cant, cli)
            if v is not None:
                print(v["ticket"])
            else:
                print("Error:", gestor.ultimo_error)
        elif op == "3":
            c = input("Codigo del producto: ")
            cant = int(pedir_numero("Cantidad: "))
            t = gestor.cotizar(c, cant)
            if t is not None:
                print("Total estimado (con IVA): $" + str(t))
            else:
                print("Error:", gestor.ultimo_error)
        elif op == "4":
            reportes.reporte_inventario()
        elif op == "5":
            reportes.resumen_ventas()
        elif op == "6":
            for par in reportes.mas_vendidos():
                print(par[0], "->", par[1], "unidades")
        elif op == "7":
            bajos = reportes.productos_stock_bajo()
            if len(bajos) == 0:
                print("No hay productos con stock bajo.")
            else:
                for p in bajos:
                    print("OJO:", p["nombre"], "solo tiene", p["stock"], "unidades")
        elif op == "8":
            almacen.guardar_datos(ARCHIVO)
            print("Datos guardados. Hasta luego.")
            break
        else:
            print("Opcion no valida.")


if __name__ == "__main__":
    menu()
