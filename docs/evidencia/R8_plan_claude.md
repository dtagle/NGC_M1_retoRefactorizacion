# Refactorización 8 de 8 — type hints, helper de error y docstrings

## Contexto
Últimos smells menores en `src/gestor.py` y `src/almacen.py`. El comportamiento debe quedar idéntico (56 tests en verde, `ruff check src` en 0). No se tocan `tests/` ni `pyproject.toml`.

## Plan por función (src/gestor.py)

**Docstring del módulo:** quitar "Historicamente este archivo lo fueron parchando varias personas, asi que hay de todo un poco". Nuevo: describe que contiene la lógica de productos, ventas y cotizaciones, y el estado global (`INVENTARIO`, `VENTAS`, `contador_ventas`, `ultimo_error`).

**Nuevo helper `_registrar_error(mensaje: str) -> None`** (junto al estado global): con `global ultimo_error` asigna la variable de módulo. No crea variable local; `main.py`, `almacen.py` y tests siguen leyendo/escribiendo `gestor.ultimo_error`.

| Función | Cambios |
|---|---|
| `reiniciar_sistema() -> None` | `ultimo_error = ""` → `_registrar_error("")`; `global` solo para `contador_ventas`. |
| `agregarProducto(codigo: str \| None, nombre: str, precio: float, stock: int) -> bool` | Comentario `# valida...` → docstring. 4 errores vía `_registrar_error` (mismo orden y mensajes). Diccionario como literal `{"codigo", "nombre", "precio", "stock"}` (mismo orden de claves). Sin `global`. |
| `eliminar_producto(codigo: str) -> bool` | `_registrar_error("producto no existe")`; sin `global`. |
| `actualizar_stock(codigo: str, cantidad: int) -> bool` | 2 errores vía helper; sin `global`. |
| `buscarProducto(texto: str) -> list[dict]` | Comentario → docstring; list comprehension `[p for p in INVENTARIO.values() if texto.lower() in p["nombre"].lower()]` (mismo orden; `texto.lower()` se sigue evaluando por elemento, por lo que con inventario vacío y `texto=None` ambas versiones no lanzan error). |
| `_validar_venta` | 4 errores vía helper; sin `global`. |
| `registrar_venta(codigo: str \| None, cantidad: int \| None, cliente: str = "") -> dict \| None` | Docstring actualizado (ya delega en `_validar_venta`, `calcular_descuento_volumen`, `_crear_venta`, `_armar_ticket`; quitar "hace de todo"). Se mantienen los comentarios útiles del VIP; se quitan los triviales (`# calculo del subtotal`, `# descontar del inventario`). Lógica y orden de operaciones sin cambios. |
| `cotizar(codigo: str, cantidad: int \| None) -> float \| None` | 2 errores vía helper; sin `global`. Sigue sin descuento VIP ni unificación con `registrar_venta`. |

Ya tipadas y sin cambio: `calcular_descuento_volumen`, `_es_cliente_vip`, `_validar_venta` (firma), `_crear_venta`, `_armar_ticket`.

## src/almacen.py
`guardar_datos`: `datos = {"inventario": ..., "ventas": ..., "contador": ...}` como literal (mismo orden de claves → mismo JSON).

## Riesgos vigilados
- Los hints no añaden validación ni conversión.
- `_registrar_error` debe ser el único punto de escritura vía `global`; `almacen.cargar_datos` sigue escribiendo `gestor.ultimo_error` directamente (sin cambios).
- Ruff: `global` sobrantes eliminados; líneas ≤ 88.

## Verificación
1. Script en el scratchpad (fuera del repo): carga `git show HEAD:src/gestor.py` y el `gestor.py` actual como módulos separados; ejecuta los mismos escenarios en ambos (altas válidas/inválidas: código vacío/None/duplicado, precio ≤0, stock <0; ventas con clientes ``, `None`, `VIP1`, cantidades 0/negativa/None/excesiva/grande para umbrales 500 y 1000; cotizaciones; búsquedas con distintas mayúsculas y sin resultados; `actualizar_stock` válido/negativo/inexistente; `eliminar_producto`; `reiniciar_sistema`) y compara tras cada operación valor de retorno (sin `fecha`), `ultimo_error`, `INVENTARIO`, `VENTAS` y `contador_ventas`. Comprueba además que la secuencia recorrió todos los mensajes de error. También compara el JSON de `guardar_datos` (sin fecha) antes/después.
2. `pytest` → 56 passed; `ruff check src` → 0 errores.
3. Mostrar `git diff`. Commit atómico `refactor: ...` y registro en `docs/bitacora.md` solo cuando el usuario lo pida/valide.
