# R2 — Constantes con nombre + extraer descuento por volumen y VIP

## Context
`registrar_venta` y `cotizar` (src/gestor.py) duplican el cálculo de descuento por volumen y
usan números mágicos; `reportes.py` repite el stock mínimo 5 (líneas 16 y 29). Objetivo:
eliminar duplicación y magia sin cambiar comportamiento. Los nombres solo se usan en
gestor.py y reportes.py (grep en main.py, almacen.py y tests/: sin otros usos).

## Constantes (gestor.py, tras el import, antes del estado global)
| Constante | Valor | Reemplaza |
|---|---|---|
| `TASA_IVA` | 0.16 | `0.16` en registrar_venta (l.131) y cotizar (l.180) |
| `UMBRAL_DESCUENTO_ALTO` / `DESCUENTO_ALTO` | 1000 / 0.10 | l.116-117, 174-175 |
| `UMBRAL_DESCUENTO_MEDIO` / `DESCUENTO_MEDIO` | 500 / 0.05 | l.119-120, 177-178 |
| `PREFIJO_VIP` | "VIP" | l.127 |
| `MONTO_MINIMO_VIP` | 200 | l.128 |
| `DESCUENTO_VIP` | 0.02 | l.129 (no estaba en tu lista, pero es otro 0.02 mágico) |
| `STOCK_MINIMO` | 5 | gestor (nueva) y `gestor.STOCK_MINIMO` en reportes.py l.16 y l.29 |

## Funciones nuevas (gestor.py, antes de `registrar_venta`)
- `calcular_descuento_volumen(subtotal: float) -> float`: guard clauses con `>=`;
  devuelve `subtotal * DESCUENTO_ALTO`, `subtotal * DESCUENTO_MEDIO` o `0` (int, igual
  que hoy, para que `round(desc, 2)` siga dando `0`). Usada por `registrar_venta` y `cotizar`.
- `_es_cliente_vip(cliente: str | None) -> bool`: `False` si `cliente` es None o `""`;
  si no, `cliente.startswith(PREFIJO_VIP)` (equivale a `len>=3 and [0:3]=="VIP"`).
  Solo la usa `registrar_venta`.

## Cambios en las funciones existentes
- `registrar_venta`: `desc = calcular_descuento_volumen(aux)`; bloque VIP queda como
  `if _es_cliente_vip(cliente) and aux - desc > MONTO_MINIMO_VIP: desc = desc + aux * DESCUENTO_VIP`
  (estricto `>`, mismo orden de operaciones). `impuesto = base * TASA_IVA`; `total` igual.
- `cotizar`: `desc = calcular_descuento_volumen(aux)`; **sin VIP**;
  `total = base + base * TASA_IVA` (NO `base * 1.16`); `round(total, 2)` igual.
- `reportes.py`: `< 5` → `< gestor.STOCK_MINIMO` (estricto) en ambos sitios.
- No se tocan mensajes de `ultimo_error`, ticket, nombres, tests/ ni pyproject.toml.
- Type hints: solo en las funciones nuevas (no se tocan firmas existentes, para no ampliar alcance).

## Verificación
1. `pytest` → 20 passed; `ruff check src` → 0 errores.
2. Comprobación extra de equivalencia (script en scratchpad): comparar versión anterior
   (`git show HEAD:src/gestor.py`) vs nueva con subtotales en 499.99/500/999.99/1000 y
   clientes None/""/"VI"/"VIP"/"VIP007" (cotizar y registrar_venta: totales y descuentos idénticos).
3. Mostrar `git diff`. Luego commit `refactor: constantes y descuento por volumen (R2)`
   y entrada en `docs/bitacora.md` con el resultado de tests — solo tras tu aprobación.
