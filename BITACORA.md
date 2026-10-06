# Bitácora de refactorización

**Nombre:** Martin Juarez
**Matrícula:**
**Fecha:** 2026-10-06

## Diagnóstico

**Modo:** plan (solo lectura; Claude Code no editó nada hasta que aprobé el plan).

**Prompt usado:**

> No edites nada todavía, solo quiero entender el código.
>
> Revisa src/ y dime qué problemas de calidad tiene (code smells). Puedes empezar por lo que marca ruff check src, pero dime también lo que ruff no detecta.
>
> Dame:
> 1. Una tabla: archivo y línea | problema | qué tan grave es | qué tan fácil es romper los tests si lo arreglo.
> 2. Un orden sugerido para arreglarlos, de lo más seguro a lo más riesgoso, un cambio por commit.
> 3. Cosas raras del programa que parecen error pero que NO debo cambiar porque los tests o el comportamiento dependen de ellas.
>
> Cuando te lo apruebe, crea BITACORA.md a partir de BITACORA_TEMPLATE.md con estas columnas:
> | # | Prompt usado | Modo | Cambio realizado | Justificación | Tests OK | Ruff (antes → después) |
> Pon este diagnóstico al inicio en una sección "Diagnóstico" junto con este prompt. Haz commit.


**Línea base:** `pytest` → 20 passed; `ruff check src` → 20 errores (7 corregibles con `--fix`). Evidencia en `docs/evidencias/00_inicio.txt`. `main.py` no tiene ninguna prueba: los cambios ahí se validan corriendo la app con entradas guionadas y comparando la salida antes/después.

### 1. Problemas encontrados

Gravedad: Alta = dificulta entender/cambiar el código o esconde bugs; Media = duplicación o confusión; Baja = cosmético. Riesgo = qué tan fácil es romper tests o comportamiento al arreglarlo.

#### Detectados por ruff (20)

| Archivo:línea | Problema | Gravedad | Riesgo al arreglar |
|---|---|---|---|
| `main.py:21` | C901 `menu` demasiado compleja (17 > 10): un `if/elif` gigante que pide datos, llama a la lógica e imprime | Alta | Medio — **sin tests**; hay que comparar la salida a mano |
| `gestor.py:86` | C901 `registrar_venta` demasiado compleja (12 > 10): valida, calcula, descuenta stock, arma folio, ticket y registro | Alta | Medio-alto — orden de mensajes de error, ticket, `descuento` entero |
| `gestor.py:126-128` | SIM102 ×3: cuatro `if` anidados para el descuento VIP | Media | Medio — la condición `> 200` es sobre `subtotal - descuento` |
| `gestor.py:120` | SIM108 `if/else` anidado para el descuento por volumen | Baja | Bajo |
| `almacen.py:16`, `:30`; `reportes.py:86` | SIM115 archivos abiertos sin `with` (si falla `json.dump`/`json.load` el archivo queda abierto) | Media | Bajo |
| `almacen.py:48` | N802 `hayArchivo` no es snake_case | Baja | Bajo — lo usa `main.py`, hay que renombrar ahí también |
| `almacen.py:50` | SIM103 `if ...: return True else: return False` | Baja | Nulo |
| `reportes.py:83` | N802 `reporteViejoCSV` (además es código muerto) | Baja | Nulo |
| `gestor.py:15` | N816 `contadorVentas` mixedCase | Baja | Bajo-medio — se reasigna; usarlo como `gestor.<nombre>` en `almacen.py` |
| `reportes.py:4` | F401 `import os` sin usar | Baja | Nulo |
| `main.py:4` | I001 imports desordenados | Baja | Nulo |
| `almacen.py:30` | UP015 `"r"` innecesario en `open` | Baja | Nulo |
| 4 archivos, línea 1 | UP009 `# -*- coding: utf-8 -*-` innecesario | Baja | Nulo |

#### Que ruff NO detecta

