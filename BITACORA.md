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
| 1 | "Refactorización 1: quiero quitar código muerto." En `gestor.py`: `calcular_descuento_viejo`, el bloque comentado de `exportar_txt` y `MODO_DEBUG`; en `reportes.py`: `reporteViejoCSV` y el `import os` sin usar; en todos los archivos: `# -*- coding: utf-8 -*-`. "Antes de borrar, revisa con grep que nadie los use, ni en src/ ni en tests/." Correr pytest y `ruff check src --statistics`, guardar en `docs/evidencias/01_codigo_muerto.txt`, revertir si algo falla, anotar y hacer commit. | normal | Se verificó con `grep` en `src/` y `tests/` que cada elemento solo aparecía en su propia definición. Se eliminaron `calcular_descuento_viejo`, el bloque comentado `exportar_txt` y `MODO_DEBUG` (`gestor.py`); `reporteViejoCSV` e `import os` (`reportes.py`); y la línea de *encoding* en los 4 archivos de `src/` (en `tests/` se dejó porque no se modifican). −35 líneas. | El código que nadie llama confunde ("¿esto se usa?"), hay que mantenerlo y aparece en búsquedas. `reporteViejoCSV` además abría el archivo sin `with` y no seguía snake_case. En Python 3 el *encoding* UTF-8 ya es el predeterminado, así que esa línea sobra. Si algún día se necesita algo de esto, está en el historial de git. Como `main.py` no tiene pruebas, se probó también la app con entradas guionadas (8 opciones, salida correcta). | ✅ 41/41 | 20 → 13 (−4 UP009, −1 F401, −1 N802, −1 SIM115) |
| 2 | "Refactorización 2: en gestor.py y reportes.py hay números sueltos que no se entiende qué significan: 1000, 500, 0.10, 0.05 (descuentos por volumen), "VIP", 3, 200, 0.02 (cliente VIP), 0.16 (IVA) y 5 (stock mínimo). Conviértelos en constantes con nombre en MAYÚSCULAS al inicio de gestor.py, con un comentario corto. En reportes.py usa gestor.STOCK_MINIMO en vez de repetirla. Úsalas en registrar_venta y también en cotizar. Importante: los resultados tienen que salir exactamente iguales. No cambies el orden de las operaciones ni dónde se redondea, y el descuento inicial se queda como 0 (no 0.0)." | normal | Nueva sección "Reglas de negocio" al inicio de `gestor.py` con 9 constantes comentadas: `MONTO_DESCUENTO_ALTO`/`TASA_DESCUENTO_ALTO`, `MONTO_DESCUENTO_MEDIO`/`TASA_DESCUENTO_MEDIO`, `PREFIJO_VIP`, `MONTO_MINIMO_VIP`, `TASA_EXTRA_VIP`, `TASA_IVA` y `STOCK_MINIMO`. Se usan en `registrar_venta` y `cotizar`; `reportes.py` usa `gestor.STOCK_MINIMO` en sus dos comparaciones. Para el `3` no se creó otra constante: se usa `len(PREFIJO_VIP)`, que es lo que significa. Solo se sustituyeron números por nombres: mismas operaciones, mismo orden, mismos redondeos y `desc = 0` entero. | Cada número ahora tiene nombre y comentario, y vive en un solo lugar: cambiar el IVA o el stock mínimo es editar una línea (antes el 5 estaba en dos funciones y el 0.16 en dos). Derivar el 3 de `PREFIJO_VIP` evita que se desincronicen si cambia el prefijo. Además de las pruebas, se comparó la versión anterior contra la nueva en 20 000 ventas y cotizaciones al azar (con precios enteros y decimales y clientes `VIP`, `vip1`, `None`, etc.): resultados y tipos idénticos. | ✅ 41/41 | 13 → 13 (ninguna regla de ruff cubre números mágicos; el SIM108 y los SIM102 se quedan para cuando se aplanen los `if`) |
| 3 | "Refactorización 3: registrar_venta y cotizar en gestor.py repiten el mismo cálculo (subtotal, descuento por volumen, base e IVA). Quiero sacarlo a funciones pequeñas que usen las dos. Antes de editar, explícame: en qué se diferencian las dos funciones (por ejemplo cotizar no aplica VIP ni revisa stock), qué funciones nuevas propones, con nombre que empiece con _ y una línea de qué hacen, por qué el resultado sigue siendo exactamente el mismo, sobre todo en 500 y 1000. Espera a que te diga que sí. No cambies los nombres de las funciones públicas, lo que regresan, los mensajes de error ni el orden en que se validan las cosas." | plan → normal | En plan, Claude Code explicó las diferencias (validación y su orden, VIP solo en ventas, efectos, retorno y redondeos) y propuso 3 funciones privadas en `gestor.py`: `_calcular_subtotal(precio, cantidad)`, `_descuento_por_volumen(subtotal)` (guardas con `return`, mismo orden `>= 1000` y luego `>= 500`, `return 0` entero) y `_calcular_iva(base)`. Ya aprobado, `registrar_venta` y `cotizar` las usan; validaciones, bloque VIP, ticket y redondeos sin tocar. | El cálculo vive en un solo lugar: cambiar una regla de descuento o el IVA ya no exige editar dos funciones que podían desincronizarse. Las comparaciones y operaciones de punto flotante son las mismas en el mismo orden, así que 1000 → 10 %, 999.99 → 5 %, 500 → 5 %, 499.99 → 0. Comprobado comparando la versión anterior contra la nueva en 32 casos límite (499.99/500/500.01, 999.99/1000/1000.01, VIP en 200/200.01, con precios `int` y `float`) y 20 000 al azar: venta completa, tipos (`descuento` 0 sigue `int`) y `cotizar` idénticos. | ✅ 41/41 | 13 → 11 (−SIM108; −C901 de `registrar_venta`, cuya complejidad bajó de 12 a 10) |
| 4 | "Refactorización 4: hay if muy anidados en gestor.py y almacen.py. Quiero que las validaciones salgan rápido en vez de meterse cada vez más adentro." (con ejemplo antes/después de cláusulas de guarda) "Aplícalo a: las validaciones de registrar_venta (mismo orden y mismos mensajes), la validación de cliente VIP (son 4 if anidados, déjalo en una sola condición clara que no truene con None o ""), el descuento por volumen (quitar el else anidado), hayArchivo en almacen.py (que regrese os.path.exists directo). No uses "if not codigo" porque cambiaría qué se considera vacío." | normal | `registrar_venta`: la pirámide de 4 niveles `if/else` pasa a 4 cláusulas de guarda en el mismo orden y con los mismos mensajes; se quitó `temp2 = None`. VIP: los 4 `if` anidados pasan a `es_vip = cliente is not None and cliente.startswith(PREFIJO_VIP)` y un solo `if es_vip and aux - desc > MONTO_MINIMO_VIP`. `hayArchivo`: `return os.path.exists(ruta)`. El descuento por volumen **ya no tenía** `else` anidado (se arregló en R3 con `_descuento_por_volumen`), así que no se tocó. Ver "Detalle de la refactorización 4" abajo. | Se lee de arriba abajo: cada guarda descarta un caso y el camino feliz queda sin sangría. Para las cantidades se negó la condición original (`not cantidad > 0`, `not stock >= cantidad`) en vez de invertir el operador (`<= 0`, `<`): con `nan` la versión "obvia" **registra una venta con cantidad NaN**, comprobado en una copia aparte. Comparación contra la versión anterior: 1 400 combinaciones de entradas raras (código `None`/`""`/inexistente/minúsculas, cantidad `None`/0/negativa/`nan`/`inf`/decimal, stock 0 y 5, 10 clientes), con el mismo `ultimo_error`, inventario, ventas y tipo de excepción; más 20 000 ventas al azar y `hayArchivo` con archivo/carpeta/inexistente/`""`. Todo idéntico. | ✅ 41/41 | 11 → 7 (−3 SIM102, −1 SIM103) |
| 5 | "Refactorización 5: registrar_venta todavía hace muchas cosas: valida, calcula, baja el stock, saca el folio, arma el registro y el ticket. ruff dice que es muy compleja (C901). Propón cómo dividirla antes de editar. Mi idea: _generar_ticket: el texto del ticket debe quedar idéntico, letra por letra. _construir_registro_venta: mismas claves y en el mismo orden. _siguiente_folio: para el contador de ventas. registrar_venta queda corta, solo llamando a las demás en el mismo orden de antes." | plan → normal | Antes de editar, Claude Code aclaró que `registrar_venta` **ya no salía en C901** (complejidad 12 → 10 en R3 y → 7 en R4; el único C901 es `menu`) y propuso la división; se aprobó sin `_validar_venta`. Nuevas en `gestor.py`: `_siguiente_folio()` (incrementa `contadorVentas` y regresa el folio), `_construir_registro_venta(...)` (mismas claves en el mismo orden; los `round` de subtotal, descuento e IVA se movieron tal cual) y `_generar_ticket(venta)` (las mismas líneas `t = t + ...`, movidas sin cambiar el texto). `registrar_venta` llama a todo en el mismo orden: validar → calcular → bajar stock → folio → registro → ticket → `VENTAS.append`. Validaciones y cálculo sin tocar. | Cada función hace una sola cosa y se puede leer, probar o cambiar por separado (p. ej. el formato del ticket ya no vive junto a la lógica de inventario). En el ticket hubo dos cambios necesarios: `str(cantidad)` → `str(venta["cantidad"])` (es el mismo objeto) y `if desc > 0` → `if venta["descuento"] > 0`, que da lo mismo porque el descuento positivo más chico es mayor a $4, así que redondear a 2 decimales no puede volverlo 0. Comparación contra la versión anterior: 400 secuencias de 25 operaciones con errores intercalados (3 537 ventas): registro con claves en el mismo orden, valores y tipos, ticket, inventario, `VENTAS` y `contadorVentas` idénticos; el folio continúa igual tras recargar. | ✅ 41/41 | 7 → 7 (`registrar_venta` ya no estaba en C901; su complejidad bajó de 7 a 6) |

