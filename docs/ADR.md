# GreenOcean · Registros de decisiones de arquitectura (ADR)

Versión del 23-10-2026. Las diez decisiones que más pesan en la arquitectura, cada una con su contexto, la decisión, las alternativas consideradas y sus consecuencias. Cada ADR conserva su número original y apunta a su entrada D-xxx de `docs/DECISIONES.md`, que tiene el detalle completo.

## ADR-01 · Usar solo los archivos oficiales de ODEPA y del INE

- **Estado:** aceptada (D-001).
- **Contexto:** los precios que el proyecto necesita ya se publican como archivos CSV en portales de datos abiertos, con licencia que permite reutilizarlos.
- **Decisión:** descargar los CSV oficiales de ODEPA (precios) y del INE (IPC de alimentos), sin modificar ningún valor.
- **Alternativas:** extraer precios de sitios de supermercados (*scraping*); registros públicos de salud.
- **Consecuencias:** la fuente es estable y verificable, y no depende del diseño de una página. A cambio, no se pueden comparar cadenas de supermercados, porque no hay una fuente oficial para eso.

## ADR-02 · Orquestar con GitHub Actions y publicar en Streamlit Community Cloud

- **Estado:** aceptada (D-012).
- **Contexto:** un proyecto público, con una carga por semana y un panel de solo lectura, que no debe tener costo ni un servidor que mantener.
- **Decisión:** GitHub Actions ejecuta la carga semanal y las pruebas de cada cambio; Streamlit Community Cloud publica el panel desde la rama `main`.
- **Alternativas:** un servidor propio; Power BI, que exige licencia para compartir un panel.
- **Consecuencias:** cualquiera puede abrir el panel desde un enlace y clonar el proyecto. La concurrencia y el volumen quedan limitados a lo que dan los planes gratuitos, suficiente para datos semanales de este tamaño.

## ADR-04 · No subir los datos crudos al repositorio

- **Estado:** aceptada (D-020).
- **Contexto:** cada CSV anual de ODEPA pesa hasta unos 65 MB y la base cruda de todos los años pesa cientos de MB; GitHub rechaza archivos de más de 100 MB y el repositorio crecería en cada carga.
- **Decisión:** los CSV y la base de aterrizaje (`etl/raw.db`) se reconstruyen en cada carga y quedan fuera del repositorio. Solo se versionan la base servida, el respaldo y el registro de descargas (`manifest.json`, con la huella SHA-256 de cada archivo).
- **Alternativas:** versionar todo; usar almacenamiento de archivos grandes.
- **Consecuencias:** el repositorio se mantiene liviano y cada archivo descargado se puede verificar contra su huella. Quien clone el proyecto debe ejecutar el agente para tener los datos crudos; los indicadores sí vienen incluidos.

## ADR-10 · Reconstruir todo en cada carga

- **Estado:** aceptada (D-024).
- **Contexto:** la base cruda ya se rehace en cada carga, y una semana que cruza dos años junta filas de dos archivos.
- **Decisión:** cada carga vuelve a calcular todos los precios semanales desde las filas crudas, en vez de agregar solo la semana nueva.
- **Alternativas:** cargas incrementales, semana a semana, con claves.
- **Consecuencias:** repetir una carga nunca duplica filas y no hace falta lógica especial para el cambio de año. La tabla de rechazos guarda solo los de la última carga; de las anteriores queda su número en `etl_run`.

## ADR-11 · Publicar solo si pasan las pruebas

- **Estado:** aceptada (D-029, D-154).
- **Contexto:** un archivo truncado o una regla rota no deben llegar nunca al panel.
- **Decisión:** la base servida se reemplaza solo si pasan todas las pruebas de dbt, si la carga lee al menos el 90 % de las filas de la última carga correcta y si pytest pasa sobre la base nueva. Si algo falla, la carga queda registrada como fallida y la base publicada no cambia.
- **Alternativas:** límites fijos de filas por semana.
- **Consecuencias:** el panel siempre muestra la última carga válida. La primera carga no tiene con qué compararse y un archivo duplicado no se detecta por conteo; lo detectan las pruebas de unicidad.

## ADR-19 · Modelo estrella con una dimensión de fechas sin huecos

- **Estado:** aceptada (D-023, D-095).
- **Contexto:** comparar un precio con la misma época de otros años exige saber, para cada semana, su semana ISO, su mes y su estación, aunque esa semana no tenga precios.
- **Decisión:** un modelo estrella con `weekly_price` al centro y las dimensiones de producto, región, canal y fecha; `dim_date` tiene una fila por semana, sin huecos, desde la primera hasta la última.
- **Alternativas:** no se registró una alternativa en su momento.
- **Consecuencias:** los cálculos por época y el IPC semanal se unen por `week_start` con una clave foránea real. Las tablas y columnas van en inglés, así que el modelo no coincide letra por letra con los nombres del diseño original.

## ADR-30 · Parquet, dbt Core y DuckDB

- **Estado:** aceptada (D-154).
- **Contexto:** las reglas de negocio estaban en un ETL en Python sin capas ni pruebas declarativas, y el proyecto debía seguir siendo gratuito y portable.
- **Decisión:** el bronce en Parquet, las transformaciones y sus pruebas en dbt Core (staging, intermedio y marts) y DuckDB como motor.
- **Alternativas:** BigQuery en modo *sandbox*, cuyas tablas vencen a los 60 días.
- **Consecuencias:** cada capa tiene sus pruebas y el motor se puede cambiar desde la configuración de dbt. El ETL en Python se conserva como respaldo independiente para comprobar la paridad.

## ADR-31 · No usar un data warehouse en la nube

- **Estado:** aceptada (D-152).
- **Contexto:** datos públicos, semanales y de pocos megabytes, leídos por un solo panel.
- **Decisión:** la base servida es un archivo DuckDB en el repositorio; no hay un warehouse en la nube.
- **Alternativas:** BigQuery como segundo destino de dbt.
- **Consecuencias:** no hay costo, secretos de nube ni vencimientos. Se reconsideraría solo si una empresa sumara sus propios datos; los umbrales están en la página Escalabilidad.

## ADR-33 · Calcular precios reales con el IPC de alimentos del INE

- **Estado:** aceptada (D-155).
- **Contexto:** sin descontar la inflación, un precio de hoy parece caro solo porque todo subió.
- **Decisión:** usar la división «Alimentos y bebidas no alcohólicas» del IPC del INE, enlazando sus dos series con la variación oficial de enero 2024; cada semana toma el IPC del mes de su lunes.
- **Alternativas:** pegar las dos series del INE sin enlazarlas, lo que deja un salto falso de −33,7 %.
- **Consecuencias:** los precios reales quedan en pesos del último mes publicado. Una semana de un mes que el INE aún no publica usa ese último mes y queda marcada como provisional; nunca se inventa un índice.

## ADR-34 · Separar la base de trabajo de dbt, la base que lee el panel y el respaldo

- **Estado:** aceptada (D-154).
- **Contexto:** el panel no debe leer nunca una base a medio construir.
- **Decisión:** dbt construye en una base de trabajo que no se sube (`etl/warehouse_build.duckdb`); al final de una carga válida, las tablas del panel se copian a un archivo nuevo y compacto que reemplaza de una vez a `etl/datos.duckdb`. El ETL en Python escribe aparte el respaldo `etl/datos.db`.
- **Alternativas:** que el panel lea directamente la base de trabajo de dbt.
- **Consecuencias:** el panel lee un archivo liviano y siempre completo, y el respaldo permite comprobar que dos caminos independientes dan las mismas cifras.
