# -*- coding: utf-8 -*-
"""Pruebas de caja negra de la persistencia en JSON."""

import gestor
import almacen


def test_guardar_y_cargar_conserva_los_datos(tmp_path):
    ruta = str(tmp_path / "datos.json")
    gestor.agregarProducto("A1", "Café", 100.0, 50)
    gestor.registrar_venta("A1", 2)
    assert almacen.guardar_datos(ruta) is True

    gestor.reiniciar_sistema()
    assert gestor.INVENTARIO == {}

    assert almacen.cargar_datos(ruta) is True
    assert gestor.INVENTARIO["A1"]["stock"] == 48
    assert len(gestor.VENTAS) == 1
    assert gestor.VENTAS[0]["total"] == 232.0


def test_el_folio_continua_despues_de_recargar(tmp_path):
    ruta = str(tmp_path / "datos.json")
    gestor.agregarProducto("A1", "Café", 10.0, 50)
    gestor.registrar_venta("A1", 1)
    almacen.guardar_datos(ruta)

    gestor.reiniciar_sistema()
    almacen.cargar_datos(ruta)
    venta = gestor.registrar_venta("A1", 1)
    assert venta["folio"] == 2


def test_cargar_archivo_inexistente_regresa_false(tmp_path):
    assert almacen.cargar_datos(str(tmp_path / "no_existe.json")) is False
