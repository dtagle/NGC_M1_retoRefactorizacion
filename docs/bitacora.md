# Bitácora de refactorización

**Nombre:** Anabelle Denisse Dueñas Sánchez de Tagle
**Matrícula:** NextGencoding
**Fecha:** 08 octubre 2026
**Herramienta:** Claude Code v2.1.295 (Sonnet 5.5)

Registro de cada refactorización hecha con Claude Code: prompt literal, cambio, justificación
y resultado de los tests. Las salidas completas de `pytest` y `ruff` y las capturas de pantalla
están en [`evidencia/`](evidencia/).

## Punto de partida

- `pytest`: 20 passed — [`00_baseline_pytest.txt`](evidencia/00_baseline_pytest.txt)
- `ruff check src`: **20 errores** — [`00_baseline_ruff_resumen.txt`](evidencia/00_baseline_ruff_resumen.txt)
- Diagnóstico de code smells (plan mode, solo lectura): [`01_diagnostico.md`](evidencia/01_diagnostico.md)

## Resumen

| #  | Refactorización | Categoría | pytest | ruff check src |
|----|-----------------|-----------|--------|----------------|
| R1 | Eliminar código muerto | Código muerto | 20 passed | 17 errores (−3) |
| R2 | Constantes con nombre y extraer descuento por volumen / cliente VIP | Extraer funciones | 20 passed | 12 errores (−5) |
| R3 | `registrar_venta`: guard clauses y extracción de `_validar_venta`, `_crear_venta`, `_armar_ticket` | Simplificar condicionales / extraer funciones | 20 passed | 12 errores (±0) |
| R4 | Renombrar símbolos y variables sin significado (snake_case, nombres descriptivos) | Renombrar | 20 passed | 10 errores (−2) |
| R5 | `almacen.py`: `with open`, excepción específica, `update`/`extend`, type hints | Mejorar manejo de errores | 20 passed | 6 errores (−4) |

---

## R1 — Eliminar código muerto

**Modo de Claude Code:** accept edits (la captura del resultado muestra `auto mode on` en la
barra inferior; el cambio igualmente se revisó con `git diff` antes de commitear).
**Capturas:** [prompt](evidencia/R1_prompt.png) · [resultado](evidencia/R1_resultado.png)

**Prompt usado:**

```
Refactorización 1 de 7 (categoría: eliminar código muerto). Lee CLAUDE.md y respétalo.

Tarea: elimina el código muerto de src/. Candidatos: la función calcular_descuento_viejo,
la variable MODO_DEBUG y el bloque comentado de exportar_txt en gestor.py; la función
reporteViejoCSV y el import os en reportes.py.

Reglas:
- Antes de borrar, verifica con grep que cada elemento no se usa en src/ ni en tests/.
  Si alguno se usa, NO lo borres y avísame.
- No cambies nada más (ni nombres, ni lógica, ni formato). No toques tests/ ni pyproject.toml.
- Al terminar ejecuta pytest y ruff check src y muéstrame los resultados y el diff.
```

**Cambio realizado** (31 líneas eliminadas, 0 agregadas):
- `src/gestor.py`: se quitó `MODO_DEBUG`, la función `calcular_descuento_viejo` y el bloque
  comentado de `exportar_txt`.
- `src/reportes.py`: se quitó `import os` y la función `reporteViejoCSV`.

**Justificación:** el código muerto confunde al lector (¿se usa?, ¿qué fórmula de descuento
vale?), aumenta la superficie a mantener y producía errores de lint reales (F401, N802, SIM115).
La eliminación es de riesgo mínimo porque `grep` confirmó 0 usos en `src/` y `tests/`, y la
historia sigue disponible en git.

**Verificación independiente (hecha por mí tras la sesión de Claude Code):**
`git diff` revisado completo; `grep -rnE "calcular_descuento_viejo|MODO_DEBUG|reporteViejoCSV|exportar_txt" src tests`
sin resultados; `tests/` y `pyproject.toml` sin cambios.

**Resultado de los tests:** `pytest` → **20 passed** ([`R1_pytest.txt`](evidencia/R1_pytest.txt)).
`ruff check src` → **17 errores** (antes 20; desaparecen F401, N802 de `reporteViejoCSV` y SIM115)
([`R1_ruff_resumen.txt`](evidencia/R1_ruff_resumen.txt)).

