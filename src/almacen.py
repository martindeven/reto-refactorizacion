"""Persistencia del gestor: carga y guardado de datos en JSON."""

import json
import os

import gestor


def guardar_datos(ruta):
    """Guarda el inventario, las ventas y el folio actual en un JSON."""
    datos = {}
    datos["inventario"] = gestor.INVENTARIO
    datos["ventas"] = gestor.VENTAS
    datos["contador"] = gestor.contador_ventas
    archivo = open(ruta, "w", encoding="utf-8")
    json.dump(datos, archivo, indent=2, ensure_ascii=False)
    archivo.close()
    return True


def cargar_datos(ruta):
    """Lee el archivo JSON y deja los datos en el estado global.

    Regresa False si el archivo no existe o esta corrupto.
    """
    if not os.path.exists(ruta):
        gestor.ultimo_error = "el archivo no existe"
        return False
    archivo = open(ruta, "r", encoding="utf-8")
    try:
        datos = json.load(archivo)
    except Exception:
        archivo.close()
        gestor.ultimo_error = "archivo corrupto"
        return False
    archivo.close()
    gestor.INVENTARIO.clear()
    for codigo in datos["inventario"]:
        gestor.INVENTARIO[codigo] = datos["inventario"][codigo]
    gestor.VENTAS.clear()
    for venta in datos["ventas"]:
        gestor.VENTAS.append(venta)
    gestor.contador_ventas = datos.get("contador", 0)
    return True


def existe_archivo(ruta):
    # checa si ya existe el archivo de datos
    return os.path.exists(ruta)
