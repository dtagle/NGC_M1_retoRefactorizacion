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
| R6 | `reportes.py`: `sorted`, `sum`, comprehension y type hints | Simplificar / type hints | 20 passed | 6 errores (±0) |
| R7 | `main.py`: `menu()` dividido en un handler por opción + despacho por diccionario | Extraer funciones / type hints | 20 passed | 5 errores (−1) |
| — | Limpieza final con `ruff check src --fix` (cabecera `coding` obsoleta y orden de imports) | Linter automático | 20 passed | **0 errores** (−5) |
| R8 | `gestor.py`/`almacen.py`: type hints, helper `_registrar_error`, literales, comprehension y docstrings al día (después de agregar los tests de casos límite) | Type hints / extraer funciones / comentarios obsoletos | 56 passed | 0 errores |

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

---

## R6 — `reportes.py`: `sorted`, `sum`, comprehension y type hints

**Modo de Claude Code:** accept edits, con plan de 5 líneas en el texto y verificación de equivalencia
escrita por la propia IA (no se generó archivo de plan).
**Capturas:** [prompt](evidencia/R6_prompt.png) · [progreso](evidencia/R6_progreso.png) · [resultado](evidencia/R6_resultado.png)

**Prompt usado:**

```
Refactorización 6 de 7 (categoría: simplificar código / type hints). Lee CLAUDE.md y respétalo.

Contexto: en src/reportes.py, mas_vendidos usa un ordenamiento de burbuja manual y un acumulador
manual (con un TODO que pide usar sorted); total_vendido y productos_stock_bajo usan bucles
acumuladores; ninguna función tiene type hints.

Tarea (solo reportes.py):
1. mas_vendidos: reemplaza la burbuja por sorted(..., key=..., reverse=True) y simplifica el
   acumulador de unidades por código; elimina el comentario TODO obsoleto.
2. total_vendido: usa sum(...) sobre los totales; productos_stock_bajo: comprehension.
3. Agrega type hints y docstrings breves a todas las funciones de reportes.py.
4. En reporte_inventario y resumen_ventas solo simplifica si el texto resultante es IDÉNTICO
   (siguen haciendo print y return del mismo texto).

Restricciones críticas (comportamiento idéntico):
- mas_vendidos: orden descendente por unidades y, en empates, orden de PRIMERA aparición
  (sorted con reverse=True conserva el orden relativo de los empates). Mismo comportamiento
  para n=0 o n mayor que el número de productos.
- total_vendido: misma suma de floats en el mismo orden, sum empezando en 0 entero, y round(..., 2).
- formatear_dinero sigue siendo "$" + str(round(valor, 2)) (sin forzar dos decimales).
- No cambies formatos de texto ni nombres públicos usados por main.py y los tests.
- No toques tests/ ni pyproject.toml.
- Meta de ruff tras este paso: se mantienen 6 errores (4x UP009, I001, C901 de menu); no deben aparecer nuevos.

Primero escribe un plan de 5 líneas. Luego aplica el cambio y verifica la equivalencia con la
versión anterior: crea en el scratchpad (fuera del repo) un script que compare las funciones de
reportes.py con git show HEAD:src/reportes.py usando varios inventarios y ventas, incluyendo
empates en unidades y ventas vacías. Ejecuta también pytest y ruff check src y muéstrame
resultados y diff.
```

**Cambio realizado** (`src/reportes.py`):
- `mas_vendidos`: acumulador con `dict.get(codigo, 0)` y `sorted(..., reverse=True)` en lugar de la burbuja;
  se elimina el `TODO` (la función pasa de ~20 a ~10 líneas).
- `total_vendido`: `round(sum(...), 2)`; `productos_stock_bajo`: comprehension sobre `INVENTARIO.values()`.
- Type hints y docstrings en todas las funciones (alias `Producto = dict[str, Any]`).
- `reporte_inventario` y `resumen_ventas`: solo type hints (se dejaron sin pasar a f-strings a propósito).

**Justificación:** `sorted` es O(n log n) frente al O(n²) de la burbuja, es la forma idiomática y elimina
el `TODO` que admitía la deuda; `sum` y la comprehension expresan la intención sin variables acumuladoras
auxiliares. Los type hints documentan el contrato de cada función. El orden de los empates se conserva
porque la burbuja con `<` estricto es estable y `sorted(..., reverse=True)` también lo es.