**Observaciones:** Claude verificó con `grep` antes de borrar y respetó el alcance (no tocó
nada más), tal como pedía el prompt. Al principio tuvo un problema de comillas/glob en zsh y
reintentó solo.

---

## R2 — Constantes con nombre y extracción del descuento por volumen / cliente VIP

**Modo de Claude Code:** plan mode (diseño) → aprobación del plan → ejecución (la captura final
muestra `auto mode on`). Plan guardado por Claude en [`R2_plan_claude.md`](evidencia/R2_plan_claude.md).
**Capturas:** [prompt](evidencia/R2_prompt.png) · [plan](evidencia/R2_plan.png) · [resultado](evidencia/R2_resultado.png)

**Prompt usado:**

```
Refactorización 2 de 7 (categoría: extraer funciones / constantes). Lee CLAUDE.md y respétalo.

Contexto: en src/gestor.py la lógica de descuento por volumen está duplicada en
registrar_venta y cotizar, y hay números mágicos (1000, 500, 0.10, 0.05, 0.02, 200, 0.16,
"VIP") y en reportes.py el stock mínimo 5 aparece repetido.

Tarea:
1. Define constantes con nombre al inicio de gestor.py (TASA_IVA, umbrales y porcentajes de
   descuento, PREFIJO_VIP, MONTO_MINIMO_VIP, STOCK_MINIMO) y úsalas también en reportes.py.
2. Extrae una función calcular_descuento_volumen(subtotal) que use ambas funciones, y
   _es_cliente_vip(cliente) para el chequeo de cliente VIP (None y "" no son VIP).

Restricciones críticas (el comportamiento debe ser idéntico):
- Conserva el orden de las operaciones con decimales: NO reescribas base + base*0.16 como
  base*1.16 ni cambies el redondeo.
- cotizar NO aplica descuento VIP y registrar_venta sí; no los unifiques.
- Umbrales con >= ; stock bajo es < STOCK_MINIMO (estricto). No cambies mensajes de ultimo_error.
- No toques tests/ ni pyproject.toml. No renombres nada más (eso viene en otra refactorización).

Primero muéstrame el plan (qué constantes y funciones y dónde se usan). Cuando lo apruebe,
aplícalo, ejecuta pytest y ruff check src y muéstrame los resultados y el diff.
```

**Cambio realizado:**
- `src/gestor.py`: 9 constantes (`TASA_IVA`, `UMBRAL_DESCUENTO_ALTO/MEDIO`, `DESCUENTO_ALTO/MEDIO`,
  `PREFIJO_VIP`, `MONTO_MINIMO_VIP`, `DESCUENTO_VIP`, `STOCK_MINIMO`); nuevas funciones
  `calcular_descuento_volumen(subtotal)` y `_es_cliente_vip(cliente)` (con type hints);
  `registrar_venta` y `cotizar` las usan. Se elimina la lógica de descuento duplicada y los
  4 `if` anidados del chequeo VIP.
- `src/reportes.py`: los dos `< 5` pasan a `< gestor.STOCK_MINIMO`.

**Justificación:** un cambio de tarifa, umbral o IVA ahora se hace en una sola línea y no puede
quedar inconsistente entre venta y cotización; los números mágicos pasan a tener significado;
`registrar_venta` baja de complejidad y de niveles de anidamiento. Se respetó lo que no debe
cambiar: orden de operaciones con decimales (`base + base * TASA_IVA`, no `base * 1.16`),
`cotizar` sin descuento VIP, umbrales con `>=` y stock bajo estricto.

**Aportes de la IA no pedidos:** Claude detectó por su cuenta otro número mágico (`0.02`,
`DESCUENTO_VIP`) que no estaba en mi lista y lo agregó. Lo acepté tras revisar el diff.

