# GreenOcean · Documento de arquitectura de software (SAD)

Versión del 20-10-2026. Los tres diagramas se generan desde el sistema real, así que siempre coinciden con lo que está en producción. El porqué de cada decisión está en el ADR y el detalle, en `docs/DECISIONES.md`.

## 1. Pipeline

[[diagrama:pipeline]]

Cada martes, un proceso en Python descarga los CSV de ODEPA, los guarda sin cambios en SQLite (aterrizaje) y los copia a Parquet (bronce). El IPC del INE se descarga aparte y va directo a Parquet, sin pasar por SQLite. Después, dbt Core sobre DuckDB arma las capas staging, intermedio y marts, y corre 31 pruebas de datos. Si todas pasan, las tablas que usa el panel se copian a `etl/datos.duckdb`, que reemplaza a la versión anterior de una sola vez.

## 2. Plataforma

[[diagrama:plataforma]]

Todo corre en servicios gratuitos. GitHub Actions ejecuta la carga semanal y las pruebas de cada cambio; el repositorio guarda el código y la base publicada; Streamlit Community Cloud publica el panel desde la rama `main` y guarda los secretos (el token de GitHub y la clave de control).

## 3. Modelo de datos

[[diagrama:modelo]]

Es un modelo estrella. Al centro está `weekly_price`, con 814.610 precios semanales, rodeada por las dimensiones de producto (1.609), región (9), canal (8) y fecha (250 semanas). El IPC semanal funciona como tabla puente y las tablas de auditoría van aparte. El mayorista es un canal más, así que el margen se calcula comparando dos filas de la misma tabla.
