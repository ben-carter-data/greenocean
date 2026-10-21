# GreenOcean · Documento de arquitectura de software (SAD)

Cómo está construido GreenOcean, en los tres diagramas vivos del panel: se dibujan desde el proyecto real, así que no quedan desactualizados. Versión del 20-10-2026; el detalle está en `docs/DECISIONES.md` y el porqué de cada elección en el ADR.

## 1. Pipeline

[[diagrama:pipeline]]

Cada martes, Python descarga los CSV de ODEPA y el IPC del INE, los guarda tal como llegan en SQLite (aterrizaje) y en Parquet (bronce), y dbt Core los transforma sobre DuckDB en staging, intermedio y marts, con 31 pruebas de datos. Solo si todo pasa, el orquestador copia las tablas del panel a `etl/datos.duckdb` y la reemplaza de una vez.

## 2. Plataforma

[[diagrama:plataforma]]

Tres plataformas gratuitas: GitHub Actions ejecuta la carga semanal y las pruebas de cada push, el repositorio guarda el código y la base publicada, y Streamlit Community Cloud publica el panel desde `main`, con el token de GitHub y la clave de control en sus secretos.

## 3. Modelo de datos

[[diagrama:modelo]]

Un modelo estrella: la tabla de hechos `weekly_price` (814.610 precios) al centro, con las dimensiones de producto (1.609), región (9), canal (8) y fecha (250 semanas), el IPC semanal como puente y las tablas de auditoría aparte. El mayorista es un canal más, así que el margen compara dos canales de la misma tabla.
