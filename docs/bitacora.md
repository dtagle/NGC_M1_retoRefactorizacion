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
