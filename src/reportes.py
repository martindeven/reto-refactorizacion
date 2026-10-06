# -*- coding: utf-8 -*-
"""Reportes de la tienda: inventario, ventas y mas vendidos."""

import os

import gestor


def hacer_cosa(v):
    # le da formato de dinero al numero
    return "$" + str(round(v, 2))


def productos_stock_bajo():
    """Regresa la lista de productos con stock por debajo del minimo."""
    temp2 = []
    for k in gestor.INVENTARIO:
        if gestor.INVENTARIO[k]["stock"] < 5:
            temp2.append(gestor.INVENTARIO[k])
    return temp2


def reporte_inventario():
    """Arma el reporte del inventario, lo imprime y lo regresa como texto."""
    s = "===== INVENTARIO =====\n"
    aux = 0
    for k in gestor.INVENTARIO:
        p = gestor.INVENTARIO[k]
        linea = p["codigo"] + " | " + p["nombre"] + " | "
        linea = linea + hacer_cosa(p["precio"]) + " | stock: " + str(p["stock"])
        if p["stock"] < 5:
            linea = linea + "  <-- STOCK BAJO"
        s = s + linea + "\n"
        aux = aux + p["precio"] * p["stock"]
    s = s + "Valor total del inventario: " + hacer_cosa(aux) + "\n"
    print(s)
    return s


def total_vendido():
    """Suma el total (con IVA) de todas las ventas registradas."""
    t = 0
    for v in gestor.VENTAS:
        t = t + v["total"]
    return round(t, 2)


def mas_vendidos(n=3):
    """Regresa los n productos mas vendidos como lista de (codigo, unidades)."""
    aux = {}
    for v in gestor.VENTAS:
        if v["codigo"] in aux:
            aux[v["codigo"]] = aux[v["codigo"]] + v["cantidad"]
        else:
            aux[v["codigo"]] = v["cantidad"]
    temp = []
    for k in aux:
        temp.append((k, aux[k]))
    # ordenamiento de burbuja (TODO: algun dia usar sorted)
    for i in range(len(temp)):
        for j in range(0, len(temp) - i - 1):
            if temp[j][1] < temp[j + 1][1]:
                t = temp[j]
                temp[j] = temp[j + 1]
                temp[j + 1] = t
    return temp[0:n]


def resumen_ventas():
    """Arma el resumen de ventas del dia, lo imprime y lo regresa."""
    s = "===== RESUMEN DE VENTAS =====\n"
    t = 0
    for v in gestor.VENTAS:
        s = s + "Folio " + str(v["folio"]) + ": " + v["nombre"]
        s = s + " x" + str(v["cantidad"]) + " = " + hacer_cosa(v["total"]) + "\n"
        t = t + v["total"]
    s = s + "Numero de ventas: " + str(len(gestor.VENTAS)) + "\n"
    s = s + "Total del dia: " + hacer_cosa(t) + "\n"
    print(s)
    return s


def reporteViejoCSV(ruta):
    # version vieja del reporte que pedia contabilidad, ya no se usa
    # desde que cambiaron de sistema, pero por si las dudas aqui sigue
    f = open(ruta, "w", encoding="utf-8")
    f.write("codigo,nombre,stock\n")
    for k in gestor.INVENTARIO:
        p = gestor.INVENTARIO[k]
        f.write(p["codigo"] + "," + p["nombre"] + "," + str(p["stock"]) + "\n")
    f.close()
    return ruta
