# GreenOcean · Registros de decisiones de arquitectura (ADR)

Versión 20-10-2026. Resume las diez decisiones de mayor impacto arquitectónico. Cada una conserva su identificador original; el contexto completo y las consecuencias están en las entradas D-xxx de `docs/DECISIONES.md`.

| ADR | Decisión | Justificación | Alternativa descartada |
|---|---|---|---|
| ADR-01 | Ingesta exclusiva de archivos oficiales (ODEPA, INE) | Fuente de verdad con licencia abierta (D-001) | Scraping de supermercados |
| ADR-02 | Orquestación en GitHub Actions y despliegue en Streamlit Community Cloud | Costo cero, sin infraestructura propia y acceso público (D-012) | Servidor propio; Power BI, que requiere licencia para compartir |
| ADR-04 | Datos crudos fuera del repositorio | Archivos anuales de hasta 46 MB, reconstruibles en cada carga (D-020) | Versionar todo; almacenamiento de archivos grandes |
| ADR-10 | Carga idempotente por reconstrucción completa | Una re-ejecución no duplica filas (D-024) | Cargas incrementales |
| ADR-11 | Pruebas de calidad como condición de publicación | Ninguna carga truncada o inválida llega al panel (D-029, D-154) | Umbrales fijos de filas por semana |
| ADR-19 | Modelo estrella con dimensión de fechas continua | El rango estacional requiere semana ISO, mes y estación sin huecos (D-023, D-095) | No registrada |
| ADR-30 | Parquet, dbt Core y DuckDB | Capas con pruebas declaradas; motor intercambiable por configuración (D-154) | BigQuery sandbox, con expiración de tablas a 60 días |
| ADR-31 | Sin data warehouse en la nube con datos públicos | Con 14 MB, carga semanal y un consumidor, la nube agrega costo y riesgo sin beneficio (D-152) | BigQuery como segundo destino de dbt |
| ADR-33 | Precios reales con el IPC de alimentos del INE | Comparación temporal sin sesgo inflacionario (D-155) | Unión directa de las dos series del INE: discontinuidad de −33,7 % |
| ADR-34 | Separación entre almacén de trabajo, base servida y respaldo con paridad | El panel consume un artefacto compacto y nunca una construcción parcial (D-154) | Lectura directa del almacén de dbt |