**Verificación:** además de la suite, Claude comparó `cotizar` y `registrar_venta` contra la versión
original (`git show HEAD:src/gestor.py`) en 96 combinaciones de precio/cantidad (cruzando 499.99, 500,
999.99 y 1000) y 9 clientes (`None`, `""`, `"V"`, `"VI"`, `"VIP"`, `"VIP007"`, `"vip1"`, `"XVIP"`,
`"Juan"`): resultados idénticos, incluido el ticket. Yo revisé el diff completo y comprobé que
`_es_cliente_vip` equivale al chequeo original (`len>=3 and [0:3]=="VIP"` ≡ `startswith("VIP")`,
con `None` y `""` como no-VIP) y que `tests/` y `pyproject.toml` no cambiaron.

**Resultado de los tests:** `pytest` → **20 passed** ([`R2_pytest.txt`](evidencia/R2_pytest.txt)).
`ruff check src` → **12 errores** (antes 17; desaparecen los SIM102 del chequeo VIP, el SIM108 del
descuento y el C901 de `registrar_venta`) ([`R2_ruff_resumen.txt`](evidencia/R2_ruff_resumen.txt)).

**Observaciones:** el plan de Claude decía que `ruff check src` daría "0 errores" tras esta
refactorización; era impreciso (0 es la meta final, no de cada paso) y el propio resumen final lo
corrigió reportando 12. Lección: indicar en el prompt la meta de ruff por paso.

---

## R3 — `registrar_venta`: guard clauses y extracción de funciones

**Modo de Claude Code:** accept edits (el prompt pidió describir el plan en 5 líneas antes de editar,
en lugar de usar plan mode; no generó archivo de plan, queda en la conversación).
**Capturas:** [prompt](evidencia/R3_prompt.png) · [plan breve](evidencia/R3_plan_breve.png) · [resultado](evidencia/R3_resultado.png)

**Prompt usado:**

```
Refactorización 3 de 7 (categoría: simplificar condicionales / extraer funciones). Lee CLAUDE.md y respétalo.

Contexto: en src/gestor.py, registrar_venta tiene 4 niveles de if anidados para validar y
además mezcla validación, cálculo de montos, creación del registro y armado del ticket.

Tarea:
1. Reemplaza los if anidados de validación por guard clauses (return None temprano),
   en el MISMO orden y con los MISMOS mensajes de ultimo_error: código vacío/None ->
   producto no existe -> cantidad inválida (None o <= 0) -> stock insuficiente.
2. Extrae el armado del ticket a _armar_ticket(venta, hay_descuento) y la creación del
   diccionario de la venta a una función privada, con type hints y docstring breve.
   Si conviene, extrae también la validación a _validar_venta. Máximo 3 funciones nuevas.

Restricciones críticas (comportamiento idéntico):
- Mismos retornos: None en error (con ultimo_error), el dict venta en éxito, con las
  mismas claves y valores; folio int desde 1; stock descontado igual; fecha igual.
- El ticket omite la línea "Descuento" cuando el descuento es 0 y usa el mismo formato
  (str(round(...))); no cambies ninguna cadena.
- No cambies la aritmética (usa las constantes y funciones que ya existen).
- No renombres variables existentes (temp2, aux, etc. se renombran en otra refactorización).
- No toques tests/ ni pyproject.toml.

Antes de editar, escribe en 5 líneas qué funciones vas a crear y qué hará cada una.
Después aplica el cambio, ejecuta pytest y ruff check src, y muéstrame resultados y diff.
Indica cuántos errores de ruff quedan y cuáles dependen de otras refactorizaciones.
```

**Cambio realizado** (`src/gestor.py`):
- `_validar_venta(codigo, cantidad)`: guard clauses en el orden pedido, con los mismos mensajes de
  `ultimo_error`; devuelve el producto o `None`.
- `_crear_venta(folio, codigo, nombre, cantidad, montos, cliente)`: construye el dict de la venta
  (mismas claves, redondeos y fecha).
- `_armar_ticket(venta, hay_descuento)`: arma el ticket y omite la línea "Descuento" si no hay.
- `registrar_venta` queda como orquestadora: valida, calcula montos (aritmética intacta), descuenta
  stock, incrementa folio, crea la venta y le agrega el ticket. Ya no necesita `global ultimo_error`.

**Justificación:** desaparecen los 4 niveles de `if` anidados (el flujo feliz queda a la vista) y
cada responsabilidad (validar, crear el registro, formatear el ticket) se puede leer y probar por
separado. Se respetó el orden de efectos (stock → folio → registro) y el orden de validaciones.

