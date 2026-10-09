# R7 — Handlers por opción en `src/main.py`

## Contexto
`menu()` (C901 = 17) mezcla bucle, prompts y llamadas a gestor/reportes/almacen en un if/elif de 8 ramas. Se extrae un handler por opción y `menu()` pasa a despachar con un diccionario. Solo se toca `src/main.py`; comportamiento observable idéntico (no hay tests de main.py).

## Handlers (todos `-> None`, docstring breve en español)
| Opción | Handler | Contenido (mismo orden de prompts) |
|---|---|---|
| 1 | `_agregar_producto` | Codigo, Nombre, `pedir_numero("Precio: ")`, `int(pedir_numero("Stock inicial: "))`; "Producto agregado." o `print("Error:", gestor.ultimo_error)` |
| 2 | `_registrar_venta` | Codigo del producto, `int(pedir_numero("Cantidad: "))`, cliente; imprime `venta["ticket"]` o error |
| 3 | `_cotizar` | Codigo, cantidad (int), imprime `"Total estimado (con IVA): $" + str(total)` o error |
| 4 | `_mostrar_inventario` | `reportes.reporte_inventario()` |
| 5 | `_mostrar_resumen_ventas` | `reportes.resumen_ventas()` |
| 6 | `_mostrar_mas_vendidos` | `for par in reportes.mas_vendidos(): print(par[0], "->", par[1], "unidades")` |
| 7 | `_mostrar_alertas_stock` | guard clause si no hay bajos ("No hay productos con stock bajo."); si no, líneas "OJO:" |
| 8 | `_guardar_y_salir` | `almacen.guardar_datos(ARCHIVO)` + "Datos guardados. Hasta luego." |

Auxiliares (para evitar duplicar el patrón de error idéntico): `_imprimir_error()` → `print("Error:", gestor.ultimo_error)` (lee el valor en el momento de la llamada, mismo formato) y `_imprimir_menu()` con las 8 líneas literales.

## Despacho
- Constante `OPCIONES: dict[str, Callable[[], None]]` a nivel de módulo (constante, no estado global mutable; MAYUSCULAS) definida tras los handlers, claves "1".."7".
- La opción 8 no está en el dict de handlers "normales": `menu()` hace
  ```
  while True:
      print("")
      _imprimir_menu()
      opcion = input("Opcion: ")
      if opcion == "8":
          _guardar_y_salir()
          break
      handler = OPCIONES.get(opcion)
      if handler is None: print("Opcion no valida."); continue
      handler()
  ```
  Así solo la 8 sale del bucle y se conserva el `print("")` por iteración. (Alternativa: meter "8" en el dict y que el handler devuelva bool; descartada por ser menos clara. `_guardar_y_salir` queda como handler propio igualmente.)
- Inicio de `menu()` intacto: bienvenida, `hay_archivo` → `cargar_datos` → `print("Datos cargados de", ARCHIVO)` siempre (bug conocido, NO se arregla; se anota en la bitácora).
- Type hints: `pedir_numero(mensaje: str) -> float`, `menu() -> None`; `from collections.abc import Callable`. Imports existentes se dejan (I001 se arregla después con `ruff --fix`, como indica la meta: quedan 4×UP009 + I001 = 5 errores, sin C901).

## Verificación de equivalencia (scratchpad, fuera del repo)
1. `old/` = `git show HEAD:src/*` (todos los .py de src + `datos_ejemplo.json`); `new/` = src del working tree + misma copia de datos.
2. Script de stdin que recorre: 1 (alta ok), 1 con código duplicado (error), 1 con precio no numérico (reintento), 2 con cliente VIP, 2 con producto inexistente, 3, 4, 5, 6, 7, opción inválida, y 8 al final.
3. Ejecutar `python main.py < entrada` en cada carpeta (cwd = carpeta propia), comparar stdout/exit code con `diff`, y comparar `datos_ejemplo.json` guardado ignorando el campo de fecha.
4. En el repo: `pytest` (20 deben pasar), `ruff check src` (esperado: 5 errores, sin C901), y `git diff` mostrado. `main.py` nunca se ejecuta dentro del repo.
5. No se hace commit hasta que lo valides; luego commit `refactor: handlers por opcion en menu (R7)` y entrada en `docs/bitacora.md`.
