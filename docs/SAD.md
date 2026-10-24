# GreenOcean · Documento de arquitectura de software (SAD)

Versión del 24-10-2026. La arquitectura se describe por vistas, cada una en un solo lugar. Los diagramas de contexto y de contenedores viven en este documento; los de datos, despliegue y seguridad viven en su página del panel, donde muestran su estado en vivo, y aquí se enlazan. El porqué de cada decisión está en el ADR y el detalle, en `docs/DECISIONES.md`.

## 1. Contexto

[[diagrama:contexto]]

GreenOcean es un pipeline semanal y un panel de solo lectura. Lee dos fuentes públicas, ODEPA y el INE, y se apoya en dos servicios gratuitos: GitHub guarda el código y la base publicada y ejecuta la carga, y Streamlit Community Cloud publica el panel. El visitante solo lee el panel; el administrador mantiene el código y los secretos.

## 2. Principios

Cinco reglas explican casi todas las decisiones de este documento:

- **Costo cero y sin vencimientos.** Solo servicios gratuitos permanentes; nada que pagar ni renovar (ADR-02, ADR-31).
- **Nunca inventar un dato.** No se interpola un precio que falta ni se estima un índice que el INE aún no publica; lo que falta se dice.
- **Rehacer todo en cada carga.** Cada martes se recalcula la historia completa desde los archivos oficiales, así repetir una carga nunca duplica nada (ADR-10).
- **Publicar solo lo validado.** El panel ve una base nueva solo si pasó todas las pruebas; si no, sigue mostrando la anterior (ADR-11).
- **Cada cifra se puede comprobar.** Las pruebas recalculan los números del panel por un segundo camino, sin dbt (ADR-34).

## 3. Contenedores

[[diagrama:contenedores]]

Dentro del sistema hay dos aplicaciones y tres almacenes de datos. La **carga semanal** (Python, dbt Core y DuckDB) es un solo contenedor porque el agente de descarga, el ETL y dbt corren en el mismo job: descarga los CSV, los guarda sin cambios, los transforma y prueba, y reemplaza la **base servida** (`etl/datos.duckdb`) solo si todo pasa. Los **archivos de trabajo** (aterrizaje en SQLite, bronce en Parquet y la base de trabajo de dbt) se rehacen en cada carga y no se suben a GitHub. El **respaldo** (`etl/datos.db`) calcula los mismos precios por otro camino, sin dbt, para comprobar la paridad. El **panel web** (Streamlit) lee la base servida en solo lectura y, con la clave de control, lanza la carga por la API de GitHub.

## 4. Datos

Los datos avanzan por capas, de lo más crudo a lo más útil: el **aterrizaje** guarda las filas tal como llegan; el **bronce** es su copia literal en Parquet, por fuente y año; **staging** limpia tipos y textos; **intermedio** aplica las reglas de negocio (unidades, semanas, rechazos) y los **marts** son el modelo estrella que lee el panel. El recorrido completo y el linaje modelo por modelo están en [[vista:Pipeline y linaje]]. El modelo estrella, el modelo entidad-relación, dónde vive cada almacén y los cruces entre bases están en [[vista:Modelo de datos]]. Las cifras de esas páginas se leen de la base en cada carga.

## 5. Ejecución: la carga de cada martes

Esta vista sigue una carga de principio a fin. Cada paso empieza solo si el anterior terminó bien:

1. A las 12:00 UTC, GitHub Actions crea una máquina nueva y recupera de su caché los CSV de los años ya cerrados.
2. El agente descarga de ODEPA el archivo del año en curso y los que falten, y anota la huella SHA-256 de cada uno en `manifest.json`.
3. El ETL en Python calcula los precios por su cuenta y escribe el respaldo `etl/datos.db`.
4. `etl/pipeline.py` guarda las filas en el aterrizaje, las copia al bronce junto con el IPC del INE y ejecuta `dbt build`, que construye y prueba cada modelo en la base de trabajo.
5. La compuerta: si falla una prueba de dbt o la carga lee menos del 90 % de las filas de la última carga correcta, el proceso se detiene. Si todo pasa, las tablas del panel se copian a un archivo nuevo que reemplaza a `etl/datos.duckdb`.
6. pytest corre sobre la base nueva, incluida la paridad entre el respaldo y DuckDB.
7. Solo entonces la máquina sube la base nueva a la rama `main`; Streamlit Community Cloud la toma desde ahí.
8. Por último, publica el informe semanal como un issue del repositorio.

