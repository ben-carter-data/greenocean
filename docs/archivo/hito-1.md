# Hito 1 · Datos crudos

Cierre escrito el 11-10-2026, al comprobar la descarga real.

## Qué se construyó

- `agent/agent.py`: descarga los CSV listados en `agent/input.csv`, valida cada archivo (tamaño, encabezado, al menos una fila), reintenta ante fallas y deja una línea de log por recurso.
- `etl/etl.py` · `load_raw_files()`: carga cada archivo tal como viene en `raw.db`, con el año y el hash del archivo.
- `.github/workflows/pruebas.yml`: ejecuta `pytest` en cada cambio.

## Cómo comprobarlo

1. `pytest -q` → todas las pruebas en verde, sin usar la red.
2. `python agent/agent.py` → dos líneas `DOWNLOADED` y `Failed resources: 0`.
3. `python etl/etl.py` → dos líneas `LOADED` (o `UNCHANGED` si ya estaban cargados).

## Resultados reales (11-10-2026)

| Fuente | Archivo | Bytes | Filas CSV | Filas en `raw.db` |
|---|---|---|---|---|
| Mayorista | `wholesale_2026.csv` | 32.350.548 | 145.231 | 145.231 |
| Consumidor | `consumer_2026.csv` | 45.798.183 | 252.583 | 252.583 |

- Ambos archivos bajaron al primer intento y pasaron la validación de encabezado.
- `raw.db` pesa 105 MB (coincide con D-020).
- Con la red bloqueada, el agente hizo los 3 intentos, registró `FAILED` y terminó con código 1 (T-04 observado en una falla real).

## Pendiente

- T-06b: el sello de estado de las pruebas en el README y la comprobación en GitHub quedan para cuando el repositorio esté publicado.
- `run_download.command` es un lanzador auxiliar para macOS; decidir si se conserva en el repositorio.