**Decisión de la IA que acepto:** Claude no convirtió los reportes a f-strings porque con valores que no son
`str` cambiaría el comportamiento (`"a" + 5` lanza `TypeError`; un f-string no). Es el tipo de cambio "estético"
que habría alterado la semántica; el prompt ya pedía "solo si es idéntico" y la IA lo aplicó con criterio.

**Verificación:** el script de equivalencia que Claude escribió en su sesión comparó retorno y texto impreso
de las 5 funciones y `formatear_dinero` contra `git show HEAD:src/reportes.py`: **4545 comparaciones idénticas**
(inventario y ventas vacíos, empates en unidades con distinto orden de primera aparición, 300 escenarios
aleatorios, `mas_vendidos` con n = 0, 1, 2, 100 y −1). Yo verifiqué que `reportes_anterior.py` era exactamente
el de `HEAD`, leí el script y lo ejecuté de forma independiente con el mismo resultado
([`R6_equivalencia.py`](evidencia/R6_equivalencia.py), [`R6_equivalencia.txt`](evidencia/R6_equivalencia.txt)).
`tests/` y `pyproject.toml` sin cambios.

**Resultado de los tests:** `pytest` → **20 passed** ([`R6_pytest.txt`](evidencia/R6_pytest.txt)).
`ruff check src` → **6 errores**, sin cambio ni errores nuevos ([`R6_ruff_resumen.txt`](evidencia/R6_ruff_resumen.txt)).

**Observaciones:** pedir en el prompt que la IA escriba y ejecute su propia verificación contra la versión
anterior dio la evidencia más fuerte hasta ahora con el menor esfuerzo; conviene hacerlo siempre que no haya
tests que cubran el comportamiento. Aun así revisé el script y lo corrí por mi cuenta: la IA puede escribir una
verificación que no pruebe lo que debe.

---

## R7 — `main.py`: `menu()` dividido en handlers por opción

**Modo de Claude Code:** plan mode (diseño de handlers y despacho) → aprobación → ejecución.
Plan guardado por Claude en [`R7_plan_claude.md`](evidencia/R7_plan_claude.md).
**Capturas:** [prompt](evidencia/R7_prompt.png) · [plan](evidencia/R7_plan.png) · [resultado](evidencia/R7_resultado.png)

**Prompt usado:**

```
Refactorización 7 de 7 (categoría: extraer funciones / type hints). Lee CLAUDE.md y respétalo.

Contexto: en src/main.py, menu() es una función larga (C901, complejidad 17 > 10) con una cadena
if/elif de 8 opciones que mezcla pedir datos al usuario y llamar a gestor/reportes/almacen.
main.py NO tiene tests, así que el comportamiento observable debe quedar idéntico.

Tarea (solo main.py):
1. Extrae un handler por opción (por ejemplo _agregar_producto, _registrar_venta, _cotizar,
   _mostrar_mas_vendidos, _mostrar_alertas_stock, ...), cada uno con type hints y docstring breve.
2. menu() queda como bucle que imprime las opciones, lee la opción y despacha al handler (por
   ejemplo con un diccionario {"1": handler, ...}); la opción 8 guarda y termina el bucle, y una
   opción inválida imprime "Opcion no valida."
3. Agrega type hints a pedir_numero y menu.

Restricciones críticas (comportamiento idéntico):
- Mismos textos de menú y de prompts, al carácter; mismo orden de preguntas al usuario.
- int(pedir_numero(...)) se mantiene (trunca decimales); no lo "corrijas".
- Se sigue imprimiendo "Datos cargados de <archivo>" aunque cargar_datos devuelva False
  (es un bug conocido; NO lo arregles, solo anótalo si quieres).
- Los mensajes de error siguen leyendo gestor.ultimo_error con el mismo formato "Error:", valor.
- Solo la opción 8 sale del bucle; las demás vuelven al menú. Se conserva el print("") entre iteraciones.
- No renombres funciones de otros módulos. No toques tests/ ni pyproject.toml.
- Meta de ruff tras este paso: desaparece C901 y quedan 5 errores (4x UP009 e I001) que se
  arreglan después con ruff --fix.

Primero muéstrame el plan: lista de handlers y cómo se despachan. Cuando lo apruebe, aplícalo y
verifica la equivalencia: en el scratchpad (fuera del repo) copia la versión anterior
(git show HEAD:src/main.py y el resto de src/ de HEAD) y la nueva a dos carpetas con su propia
copia de datos_ejemplo.json, ejecuta main.py en cada una con la MISMA entrada simulada por stdin
que recorra las 8 opciones, un error de duplicado, una entrada no numérica, una opción inválida,
una venta con cliente VIP y un producto inexistente, y compara la salida y el JSON guardado
(ignorando la fecha). NO ejecutes main.py dentro del repo (la opción 8 sobrescribe
datos_ejemplo.json). Ejecuta también pytest y ruff check src y muéstrame resultados y diff.
```

