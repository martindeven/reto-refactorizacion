# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es este proyecto

Aplicación de consola en Python 3.10+ para administrar el inventario y las ventas de la tienda "La Esquina": alta de productos, ventas con descuentos e IVA, cotizaciones, alertas de stock bajo, reportes y guardado en JSON. Es un **reto de refactorización**: el código funciona (todas las pruebas pasan) pero está escrito con malas prácticas a propósito. El objetivo es mejorarlo **sin cambiar su comportamiento**.

Archivos de `src/` (módulos planos que se importan entre sí con `import gestor`; `tests/conftest.py` agrega `src/` al `sys.path` y llama a `gestor.reiniciar_sistema()` antes y después de cada prueba):

| Archivo | Contenido |
|---|---|
| `gestor.py` | Estado global (`INVENTARIO`, `VENTAS`, `contadorVentas`, `ultimo_error`) y la lógica de negocio: alta/baja de productos, stock, búsqueda, `registrar_venta` (valida, calcula descuentos e IVA, descuenta stock, asigna folio y arma el ticket) y `cotizar`. |
| `almacen.py` | Guarda y carga el estado de `gestor` en un JSON (`inventario`, `ventas`, `contador`). |
| `reportes.py` | Stock bajo, reporte de inventario, total vendido, más vendidos y resumen de ventas. |
| `main.py` | Menú interactivo de consola. Solo entrada/salida; llama a los otros módulos. |

## Comandos

```bash
.venv/bin/pytest -v                                        # todas las pruebas
.venv/bin/pytest -v tests/test_gestor.py                   # un archivo
.venv/bin/pytest -v tests/test_gestor.py::test_cotizar_coincide_con_el_total_de_la_venta  # una prueba
.venv/bin/ruff check src                                   # linter (meta del reto: 0 errores)
cd src && python main.py                                   # app interactiva
```

Si `.venv` no existe: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.

## Reglas

- **No modificar** los tests existentes (`tests/`) ni `pyproject.toml`. Si un test falla, el error está en el código, no en el test. Tampoco silenciar ruff con `# noqa`.
- **No renombrar** `agregarProducto` ni `buscarProducto`: los usan los tests (por eso están en `ignore-names` de ruff).
- **El programa debe comportarse igual que antes**: mismos valores de regreso, mismos mensajes de error, mismo texto del ticket y de los reportes, mismos resultados de descuentos e IVA.
- También son API usada por los tests: `gestor.INVENTARIO`, `gestor.VENTAS`, `reiniciar_sistema`, `eliminar_producto`, `actualizar_stock`, `registrar_venta`, `cotizar`, `almacen.guardar_datos`/`cargar_datos` y `reportes.productos_stock_bajo`/`reporte_inventario`/`total_vendido`/`mas_vendidos`, además de las llaves de los dicts de producto (`codigo`, `nombre`, `precio`, `stock`) y de venta (`folio`, `codigo`, `nombre`, `cantidad`, `subtotal`, `descuento`, `impuesto`, `total`, `cliente`, `fecha`, `ticket`).
- **Archivos que no se leen**: `.claudeignore` lista lo que Claude Code no necesita leer (`.venv`, cachés, `.git`, basura de SO, `src/datos_ejemplo.json`). Como Claude Code no aplica ese archivo por sí solo, las mismas exclusiones están en `.claude/settings.json` como reglas `Read(...)` de `permissions.deny`. Si cambias una lista, cambia también la otra.

## Lo que es fácil romper sin darse cuenta

**Mensajes exactos de `ultimo_error`** (en este orden de validación; el orden importa porque decide qué mensaje sale):

| Función | Mensajes |
|---|---|
| `agregarProducto` | `"codigo vacio"` → `"el producto ya existe"` → `"precio invalido"` (precio ≤ 0) → `"stock invalido"` (stock < 0; 0 sí vale) |
| `eliminar_producto` | `"producto no existe"` |
| `actualizar_stock` | `"producto no existe"` → `"el stock no puede quedar negativo"` |
| `registrar_venta` | `"codigo vacio"` → `"producto no existe"` → `"cantidad invalida"` → `"stock insuficiente"` |
| `cotizar` | `"producto no existe"` → `"cantidad invalida"` (con código `""` da `"producto no existe"`; no revisa stock) |
| `almacen.cargar_datos` | `"el archivo no existe"`, `"archivo corrupto"` |

Los errores se señalan regresando `False` (altas, bajas, stock, carga) o `None` (venta, cotización), nunca con excepciones. `main.py` imprime `"Error:", gestor.ultimo_error`.

**Dinero y redondeo**
- En reportes el dinero se muestra con `"$" + str(round(v, 2))`: `$10.0`, `$32.5`, `$1234.56`. **No** `$10.00` (no usar f-strings con `:.2f`).
- En el ticket se usa `str()` del valor guardado: si el precio es entero, el subtotal sale `$20` y no `$20.0`.
- Sin descuento, `descuento` es `0` **entero**, no `0.0`. La línea `Descuento: -$...` del ticket solo aparece si el descuento es > 0.
- `subtotal`, `descuento` e `impuesto` se guardan redondeados a 2, pero `total = round(base + impuesto_sin_redondear, 2)`. No calcular el total sumando los valores ya redondeados.

