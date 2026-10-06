# -*- coding: utf-8 -*-
"""Pruebas de caja negra del modulo de reportes."""

import gestor
import reportes


def test_stock_bajo_detecta_los_correctos():
    gestor.agregarProducto("A1", "Leche", 26.0, 3)
    gestor.agregarProducto("A2", "Azúcar", 32.5, 40)
    gestor.agregarProducto("A3", "Chocolate", 78.9, 2)
    bajos = reportes.productos_stock_bajo()
    codigos = [p["codigo"] for p in bajos]
    assert sorted(codigos) == ["A1", "A3"]


def test_total_vendido_suma_las_ventas():
    assert reportes.total_vendido() == 0  # sin ventas
    gestor.agregarProducto("A1", "Café", 10.0, 100)
    gestor.registrar_venta("A1", 2)  # $23.20
    gestor.registrar_venta("A1", 2)  # $23.20
    assert reportes.total_vendido() == 46.4


def test_mas_vendidos_ordena_por_unidades():
    gestor.agregarProducto("A1", "Café", 10.0, 100)
    gestor.agregarProducto("B1", "Galletas", 5.0, 100)
    gestor.registrar_venta("A1", 5)
    gestor.registrar_venta("B1", 2)
    gestor.registrar_venta("A1", 1)
    top = reportes.mas_vendidos(2)
    assert top[0] == ("A1", 6)
    assert top[1] == ("B1", 2)


def test_reporte_inventario_marca_stock_bajo():
    gestor.agregarProducto("A1", "Leche", 26.0, 3)
    gestor.agregarProducto("A2", "Azúcar", 32.5, 40)
    texto = reportes.reporte_inventario()
    assert "Leche" in texto
    assert "STOCK BAJO" in texto
