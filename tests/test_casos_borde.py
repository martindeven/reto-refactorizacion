# -*- coding: utf-8 -*-
"""Pruebas de caracterizacion: fijan como se comporta el codigo HOY.

Se agregaron antes de refactorizar para detectar cambios de comportamiento
que la suite original no cubre (texto exacto del ticket y los reportes,
mensajes de error, limites del descuento VIP, empates, stock bajo).
Algunas cosas parecen raras ("$10.0", descuento 0 entero, cotizar sin VIP),
pero son el comportamiento actual y una refactorizacion debe conservarlas.
"""

import gestor
import reportes
import almacen


# ---------------------------------------------------------------
# Ticket
# ---------------------------------------------------------------

def test_ticket_sin_descuento():
    gestor.agregarProducto("A1", "Café", 10.0, 50)
    venta = gestor.registrar_venta("A1", 2)
    assert venta["ticket"] == (
        "TIENDA LA ESQUINA\n"
        "----------------------------\n"
        "Folio: 1\n"
        "Café x2\n"
        "Subtotal: $20.0\n"
        "IVA: $3.2\n"
        "TOTAL: $23.2\n"
    )


def test_ticket_con_descuento():
    gestor.agregarProducto("B1", "Galletas", 100.0, 50)
    venta = gestor.registrar_venta("B1", 6)
    assert venta["ticket"] == (
        "TIENDA LA ESQUINA\n"
        "----------------------------\n"
        "Folio: 1\n"
        "Galletas x6\n"
        "Subtotal: $600.0\n"
        "Descuento: -$30.0\n"
        "IVA: $91.2\n"
        "TOTAL: $661.2\n"
    )


def test_sin_descuento_el_descuento_es_cero_entero():
    gestor.agregarProducto("A1", "Café", 10.0, 50)
    venta = gestor.registrar_venta("A1", 2)
    assert venta["descuento"] == 0
    assert type(venta["descuento"]) is int


# ---------------------------------------------------------------
# Mensajes de ultimo_error (y el orden en que se validan)
# ---------------------------------------------------------------

def test_errores_de_agregar_producto():
    assert gestor.agregarProducto("", "X", 10.0, 1) is False
    assert gestor.ultimo_error == "codigo vacio"
    assert gestor.agregarProducto(None, "X", 10.0, 1) is False
    assert gestor.ultimo_error == "codigo vacio"
    assert gestor.agregarProducto("A1", "X", 0, 1) is False
    assert gestor.ultimo_error == "precio invalido"
    assert gestor.agregarProducto("A1", "X", 10.0, -1) is False
    assert gestor.ultimo_error == "stock invalido"
    # stock 0 si es valido
    assert gestor.agregarProducto("A1", "X", 10.0, 0) is True
    # el duplicado se revisa antes que el precio
    assert gestor.agregarProducto("A1", "X", -5.0, 1) is False
    assert gestor.ultimo_error == "el producto ya existe"


def test_errores_de_eliminar_y_actualizar_stock():
    assert gestor.eliminar_producto("ZZ") is False
    assert gestor.ultimo_error == "producto no existe"
    assert gestor.actualizar_stock("ZZ", 1) is False
    assert gestor.ultimo_error == "producto no existe"
    gestor.agregarProducto("A1", "X", 10.0, 3)
    assert gestor.actualizar_stock("A1", -4) is False
    assert gestor.ultimo_error == "el stock no puede quedar negativo"


def test_errores_de_registrar_venta_en_orden():
    gestor.agregarProducto("A1", "X", 10.0, 3)
    assert gestor.registrar_venta("", 1) is None
    assert gestor.ultimo_error == "codigo vacio"
    assert gestor.registrar_venta(None, 1) is None
    assert gestor.ultimo_error == "codigo vacio"
    # producto inexistente se revisa antes que la cantidad
    assert gestor.registrar_venta("ZZ", 0) is None
    assert gestor.ultimo_error == "producto no existe"
    assert gestor.registrar_venta("A1", 0) is None
    assert gestor.ultimo_error == "cantidad invalida"
    assert gestor.registrar_venta("A1", None) is None
    assert gestor.ultimo_error == "cantidad invalida"
    assert gestor.registrar_venta("A1", 4) is None
    assert gestor.ultimo_error == "stock insuficiente"


def test_errores_de_cotizar():
    gestor.agregarProducto("A1", "X", 10.0, 3)
    # con codigo vacio cotizar dice "producto no existe", no "codigo vacio"
    assert gestor.cotizar("", 1) is None
    assert gestor.ultimo_error == "producto no existe"
    assert gestor.cotizar("A1", 0) is None
    assert gestor.ultimo_error == "cantidad invalida"
    # cotizar no revisa el stock
    assert gestor.cotizar("A1", 100) == 1044.0


def test_errores_de_cargar_datos(tmp_path):
    assert almacen.cargar_datos(str(tmp_path / "no_existe.json")) is False
    assert gestor.ultimo_error == "el archivo no existe"
    corrupto = tmp_path / "corrupto.json"
    corrupto.write_text("{esto no es json", encoding="utf-8")
    assert almacen.cargar_datos(str(corrupto)) is False
    assert gestor.ultimo_error == "archivo corrupto"