> Agrega más filas si realizas más de 5 refactorizaciones.

### Detalle de la refactorización 4: por qué cada condición nueva hace lo mismo

| Antes | Después | Por qué es lo mismo |
|---|---|---|
| `if codigo is not None and codigo != "":` … `else: "codigo vacio"` | `if codigo is None or codigo == "":` → `"codigo vacio"` | Negación exacta (De Morgan): `not (A and B)` = `not A or not B`. Igual que antes, solo `None` y `""` son "vacío": no se usó `if not codigo`, que también trataría `0` como vacío. |
| `if codigo in INVENTARIO:` … `else: "producto no existe"` | `if codigo not in INVENTARIO:` → `"producto no existe"` | `not in` es la negación exacta de `in`. Va en segundo lugar, como antes. |
| `if cantidad is not None and cantidad > 0:` … `else: "cantidad invalida"` | `if cantidad is None or not cantidad > 0:` → `"cantidad invalida"` | De Morgan sobre la misma comparación. **No** se usó `cantidad <= 0`: con `nan`, `nan > 0` y `nan <= 0` son ambos `False`, así que `<= 0` dejaría pasar NaN (comprobado: registra la venta). `is None` va primero, como antes, para no comparar `None > 0`. |
| `if INVENTARIO[codigo]["stock"] >= cantidad:` … `else: "stock insuficiente"` | `temp2 = INVENTARIO[codigo]` y `if not temp2["stock"] >= cantidad:` → `"stock insuficiente"` | Misma comparación negada (mismo motivo que arriba: `stock < nan` también es `False`). `temp2` es el mismo dict que antes, ahora asignado después de comprobar que existe. |
| 4 `if` VIP: `cliente != "" and cliente is not None`, `len(cliente) >= len(PREFIJO_VIP)`, `cliente[0:len(PREFIJO_VIP)] == PREFIJO_VIP`, `aux - desc > MONTO_MINIMO_VIP` | `es_vip = cliente is not None and cliente.startswith(PREFIJO_VIP)` y `if es_vip and aux - desc > MONTO_MINIMO_VIP:` | `startswith` hace exactamente "largo suficiente y los primeros caracteres iguales"; con `""` regresa `False`, así que el chequeo de vacío sobra. `is not None` va antes, así que `None` no truena. Sigue distinguiendo mayúsculas (`"vip1"` no aplica) y el `> 200` sigue siendo estricto y después del descuento por volumen. Ningún cliente de texto da resultado distinto. |
| `if os.path.exists(ruta): return True else: return False` | `return os.path.exists(ruta)` | `os.path.exists` ya regresa `True`/`False` (tipo `bool`), así que el `if` no agregaba nada. |
| Descuento por volumen (`else: if ...`) | Sin cambio | Ya se había aplanado en la refactorización 3 (`_descuento_por_volumen` con `return` tempranos). |

