# GreenOcean · Registros de decisiones de arquitectura (ADR)

Las diez decisiones que más pesan en la arquitectura. Cada una conserva su número original y sus entradas en `docs/DECISIONES.md`, donde está el detalle.

| ADR | Decisión | Motivo | Alternativa descartada |
|---|---|---|---|
| ADR-01 | Solo archivos oficiales de ODEPA y del INE | Los datos ya existen con licencia abierta y son la fuente de verdad (D-001) | Scraping de supermercados |
| ADR-02 | GitHub Actions y Streamlit Community Cloud | Costo cero, sin servidor que mantener y con enlace público (D-012) | Servidor propio o Power BI, que exige licencia para compartir |
| ADR-04 | Los datos crudos no se suben al repositorio | Cada archivo anual pesa hasta 46 MB y se reconstruye en cada carga (D-020) | Subir todo o usar almacenamiento de archivos grandes |
| ADR-10 | Carga idempotente por reconstrucción completa | Repetir una semana no debe duplicar filas (D-024) | Cargas incrementales semana a semana |
| ADR-11 | Pruebas antes de publicar | Una carga truncada o rota nunca llega al panel (D-029, D-154) | Rangos fijos de filas por semana |
| ADR-19 | Modelo estrella con dimensión de fechas | El rango habitual necesita semana ISO, mes y estación sin huecos (D-023, D-095) | No registrada |
| ADR-30 | Parquet, dbt Core y DuckDB | Capas con pruebas declaradas y un motor que se cambia en la configuración (D-154) | BigQuery sandbox, cuyas tablas vencen a los 60 días |
| ADR-31 | Sin warehouse en la nube mientras los datos sean públicos | Con unos 14 MB, carga semanal y un panel de lectura, la nube suma costo y vencimientos sin beneficio (D-152) | BigQuery como segundo destino de dbt solo para demostrarlo |
| ADR-33 | Precios reales con el IPC de alimentos del INE | Sin descontar la inflación, lo que solo subió con los precios parece caro (D-155) | Pegar las dos series del INE sin enlazar: salto de −33,7 % |
| ADR-34 | Almacén de trabajo, base servida y respaldo con paridad | El panel lee un archivo chico y nunca una construcción a medias (D-154) | Que el panel lea directamente el almacén de dbt |
