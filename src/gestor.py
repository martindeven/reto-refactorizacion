"""Modulo principal del gestor de inventario y ventas de "La Esquina".

Aqui vive casi toda la logica del negocio. Historicamente este archivo
lo fueron parchando varias personas, asi que hay de todo un poco.
"""

from datetime import datetime
from typing import Any

# Un producto: {"codigo", "nombre", "precio", "stock"}.
Producto = dict[str, Any]
# Una venta: {"folio", "codigo", "nombre", "cantidad", "subtotal", "descuento",
# "impuesto", "total", "cliente", "fecha", "ticket"}.
Venta = dict[str, Any]

# ---------------------------------------------------------------
# Reglas de negocio
# ---------------------------------------------------------------
# Descuento por volumen: se aplica sobre el subtotal (precio * cantidad)
MONTO_DESCUENTO_ALTO = 1000  # subtotal >= 1000 -> 10%
TASA_DESCUENTO_ALTO = 0.10
MONTO_DESCUENTO_MEDIO = 500  # subtotal >= 500 -> 5%
TASA_DESCUENTO_MEDIO = 0.05

# Cliente VIP: codigo que empieza con este prefijo (distingue mayusculas)
PREFIJO_VIP = "VIP"
MONTO_MINIMO_VIP = 200  # el extra aplica si subtotal - descuento > 200
TASA_EXTRA_VIP = 0.02  # 2% extra calculado sobre el subtotal

TASA_IVA = 0.16  # IVA sobre el subtotal ya descontado

STOCK_MINIMO = 5  # stock por debajo de este numero es "stock bajo"

# ---------------------------------------------------------------
# Estado global de la aplicacion (inventario, ventas y contadores)
# ---------------------------------------------------------------
INVENTARIO: dict[str, Producto] = {}
VENTAS: list[Venta] = []
contador_ventas: int = 0
ultimo_error: str = ""


def reiniciar_sistema() -> None:
    """Borra todo el estado del sistema (inventario, ventas y folios)."""
    global contador_ventas, ultimo_error
    INVENTARIO.clear()
    VENTAS.clear()
    contador_ventas = 0
    ultimo_error = ""


def agregarProducto(codigo: str | None, nombre: str, precio: float, stock: int) -> bool:
    """Valida los datos y da de alta un producto en el inventario."""
    global ultimo_error
    if codigo is None or codigo == "":
        ultimo_error = "codigo vacio"
        return False
    if codigo in INVENTARIO:
        ultimo_error = "el producto ya existe"
        return False
    if precio <= 0:
        ultimo_error = "precio invalido"
        return False
    if stock < 0:
        ultimo_error = "stock invalido"
        return False
    producto: Producto = {}
    producto["codigo"] = codigo
    producto["nombre"] = nombre
    producto["precio"] = precio
    producto["stock"] = stock
    INVENTARIO[codigo] = producto
    return True


def eliminar_producto(codigo: str) -> bool:
    """Quita un producto del inventario. Regresa False si no existe."""
    global ultimo_error
    if codigo in INVENTARIO:
        del INVENTARIO[codigo]
        return True
    ultimo_error = "producto no existe"
    return False


def actualizar_stock(codigo: str, cantidad: int) -> bool:
    """Suma unidades al stock (o resta si la cantidad es negativa)."""
    global ultimo_error
    if codigo not in INVENTARIO:
        ultimo_error = "producto no existe"
        return False
    nuevo_stock = INVENTARIO[codigo]["stock"] + cantidad
    if nuevo_stock < 0:
        ultimo_error = "el stock no puede quedar negativo"
        return False
    INVENTARIO[codigo]["stock"] = nuevo_stock
    return True


def buscarProducto(texto: str) -> list[Producto]:
    """Busca productos cuyo nombre contenga el texto (sin importar mayusculas)."""
    encontrados: list[Producto] = []
    for codigo in INVENTARIO:
        if texto.lower() in INVENTARIO[codigo]["nombre"].lower():
            encontrados.append(INVENTARIO[codigo])
    return encontrados


def _calcular_subtotal(precio: float, cantidad: int) -> float:
    """Regresa el subtotal de la compra: precio por cantidad, sin descuentos."""
    return precio * cantidad


def _descuento_por_volumen(subtotal: float) -> float:
    """Regresa el descuento por volumen: 10% desde 1000, 5% desde 500, si no 0."""
    if subtotal >= MONTO_DESCUENTO_ALTO:
        return subtotal * TASA_DESCUENTO_ALTO
    if subtotal >= MONTO_DESCUENTO_MEDIO:
        return subtotal * TASA_DESCUENTO_MEDIO
    return 0