**Verificación:** además de la suite, comparé `registrar_venta` contra la versión del commit anterior
con **420 casos** (códigos `None`/`""`/inexistente/válidos × cantidades `None`, 0, −1, 1…41 × clientes
`""`, `None`, `VIP`, `VIP9`, `vip`, `VI`, `Juan`), cotejando valor de retorno (sin la fecha),
`ultimo_error`, contador de folios e inventario: **0 diferencias, 58 ventas idénticas**
([`R3_equivalencia.py`](evidencia/R3_equivalencia.py), salida en [`R3_equivalencia.txt`](evidencia/R3_equivalencia.txt)).
`tests/` y `pyproject.toml` sin cambios.

**Resultado de los tests:** `pytest` → **20 passed** ([`R3_pytest.txt`](evidencia/R3_pytest.txt)).
`ruff check src` → **12 errores**, sin cambio ([`R3_ruff_resumen.txt`](evidencia/R3_ruff_resumen.txt)):
el C901 y los SIM102 de `registrar_venta` ya habían desaparecido en R2, así que el beneficio de R3 es
de estructura y legibilidad, no de conteo de lint.

**Observaciones:** Claude admitió que no comparó el detalle de ruff antes/después y que `_crear_venta`
recibe seis parámetros (ofreció reducirlos); lo dejo así porque agrupar los montos en un dict ya
evita una firma más larga. Prompt acotado ("máximo 3 funciones nuevas", "no renombres") evitó que se
desbordara el alcance: las variables `temp2`/`aux`/`desc` se conservaron para R4.

---

## R4 — Renombrar símbolos y variables sin significado

**Modo de Claude Code:** accept edits (se pidió grep de usos y mapa de renombres antes de aplicar).
Claude ofreció "switch to auto mode" ante un comando con `source`; se aprobó solo esa ejecución.
**Capturas:** [prompt](evidencia/R4_prompt.png) · [progreso](evidencia/R4_progreso.png) · [resultado](evidencia/R4_resultado.png)

**Prompt usado:**

```
Refactorización 4 de 7 (categoría: renombrar para mayor claridad). Lee CLAUDE.md y respétalo.

Contexto: hay nombres sin significado (temp2, aux, desc, t, s, d, f, x, k, hacer_cosa) y
estilos mezclados (contadorVentas, hayArchivo) en src/gestor.py, src/almacen.py,
src/reportes.py y src/main.py.

Tarea: renombra a nombres descriptivos en español y snake_case, siguiendo CLAUDE.md:
- hacer_cosa -> formatear_dinero
- contadorVentas -> contador_ventas (gestor.py, almacen.py y donde se use)
- hayArchivo -> hay_archivo (almacen.py y main.py)
- variables locales sin significado (temp2, aux, desc, t, s, d, f, x, k, etc.) -> nombres que
  describan su contenido (producto, subtotal, descuento, ticket, reporte, datos, archivo...).

Reglas:
- ANTES de renombrar cualquier símbolo público, haz grep de sus usos en src/ y tests/ y
  renómbralo en todos los usos a la vez. Si un test lo usa, NO lo renombres y avísame.
- NO renombres: agregarProducto, buscarProducto, INVENTARIO, VENTAS, reiniciar_sistema,
  ultimo_error (lo usa main.py como gestor.ultimo_error), ni funciones/atributos que usen los tests.
- No cambies lógica, aritmética, mensajes, claves de diccionario ni textos de salida.
- No toques tests/ ni pyproject.toml.
- Meta de ruff tras este paso: deben desaparecer N802 y N816 (quedarán unos 10 errores de otras categorías).

Primero lista el mapa de renombres (viejo -> nuevo) y los usos encontrados; después aplícalo,
ejecuta pytest y ruff check src y muéstrame resultados y diff.
```

**Cambio realizado** (4 archivos, 145 inserciones / 128 eliminaciones, solo nombres y saltos de línea):
- Símbolos: `hacer_cosa → formatear_dinero`, `contadorVentas → contador_ventas`, `hayArchivo → hay_archivo`
  (renombrados a la vez en `gestor.py`, `almacen.py`, `reportes.py` y `main.py`).