**Cambio realizado** (`src/main.py`):
- Un handler por opción, cada uno con type hints y docstring: `_agregar_producto`, `_registrar_venta`,
  `_cotizar`, `_mostrar_inventario`, `_mostrar_resumen_ventas`, `_mostrar_mas_vendidos`,
  `_mostrar_alertas_stock`, `_guardar_y_salir`; más dos auxiliares (`_imprimir_error`, `_imprimir_menu`).
- `OPCIONES` (diccionario constante opción → handler) para las opciones 1–7; `menu()` trata la 8 aparte
  (guarda y sale) y una opción inválida imprime `Opcion no valida.` y vuelve al menú. `menu()` pasa de ~60
  líneas con 8 ramas a un bucle de ~10 líneas.
- Los `if/else` de las opciones 2, 3 y 7 pasaron a guard clauses; `pedir_numero` y `menu` con type hints.

**Justificación:** cada opción del menú queda aislada y legible, agregar una opción nueva es agregar un handler
y una entrada del diccionario (en lugar de otra rama `elif`), y desaparece el último error de complejidad
ciclomática (C901). La lógica de negocio no se movió: los handlers solo piden datos y llaman a
`gestor`/`reportes`/`almacen`, igual que antes.

**Comportamiento conservado a propósito (hallazgos del diagnóstico que NO se corrigieron):**
`int(pedir_numero(...))` sigue truncando decimales (3.9 → 3), y `menu()` sigue imprimiendo "Datos cargados de ..."
aunque `cargar_datos` devuelva `False` (mensaje engañoso). Son bugs latentes que habría que arreglar en un cambio
aparte, con tests, porque alteran lo que el usuario ve.

**Verificación:** `main.py` no tiene tests, así que se verificó ejecutándolo con entrada simulada por stdin, en
carpetas temporales (nunca dentro del repo, porque la opción 8 sobrescribe `datos_ejemplo.json`), contra la
versión del commit anterior:
- Verificación de Claude (203 líneas de salida): salida, código de salida y JSON guardado idénticos
  ([`R7_claude_entrada.txt`](evidencia/R7_claude_entrada.txt), [`R7_claude_salida.txt`](evidencia/R7_claude_salida.txt)).
  Claude reconoció que su primer script de entrada quedó desalineado con los prompts y lo rehízo. Su sesión no
  probó el descuento VIP en una segunda venta porque la compra no alcanzaba el mínimo de $200.
- Mi verificación independiente, con la sesión de 44 entradas de R4 (las 8 opciones, duplicado, entrada no numérica,
  opción inválida, producto inexistente, stock insuficiente y ventas VIP con descuento): **196 líneas de salida
  idénticas y JSON idéntico**; además la salida es byte a byte la misma que la de R4
  ([`R7_menu_entrada.txt`](evidencia/R7_menu_entrada.txt), [`R7_menu_salida.txt`](evidencia/R7_menu_salida.txt)).
`tests/`, `pyproject.toml` y `datos_ejemplo.json` sin cambios.

**Resultado de los tests:** `pytest` → **20 passed** ([`R7_pytest.txt`](evidencia/R7_pytest.txt)).
`ruff check src` → **5 errores** (antes 6; desaparece C901 de `menu`; quedan 4× UP009 e I001, ambos
autocorregibles) ([`R7_ruff_resumen.txt`](evidencia/R7_ruff_resumen.txt)).

