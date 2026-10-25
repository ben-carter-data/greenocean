# Hito 2 · ETL y reglas

Cierre del 11-10-2026. Datos: archivos 2026 descargados ese día. Incluye los ajustes decididos al cierre (D-026, D-028, D-030).

## Qué se construyó

| Tarea | Resultado |
|---|---|
| T-07 | `etl/schema.sql` define `datos.db`; `etl/raw_schema.sql` define `raw.db` |
| T-08 | `clean()` con RN-01, RN-02 y RN-13 |
| T-09 | `validate_rows()` y `build_rejections()` (RN-11) |
| T-10 | `convert_unit()` y `normalize_units()` (RN-03, RN-04, RN-05) |
| T-11 | Agregación semanal (RN-07, RN-08, RN-09, RN-10) |
| T-12 | `flag_outliers()` (RN-12) |
| T-13 | `load()` y `run_etl()` (RN-14) |
| T-14 | `measure_match_coverage()` (K7) |
| T-14b | `check_quality()` |

Equivalencia con el diagrama de `DISENO.md` 8.3 (D-023):

| Diseño | Base |
|---|---|
| `dim_producto` | `dim_product` |
| `dim_region` | `dim_region` |
| `dim_canal` | `dim_channel` |
| `precio_semanal` | `weekly_price` |
| `ejecucion` | `etl_run` |
| `rechazo` | `rejection` |

`weekly_price` agrega dos cosas al diagrama: `normalized_unit` forma parte de la clave (un producto puede tener precio por kilo y por unidad en la misma semana) y la columna `flag` guarda `UNIDAD_NO_CONVERTIBLE` o `ATIPICO`.

## Cómo comprobarlo

1. `pytest -q` → todas las pruebas en verde (52 al cierre de este hito). Cada regla RN-01 a RN-14 aparece en el nombre de al menos una prueba (`pytest -q -k rn07`).
2. `python agent/agent.py` y luego `python etl/etl.py`. La última parte de la salida debe ser:
   ```
   LOADED | read 397814 | loaded 397814 | rejected 0 | weekly prices 131144
   K7 | 131 of 168 consumer keys have a margin
   ```
   Las cifras cambian cuando ODEPA publica semanas nuevas.
3. Ejecutar `python etl/etl.py` otra vez: mismas cifras (RN-14).
4. Crear la base vacía desde cero: `sqlite3 etl/datos.db < etl/schema.sql`.
5. Reproducir un valor a mano (T-11): tomate Semiduro Extra, RM, semana del 20-04-2026.
   En `wholesale_2026.csv` hay cuatro filas, todas en `$/bandeja 18 kilos`:

   | Fecha | Volumen | Precio promedio | Por kilo |
   |---|---|---|---|
   | 2026-04-20 | 220 | 12.000 | 666,67 |
   | 2026-04-21 | 250 | 12.000 | 666,67 |
   | 2026-04-21 | 160 | 12.500 | 694,44 |
   | 2026-04-21 | 470 | 12.000 | 666,67 |

   (666,67 × 940 + 694,44 × 160) / 1.100 = 670,71. En la base:
   ```sql
   SELECT weekly_price.price, weekly_price.volume, weekly_price.observation_count
   FROM weekly_price
   JOIN dim_product ON dim_product.product_id = weekly_price.product_id
   JOIN dim_channel ON dim_channel.channel_id = weekly_price.channel_id
   WHERE dim_product.product = 'Tomate' AND dim_product.variety = 'Semiduro'
     AND dim_product.quality = 'Extra' AND dim_channel.source = 'wholesale'
     AND weekly_price.region_id = 13 AND weekly_price.week_start = '2026-04-20';
   ```
   Devuelve 670,707…, 1100 y 4.

## Resultados reales

| Medida | Valor |
|---|---|
| Filas leídas | 397.814 (145.231 mayorista + 252.583 consumidor) |
| Filas rechazadas (RN-11) | 0 |
| Filas cargadas | 397.814 (leídas = cargadas + rechazadas) |
| Precios semanales | 131.144, en 41 semanas (29-12-2025 a 05-10-2026) |
| · sin marca | 128.971 |
| · `UNIDAD_NO_CONVERTIBLE` | 1.980 (solo mayorista) |
| · `ATIPICO` | 193 (0,15 % de los que tienen precio) |
| Productos / regiones / canales | 999 claves / 9 / 8 |
| K7 | 131 de 168 claves = 78,0 % |
| Tamaño de `datos.db` | 10 MB |
| Duración del ETL | unos 3 segundos |

Unidades (filas de origen):

| Fuente | A kilo | A unidad | A litro | Sin convertir |
|---|---|---|---|---|
| Mayorista | 102.226 (70,39 %) | 35.074 (24,15 %) | 0 | 7.931 (5,46 %) |
| Consumidor | 192.839 (76,35 %) | 53.134 (21,04 %) | 6.610 (2,62 %) | 0 |

Claves sin margen (37): 22 no existen en el mayorista, 8 están en unidades distintas (pimiento y ajo) y 7 no coinciden en semana y región.

## Qué quedó pendiente

- **Papa sin margen** (D-030): las calidades no coinciden entre fuentes. El criterio 5 de `DISENO.md` 11 se cumple para cuatro de los cinco productos. Mejora T-37.
- **Atípicos que parecen precios reales** (D-028): 49 de arándano en consumidor y 71 de limón mayorista. La mediana mezcla variedades.
- **Volumen en envases** (D-027): el promedio ponderado usa el volumen publicado, no kilos.
- **Tamaño del repositorio:** `datos.db` pesa 10 MB. Medido después en una simulación (D-034): cada semana agrega unos 0,7 MB al historial de Git, no 10 MB.
- **`datos.db` de esta entrega** se generó en una carpeta temporal y se copió a `etl/`, porque el entorno del asistente no permite a SQLite escribir en la carpeta del proyecto. Quedó un archivo vacío `etl/datos.db-journal` que se puede borrar. Ejecutar `python etl/etl.py` en el computador del autor confirma el resultado en su sitio.
- No se ha verificado el workflow de pruebas en GitHub con el código nuevo (aún no hay commits del hito 2).
