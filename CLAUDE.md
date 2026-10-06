# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Contexto

Aplicación de consola en Python (3.10+) para el inventario y las ventas de la tienda "La Esquina". Es un **reto de refactorización**: el código funciona y todas las pruebas pasan, pero tiene malas prácticas a propósito. El objetivo es mejorar la calidad **sin cambiar el comportamiento observable**.

## Comandos

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

pytest                                              # suite completa (debe pasar siempre)
pytest tests/test_gestor.py                         # un archivo
pytest tests/test_gestor.py::test_cotizar_coincide_con_el_total_de_la_venta  # una prueba
ruff check src                                      # linter (meta: 0 errores)
ruff check src --fix                                # solo corrige lo trivial

cd src && python main.py                            # menú interactivo (usa datos_ejemplo.json)
```

Después de **cada** refactorización corre `pytest` y `ruff check src`.

## Reglas del reto (obligatorias)

- **No modificar** nada en `tests/` ni `pyproject.toml` (incluye no relajar reglas de ruff para que pase el linter).
- Los nombres `agregarProducto` y `buscarProducto` se conservan (los usan los tests; están en `ignore-names` de ruff). Todo lo demás debe ser snake_case.
- Una refactorización a la vez, con commits atómicos (idealmente uno por refactorización) en la rama `refactorizacion`. Cada una se documenta en `BITACORA.md` (copia de `BITACORA_TEMPLATE.md`).
- Ruff tiene activadas las reglas E, W, F, I, N, B, SIM, UP y C90 con `max-complexity = 10`: las funciones grandes (p. ej. `registrar_venta`, `menu`) hay que dividirlas, no silenciarlas con `# noqa`.

## Arquitectura

Todo está en `src/` como módulos planos que se importan entre sí sin paquete (`import gestor`). `tests/conftest.py` agrega `src/` a `sys.path` y llama a `gestor.reiniciar_sistema()` antes y después de cada prueba.

- `gestor.py` — dueño del **estado global** del módulo: `INVENTARIO` (dict código → dict de producto), `VENTAS` (lista de dicts), `contadorVentas` (último folio) y `ultimo_error` (mensaje del último fallo). Las funciones reportan errores regresando `False`/`None` y dejando el motivo en `ultimo_error`; `main.py` lo muestra al usuario.
- `almacen.py` — guarda/carga ese estado en JSON (`inventario`, `ventas`, `contador`). Escribe directamente sobre `gestor.INVENTARIO`, `gestor.VENTAS` y `gestor.contadorVentas`.
- `reportes.py` — lee `gestor.INVENTARIO` / `gestor.VENTAS`; `reporte_inventario` y `resumen_ventas` imprimen **y** regresan el texto.
- `main.py` — menú de consola (E/S únicamente).

Puntos delicados al refactorizar el estado global:

- Los tests acceden a `gestor.INVENTARIO`, `gestor.VENTAS` y a los dicts de producto/venta directamente, así que esos nombres y la forma de los dicts (llaves `codigo`, `nombre`, `precio`, `stock`; venta con `folio`, `codigo`, `nombre`, `cantidad`, `subtotal`, `descuento`, `impuesto`, `total`, `cliente`, `fecha`, `ticket`) son API pública.
- `contadorVentas` y `ultimo_error` se **reasignan**, por lo que otros módulos deben leerlos como `gestor.<nombre>`; un `from gestor import ...` capturaría un valor viejo. Si se renombran, hay que actualizar `almacen.py`, `main.py` y `reiniciar_sistema` a la vez.
- `INVENTARIO` y `VENTAS` se mutan en sitio (`.clear()`, `.append`); mantener esa semántica.
- `registrar_venta` muta el dict del producto en `INVENTARIO` (descuenta stock).

## Reglas de negocio (deben conservarse exactas)

- Descuento por volumen sobre el subtotal (`precio * cantidad`): 10% si ≥ 1000, 5% si ≥ 500, 0 en otro caso.
- Cliente cuyo código empieza con `"VIP"`: +2% **del subtotal** adicional, solo si `subtotal - descuento > 200`.
- IVA 16% sobre `subtotal - descuento`; `total` se redondea a 2 decimales. Subtotal, descuento e impuesto se guardan redondeados.
- `cotizar` usa la misma fórmula de volumen + IVA pero **sin** el extra VIP y sin tocar stock ni folios.
- Stock bajo: `stock < 5` (usado en `productos_stock_bajo` y en la marca `<-- STOCK BAJO` del reporte).
- El folio es consecutivo y continúa tras recargar desde JSON.
- El texto del ticket (y la línea de "Descuento" solo cuando hay descuento) y el formato de los reportes forman parte del comportamiento observable.

Código muerto conocido (sin llamadas): `gestor.calcular_descuento_viejo`, el bloque comentado `exportar_txt`, `reportes.reporteViejoCSV`.