| Archivo:línea | Problema | Gravedad | Riesgo al arreglar |
|---|---|---|---|
| `gestor.py:114-121` y `173-179` | **Lógica duplicada**: el descuento por volumen y el IVA están copiados en `registrar_venta` y `cotizar`; si cambia una regla hay que acordarse de las dos | Alta | Medio — `cotizar` no debe aplicar VIP |
| `gestor.py:117-132`, `173-181`; `reportes.py:18`, `:31` | **Números mágicos**: 1000, 500, 0.10, 0.05, 200, 0.02, 0.16, 5, `"VIP"` | Media | Bajo si se respetan `>=`, `>` y `<` |
| `gestor.py:148-159` | Ticket armado con `t = t + ...` dentro de `registrar_venta` (mezcla formato con lógica de negocio) | Media | Medio — el texto debe quedar idéntico |
| `gestor.py:95-112` | Validación con 4 niveles de `if/else` en vez de cláusulas de guarda | Media | Medio — el orden decide el mensaje |
| `gestor.py:185-197`, `:17`; `reportes.py:83-92` | **Código muerto**: `calcular_descuento_viejo`, `exportar_txt` comentado, `reporteViejoCSV`, `MODO_DEBUG` | Media | Nulo (nadie los llama) |
| todos | **Nombres crípticos**: `x`, `aux`, `temp`, `temp2`, `t`, `s`, `d`, `p`, `c`, `n`, `op`, `hacer_cosa` | Media | Bajo |
| `reportes.py:59-66` | Ordenamiento de burbuja hecho a mano (el propio comentario dice "usar sorted") | Media | Bajo — conservar orden en empates y que sean tuplas |
| `reportes.py:18` y `:31` | Regla de stock bajo (`< 5`) repetida en dos funciones | Baja | Bajo |
| `reportes.py:69-79` | `resumen_ventas` vuelve a sumar los totales en vez de usar `total_vendido` | Baja | Bajo |
| `gestor.py:13-17`, `almacen.py`, `reportes.py` | **Estado global** compartido entre módulos; `almacen` escribe directo en `gestor` | Alta | **Alto** — los tests usan `gestor.INVENTARIO`/`VENTAS`; recomiendo no eliminarlo, solo encapsular el acceso |
| `gestor.py` (todas) | Errores comunicados por la variable global `ultimo_error` en vez de excepciones | Media | **Alto** — `main.py` y el contrato `False`/`None` dependen de ella; no cambiar |
| `main.py:21-82` | Entrada/salida mezclada con la lógica (formato de `mas_vendidos` y de stock bajo vive en el menú) | Media | Medio — sin tests |
| `almacen.py:33` | `except Exception` demasiado amplio | Baja | Bajo — si se acota, usar `ValueError` (cubre JSON y UTF-8 inválidos) |
| `almacen.py:39-44` | Copia elemento por elemento en vez de `.update()` / `.extend()` | Baja | Bajo — debe seguir mutando en sitio |
| todos | Sin type hints; algunas funciones con comentario en vez de docstring (`agregarProducto`, `buscarProducto`, `hayArchivo`, `hacer_cosa`, `pedir_numero`) | Baja | Nulo |

---

### 2. Orden sugerido (de lo más seguro a lo más riesgoso, un commit cada uno)

| # | Refactorización | Archivos | Ruff esperado | Riesgo |
|---|---|---|---|---|
| 1 | `ruff check src --fix` (encoding, `"r"`, imports, `os` sin usar). *Cosmético: no cuenta entre las 5 significativas* | todos | 20 → 13 | Nulo |
| 2 | Eliminar código muerto (`calcular_descuento_viejo`, `exportar_txt`, `reporteViejoCSV`, `MODO_DEBUG`) | gestor, reportes | 13 → 11 | Nulo |
| 3 | Persistencia: `with open`, `hayArchivo` → `hay_archivo` (y en `main.py`), `return os.path.exists(...)`, nombres claros | almacen, main | 11 → 7 | Bajo |
| 4 | `contadorVentas` → `contador_ventas` (la llave `"contador"` del JSON no cambia) | gestor, almacen | 7 → 6 | Bajo |
| 5 | Reportes: `hacer_cosa` → `formatear_dinero`, `sorted(..., reverse=True)` en vez de burbuja, constante `STOCK_MINIMO`, nombres claros, reusar `total_vendido` | reportes | 6 → 6 | Bajo |
| 6 | Constantes de negocio + función única de descuento por volumen e IVA usada por `registrar_venta` y `cotizar` | gestor | 6 → 5 | Medio |
| 7 | Dividir `registrar_venta`: guardas para validar, `calcular_extra_vip`, `armar_ticket` | gestor | 5 → 1 | Medio-alto |
| 8 | Dividir `menu`: una función por opción + diccionario de opciones (validar con salida guionada antes/después) | main | 1 → 0 | Medio |
| 9 | Type hints y docstrings en español en todo `src/` | todos | 0 → 0 | Nulo |

No recomendado: quitar el estado global o cambiar `ultimo_error` por excepciones (rompería tests y el contrato con `main.py`).

---

### 3. Cosas raras que NO hay que cambiar