**Observaciones:** donde no hay tests, la verificación debe pedirse explícitamente en el prompt y conviene
repetirla de forma independiente; el fallo de alineación del primer script de Claude (y el mío en R4) muestra
que las verificaciones con entrada simulada también pueden estar mal construidas y hay que comprobar que
realmente recorrieron lo que decían recorrer (aquí: contar `Opcion no valida`, `Eso no es un numero` y
`Descuento` en la salida).

---

## Limpieza final — `ruff check src --fix`

No es una de las 7 refactorizaciones: son los 5 errores restantes, todos mecánicos y autocorregibles por el propio
linter. Se aplicó `ruff check src --fix` y se revisó el diff: se elimina la cabecera `# -*- coding: utf-8 -*-`
en los 4 módulos (UP009; innecesaria en Python 3) y se reordenan los imports de `main.py` (I001). Sin cambios
de lógica. Resultado: `ruff check src` → **All checks passed!** ([`99_final_ruff.txt`](evidencia/99_final_ruff.txt));
`pytest -v` → **20 passed** ([`99_final_pytest.txt`](evidencia/99_final_pytest.txt)).

---

## Resultado global

| Métrica | Original (`7d67b8b`) | Final |
|---|---|---|
| Errores de `ruff check src` | 20 | **0** |
| Tests (`pytest`) | 20 passed | 56 passed (20 originales, que pasaron tras cada refactorización, + 36 de casos límite) |
| Complejidad máxima (C901) | `menu` 17, `registrar_venta` 12 | **5** (`menu`, `agregarProducto`, `_validar_venta`) |
| Líneas en `src/` | 429 | 486 (más docstrings, type hints, constantes y funciones pequeñas) |
| Código muerto | 5 elementos | 0 |
| Números mágicos del negocio | 8 | 0 (constantes con nombre) |
| Estilos de nombres mezclados | `contadorVentas`, `hayArchivo`, `hacer_cosa`, `temp2`, `aux`... | `snake_case` descriptivo |

**Validación de que el comportamiento no cambió:** el programa final se ejecutó con la sesión simulada de 44
entradas (las 8 opciones del menú, producto duplicado, entrada no numérica, opción inválida, producto inexistente,
stock insuficiente, ventas con y sin cliente VIP) y produjo una **salida de 196 líneas idéntica a la del código
original del reto, y el mismo JSON guardado** (sin la fecha)
([`99_final_comparacion_original.txt`](evidencia/99_final_comparacion_original.txt),
[`99_final_menu_salida.txt`](evidencia/99_final_menu_salida.txt)). `tests/` y `pyproject.toml` no se modificaron
en ningún commit.

