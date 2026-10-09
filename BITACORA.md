# Bitácora de refactorización

**Nombre:** Anabelle Denisse Dueñas Sánchez de Tagle
**Matrícula:** NextGencoding
**Fecha:** 08 octubre 2026

Registro de cada refactorización realizada con Claude Code. Esta tabla sigue la plantilla del README
(con un resumen fiel de cada prompt). Los **prompts completos**, las capturas de pantalla, los planes de Claude, los
scripts de verificación y las salidas de `pytest`/`ruff` están en [`docs/bitacora.md`](docs/bitacora.md) y en
[`docs/evidencia/`](docs/evidencia/). Punto de partida: `pytest` 20 passed y `ruff check src` con 20 errores;
diagnóstico en [`docs/evidencia/01_diagnostico.md`](docs/evidencia/01_diagnostico.md).

| #  | Prompt usado | Cambio realizado | Justificación | Tests OK |
|----|--------------|------------------|---------------|----------|
| 1  | Elimina el código muerto (`calcular_descuento_viejo`, `MODO_DEBUG`, `exportar_txt` comentado, `reporteViejoCSV`, `import os`); verifica con grep que no se usan; no cambies nada más. | Se eliminan 31 líneas en `gestor.py` y `reportes.py`. | El código muerto confunde, aumenta el mantenimiento y causaba errores de lint (F401, N802, SIM115). | Sí: 20 passed; ruff 20 → 17 ([detalle](docs/bitacora.md#r1--eliminar-código-muerto)) |
| 2  | Define constantes con nombre (IVA, umbrales y porcentajes de descuento, VIP, stock mínimo), extrae `calcular_descuento_volumen` y `_es_cliente_vip`; conserva el orden de operaciones con decimales; `cotizar` no aplica VIP. Plan mode primero. | 9 constantes y 2 funciones nuevas; `registrar_venta` y `cotizar` dejan de duplicar el descuento. | Un cambio de tarifa se hace en un solo lugar y los números mágicos pasan a tener significado. | Sí: 20 passed; ruff 17 → 12; 96 combinaciones idénticas a la versión anterior |
| 3  | Aplana las validaciones de `registrar_venta` con guard clauses (mismo orden y mensajes) y extrae `_armar_ticket` y la creación de la venta; máximo 3 funciones nuevas. | `_validar_venta`, `_crear_venta` y `_armar_ticket`; `registrar_venta` solo orquesta. | Desaparecen 4 niveles de `if` anidados y cada responsabilidad se lee por separado. | Sí: 20 passed; ruff 12 → 12; 420 casos idénticos |
| 4  | Renombra `hacer_cosa`, `contadorVentas`, `hayArchivo` y las variables sin significado a nombres descriptivos en `snake_case`; grep de usos antes; no renombrar nombres que usan los tests. | Renombrados en los 4 módulos. | Nombres que se explican solos y estilo PEP 8 uniforme (elimina N802 y N816). | Sí: 20 passed; ruff 12 → 10; menú completo con salida idéntica |
| 5  | Mejora el manejo de errores de `almacen.py`: `with open`, excepción específica, `update`/`extend`, `hay_archivo` simplificada, type hints; `open()` fuera del `try`. Plan mode primero. | `except ValueError` en lugar de `Exception`, archivos con `with`, copia con `update`/`extend`. | Cierre garantizado de archivos y sin ocultar errores ajenos (elimina SIM115, SIM103, UP015). | Sí: 20 passed; ruff 10 → 6; 11 casos de error idénticos |
| 6  | Reemplaza la burbuja de `mas_vendidos` por `sorted`, usa `sum` y comprehension, agrega type hints; conserva el orden de empates; la IA verifica contra la versión anterior. | `reportes.py` más corto y tipado. | Forma idiomática y O(n log n); elimina el `TODO` de deuda técnica. | Sí: 20 passed; ruff 6 → 6; 4545 comparaciones idénticas |
| 7  | Extrae un handler por opción de `menu()` con despacho por diccionario, conservando textos, prompts y bugs conocidos; verifica con una sesión simulada contra la versión anterior. Plan mode primero. | 8 handlers, 2 auxiliares y el diccionario `OPCIONES`. | Elimina el último C901 (complejidad 17 → 5) y facilita agregar opciones. | Sí: 20 passed; ruff 6 → 5; salida y JSON idénticos |
| —  | Limpieza final: `ruff check src --fix` (cabecera `coding` obsoleta y orden de imports). | 4 líneas eliminadas y imports ordenados. | Cumple el requisito de linting sin errores. | Sí: 20 passed; **ruff 0 errores**; salida idéntica al código original |

> Resultado global: `ruff check src` pasó de 20 errores a 0; complejidad máxima de 17 a 5; `tests/` y
> `pyproject.toml` sin cambios; el programa final produce la misma salida y el mismo JSON que el código original.

## Reflexión final

Claude Code me resultó muy útil porque me fue llevando de la mano a lo largo de las siete refactorizaciones, desde el diagnóstico hasta la limpieza final. Mi perfil es de desarrollador Java y tengo poco acercamiento a las tendencias recientes de Python, así que la herramienta me ayudó a conocer idiomas como `sorted` con `reverse=True`, las comprehensions, `with open`, `dict.get` y los type hints modernos, sin que el código perdiera trazabilidad. Como limitación práctica, mi equipo corporativo tiene la herramienta bloqueada y tuve que pedir prestada otra máquina para completar el reto.

Entre lo que la IA detectó y yo no había notado destaca la inconsistencia entre `cotizar` y `registrar_venta`: la cotización no aplica el descuento VIP, de modo que una cotización puede diferir del total de la venta real. Claude lo señaló en el diagnóstico y recomendó documentarlo en lugar de unificarlo, porque hacerlo habría cambiado resultados observables. También identificó por su cuenta un número mágico adicional (`DESCUENTO_VIP`) que no estaba en mi lista.

Hubo casos en los que tuve que corregir el rumbo o mantenerme atenta. En la refactorización de renombrados le pedí explícitamente que listara primero el mapa de renombres y lo aplicó directamente, sin mostrarlo antes de editar. El resultado fue correcto porque las reglas de exclusión eran claras, pero no pude aprobar el mapa previamente. Además, en una refactorización su plan prometía cero errores de `ruff` cuando la meta correspondía solo al final, y los primeros scripts de verificación con entrada simulada quedaron desalineados con los prompts. Por eso revisé cada diff, ejecuté las pruebas tras cada cambio y repetí las verificaciones de forma independiente.

Las técnicas de prompting que mejor funcionaron fueron cuatro: los guardrails (restricciones explícitas de lo que no debe cambiar, como no tocar `tests/`, conservar los mensajes de `ultimo_error` y mantener el orden de las operaciones con decimales), el contexto (apoyarme en `CLAUDE.md` y en el diagnóstico previo), la asignación de un rol (revisor senior de código) y una estructura clara con alcance acotado, y el uso de plan mode para validar el diseño antes de editar. Aprendí que refactorizar con apoyo de IA exige delimitar el alcance, validar de forma incremental con pruebas y, donde no hay tests (como en `main.py`), pedir una verificación de equivalencia contra la versión anterior y comprobar que realmente prueba lo que afirma.