**Reglas de negocio**
- Descuento por volumen sobre el subtotal (`precio * cantidad`): 10% si ≥ 1000; 5% si ≥ 500; si no, 0.
- VIP: el código de cliente empieza con `"VIP"`, y el extra solo aplica si `subtotal - descuento > 200` (estrictamente mayor, ya con el descuento por volumen). El extra es 2% **del subtotal**, no de lo ya descontado.
- IVA 16% sobre `subtotal - descuento`.
- `cotizar` usa la misma fórmula de volumen + IVA pero **no aplica VIP** y no toca stock, folios ni `VENTAS`.
- Stock bajo es `stock < 5` (estrictamente menor). Se usa en `productos_stock_bajo` y en la marca `  <-- STOCK BAJO` de `reporte_inventario`; si se vuelve constante, que sea una sola para los dos.
- Los folios son consecutivos (`contadorVentas + 1`) y continúan después de cargar el JSON.
- `fecha` usa el formato `"%Y-%m-%d %H:%M:%S"`.

**Estado global**
- `INVENTARIO` y `VENTAS` **no se deben reasignar** (`INVENTARIO = {}`), solo mutar en sitio (`.clear()`, `.append()`, `[k] = v`), como ya hacen `reiniciar_sistema` y `cargar_datos`. Reasignarlos dejaría desconectada cualquier referencia guardada al objeto (p. ej. un `from gestor import INVENTARIO`).
- `contadorVentas` y `ultimo_error` sí se reasignan, así que fuera de `gestor.py` se leen como `gestor.contadorVentas` / `gestor.ultimo_error`. Un `from gestor import contadorVentas` copiaría un valor viejo. Si se renombran, hay que cambiar a la vez `gestor.py`, `almacen.py` y `main.py`.
- `registrar_venta` descuenta el stock mutando el dict del producto dentro de `INVENTARIO`, y regresa el mismo dict que agrega a `VENTAS`.

**Reportes y app**
- `reporte_inventario` y `resumen_ventas` imprimen **y** regresan el texto; hay que conservar ambas cosas.
- `mas_vendidos`: en empates queda primero el que se vendió primero. `sorted(..., key=..., reverse=True)` lo respeta (es estable); `sorted(...)[::-1]` no.
- `cd src && python main.py` busca `src/datos_ejemplo.json`, no el de la raíz, así que arranca vacío hasta que guardas (opción 8). Es el comportamiento actual: no "arreglarlo" dentro de una refactorización.

**Código muerto** (nadie lo llama; se puede borrar): `gestor.calcular_descuento_viejo`, el bloque comentado `exportar_txt`, `reportes.reporteViejoCSV`, `gestor.MODO_DEBUG`.

## Convenciones

- Funciones y variables en `snake_case` (excepto `agregarProducto`/`buscarProducto`); constantes en `MAYÚSCULAS` en lugar de números mágicos.
- Type hints en funciones nuevas o modificadas (sintaxis 3.10: `str | None`, `list[dict]`).
- Docstrings en español.
- Archivos siempre con `with open(...)`.
- Evitar `if` anidados: cláusulas de guarda con `return` temprano.
- Nombres descriptivos (`subtotal`, `descuento`), no `aux`, `temp2`, `x`, `hacer_cosa`.
- Funciones con complejidad ≤ 10 (regla C901 de ruff).

Ejemplo (descuento VIP de `registrar_venta`):

```python
# Antes
if cliente != "" and cliente is not None:
    if len(cliente) >= 3:
        if cliente[0:3] == "VIP":
            if aux - desc > 200:
                desc = desc + aux * 0.02

# Después
PREFIJO_VIP = "VIP"
MONTO_MINIMO_VIP = 200
TASA_EXTRA_VIP = 0.02


def calcular_extra_vip(cliente: str | None, subtotal: float, descuento: float) -> float:
    """Regresa el descuento extra VIP, o 0 si el cliente no califica."""
    if not cliente or not cliente.startswith(PREFIJO_VIP):
        return 0
    if subtotal - descuento <= MONTO_MINIMO_VIP:
        return 0
    return subtotal * TASA_EXTRA_VIP

# ...y en registrar_venta:
descuento = descuento + calcular_extra_vip(cliente, subtotal, descuento)
```

## Cómo trabajar

1. **Un cambio a la vez.** Una refactorización = un commit.
2. **Antes de editar, explica el plan**: qué vas a cambiar, en qué archivos, por qué mejora el código y qué riesgo hay de cambiar el comportamiento (revisa la sección anterior). Espera mi visto bueno.
3. Al terminar corre `.venv/bin/pytest -v` y `.venv/bin/ruff check src`. Si falla un test, corrige el código, nunca el test.
4. Agrega una fila a `BITACORA.md` (copia de `BITACORA_TEMPLATE.md`): prompt usado, cambio realizado, justificación y resultado de los tests.
5. Haz commit en la rama `refactorizacion` con un mensaje en español que describa la refactorización.

## Cambios a este archivo

| Versión | Fecha | Cambio |
|---|---|---|
| 1 | 2026-10-06 | Versión inicial: proyecto, comandos, reglas, puntos frágiles, convenciones y forma de trabajo. |
| 2 | 2026-10-06 | Regla sobre `.claudeignore` y su equivalente en `.claude/settings.json` (`permissions.deny`). |
