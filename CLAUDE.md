# CLAUDE.md — Gestor de inventario y ventas "La Esquina"

## Qué es este proyecto
Aplicación de consola en Python (>= 3.10) para administrar inventario y ventas de una
tienda: alta de productos, ventas con descuentos e IVA, cotizaciones, alertas de stock
bajo, más vendidos y persistencia en JSON. Es un **reto de refactorización**: el código
funciona pero tiene mala calidad; el objetivo es mejorarlo sin cambiar su comportamiento.
Estado actual: refactorizado (7 refactorizaciones documentadas en `docs/bitacora.md`);
`pytest` 20 passed y `ruff check src` en 0 errores.

## Estructura
- `src/gestor.py` — lógica de productos y ventas (estado global: `INVENTARIO`, `VENTAS`, ...)
- `src/almacen.py` — carga/guardado en JSON
- `src/reportes.py` — reportes e indicadores
- `src/main.py` — menú interactivo de consola
- `tests/` — suite pytest de caja negra (solo lectura)
- `docs/` — `bitacora.md`, `reflexion.md` y `evidencia/` (salidas de pytest/ruff)

## Comandos
```bash
source .venv/bin/activate        # entorno virtual (ya creado; pip install -r requirements.txt)
pytest                           # TODOS deben pasar (20 tests)
ruff check src                   # debe terminar en 0 errores
ruff check src --fix             # solo para arreglos triviales; revisar el diff
cd src && python main.py         # prueba manual (la opción 8 sobrescribe datos_ejemplo.json)
```

## Convenciones de código
- PEP 8, `snake_case` para funciones, variables y módulos; `MAYUSCULAS` para constantes.
- Nombres descriptivos en español, consistentes con el dominio (`precio`, `subtotal`, `cliente`).
  Prohibidos nombres como `temp2`, `aux`, `x`, `hacer_cosa`.
- Type hints en funciones nuevas o modificadas; docstring breve en español.
- Líneas <= 88 caracteres; funciones cortas y de una sola responsabilidad (complejidad ciclomática <= 10).
- Constantes con nombre en lugar de números mágicos (tasa de IVA, umbrales de descuento, stock mínimo).
- Preferir guard clauses a `if` anidados; `with open(...)` para archivos; excepciones específicas.
- No agregar estado global nuevo; no agregar dependencias.

## Restricciones (no negociables)
1. **No modificar `tests/` ni `pyproject.toml`**, ni "ajustar" tests para que pasen.
2. **Conservar los nombres `agregarProducto` y `buscarProducto`** (los usan los tests).
3. El comportamiento observable debe quedar **idéntico**: mismos valores de retorno,
   mensajes de `ultimo_error`, formato de tickets/reportes y redondeos.
4. Antes de renombrar o eliminar algo, buscar con `grep` quién lo usa (incluidos `tests/`).
5. No leer ni editar `.venv/`, cachés ni `docs/evidencia/`.

## Flujo de trabajo esperado
- **Una refactorización a la vez**, de alcance acotado; explicar el plan antes de editar.
- Después de CADA cambio: `pytest` y `ruff check src`; si algo falla, corregir antes de continuar.
- Un commit atómico por refactorización (`refactor: ...`), con el resultado de los tests en la bitácora.
- Mostrar el diff y justificar por qué mejora el código; el humano revisa y valida cada cambio.

## Ejemplos del estilo esperado (tomados de este proyecto)

**Guard clauses en lugar de `if` anidados** (`gestor._validar_venta`, mismo orden de validación y mismos mensajes):
```python
# antes: 4 niveles de if/else anidados dentro de registrar_venta
# después:
if codigo is None or codigo == "":
    ultimo_error = "codigo vacio"
    return None
if codigo not in INVENTARIO:
    ultimo_error = "producto no existe"
    return None
```

**Constantes con nombre y una sola fuente de verdad** (`gestor.py`):
```python
# antes: if aux >= 1000: desc = aux * 0.10   (duplicado en registrar_venta y cotizar)
UMBRAL_DESCUENTO_ALTO = 1000
DESCUENTO_ALTO = 0.10
descuento = calcular_descuento_volumen(subtotal)   # usado por ambas funciones
```

**Nombres que describen el contenido:** `temp2` → `coincidencias` / `producto`; `aux` → `subtotal` / `nuevo_stock`;
`hacer_cosa` → `formatear_dinero`; `contadorVentas` → `contador_ventas`.

**Recursos y errores:** `with open(...)` y `except ValueError` (no `except Exception`); `open()` fuera del `try`.

**Cuando algo "se ve mejor" pero cambia el comportamiento, NO se hace.** Ejemplos reales que se evitaron:
`base * 1.16` en lugar de `base + base * TASA_IVA` (puede variar el redondeo); f-strings en los reportes
(un valor no-`str` dejaría de lanzar `TypeError`); unificar `cotizar` con `registrar_venta` (la cotización no
aplica descuento VIP); corregir el `KeyError` de `cargar_datos` o el mensaje "Datos cargados" de `main.py`.

## Cómo verificar cuando no hay tests (p. ej. `main.py`)
1. Copiar la versión anterior (`git show HEAD:...` / `git archive HEAD src`) y la nueva a **carpetas temporales**
   con su propia copia de `datos_ejemplo.json` (la opción 8 del menú sobrescribe ese archivo).
2. Ejecutar `main.py` en cada una con la **misma entrada simulada por stdin** (las 8 opciones, duplicado, entrada
   no numérica, opción inválida, producto inexistente, venta VIP) y comparar salida y JSON guardado (sin la fecha).
3. Comprobar que la simulación recorrió lo que dice (contar `Opcion no valida`, `Descuento`, etc.): una
   verificación mal construida da una falsa seguridad.

## Plantilla de prompt que funcionó
`Refactorización N de 7 (categoría). Lee CLAUDE.md.` → **Contexto** (qué smell y dónde) → **Tarea** numerada y
acotada (un solo archivo o tema) → **Restricciones críticas** (lo que no debe cambiar, con el motivo) →
**Meta de ruff para este paso** → **Pide primero el plan** (plan mode o plan de 5 líneas) → **Verificación**
(pytest, ruff, y comparación contra la versión anterior si no hay tests) → mostrar el diff.

## Ajustes a estas instrucciones durante el reto (iteración)
- **Paso 2 (inicio):** versión inicial con proyecto, comandos, convenciones, restricciones y flujo.
- **Tras R2:** el plan de Claude prometió `ruff` en 0 errores en un paso intermedio → desde R3 cada prompt declara la
  *meta de ruff de ese paso* (R4: ~10, R5: 6, R6: 6, R7: 5; todas se cumplieron).
- **Tras R2:** Claude escribió por iniciativa propia (R2) una comparación contra la versión anterior; desde R6 el
  prompt pide que la IA escriba y ejecute esa verificación, y en R7 es obligatoria por no existir tests de `main.py`.
- **Tras R4:** Claude no mostró el mapa de renombres antes de aplicarlo → para cambios masivos, pedir el mapa como
  paso aparte y aprobarlo antes de editar.
- **Cierre del reto:** se incorporaron a este archivo los ejemplos, la guía de verificación sin tests y la plantilla de
  prompt de arriba, con lo aprendido en las 7 refactorizaciones.