Si algo falla, los pasos siguientes no corren: la base publicada no cambia, GitHub Actions marca la ejecución en rojo y avisa al autor por correo, y el [[vista:Centro de operación]] muestra en qué paso se detuvo. El administrador también puede lanzar esta misma carga desde el panel, con la clave de control.

## 6. Despliegue

Cada pieza corre en un servicio gratuito, sin servidor propio. El job semanal y las pruebas de cada cambio corren en máquinas de GitHub Actions (Ubuntu, Python 3.11), que se crean y se descartan en cada ejecución; los CSV de los años cerrados se guardan en la caché de Actions. La base servida vive en el repositorio de GitHub, en la rama `main`, junto al código. Streamlit Community Cloud ejecuta el panel desde esa rama y guarda los secretos (el token de GitHub y la clave de control). El aterrizaje (`etl/raw.db`, de cientos de MB) solo existe en el computador del autor y en la máquina de cada carga. El diagrama de despliegue, con el estado en vivo de cada pieza, está en la pestaña «Despliegue» de [[vista:Centro de operación]]; el camino de un cambio hasta producción, en su pestaña «CI/CD».

## 7. Seguridad

Las amenazas, el control que mitiga cada una, la prueba que lo verifica y la mejora continua que los mantiene están en [[vista:Arquitectura de seguridad]]; el procedimiento para comprobarlas, en [[vista:Plan de pruebas de seguridad]].

## 8. Calidad y observabilidad

La calidad se controla en tres puertas: el archivo (¿llegó completo y al día?), cada fila (¿es válida?) y la base (¿es coherente y pasó sus pruebas?). Once indicadores, repartidos en seis dimensiones, se miden en cada carga contra su umbral; uno fuera de rango pone el veredicto en rojo. El detalle, con la consulta de cada indicador y la evidencia de cada control, está en [[vista:Calidad y auditoría]].

Para saber qué pasó, cada carga deja rastro en cuatro lugares: `etl_run` (filas leídas, cargadas y rechazadas de cada carga publicada), `dbt_result` (el resultado de cada modelo y prueba), el registro de GitHub Actions (cada paso, también los que fallan) y el correo que GitHub envía al autor si la carga falla. El Centro de operación los reúne en su pestaña «Monitoreo».

## 9. Componentes

Se omite la vista de componentes (nivel 3 del modelo C4). El panel es una sola aplicación de Streamlit cuyos módulos de `bi/` no se despliegan por separado, y la carga semanal ya se muestra paso a paso en el diagrama de CI/CD y en el linaje de dbt: un diagrama de componentes repetiría esas vistas sin decir nada nuevo.

## 10. Riesgos técnicos

| Riesgo | Qué pasaría | Cómo se mitiga hoy |
|---|---|---|
| ODEPA cambia el formato de sus archivos | Una carga mal leída | La compuerta de la sección 5 la rechaza y el panel sigue con la última carga válida |
| Una dependencia cambia sin aviso | Una carga lenta o rota sin que el código cambie: pasó con DuckDB 2 (D-227) y con certifi, que retiró la raíz del certificado de ODEPA (D-164) | DuckDB tiene versión máxima en `requirements.txt`; la raíz de ODEPA viaja con el agente, sin desactivar la verificación |
| El historial de Git crece con cada carga | Cada carga agrega una versión nueva de las dos bases al historial del repositorio | Por ahora se acepta; las opciones están en [[vista:Escalabilidad]] |
| Los planes gratuitos cambian sus condiciones | Habría que mover la carga o el panel a otro servicio | El pipeline no depende de la plataforma: corre igual en cualquier máquina con Python 3.11 o 3.12 |