**Hallazgos del diagnóstico que se dejaron sin corregir a propósito** (cambiarían el comportamiento observable;
quedan como mejoras futuras con sus propios tests): cotización sin descuento VIP y validaciones distintas a las
de la venta (#25); mensaje "Datos cargados" aunque la carga falle (#23); truncado de decimales en
`int(pedir_numero(...))` (#22); `KeyError` si faltan claves en el JSON; estado global (`INVENTARIO`, `VENTAS`,
`ultimo_error`, `contador_ventas`), que no se eliminó para no alterar la API que usan los tests.

---

## Análisis de técnicas de prompting (qué funcionó mejor)

No se probaron dos variantes del mismo prompt sobre la misma refactorización; la comparación es entre
refactorizaciones con enfoques distintos, y la conclusión se apoya en lo observado en cada una:

| Variación | Dónde se usó | Qué se observó |
|---|---|---|
| **Plan mode** antes de editar | R2, R5, R7, R8 (y diagnóstico) | Sacó a la luz decisiones de diseño antes de tocar código: qué constantes crear (R2), por qué `ValueError` y no `JSONDecodeError` (R5), cómo despachar las opciones del menú (R7). Más lento, pero cada plan se pudo revisar y aprobar. |
| **Plan de 5 líneas** en el propio prompt (accept edits) | R3, R6 | Suficiente para cambios acotados a un archivo; menos evidencia visual que plan mode. |
| **Sin plan** (acotado por restricciones) | R1, R4 | R1 (cambio trivial) funcionó. En R4 Claude **no mostró** el mapa de renombres pedido antes de aplicar; las restricciones explícitas evitaron daños, pero no se pudo aprobar el mapa. |
| **Guardrails**: "qué NO debe cambiar" con el motivo | Todas | Fue la técnica de mayor impacto: evitó `base * 1.16`, los f-strings en reportes, unificar `cotizar` con `registrar_venta` y "arreglar" bugs latentes. 0 regresiones en los 9 commits de código (R1–R8 y la limpieza final). |
| **Meta de `ruff` por paso** | R4–R7 | Tras el plan de R2 que prometía 0 errores en un paso intermedio, las metas explícitas (~10, 6, 6, 5) se cumplieron exactamente y permitieron validar el avance. |
| **Pedir a la IA su propia verificación de equivalencia** | R2 (espontánea), R6, R7 | Dio la evidencia más fuerte (96, 4545 y 203 líneas comparadas) con poco esfuerzo; aun así hubo que leer el script y repetir la verificación por separado. |
| **Rol + contexto** ("revisor senior", "lee CLAUDE.md") | Diagnóstico y todas | El diagnóstico salió priorizado y con riesgos; destacó hallazgos que no se habían visto (cotización sin VIP, `DESCUENTO_VIP`, mensaje "Datos cargados" engañoso). |

**Conclusión:** la combinación que mejor funcionó fue *alcance acotado + guardrails con motivo + meta de lint por paso +
plan previo + verificación de equivalencia*, usando plan mode cuando el cambio tiene decisiones de diseño.

## Intentos fallidos y cómo se resolvieron

| Qué falló | Cómo se detectó | Resolución |
|---|---|---|
| R1: el primer `grep` de Claude falló por comillas/glob en zsh | Se vio en la captura de la sesión | Claude lo reintentó solo ("zsh glob issue with the quoting; retry"). |
| R2: el plan prometía `ruff` en 0 errores en un paso intermedio | Al comparar con el resultado real (12) | El resumen final de Claude lo corrigió; desde R3 cada prompt declara la meta de `ruff` del paso. |
| R3: no hubo plan guardado y el conteo de `ruff` no bajó | Revisión del diff y de las estadísticas | Se documentó que el C901 de `registrar_venta` ya había desaparecido en R2; el valor de R3 es estructural. |
| R4: Claude no mostró el mapa de renombres antes de aplicar; sus nombres largos dejaron una línea de 97 caracteres (E501) | Captura de progreso y `ruff` | Corrigió la línea; se anotó la lección (pedir el mapa como paso aparte). |
| R4: mi primera comparación del menú contra la versión anterior no valía (ruta de Python mal armada y luego modo `-I` que impide importar los módulos) | Salida idéntica pero con un traceback en ambas | Se rehízo con ruta absoluta y sin `-I`; la sesión final recorrió las 8 opciones. |
| R5: posible diferencia teórica por `RecursionError` al pasar de `except Exception` a `except ValueError` | Revisión del diff | Se intentó reproducir con un JSON anidado 100 000 niveles: en este Python ambas versiones se comportan igual; se documentó como matiz no reproducible. |
| R7: el primer script de entrada de Claude quedó desalineado con los prompts | Lo reconoció en su resumen | Lo rehízo alineado; además se repitió la verificación con la sesión de R4 y se contó que recorriera `Opcion no valida`, `Eso no es un numero` y `Descuento`. |

---

## Tests adicionales de casos límite (`tests/test_casos_edge.py`)

**Motivo:** la suite original (20 tests) no cubre varios comportamientos que se descubrieron al refactorizar, y
`main.py` solo se pudo verificar con una sesión simulada. Para que cualquier cambio futuro los conserve, se agregó
un archivo **nuevo** de tests de caracterización, sin modificar los 3 archivos originales ni `pyproject.toml`.

**Qué fijan (36 tests):** umbrales de descuento inclusivos (499.99 / 500 / 999.99 / 1000); `cotizar` **no** aplica el
descuento VIP pero la venta sí (611.61 vs 598.73); VIP solo con prefijo `VIP` en mayúsculas y compra > 200 estricta;
orden y mensaje de cada validación de venta; una venta fallida no consume folio ni stock; `cotizar` valida distinto
que `registrar_venta` (no revisa código vacío ni stock); ticket con y sin línea de descuento y claves de la venta;
`actualizar_stock` y `buscarProducto`; `mas_vendidos` con empates, `n=0` y `n` mayor al total; stock bajo estricto;
reportes vacíos, formato `$23.2` e `imprimir == regresar`; `cargar_datos` que reemplaza el estado en el sitio y
continúa el folio, archivos corruptos (mal formado, vacío, no UTF-8), `KeyError` por claves faltantes (comportamiento
actual) y formato del JSON guardado (`indent=2`, `ensure_ascii=False`).

**Validación de los tests:**
1. Pasan contra el código **actual** (56 passed) y contra el código **original** del reto en `7d67b8b` (56 passed): no
   inventan comportamiento, lo describen ([`T1_pytest_actual.txt`](evidencia/T1_pytest_actual.txt),
   [`T1_pytest_contra_original.txt`](evidencia/T1_pytest_contra_original.txt)).
2. Detectan regresiones: se aplicaron 7 mutaciones en una copia fuera del repo (cambiar `>=` por `>`, aplicar VIP en
   `cotizar`, `<` por `<=` en stock bajo, `ValueError` por `JSONDecodeError`, quitar `reverse=True`, etc.) y **las 7
   hicieron fallar al menos un test** ([`T1_mutaciones.txt`](evidencia/T1_mutaciones.txt)).

**Intento fallido:** mis dos primeras expectativas aritméticas estaban mal (esperé el 5 % de descuento donde un
subtotal de 1000 ya cae en el 10 %); fallaron **igual** contra el código original y el actual, lo que mostró que el
error era del test y no de la refactorización, y se corrigieron.

**Resultado:** `pytest` → **56 passed**; `ruff check src` → 0 errores.

---

## R8 — Smells menores de `gestor.py` (type hints, helper de error, literales, docstrings)

Se hizo **después** de la limpieza final y de agregar los tests de casos límite: ahora hay 56 tests que fijan el
comportamiento, así que se pudo tocar `gestor.py` con menos riesgo. Cubre los smells menores del diagnóstico que
quedaban (#10, #11, #12, #16 y comentarios obsoletos).

**Modo de Claude Code:** plan mode (lista de cambios por función) → aprobación → ejecución. Plan guardado en
[`R8_plan_claude.md`](evidencia/R8_plan_claude.md).
**Capturas:** [prompt](evidencia/R8_prompt.png) · [plan](evidencia/R8_plan.png) · [resultado](evidencia/R8_resultado.png)

**Prompt usado:**

```
Refactorización 8 de 8 (categorías: type hints / extraer funciones / eliminar comentarios obsoletos). Lee CLAUDE.md y respétalo.

Contexto: quedan smells menores del diagnóstico en src/gestor.py: (1) las funciones públicas no tienen
type hints; (2) agregarProducto construye el diccionario en 5 líneas; (3) buscarProducto usa bucle con
append; (4) el patrón "global ultimo_error; ultimo_error = ...; return ..." se repite ~12 veces;
(5) hay docstrings/comentarios obsoletos (el docstring de registrar_venta dice que "hace de todo" y el
docstring del módulo menciona que "lo fueron parchando varias personas"). En src/almacen.py,
guardar_datos arma su diccionario en 4 líneas. Ahora hay 56 tests (los 3 archivos originales más
tests/test_casos_edge.py) que fijan el comportamiento.

Tarea:
1. Type hints en TODAS las funciones públicas de gestor.py (sin cambiar nombres, p. ej.
   cantidad: int | None, precio: float) y docstring breve donde falte.
2. agregarProducto: construye el diccionario con un literal {...} (mismas claves y orden).
3. buscarProducto: list comprehension sobre INVENTARIO.values() (mismo orden).
4. Extrae un helper privado _registrar_error(mensaje) que asigne la variable GLOBAL ultimo_error
   del módulo (con `global`), y úsalo donde se repite el patrón.
5. Actualiza los docstrings/comentarios obsoletos para que describan el estado actual.
6. almacen.guardar_datos: diccionario como literal.

Restricciones críticas (comportamiento idéntico):
- gestor.ultimo_error debe seguir siendo una variable de módulo que main.py, almacen.py y los tests
  leen y escriben; el helper NO debe crear una variable local ni cambiar ese mecanismo.
- Conserva los nombres agregarProducto y buscarProducto, el orden de validaciones y los mensajes exactos.
- Los type hints NO agregan validaciones ni conversiones de tipos.
- No toques ningún archivo de tests/ ni pyproject.toml.
- Meta: pytest 56 passed y ruff check src con 0 errores.

Primero muéstrame el plan (qué cambia en cada función). Cuando lo apruebe, aplícalo y verifica la
equivalencia con la versión anterior: crea en el scratchpad (fuera del repo) un script que compare
gestor.py actual vs `git show HEAD:src/gestor.py` con muchos escenarios (altas válidas e inválidas,
ventas con distintos clientes/cantidades, cotizaciones, búsquedas, actualizar_stock) y que también
compare el valor de gestor.ultimo_error tras cada operación. Ejecuta pytest y ruff check src y
muéstrame resultados y diff.
```

**Cambio realizado:**
- `gestor.py`: type hints en todas las funciones públicas (nombres intactos, sin validaciones ni conversiones nuevas);
  helper `_registrar_error(mensaje)` que asigna con `global` la variable de módulo `ultimo_error` y reemplaza el patrón
  repetido en 13 sitios (varias funciones dejan de necesitar `global`); `agregarProducto` con diccionario literal;
  `buscarProducto` como list comprehension sobre `INVENTARIO.values()`; docstrings actualizados (se quitan
  "lo fueron parchando varias personas" y "hace de todo") y tres comentarios triviales eliminados.
- `almacen.py`: `guardar_datos` arma el diccionario como literal.

**Justificación:** el helper concentra en un solo punto cómo se registra un error, sin cambiar el mecanismo del que
dependen `main.py`, `almacen.py` y los tests (sigue siendo la variable de módulo `gestor.ultimo_error`); los type
hints documentan el contrato de la API pública; los literales y la comprehension son la forma idiomática; y los
docstrings dejan de contradecir al código. Se mantuvo a propósito el estado global (cambiarlo alteraría la API que
usan los tests).

**Detalle que Claude identificó en el plan:** con la comprehension, `texto.lower()` se evalúa por elemento, igual que en
el bucle original, por lo que con inventario vacío y `texto=None` ninguna versión lanza error; el comportamiento se
conserva.

**Verificación:**
- Script de Claude (143 operaciones sobre `gestor.py` anterior vs nuevo, comparando retorno sin fecha, `ultimo_error`,
  inventario, ventas y folio tras cada una; 8 mensajes de error más el estado vacío; 16 ventas exitosas, 9 con
  descuento; 3 excepciones idénticas): **0 diferencias**. Comparación de `guardar_datos`: JSON idéntico byte a byte
  ([`R8_equivalencia_gestor.py`](evidencia/R8_equivalencia_gestor.py), [`.txt`](evidencia/R8_equivalencia_gestor.txt),
  [`R8_equivalencia_almacen.py`](evidencia/R8_equivalencia_almacen.py), [`.txt`](evidencia/R8_equivalencia_almacen.txt)).
  Comprobé que los módulos "viejos" del script eran exactamente los de `HEAD`, leí los scripts y los ejecuté por mi cuenta
  con el mismo resultado.
- Sesión simulada del menú contra el **código original del reto**: salida de 196 líneas y JSON guardado **idénticos**
  ([`R8_menu_salida.txt`](evidencia/R8_menu_salida.txt)).
- `tests/` y `pyproject.toml` sin cambios en este commit.

**Resultado de los tests:** `pytest` → **56 passed** ([`R8_pytest.txt`](evidencia/R8_pytest.txt));
`ruff check src` → **All checks passed!** ([`R8_ruff.txt`](evidencia/R8_ruff.txt)). Complejidad máxima sin cambio
(5); líneas en `src/`: 486.

**Observaciones:** con tests de caracterización ya presentes, el prompt pudo pedir una verificación "adicional" en
lugar de "la única"; el riesgo principal (que un helper creara una variable local en lugar de modificar el global)
estaba nombrado explícitamente en las restricciones y el plan lo resolvió con `global ultimo_error` dentro del helper.
