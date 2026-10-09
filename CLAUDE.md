# CLAUDE.md — Gestor de inventario y ventas "La Esquina"

## Qué es este proyecto
Aplicación de consola en Python (>= 3.10) para administrar inventario y ventas de una
tienda: alta de productos, ventas con descuentos e IVA, cotizaciones, alertas de stock
bajo, más vendidos y persistencia en JSON. Es un **reto de refactorización**: el código
funciona pero tiene mala calidad; el objetivo es mejorarlo sin cambiar su comportamiento.

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