- Locales: `x → producto`, `aux → nuevo_stock / subtotal / valor_total / unidades_por_codigo`,
  `desc → descuento`, `temp2 → coincidencias / productos_bajos / producto / texto`, `d → datos`,
  `f → archivo`, `k → codigo`, `v → venta`, `s → reporte / resumen`, `t → total / anterior`,
  `op → opcion`, `c/n/p/s → codigo/nombre/precio/stock`, `cli → cliente`, `cant → cantidad`.
- Por la longitud de los nombres se partieron algunas líneas (diccionario `montos`, `print("OJO:", ...)`,
  concatenaciones largas en los reportes) para respetar el límite de 88 caracteres (E501).

**Justificación:** los nombres de una letra y `temp2`/`aux` (que significaba 3 cosas distintas) obligaban
a leer el cuerpo para entender qué contenían; ahora el código se lee sin comentarios. Se unifica el
estilo a `snake_case` (PEP 8) y desaparecen los errores N802 y N816 de ruff. Se respetaron los
nombres que usan los tests y `ultimo_error`, que `main.py` lee desde `gestor`.

**Verificación:** `grep` ya no encuentra `hacer_cosa`, `contadorVentas`, `hayArchivo`, `temp2` ni `aux` en
`src/`; `tests/`, `pyproject.toml` y `datos_ejemplo.json` sin cambios. Como `main.py` no tiene tests,
ejecuté el **menú completo con una sesión simulada** (196 líneas de salida: alta de productos
con error de duplicado y entrada no numérica, ventas con y sin cliente VIP, stock insuficiente, producto
inexistente, cotización, reportes de inventario/ventas, más vendidos, alertas y guardado) contra la versión
del commit anterior: **salida idéntica y JSON guardado idéntico** (sin la fecha)
([`R4_menu_entrada.txt`](evidencia/R4_menu_entrada.txt), [`R4_menu_salida.txt`](evidencia/R4_menu_salida.txt)).

**Resultado de los tests:** `pytest` → **20 passed** ([`R4_pytest.txt`](evidencia/R4_pytest.txt)).
`ruff check src` → **10 errores** (antes 12; desaparecen N802 y N816)
([`R4_ruff_resumen.txt`](evidencia/R4_ruff_resumen.txt)).

**Observaciones:** el prompt pedía "primero lista el mapa de renombres", pero Claude lo resumió en una
línea y aplicó directamente (la captura de progreso lo muestra); funcionó porque las reglas de
exclusión eran explícitas, pero para renombres masivos conviene pedir el mapa como paso aparte y
aprobarlo. Además corrigió solo una línea de 97 caracteres (E501) que sus propios renombres provocaron.

---

## R5 — Manejo de errores y recursos en `almacen.py`

**Modo de Claude Code:** plan mode (diseño y elección de la excepción) → aprobación → ejecución.
Plan guardado por Claude en [`R5_plan_claude.md`](evidencia/R5_plan_claude.md).
**Capturas:** [prompt](evidencia/R5_prompt.png) · [plan](evidencia/R5_plan.png) · [resultado](evidencia/R5_resultado.png)

**Prompt usado:**

