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
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=2, ensure_ascii=False)
    return True


def cargar_datos(ruta):
    """Lee el archivo JSON y deja los datos en el estado global.

    Regresa False si el archivo no existe o esta corrupto.
    """
    if not os.path.exists(ruta):
        gestor.ultimo_error = "el archivo no existe"
        return False
    with open(ruta, encoding="utf-8") as archivo:
        try:
            datos = json.load(archivo)
        except (json.JSONDecodeError, UnicodeDecodeError):
            gestor.ultimo_error = "archivo corrupto"
            return False
    # se vacian y rellenan en sitio: nunca reasignar INVENTARIO ni VENTAS
    gestor.INVENTARIO.clear()
    gestor.INVENTARIO.update(datos["inventario"])
    gestor.VENTAS.clear()
    gestor.VENTAS.extend(datos["ventas"])
    gestor.contador_ventas = datos.get("contador", 0)
    return True


def existe_archivo(ruta):
    # checa si ya existe el archivo de datos
    return os.path.exists(ruta)
