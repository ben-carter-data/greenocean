# GreenOcean · Documento de arquitectura de software (SAD)

Versión del 23-10-2026. La arquitectura se describe por vistas, cada una en un solo lugar. Los diagramas de contexto y de contenedores viven en este documento; los de datos, despliegue y seguridad viven en su página del panel, donde muestran su estado en vivo, y aquí se enlazan. El porqué de cada decisión está en el ADR y el detalle, en `docs/DECISIONES.md`.

## 1. Contexto

[[diagrama:contexto]]

GreenOcean es un pipeline semanal y un panel de solo lectura. Lee dos fuentes públicas, ODEPA y el INE, y se apoya en dos servicios gratuitos: GitHub guarda el código y la base publicada y ejecuta la carga, y Streamlit Community Cloud publica el panel. El visitante solo lee el panel; el administrador mantiene el código y los secretos.

## 2. Contenedores

[[diagrama:contenedores]]

Dentro del sistema hay dos aplicaciones y tres almacenes de datos. La **carga semanal** (Python, dbt Core y DuckDB) es un solo contenedor porque el agente de descarga, el ETL y dbt corren en el mismo job: descarga los CSV, los guarda sin cambios, los transforma y prueba, y reemplaza la **base servida** (`etl/datos.duckdb`) solo si todo pasa. Los **archivos de trabajo** (aterrizaje en SQLite, bronce en Parquet y la base de trabajo de dbt) se rehacen en cada carga y no se suben a GitHub. El **respaldo** (`etl/datos.db`) calcula los mismos precios por otro camino, sin dbt, para comprobar la paridad. El **panel web** (Streamlit) lee la base servida en solo lectura y, con la clave de control, lanza la carga por la API de GitHub.

## 3. Datos

El recorrido del dato por capas (fuentes, aterrizaje, bronce, staging, intermedio, marts y consumo) y el linaje modelo por modelo están en [[vista:Pipeline y linaje]]. El modelo estrella, el modelo entidad-relación, dónde vive cada almacén y los cruces entre bases están en [[vista:Modelo de datos]]. Las cifras de esas páginas se leen de la base en cada carga.

## 4. Despliegue

Cada pieza corre en un servicio gratuito, sin servidor propio. El job semanal y las pruebas de cada cambio corren en máquinas de GitHub Actions (Ubuntu, Python 3.11), que se crean y se descartan en cada ejecución; los CSV de los años cerrados se guardan en la caché de Actions. La base servida vive en el repositorio de GitHub, en la rama `main`, junto al código. Streamlit Community Cloud ejecuta el panel desde esa rama y guarda los secretos (el token de GitHub y la clave de control). El aterrizaje de 665 MB solo existe en el computador del autor y en la máquina de cada carga. El diagrama de despliegue, con el estado en vivo de cada pieza, está en la pestaña «Despliegue» de [[vista:Centro de operación]]; el camino de un cambio hasta producción, en su pestaña «CI/CD».

## 5. Seguridad

Las fronteras del sistema, el control que protege cada una y la prueba que lo verifica están en [[vista:Mapa de seguridad]]; el procedimiento para comprobarlas, en [[vista:Plan de pruebas de seguridad]].

## 6. Componentes

Se omite la vista de componentes (nivel 3 del modelo C4). El panel es una sola aplicación de Streamlit cuyos módulos de `bi/` no se despliegan por separado, y la carga semanal ya se muestra paso a paso en el diagrama de CI/CD y en el linaje de dbt: un diagrama de componentes repetiría esas vistas sin decir nada nuevo.
