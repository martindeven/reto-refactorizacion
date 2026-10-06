"""Persistencia del gestor: carga y guardado de datos en JSON."""

import json
import os

import gestor


def guardar_datos(ruta):
    """Guarda el inventario, las ventas y el folio actual en un JSON."""
    d = {}
    d["inventario"] = gestor.INVENTARIO
    d["ventas"] = gestor.VENTAS
    d["contador"] = gestor.contadorVentas
    f = open(ruta, "w", encoding="utf-8")
    json.dump(d, f, indent=2, ensure_ascii=False)
    f.close()
    return True


def cargar_datos(ruta):
    """Lee el archivo JSON y deja los datos en el estado global.

    Regresa False si el archivo no existe o esta corrupto.
    """
    if not os.path.exists(ruta):
        gestor.ultimo_error = "el archivo no existe"
        return False
    f = open(ruta, "r", encoding="utf-8")
    try:
        d = json.load(f)
    except Exception:
        f.close()
        gestor.ultimo_error = "archivo corrupto"
        return False
    f.close()
    gestor.INVENTARIO.clear()
    for k in d["inventario"]:
        gestor.INVENTARIO[k] = d["inventario"][k]
    gestor.VENTAS.clear()
    for v in d["ventas"]:
        gestor.VENTAS.append(v)
    gestor.contadorVentas = d.get("contador", 0)
    return True


def hayArchivo(ruta):
    # checa si ya existe el archivo de datos
    if os.path.exists(ruta):
        return True
    else:
        return False
