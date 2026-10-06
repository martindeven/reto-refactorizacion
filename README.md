# Gestor de inventario y ventas — Tienda "La Esquina"

Aplicación de consola en Python para administrar el inventario y las ventas de
una tienda pequeña: alta de productos, registro de ventas con descuentos e IVA,
cotizaciones, alertas de stock bajo, reporte de más vendidos y guardado de datos
en JSON.

Este repositorio es la solución del **reto "Refactorización asistida por IA"**:
el código original funcionaba pero tenía muchas malas prácticas, y se mejoró con
Claude Code **sin cambiar su comportamiento**. Cada cambio, el prompt que se usó
y cómo se verificó están en la **[bitácora (BITACORA.md)](BITACORA.md)**; la
salida de las pruebas de cada paso está en [`docs/evidencias/`](docs/evidencias/).

## Requisitos

- **Python 3.10 o superior** (el código usa anotaciones como `str | None`).
- `git`.
- Las dependencias de desarrollo (`pytest` y `ruff`) se instalan con
  `requirements.txt`. La app no usa ninguna librería externa.

## Clonar e instalar

```bash
git clone https://github.com/martindeven/reto-refactorizacion.git
cd reto-refactorizacion
# Mientras el Pull Request no se haya integrado a main, el código está en esta rama:
git switch refactorizacion

python3 -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

En Windows usa `python` en lugar de `python3`. Todos los comandos siguientes
suponen que el entorno virtual está activado y que estás en la raíz del
proyecto.

## Correr las pruebas

```bash
pytest                       # toda la suite
pytest -v                    # mostrando cada prueba
pytest tests/test_gestor.py  # un solo archivo
pytest tests/test_gestor.py::test_cotizar_coincide_con_el_total_de_la_venta  # una sola prueba
```

Resultado esperado: `41 passed`. Son las 20 pruebas originales del reto (sin
modificar) más 21 pruebas de caracterización en `tests/test_casos_borde.py`, que
fijan el comportamiento exacto (texto del ticket y de los reportes, mensajes de
error, límites del descuento VIP, empates en "más vendidos", stock bajo).

## Correr el linter

```bash
ruff check src
```

Resultado esperado: `All checks passed!`. Las reglas están en `pyproject.toml`
(estilo PEP 8, nombres, imports, `with open`, `if` anidados, complejidad
máxima 10).

## Abrir la app

```bash
cd src
python main.py
```

Aparece un menú con 8 opciones; la 8 guarda y sale. Ojo: la app lee y guarda
`src/datos_ejemplo.json` (relativo a `src/`), **no** el `datos_ejemplo.json` de
la raíz, así que la primera vez arranca vacía. Para empezar con los productos de
ejemplo, cópialo antes de abrirla:

```bash
cp datos_ejemplo.json src/       # desde la raíz del proyecto
```

`src/datos_ejemplo.json` está en `.gitignore`: lo que guardes ahí no se sube al
repositorio.

## Antes y después

Medido con los comandos de arriba sobre el commit original (`e42f747`) y sobre
el resultado final.

| Métrica | Antes | Después |
|---|---|---|
| Errores de `ruff check src` | 20 | **0** |
| Pruebas (`pytest`) | 20 (pasan) | **41** (pasan): 20 originales + 21 de caracterización |
| Complejidad ciclomática máxima | 17 (`menu`) | **6** (`registrar_venta`) |
| Funciones con complejidad > 10 | 2 (`menu` 17, `registrar_venta` 12) | **0** |
| Funciones en `src/` | 20 | 33 (más pequeñas, con type hints y docstring) |

La complejidad de cada función se midió con:

```bash
ruff check src --select C901 --config "lint.mccabe.max-complexity=0"
```

El detalle de las 10 refactorizaciones (código muerto, constantes, cálculo
compartido, cláusulas de guarda, división de `registrar_venta` y de `menu`,
nombres, manejo de errores, reportes y type hints) está en
[BITACORA.md](BITACORA.md).

## Estructura del proyecto

```
.
├── src/
│   ├── gestor.py         # Reglas de negocio, estado global, productos y ventas
│   ├── almacen.py        # Carga y guardado de datos (JSON)
│   ├── reportes.py       # Reportes e indicadores
│   └── main.py           # Menú interactivo de consola
├── tests/                # Pruebas (pytest); test_casos_borde.py es nuevo
├── docs/evidencias/      # Salida de pytest y ruff de cada refactorización
├── BITACORA.md           # Bitácora: diagnóstico, prompts, cambios y reflexión
├── CLAUDE.md             # Contexto y reglas para Claude Code
├── .claudeignore         # Lo que Claude Code no necesita leer
├── .claude/settings.json # Las mismas exclusiones, aplicadas con permissions.deny
├── datos_ejemplo.json    # Datos de ejemplo (ver "Abrir la app")
├── requirements.txt
└── pyproject.toml        # Configuración de ruff y pytest
```

---

## Sobre el reto (enunciado original)

### Instrucciones

1. **Configura el proyecto para Claude Code.** Crea un `CLAUDE.md` con el
   contexto del proyecto (qué hace, cómo correr las pruebas, reglas que la IA
   debe respetar — por ejemplo, *no modificar los tests*) y un `.claudeignore`
   con lo que no debe leer (entornos virtuales, cachés, datos generados).
2. **Explora el código con Claude Code.** Pídele un diagnóstico: qué *code
   smells* detecta y qué refactorizaciones recomienda. Prioriza.
3. **Aplica al menos 5 refactorizaciones significativas**, una a la vez.
4. **Valida con `pytest` y `ruff check src` después de CADA refactorización.**
   La suite de pruebas es de caja negra: si un cambio la rompe, la
   refactorización alteró el comportamiento. **No está permitido modificar los
   tests** para hacerlos pasar.
5. **Documenta cada prompt en la bitácora** (`BITACORA.md`) y cierra con una
   reflexión.
6. **Entrega mediante Pull Request** (rama `refactorizacion` → `main`), con
   commits atómicos y la bitácora incluida.

### Criterios de evaluación

| Criterio | Descripción | Peso |
|----------|-------------|------|
| Configuración | `CLAUDE.md` y `.claudeignore` completos y pertinentes | 15% |
| Calidad de refactorizaciones | ≥5 refactorizaciones significativas, bien elegidas y bien ejecutadas | 30% |
| Tests pasando | La suite completa pasa al final (y después de cada cambio) | 20% |
| Bitácora | Prompts documentados, cambios explicados y justificados | 25% |
| Reflexión | Análisis crítico del trabajo con la IA | 10% |

### Reglas

- No modificar los archivos de `tests/` ni `pyproject.toml`.
- El código final de `src/` debe pasar `ruff check src` **sin errores**. Las
  funciones `agregarProducto` y `buscarProducto` conservan su nombre porque los
  tests las usan.
- El comportamiento observable del programa debe mantenerse idéntico.
- Se puede (y se debe) usar Claude Code, pero quien lo usa es responsable de
  revisar, entender y validar cada cambio que la IA proponga.
