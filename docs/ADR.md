# GreenOcean · Registros de decisiones de arquitectura (ADR)

Versión del 20-10-2026. Estas son las diez decisiones que más pesan en la arquitectura. Cada una mantiene su número original; el contexto completo está en la entrada D-xxx correspondiente de `docs/DECISIONES.md`.

| ADR | Decisión | Por qué | Alternativa descartada |
|---|---|---|---|
| ADR-01 | Usar solo los archivos oficiales de ODEPA y del INE | Son la fuente de verdad y tienen licencia abierta (D-001) | Scraping de sitios de supermercados |
| ADR-02 | Orquestar con GitHub Actions y publicar en Streamlit Community Cloud | No cuesta nada, no hay servidor que mantener y el panel queda en un enlace público (D-012) | Un servidor propio; Power BI, que exige licencia para compartir |
| ADR-04 | No subir los datos crudos al repositorio | Cada archivo anual pesa hasta 46 MB y se vuelve a descargar en cada carga (D-020) | Versionar todo o usar almacenamiento de archivos grandes |
| ADR-10 | Reconstruir todo en cada carga | Repetir una semana nunca duplica filas (D-024) | Cargas incrementales semana a semana |
| ADR-11 | Publicar solo si pasan las pruebas | Una carga incompleta o con errores nunca llega al panel (D-029, D-154) | Límites fijos de filas por semana |
| ADR-19 | Modelo estrella con una dimensión de fechas sin huecos | El rango de temporada necesita semana ISO, mes y estación para cada semana (D-023, D-095) | No registrada |
| ADR-30 | Parquet, dbt Core y DuckDB | Cada capa tiene sus pruebas y el motor se puede cambiar desde la configuración (D-154) | BigQuery en modo sandbox, que borra las tablas a los 60 días |
| ADR-31 | No usar un data warehouse en la nube | Con 14 MB, una carga semanal y un solo panel, la nube suma costo y riesgos sin aportar nada (D-152) | BigQuery como segundo destino de dbt |
| ADR-33 | Calcular precios reales con el IPC de alimentos del INE | Sin descontar la inflación, un precio de hoy parece caro solo porque todo subió (D-155) | Pegar las dos series del INE sin empalmar, que deja un salto falso de −33,7 % |
| ADR-34 | Separar la base de trabajo de dbt, la base que lee el panel y el respaldo | El panel lee un archivo liviano y nunca ve una construcción a medias (D-154) | Que el panel lea directamente la base de trabajo de dbt |