```
Refactorización 5 de 7 (categoría: mejorar manejo de errores). Lee CLAUDE.md y respétalo.

Contexto: src/almacen.py abre archivos sin `with` (en cargar_datos el archivo se cierra a mano en
dos sitios), usa `except Exception` genérico, copia datos elemento por elemento y hay_archivo
usa un if/else para devolver un booleano.

Tarea (solo almacen.py):
1. Usa `with open(...)` en guardar_datos y cargar_datos; quita el modo "r" redundante.
2. Reemplaza `except Exception` por una excepción específica (json.JSONDecodeError cubre JSON
   mal formado; considera ValueError si también debe cubrir UnicodeDecodeError).
3. Reemplaza los bucles de copia por INVENTARIO.update(...) y VENTAS.extend(...), manteniendo
   clear() para mutar en el sitio (NO reasignar INVENTARIO ni VENTAS).
4. hay_archivo debe devolver directamente os.path.exists(ruta).
5. Agrega type hints y docstring breve a las funciones de almacen.py.

Restricciones críticas (comportamiento idéntico):
- open() debe seguir FUERA del manejo de errores de JSON: un error de permisos o de ruta debe
  seguir propagándose igual que hoy.
- Un JSON corrupto sigue dando ultimo_error = "archivo corrupto" y retorno False; un archivo
  inexistente, "el archivo no existe" y False; éxito True; guardar_datos sigue devolviendo True.
- NO "arregles" el KeyError cuando falte "inventario" o "ventas" en el JSON: cambiaría el comportamiento.
- El formato del JSON guardado no cambia (indent=2, ensure_ascii=False, mismas claves).
- No toques tests/ ni pyproject.toml.
- Meta de ruff tras este paso: deben desaparecer SIM115, SIM103 y UP015 (quedarán 6 errores:
  4x UP009, I001 y C901 de menu).

Primero muéstrame el plan: qué excepción elegirás y por qué, y qué casos de error siguen
comportándose igual. Cuando lo apruebe, aplícalo, ejecuta pytest y ruff check src y muéstrame
resultados y diff.
```

**Cambio realizado** (`src/almacen.py`):
- `guardar_datos` y `cargar_datos` usan `with open(...)` (se eliminan los `close()` manuales y el modo `"r"`).
- `except Exception` → `except ValueError` (cubre `json.JSONDecodeError` y `UnicodeDecodeError`, ambas subclases);
  `open()` queda fuera del `try`, así que los errores de ruta/permisos se propagan como antes.
- Los bucles de copia pasan a `INVENTARIO.update(...)` y `VENTAS.extend(...)`, conservando `clear()` (mutación en el sitio).
- `hay_archivo` devuelve directamente `os.path.exists(ruta)`; type hints y docstrings en las tres funciones.

**Justificación:** `with` garantiza el cierre del archivo aunque ocurra una excepción; capturar solo
`ValueError` evita ocultar errores ajenos al formato del archivo (antes `except Exception` se los tragaba);
`update`/`extend` expresan la intención sin bucles; y `hay_archivo` deja de repetir un `if/else` que solo
devolvía el booleano de su condición. El plan de Claude eligió `ValueError` y no `JSONDecodeError` porque
con un archivo no UTF-8 el comportamiento habría pasado de devolver `False` a propagar una excepción.

**Verificación:** además de la suite, comparé `almacen.py` anterior vs nuevo con **11 casos** (archivo inexistente,
válido, sin `contador`, JSON mal formado, vacío, bytes no UTF-8, sin `inventario`, sin `ventas`, ruta que es un
directorio, JSON anidado profundo y `guardar_datos` byte a byte), cotejando retorno o excepción, `ultimo_error`,
inventario, ventas, folio y `hay_archivo`: **0 diferencias**, incluidas las excepciones que siguen propagándose
(`KeyError`, `IsADirectoryError`) ([`R5_equivalencia.py`](evidencia/R5_equivalencia.py),
[`R5_equivalencia.txt`](evidencia/R5_equivalencia.txt)). `tests/` y `pyproject.toml` sin cambios.

**Resultado de los tests:** `pytest` → **20 passed** ([`R5_pytest.txt`](evidencia/R5_pytest.txt)).
`ruff check src` → **6 errores** (antes 10; desaparecen SIM115 ×2, SIM103 y UP015; quedan 4× UP009, I001
y C901 de `menu`) ([`R5_ruff_resumen.txt`](evidencia/R5_ruff_resumen.txt)).

**Observaciones:** el prompt incluyó una lista explícita de casos que no debían cambiar y Claude la respetó
(dejó el `KeyError` intacto). Claude señaló un matiz que yo no había considerado: `update` aceptaría un
`"inventario"` con forma de lista de pares donde antes había un `TypeError`; no afecta a los datos que genera
`guardar_datos`. Matiz teórico propio: `except Exception` también atrapaba `RecursionError`, que `except ValueError`
ya no atrapa; intenté reproducirlo con un JSON anidado 100 000 niveles y en este Python ambas versiones se
comportan igual (el JSON se carga), por lo que no es un cambio observable aquí. Como en R2, el modo de la
barra al terminar fue `auto mode on` tras aprobar el plan.
