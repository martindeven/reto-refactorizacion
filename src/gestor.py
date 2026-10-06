"""Modulo principal del gestor de inventario y ventas de "La Esquina".

Aqui vive casi toda la logica del negocio. Historicamente este archivo
lo fueron parchando varias personas, asi que hay de todo un poco.
"""

from datetime import datetime

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
INVENTARIO = {}
VENTAS = []
contadorVentas = 0
ultimo_error = ""


def reiniciar_sistema():
    """Borra todo el estado del sistema (inventario, ventas y folios)."""
    global contadorVentas, ultimo_error
    INVENTARIO.clear()
    VENTAS.clear()
    contadorVentas = 0
    ultimo_error = ""


def agregarProducto(codigo, nombre, precio, stock):
    # valida los datos y da de alta un producto en el inventario
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
    x = {}
    x["codigo"] = codigo
    x["nombre"] = nombre
    x["precio"] = precio
    x["stock"] = stock
    INVENTARIO[codigo] = x
    return True


def eliminar_producto(codigo):
    """Quita un producto del inventario. Regresa False si no existe."""
    global ultimo_error
    if codigo in INVENTARIO:
        del INVENTARIO[codigo]
        return True
    ultimo_error = "producto no existe"
    return False


def actualizar_stock(codigo, cantidad):
    """Suma unidades al stock (o resta si la cantidad es negativa)."""
    global ultimo_error
    if codigo not in INVENTARIO:
        ultimo_error = "producto no existe"
        return False
    aux = INVENTARIO[codigo]["stock"] + cantidad
    if aux < 0:
        ultimo_error = "el stock no puede quedar negativo"
        return False
    INVENTARIO[codigo]["stock"] = aux
    return True


def buscarProducto(texto):
    # busca productos cuyo nombre contenga el texto (sin importar mayusculas)
    temp2 = []
    for k in INVENTARIO:
        if texto.lower() in INVENTARIO[k]["nombre"].lower():
            temp2.append(INVENTARIO[k])
    return temp2


def _calcular_subtotal(precio, cantidad):
    """Regresa el subtotal de la compra: precio por cantidad, sin descuentos."""
    return precio * cantidad


def _descuento_por_volumen(subtotal):
    """Regresa el descuento por volumen: 10% desde 1000, 5% desde 500, si no 0."""
    if subtotal >= MONTO_DESCUENTO_ALTO:
        return subtotal * TASA_DESCUENTO_ALTO
    if subtotal >= MONTO_DESCUENTO_MEDIO:
        return subtotal * TASA_DESCUENTO_MEDIO
    return 0


def _calcular_iva(base):
    """Regresa el IVA de la base (subtotal ya con descuentos), sin redondear."""
    return base * TASA_IVA


def registrar_venta(codigo, cantidad, cliente=""):
    """Registra una venta completa.

    Esta funcion hace de todo: valida los datos, calcula descuentos e
    impuestos, descuenta el stock, genera el folio, arma el ticket en
    texto y guarda el registro en la lista de ventas. Si algo falla
    regresa None y deja el motivo en ultimo_error.
    """
    global contadorVentas, ultimo_error
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
    temp2 = INVENTARIO[codigo]
    if not temp2["stock"] >= cantidad:
        ultimo_error = "stock insuficiente"
        return None
    aux = _calcular_subtotal(temp2["precio"], cantidad)
    desc = _descuento_por_volumen(aux)
    # los clientes cuyo codigo empieza con VIP tienen un extra,
    # pero solo si su compra (ya con descuento) pasa de cierto monto
    es_vip = cliente is not None and cliente.startswith(PREFIJO_VIP)
    if es_vip and aux - desc > MONTO_MINIMO_VIP:
        desc = desc + aux * TASA_EXTRA_VIP
    base = aux - desc
    impuesto = _calcular_iva(base)
    total = round(base + impuesto, 2)
    # descontar del inventario
    temp2["stock"] = temp2["stock"] - cantidad
    contadorVentas = contadorVentas + 1
    venta = {}
    venta["folio"] = contadorVentas
    venta["codigo"] = codigo
    venta["nombre"] = temp2["nombre"]
    venta["cantidad"] = cantidad
    venta["subtotal"] = round(aux, 2)
    venta["descuento"] = round(desc, 2)
    venta["impuesto"] = round(impuesto, 2)
    venta["total"] = total
    venta["cliente"] = cliente
    venta["fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # armar el ticket en texto plano
    t = ""
    t = t + "TIENDA LA ESQUINA\n"
    t = t + "----------------------------\n"
    t = t + "Folio: " + str(venta["folio"]) + "\n"
    t = t + venta["nombre"] + " x" + str(cantidad) + "\n"
    t = t + "Subtotal: $" + str(venta["subtotal"]) + "\n"
    if desc > 0:
        t = t + "Descuento: -$" + str(venta["descuento"]) + "\n"
    t = t + "IVA: $" + str(venta["impuesto"]) + "\n"
    t = t + "TOTAL: $" + str(venta["total"]) + "\n"
    venta["ticket"] = t
    VENTAS.append(venta)
    return venta


def cotizar(codigo, cantidad):
    """Calcula cuanto costaria una compra sin registrar la venta."""
    global ultimo_error
    if codigo not in INVENTARIO:
        ultimo_error = "producto no existe"
        return None
    if cantidad is None or cantidad <= 0:
        ultimo_error = "cantidad invalida"
        return None
    aux = _calcular_subtotal(INVENTARIO[codigo]["precio"], cantidad)
    desc = _descuento_por_volumen(aux)
    base = aux - desc
    total = base + _calcular_iva(base)
    return round(total, 2)