## Experimento: prompt vago vs detallado

**Modo:** plan (solo lectura; no se editó código).

**Prompt A (vago):**

> mejora el código de gestor.py

**Prompt B (detallado, refactorización 2):** ver la fila 2 de la tabla de arriba (números mágicos → constantes, con la condición de que los resultados salgan exactamente iguales, sin cambiar el orden de las operaciones ni los redondeos, y con el descuento inicial en `0`).

**Qué respondió Claude Code al prompt A:** un plan con 7 cambios juntos en `gestor.py`: cláusulas de guarda en `registrar_venta`, función de descuento compartida con `cotizar`, función para el ticket con f-strings, renombrar variables (incluido `contadorVentas` → `contador_ventas`), *list comprehension* en `buscarProducto`, diccionarios literales y type hints; y como sugerencia, excepciones en vez de `ultimo_error` y una clase en vez del estado global.

**Revisión de esa respuesta:**

- **Muchos cambios a la vez:** ~120 líneas en un solo diff, equivalente a 4–5 refactorizaciones. Si un test falla, no se sabe qué lo rompió.
- **Nombres que usan otros módulos:** respetaba `agregarProducto`/`buscarProducto` solo porque CLAUDE.md lo dice. Pero renombraba `contadorVentas` únicamente en `gestor.py`, y `almacen.py` lo usa: `guardar_datos` tronaría y el folio se reiniciaría al cargar. **Comprobado** en una copia aparte: renombrarlo solo en `gestor.py` hace fallar `test_guardar_y_cargar_conserva_los_datos` y `test_el_folio_continua_despues_de_recargar` con `AttributeError` (39/41).
- **Textos de salida:** el prompt no los protege. Pasar el ticket a f-strings invita a `:.2f` (`$20.00` en vez de `$20.0`) o a un `descuento` `0.0`; solo lo atraparían las pruebas de caracterización.
- **Reglas de CLAUDE.md:** rompía "un cambio a la vez" y "una refactorización = un commit".