def test_reiniciar_sistema_limpia_el_error():
    gestor.eliminar_producto("ZZ")
    gestor.reiniciar_sistema()
    assert gestor.ultimo_error == ""


# ---------------------------------------------------------------
# Descuento VIP y cotizar
# ---------------------------------------------------------------

def test_vip_justo_en_200_no_aplica():
    # 2 x $100 = $200, sin descuento por volumen; 200 no es > 200
    gestor.agregarProducto("A1", "X", 100.0, 50)
    venta = gestor.registrar_venta("A1", 2, "VIP007")
    assert venta["descuento"] == 0
    assert venta["total"] == 232.0


def test_vip_arriba_de_200_si_aplica():
    # $201 -> 2% de $201 = $4.02 -> $196.98 + IVA = $228.50
    gestor.agregarProducto("A1", "X", 201.0, 50)
    venta = gestor.registrar_venta("A1", 1, "VIP007")
    assert venta["descuento"] == 4.02
    assert venta["total"] == 228.5


def test_vip_se_suma_al_descuento_por_volumen_y_es_sobre_el_subtotal():
    # $500 -> 5% = $25; quedan $475 > 200 -> +2% de $500 = $10 -> $35
    gestor.agregarProducto("A1", "X", 100.0, 50)
    venta = gestor.registrar_venta("A1", 5, "VIP007")
    assert venta["descuento"] == 35.0


def test_vip_en_minusculas_no_aplica():
    gestor.agregarProducto("A1", "X", 201.0, 50)
    venta = gestor.registrar_venta("A1", 1, "vip1")
    assert venta["descuento"] == 0
    assert venta["total"] == 233.16


def test_cotizar_no_aplica_vip():
    gestor.agregarProducto("A1", "X", 100.0, 50)
    estimado = gestor.cotizar("A1", 6)
    venta_vip = gestor.registrar_venta("A1", 6, "VIP007")
    assert estimado == 661.2
    assert venta_vip["total"] == 647.28
    # cotizar no toca stock, folios ni ventas
    assert gestor.INVENTARIO["A1"]["stock"] == 44
    assert len(gestor.VENTAS) == 1


# ---------------------------------------------------------------
# Formato de dinero en reportes
# ---------------------------------------------------------------

def test_reporte_inventario_texto_completo():
    gestor.agregarProducto("A1", "Leche", 10.0, 4)
    gestor.agregarProducto("A2", "Pan", 2.5, 5)
    assert reportes.reporte_inventario() == (
        "===== INVENTARIO =====\n"
        "A1 | Leche | $10.0 | stock: 4  <-- STOCK BAJO\n"
        "A2 | Pan | $2.5 | stock: 5\n"
        "Valor total del inventario: $52.5\n"
    )


def test_resumen_ventas_texto_completo():
    gestor.agregarProducto("A1", "Leche", 10.0, 4)
    gestor.registrar_venta("A1", 1)
    assert reportes.resumen_ventas() == (
        "===== RESUMEN DE VENTAS =====\n"
        "Folio 1: Leche x1 = $11.6\n"
        "Numero de ventas: 1\n"
        "Total del dia: $11.6\n"
    )


def test_reportes_sin_datos_muestran_cero_sin_decimales():
    assert reportes.resumen_ventas() == (
        "===== RESUMEN DE VENTAS =====\n"
        "Numero de ventas: 0\n"
        "Total del dia: $0\n"
    )
    assert reportes.reporte_inventario() == (
        "===== INVENTARIO =====\n"
        "Valor total del inventario: $0\n"
    )
    assert reportes.total_vendido() == 0


def test_reportes_tambien_imprimen_el_texto(capsys):
    texto = reportes.resumen_ventas()
    assert texto in capsys.readouterr().out


# ---------------------------------------------------------------
# Mas vendidos
# ---------------------------------------------------------------

def test_mas_vendidos_empate_conserva_el_orden_de_primera_venta():
    gestor.agregarProducto("A1", "Café", 10.0, 100)
    gestor.agregarProducto("B1", "Galletas", 5.0, 100)
    gestor.agregarProducto("C1", "Pan", 2.0, 100)
    gestor.registrar_venta("B1", 2)
    gestor.registrar_venta("A1", 2)
    gestor.registrar_venta("C1", 5)
    assert reportes.mas_vendidos() == [("C1", 5), ("B1", 2), ("A1", 2)]
    assert reportes.mas_vendidos(1) == [("C1", 5)]


def test_mas_vendidos_sin_ventas_es_lista_vacia():
    assert reportes.mas_vendidos() == []


# ---------------------------------------------------------------
# Stock bajo
# ---------------------------------------------------------------

def test_stock_en_5_no_es_bajo_y_en_4_si():
    gestor.agregarProducto("A1", "Cinco", 10.0, 5)
    gestor.agregarProducto("A2", "Cuatro", 10.0, 4)
    bajos = reportes.productos_stock_bajo()
    assert [p["codigo"] for p in bajos] == ["A2"]
