# R5 — Manejo de errores en src/almacen.py

## Context
`almacen.py` abre archivos sin `with`, cierra a mano en dos sitios, usa `except Exception`,
copia datos con bucles y `hay_archivo` usa if/else. Solo se edita `src/almacen.py`.
Usos externos: `main.py` (hay_archivo, cargar_datos, guardar_datos) y `tests/test_almacen.py`;
no se renombra nada.

## Excepción elegida: `ValueError`
`json.JSONDecodeError` y `UnicodeDecodeError` son subclases de `ValueError`. Hoy `except Exception`
atrapa ambos (JSON mal formado y bytes no UTF-8) y responde "archivo corrupto". Solo
`JSONDecodeError` cambiaría el comportamiento con un archivo no UTF-8 (pasaría de False a
propagar excepción). `ValueError` conserva ambos casos y deja de tragarse errores ajenos.

## Cambios
- `guardar_datos(ruta: str) -> bool`: `with open(ruta, "w", encoding="utf-8")` + `json.dump(...)`
  con los mismos `indent=2`, `ensure_ascii=False`, mismas claves; retorna True.
- `cargar_datos(ruta: str) -> bool`:
  - guard clause de inexistente (igual).
  - `with open(ruta, encoding="utf-8") as archivo:` (sin "r"); dentro, `try: json.load / except ValueError`
    → `ultimo_error = "archivo corrupto"`, `return False`. `open()` queda fuera del try.
  - mismo orden: `INVENTARIO.clear()`, `INVENTARIO.update(datos["inventario"])`,
    `VENTAS.clear()`, `VENTAS.extend(datos["ventas"])`, `contador_ventas = datos.get("contador", 0)`.
    Sin reasignar los globales; el KeyError por claves faltantes se conserva.
- `hay_archivo(ruta: str) -> bool`: `return os.path.exists(ruta)`, con docstring (reemplaza el comentario).
- Type hints + docstring breve en español en las tres funciones.

## Casos que siguen igual
| Caso | Resultado |
|---|---|
| Archivo inexistente | `ultimo_error="el archivo no existe"`, False |
| JSON mal formado / no UTF-8 | `"archivo corrupto"`, False |
| Permisos/ruta inválida en `open` | La excepción se propaga (open fuera del try) |
| Falta "inventario"/"ventas" | KeyError (con el mismo estado parcial) |
| Éxito | True; guardar siempre True |

Diferencia teórica mínima: si `"inventario"` fuera una lista de pares, `update` la aceptaría
y el bucle viejo daba TypeError. Es un formato que `guardar_datos` nunca produce.

## Verificación
`pytest` (20 tests), `ruff check src` → esperado 6 errores (4×UP009, I001, C901 de menu;
desaparecen SIM115, SIM103, UP015), mostrar `git diff`. Commit atómico
`refactor: ... (R5)` y entrada en la bitácora solo cuando lo apruebes.