| | Prompt A: "mejora el código de gestor.py" | Prompt B: refactorización 2 |
|---|---|---|
| Qué tanto cambia | Mucho: casi todo `gestor.py` (~120 líneas, 7 tipos de cambio) y obliga a tocar `almacen.py` | Poco: solo números → constantes; 2 archivos, +34/−16, sin cambiar la lógica |
| Qué tan riesgoso es | Alto: rompe 2 tests (`contadorVentas`) y puede cambiar textos, tipos y el orden de los mensajes de error | Bajo: 41/41 tests y salidas idénticas en 20 000 casos al azar |
| Qué tan fácil es revisar | Difícil: un diff grande que mezcla estructura, nombres y formato | Fácil: cada línea cambiada es "número → nombre" |

**Conclusión:** el prompt vago no está "mal", pero le deja a la IA decidir el alcance, y la IA tiende a arreglar todo a la vez. Eso produce cambios grandes, difíciles de revisar y con riesgos que el prompt no menciona (como un nombre que se usa en otro archivo). El prompt detallado acota **qué** cambiar, **qué no** debe cambiar (resultados, orden, redondeos, `0` entero) y **cómo** validarlo. Así el cambio es pequeño, verificable y cabe en un commit. CLAUDE.md y las pruebas de caracterización ayudan como red de seguridad, pero no sustituyen a un buen prompt: atrapan errores después; el prompt detallado los evita antes.

