# Gestor de inventario y ventas — Tienda "La Esquina"

Aplicación de consola en Python para administrar el inventario y las ventas de una tienda pequeña: alta de
productos, ventas con descuentos por volumen/VIP e IVA, cotizaciones, alertas de stock bajo, reporte de más
vendidos y persistencia en JSON.

Este repositorio es la entrega del reto **M1 — Refactorización asistida por IA** (Certificado en Desarrollo de
Software con IA Generativa): el código original funcionaba pero tenía baja calidad, y se refactorizó con Claude
Code sin romper su comportamiento.

## Requisitos previos
- Python 3.10 o superior
- `git`
- Dependencias de desarrollo (en `requirements.txt`): `pytest>=8.0` y `ruff>=0.6`

## Clonar e instalar
```bash
git clone https://github.com/dtagle/NGC_M1_retoRefactorizacion.git
cd NGC_M1_retoRefactorizacion
git checkout refactorizacion        # rama con la refactorización

python -m venv .venv
source .venv/bin/activate           # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecutar los tests
```bash
pytest                              # 56 tests (20 originales + 36 de casos límite), todos deben pasar
```

## Ejecutar el linter
```bash
ruff check src                      # debe terminar con "All checks passed!"
```

## Ejecutar la aplicación (opcional)
```bash
cd src && python main.py
```
La opción 8 ("Guardar y salir") escribe `datos_ejemplo.json`; si solo vas a probar, restaura el archivo con
`git checkout datos_ejemplo.json`.

## Estructura
```
.
├── CLAUDE.md                 # Instrucciones para Claude Code
├── .claudeignore             # Archivos que Claude Code no debe leer
├── README.md
├── requirements.txt
├── pyproject.toml            # Configuración de ruff y pytest (no se modifica)
├── datos_ejemplo.json        # Datos de ejemplo para el menú
├── src/
│   ├── gestor.py             # Lógica de productos y ventas
│   ├── almacen.py            # Carga y guardado de datos (JSON)
│   ├── reportes.py           # Reportes e indicadores
│   └── main.py               # Menú interactivo de consola
├── tests/                    # Suite pytest (3 archivos originales sin modificar + test_casos_edge.py)
└── docs/
    ├── bitacora.md           # Registro de cada refactorización (prompts, cambios, justificación, tests)
    ├── reflexion.md          # Aprendizajes y conclusiones
    └── evidencia/            # Salidas de pytest/ruff, capturas y scripts de verificación
```

## Resultado de la refactorización
| Métrica | Original | Final |
|---|---|---|
| Errores de `ruff check src` | 20 | **0** |
| Tests | 20 passed | 56 passed (20 originales + 36 de casos límite); los 20 originales pasaron tras cada refactorización |
| Complejidad ciclomática máxima | 17 (`menu`) | 5 |

El programa final produce la misma salida y el mismo JSON que el código original (verificado con una sesión
simulada del menú). Detalle completo en [`docs/bitacora.md`](docs/bitacora.md) y [`BITACORA.md`](BITACORA.md);
reflexión en [`docs/reflexion.md`](docs/reflexion.md).

## Reglas del reto
- No se modifican los tests originales ni `pyproject.toml` (solo se agrega `tests/test_casos_edge.py`).
- `agregarProducto` y `buscarProducto` conservan su nombre porque los tests los usan.
- El comportamiento observable del programa se mantiene idéntico.