1. `cotizar("")` responde `"producto no existe"` (no `"codigo vacio"`) y `cotizar` no revisa stock.
2. `cotizar` no aplica el descuento VIP; `registrar_venta` sí.
3. El extra VIP es 2% **del subtotal** (no de lo ya descontado) y solo si `subtotal - descuento > 200` (estricto).
4. Sin descuento, `descuento` vale `0` entero, no `0.0`; la línea "Descuento" del ticket solo sale si es > 0.
5. El dinero se muestra como `$10.0`, `$32.5` (`str(round(v, 2))`), nunca `$10.00`. En el ticket, un subtotal entero sale `$20`.
6. `total` usa el IVA **sin redondear**; `impuesto` se guarda redondeado. Puede que `subtotal - descuento + impuesto` difiera por un centavo de `total`: es así a propósito.
7. Stock bajo es `< 5`: un producto con 5 unidades **no** es stock bajo. Stock inicial 0 sí es válido; precio 0 no.
8. `mas_vendidos` regresa **tuplas** `(codigo, unidades)`, en empates queda primero el que se vendió primero, y el menú imprime el código, no el nombre.
9. `reporte_inventario` y `resumen_ventas` imprimen **y** regresan el texto.
10. `cd src && python main.py` carga `src/datos_ejemplo.json`, no el de la raíz: arranca vacío.
11. En el menú, `int(pedir_numero(...))` trunca (`2.7` → `2`), y escribir `nan` o `inf` truena el programa. Es un bug real, pero arreglarlo cambia el comportamiento: va aparte, no dentro de una refactorización.
12. `cargar_datos`: si falta `"contador"` usa 0, pero si falta `"inventario"` lanza `KeyError` (no se atrapa). `guardar_datos` siempre regresa `True`.
13. `cliente=None` en `registrar_venta` funciona y se guarda como `None`.

## Refactorizaciones

Registra aquí **cada refactorización** que realices con Claude Code. Copia el
prompt tal cual lo escribiste (o un resumen fiel si fue una conversación larga),
describe el cambio que se aplicó al código y justifica por qué mejora la calidad.
Después de cada cambio ejecuta `pytest` y `ruff check src` y anota el resultado.

**Modo** = modo de Claude Code con el que se hizo el cambio: plan, normal (aprobando cada edición) o auto-aceptar ediciones.

| # | Prompt usado | Modo | Cambio realizado | Justificación | Tests OK | Ruff (antes → después) |
|---|--------------|------|------------------|---------------|----------|------------------------|
| 0 | "Antes de empezar a refactorizar quiero más seguridad de no romper nada. Crea un archivo NUEVO tests/test_casos_borde.py (no toques los otros tests) que pruebe cómo funciona el código HOY, aunque algo parezca raro": ticket con y sin descuento, mensajes de `ultimo_error`, VIP en 200 / arriba de 200 / `"vip1"`, cotizar sin VIP, formato `$10.0` y `$0`, `mas_vendidos` con empate, stock 5 vs 4. "Si uno falla, el que está mal es el test." | normal | **Red de seguridad, no es refactorización.** Nuevo `tests/test_casos_borde.py` con 21 pruebas de caracterización que fijan el texto exacto del ticket y de los reportes, los 10 mensajes de error y su orden, los límites del VIP (incluye VIP + volumen), `cotizar` sin VIP ni stock, `descuento` 0 entero, empates en `mas_vendidos` y stock bajo `< 5`. No se tocaron `src/` ni los tests originales. | La suite original solo revisa totales; no detectaría un cambio en el ticket, en los mensajes de error, en `$10.0` → `$10.00` o en el orden de empates, que son justo los riesgos de las refactorizaciones 6–8. Evidencia: `docs/evidencias/00_casos_borde.txt`. | ✅ 41/41 (20 originales + 21 nuevas; las nuevas pasaron a la primera) | 20 → 20 |
| 1 |              |      |                  |               |          |                        |
| 2 |              |      |                  |               |          |                        |
| 3 |              |      |                  |               |          |                        |
| 4 |              |      |                  |               |          |                        |
| 5 |              |      |                  |               |          |                        |

> Agrega más filas si realizas más de 5 refactorizaciones.

## Reflexión final (10-15 líneas)

Responde: ¿Qué tan útil fue Claude Code para detectar y corregir los problemas?
¿Qué propuso la IA que tú no habías notado? ¿En qué casos tuviste que corregir
o rechazar sus sugerencias? ¿Qué aprendiste sobre refactorizar con apoyo de IA?

*(Escribe aquí tu reflexión)*