def _calcular_iva(base: float) -> float:
    """Regresa el IVA de la base (subtotal ya con descuentos), sin redondear."""
    return base * TASA_IVA


def _siguiente_folio() -> int:
    """Incrementa el contador de ventas y regresa el nuevo folio."""
    global contador_ventas
    contador_ventas = contador_ventas + 1
    return contador_ventas


def _construir_registro_venta(folio: int, codigo: str, producto: Producto,
                              cantidad: int, cliente: str | None,
                              subtotal: float, descuento: float,
                              impuesto: float, total: float) -> Venta:
    """Arma el dict de la venta (sin ticket); redondea subtotal, descuento e IVA."""
    venta: Venta = {}
    venta["folio"] = folio
    venta["codigo"] = codigo
    venta["nombre"] = producto["nombre"]
    venta["cantidad"] = cantidad
    venta["subtotal"] = round(subtotal, 2)
    venta["descuento"] = round(descuento, 2)
    venta["impuesto"] = round(impuesto, 2)
    venta["total"] = total
    venta["cliente"] = cliente
    venta["fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return venta


def _generar_ticket(venta: Venta) -> str:
    """Regresa el ticket de la venta en texto plano."""
    ticket = ""
    ticket = ticket + "TIENDA LA ESQUINA\n"
    ticket = ticket + "----------------------------\n"
    ticket = ticket + "Folio: " + str(venta["folio"]) + "\n"
    ticket = ticket + venta["nombre"] + " x" + str(venta["cantidad"]) + "\n"
    ticket = ticket + "Subtotal: $" + str(venta["subtotal"]) + "\n"
    if venta["descuento"] > 0:
        ticket = ticket + "Descuento: -$" + str(venta["descuento"]) + "\n"
    ticket = ticket + "IVA: $" + str(venta["impuesto"]) + "\n"
    ticket = ticket + "TOTAL: $" + str(venta["total"]) + "\n"
    return ticket


def registrar_venta(codigo: str | None, cantidad: int | None,
                    cliente: str | None = "") -> Venta | None:
    """Registra una venta completa.

    Valida los datos, calcula descuentos e impuestos, descuenta el stock,
    asigna el folio, arma el registro y el ticket y lo guarda en VENTAS.
    Si algo falla regresa None y deja el motivo en ultimo_error.
    """
    global ultimo_error
    if codigo is None or codigo == "":
        ultimo_error = "codigo vacio"
        return None
    if codigo not in INVENTARIO:
        ultimo_error = "producto no existe"
        return None
    # "not ... > 0" en vez de "<= 0" para que NaN siga siendo invalido
    if cantidad is None or not cantidad > 0:
        ultimo_error = "cantidad invalida"
        return None
    producto = INVENTARIO[codigo]
    if not producto["stock"] >= cantidad:
        ultimo_error = "stock insuficiente"
        return None
    subtotal = _calcular_subtotal(producto["precio"], cantidad)
    descuento = _descuento_por_volumen(subtotal)
    # los clientes cuyo codigo empieza con VIP tienen un extra,
    # pero solo si su compra (ya con descuento) pasa de cierto monto
    es_vip = cliente is not None and cliente.startswith(PREFIJO_VIP)
    if es_vip and subtotal - descuento > MONTO_MINIMO_VIP:
        descuento = descuento + subtotal * TASA_EXTRA_VIP
    base = subtotal - descuento
    impuesto = _calcular_iva(base)
    total = round(base + impuesto, 2)
    # descontar del inventario
    producto["stock"] = producto["stock"] - cantidad
    folio = _siguiente_folio()
    venta = _construir_registro_venta(folio, codigo, producto, cantidad, cliente,
                                      subtotal, descuento, impuesto, total)
    venta["ticket"] = _generar_ticket(venta)
    VENTAS.append(venta)
    return venta


def cotizar(codigo: str | None, cantidad: int | None) -> float | None:
    """Calcula cuanto costaria una compra sin registrar la venta."""
    global ultimo_error
    if codigo not in INVENTARIO:
        ultimo_error = "producto no existe"
        return None
    if cantidad is None or cantidad <= 0:
        ultimo_error = "cantidad invalida"
        return None
    subtotal = _calcular_subtotal(INVENTARIO[codigo]["precio"], cantidad)
    descuento = _descuento_por_volumen(subtotal)
    base = subtotal - descuento
    total = base + _calcular_iva(base)
    return round(total, 2)
