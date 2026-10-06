# -*- coding: utf-8 -*-
"""Pruebas de caja negra del modulo gestor (productos y ventas).

Estas pruebas verifican COMPORTAMIENTO observable, no detalles internos:
una refactorizacion bien hecha no deberia romper ninguna.
"""

import gestor


def _alta_producto_basico(codigo="A1", precio=100.0, stock=50):
    assert gestor.agregarProducto(codigo, "Producto de prueba", precio, stock)


def test_agregar_producto_queda_en_inventario():
    assert gestor.agregarProducto("A1", "Café", 185.0, 10) is True
    assert "A1" in gestor.INVENTARIO
    assert gestor.INVENTARIO["A1"]["nombre"] == "Café"
    assert gestor.INVENTARIO["A1"]["stock"] == 10


def test_rechaza_altas_invalidas():
    _alta_producto_basico("A1")
    # codigo duplicado
    assert gestor.agregarProducto("A1", "Otro", 10.0, 1) is False
    # precio y stock invalidos
    assert gestor.agregarProducto("A2", "Café", 0, 10) is False
    assert gestor.agregarProducto("A3", "Café", -5.0, 10) is False
    assert gestor.agregarProducto("A4", "Café", 10.0, -1) is False


def test_actualizar_stock_suma_y_resta():
    _alta_producto_basico("A1", stock=10)
    assert gestor.actualizar_stock("A1", 5) is True
    assert gestor.INVENTARIO["A1"]["stock"] == 15
    assert gestor.actualizar_stock("A1", -15) is True
    assert gestor.INVENTARIO["A1"]["stock"] == 0
    assert gestor.actualizar_stock("A1", -1) is False


def test_eliminar_producto():
    _alta_producto_basico("A1")
    assert gestor.eliminar_producto("A1") is True
    assert "A1" not in gestor.INVENTARIO
    assert gestor.eliminar_producto("A1") is False


def test_buscar_producto_por_nombre():
    gestor.agregarProducto("A1", "Café de grano", 185.0, 10)
    gestor.agregarProducto("A2", "Azúcar", 32.5, 40)
    resultados = gestor.buscarProducto("café")
    assert len(resultados) == 1
    assert resultados[0]["codigo"] == "A1"


def test_venta_descuenta_stock_y_asigna_folio():
    _alta_producto_basico("A1", precio=10.0, stock=50)
    venta = gestor.registrar_venta("A1", 3)
    assert venta is not None
    assert venta["folio"] == 1
    assert gestor.INVENTARIO["A1"]["stock"] == 47
    assert len(gestor.VENTAS) == 1


def test_venta_sin_descuento_aplica_iva():
    # 2 x $10 = $20, sin descuento, +16% de IVA = $23.20
    _alta_producto_basico("A1", precio=10.0, stock=50)
    venta = gestor.registrar_venta("A1", 2)
    assert venta["total"] == 23.2


def test_venta_con_descuento_por_volumen_medio():
    # 6 x $100 = $600 -> 5% de descuento -> $570 + IVA = $661.20
    _alta_producto_basico("A1", precio=100.0, stock=50)
    venta = gestor.registrar_venta("A1", 6)
    assert venta["total"] == 661.2


def test_venta_con_descuento_por_volumen_alto():
    # 20 x $100 = $2000 -> 10% de descuento -> $1800 + IVA = $2088.00
    _alta_producto_basico("A1", precio=100.0, stock=50)
    venta = gestor.registrar_venta("A1", 20)
    assert venta["total"] == 2088.0


def test_venta_cliente_vip_recibe_descuento_extra():
    # 6 x $100 = $600 -> 5% + 2% VIP = $42 de descuento -> $558 + IVA = $647.28
    _alta_producto_basico("A1", precio=100.0, stock=50)
    venta = gestor.registrar_venta("A1", 6, "VIP007")
    assert venta["total"] == 647.28


def test_venta_rechaza_stock_insuficiente():
    _alta_producto_basico("A1", stock=2)
    assert gestor.registrar_venta("A1", 3) is None
    # el stock no debe cambiar si la venta falla
    assert gestor.INVENTARIO["A1"]["stock"] == 2
    assert len(gestor.VENTAS) == 0


def test_venta_rechaza_producto_inexistente_y_cantidad_invalida():
    _alta_producto_basico("A1")
    assert gestor.registrar_venta("ZZZ", 1) is None
    assert gestor.registrar_venta("A1", 0) is None
    assert gestor.registrar_venta("A1", -2) is None


def test_cotizar_coincide_con_el_total_de_la_venta():
    _alta_producto_basico("A1", precio=100.0, stock=50)
    estimado = gestor.cotizar("A1", 6)
    venta = gestor.registrar_venta("A1", 6)
    assert estimado == venta["total"]
