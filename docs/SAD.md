# GreenOcean · Documento de arquitectura de software (SAD)

Versión 20-10-2026. Describe la arquitectura mediante tres vistas generadas a partir del sistema en ejecución, lo que garantiza su consistencia con la implementación. La justificación de las decisiones está en el ADR y el detalle, en `docs/DECISIONES.md`.

## 1. Vista de datos: pipeline

[[diagrama:pipeline]]

Arquitectura por capas con ejecución semanal. La ingesta en Python descarga los CSV de ODEPA y el IPC del INE; los datos se persisten sin transformar en SQLite (aterrizaje) y en Parquet (bronce). dbt Core sobre DuckDB construye las capas staging, intermedio y marts, validadas por 31 pruebas de datos. La publicación es atómica: el orquestador copia las tablas de consumo a `etl/datos.duckdb` solo si todas las pruebas pasan.

## 2. Vista de despliegue: plataforma

[[diagrama:plataforma]]

Tres plataformas gratuitas. GitHub Actions ejecuta el workflow semanal y la integración continua en cada push; el repositorio versiona el código y la base publicada; Streamlit Community Cloud despliega el panel desde la rama `main` y almacena los secretos (token de GitHub y clave de control).

## 3. Vista lógica: modelo de datos

[[diagrama:modelo]]

Modelo estrella. La tabla de hechos `weekly_price` (814.610 filas) se relaciona con las dimensiones de producto (1.609), región (9), canal (8) y fecha (250 semanas); el IPC semanal actúa como tabla puente y las tablas de auditoría quedan separadas. El canal mayorista se modela como un canal más, de modo que el margen se calcula entre filas de la misma tabla de hechos.