## Mejoras a CLAUDE.md

**Modo:** normal.

**Prompt usado:**

> Ya llevo 3 refactorizaciones. Revisa la bitácora y el git log y dime qué reglas le faltan a CLAUDE.md para que no se repitan los problemas o dudas que tuvimos (por ejemplo: "antes de borrar algo revisa con grep que no se use", "no cambies el texto del ticket").
> Agrégalas, añade un ejemplo de un buen prompt para este proyecto y una fila nueva en la tabla "Cambios a este archivo" (versión 2).
> Anótalo en la bitácora en una sección "Mejoras a CLAUDE.md" con este prompt y haz commit.

> Nota: la versión 2 de CLAUDE.md ya existía (regla de `.claudeignore` / `permissions.deny`), así que esta quedó como **versión 3**.

| Qué pasó (bitácora / git log) | Regla agregada a CLAUDE.md |
|---|---|
| Dos prompts pidieron `docs/bitacora.md` y se terminó usando `BITACORA.md` en la raíz | La bitácora es `BITACORA.md` en la raíz, con sus columnas (incluye Modo y Ruff antes → después) |
| Refactorización 1: se revisó con grep antes de borrar | `grep -rn <nombre> src tests` antes de borrar o renombrar |
| Experimento: renombrar `contadorVentas` solo en `gestor.py` rompió 2 tests de `almacen` | Si un nombre se usa en otro módulo, renombrarlo en todos en el mismo commit |
| R1: la línea `# -*- coding` también estaba en `tests/` y se dejó | Los 4 tests originales no se tocan ni para limpiarlos; `test_casos_borde.py` es nuestro y, si falla, probablemente cambió el comportamiento |
| Riesgo visto en el experimento: f-strings con `:.2f` → `$20.00` | No cambiar el texto del ticket ni de los reportes; f-strings solo con `{valor}` |
| R2/R3: cuidado de no alterar operaciones ni redondeos | No reescribir fórmulas "equivalentes" (`base * 1.16`); mismas operaciones, mismo orden, `round` donde está, `0` entero |
| R2/R3: comparación contra la versión anterior en miles de casos | Si se toca un cálculo, comparar contra `HEAD` en casos al azar y en los límites |
| R1: `main.py` no tiene pruebas; se probó con entrada guionada | Comando de prueba manual del menú, corrido fuera de `src/` para no crear `src/datos_ejemplo.json` |
| R2: ruff se quedó en 13 | Anotar el resultado real de ruff aunque no baje |
| R3: VIP, ticket y validación se dejaron fuera a propósito | Hacer solo lo que pide el prompt y listar lo demás como pendiente |
| Evidencias `NN_nombre.txt` y commits "Refactorización N: …" | Formato de evidencias y de commits, con código, evidencia y bitácora en un solo commit |

También se **actualizó información vieja**: la tabla de `gestor.py` ahora menciona las constantes y las funciones `_calcular_subtotal`, `_descuento_por_volumen` y `_calcular_iva`; el stock bajo usa `STOCK_MINIMO`; se quitó la lista de "código muerto" (ya se borró en R1); y el ejemplo de convenciones usa `_calcular_extra_vip` (privada) y las constantes que ya existen. Se agregó un **ejemplo de buen prompt** (la refactorización del VIP) que dice qué cambiar, qué no, pide plan antes de editar y cómo validar. Sin cambios en `src/`: 41/41 tests, ruff 11.

## Reflexión final (10-15 líneas)

Responde: ¿Qué tan útil fue Claude Code para detectar y corregir los problemas?
¿Qué propuso la IA que tú no habías notado? ¿En qué casos tuviste que corregir
o rechazar sus sugerencias? ¿Qué aprendiste sobre refactorizar con apoyo de IA?

*(Escribe aquí tu reflexión)*
