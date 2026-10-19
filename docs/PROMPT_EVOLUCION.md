# Prompt de evolución · GreenOcean

Este documento guía la próxima etapa del proyecto. Lo lee quien la ejecute (el autor o un agente de IA) antes de tocar el código. Resume para quién se construye, con qué tecnologías, en qué orden y con qué reglas.

---

## 1. Punto de partida

GreenOcean es un pipeline semanal que descarga los precios de alimentos de ODEPA (mayoristas y consumidor), los limpia con 14 reglas de negocio, controla su calidad, los guarda en un data warehouse con modelo estrella y los publica en un panel Streamlit. Corre solo cada martes en GitHub Actions.

| Cifra actual | Valor |
|---|---|
| Precios semanales | 811.578, de 2022-01-03 a 2026-10-05 (249 semanas) |
| Filas leídas · cargadas · rechazadas | 2.512.298 · 2.512.097 · 201 |
| Regiones con datos | 9 de 16 |
| Almacenamiento | SQLite (`etl/datos.db`, unos 34 MB, subido al repositorio cada semana) |
| Pruebas | Más de 420, incluida la auditoría que reconstruye precios desde la fuente (`tests/test_data_audit.py`) |

Los documentos de referencia son `docs/PRD.md`, `docs/SAD.md`, `docs/ADR.md` y el registro completo `docs/DECISIONES.md`.

---

## 2. Para quién se construye

### 2.1 Usuarios del producto

El panel sirve a **profesionales que toman decisiones con estos precios**, no al consumidor final.

| Usuario | Su decisión | Qué le responde el panel |
|---|---|---|
| Analista de pricing | Ajustar sus precios de venta | ¿El precio de esta semana es normal para la época? |
| Comprador / abastecimiento | Cuándo comprar, qué negociar | ¿Cuánto paga el consumidor sobre el mayorista, y es lo habitual? |
| Gerencia | Dónde mirar esta semana | ¿Qué se movió y qué es inusual? (indicadores y alertas) |
| Equipo de datos | Si la carga es confiable | Calidad de datos y Ejecuciones |

Toda nueva funcionalidad debe responder a una decisión de uno de estos usuarios. Si no responde a ninguna, no se construye.

### 2.2 Público del portafolio

Quien evalúa el proyecto es una persona que contrata en **ingeniería de datos o analytics engineering**. En los primeros 30 segundos debe ver: el problema en una frase, el diagrama de arquitectura, cifras reales, el enlace al panel en vivo y, para profundizar, PRD, SAD y ADR. Lo que diferencia este proyecto es la calidad de sus decisiones y su verificación, no la cantidad de tecnologías.

---

## 3. Tecnologías elegidas

Todas son de código abierto o gratuitas **sin vencimiento**: el proyecto debe seguir corriendo solo, cada semana, sin pruebas que expiren ni cuentas que se pausen.

| Capa | Tecnología | Por qué |
|---|---|---|
| Ingesta | Python (agente actual) | Ya funciona y está probado |
| Capa bronce | **Parquet** | Formato estándar de data lake; lo leen BigQuery, Snowflake y Databricks |
| Transformaciones y pruebas | **dbt Core** | La herramienta de transformación más pedida; las reglas RN-01 a RN-14 pasan a ser pruebas de dbt |
| Motor analítico | **DuckDB** (con el adaptador `dbt-duckdb`) | Motor en columnas, un solo archivo, sin servidor ni costo |
| Orquestación | GitHub Actions | Gratis en repositorios públicos; el commit semanal mantiene vivo el workflow programado |
| Panel | Streamlit Community Cloud | Gratis; la app puede dormirse tras un período sin visitas y se despierta al abrirla |

### Descartadas, con su motivo (van al ADR)

| Opción | Motivo |
|---|---|
| BigQuery (sandbox) | Las tablas y particiones vencen a los 60 días: si el pipeline se detiene, el panel queda vacío y se pierde el histórico particionado |
| Snowflake, Redshift | Solo periodos de prueba: el portafolio dejaría de funcionar al terminar |
| Databricks | Pensado para Spark; sobredimensionado para 34 MB |
| PostgreSQL gratuito (Neon, Supabase) | Algunos planes gratuitos pausan proyectos inactivos |

Dependencias autorizadas por el autor para la refonte: `dbt-core`, `dbt-duckdb`, `duckdb` y, si hace falta para Parquet, `pyarrow`. Ninguna otra sin avisar.

---

## 4. Portabilidad: migrar cambiando configuración, no código

1. **Un solo punto de conexión.** El motor se elige en `profiles.yml` de dbt. Hoy `duckdb`; mañana `bigquery`, `snowflake`, `postgres` o `databricks`, con los mismos modelos.
2. **SQL estándar.** Los modelos evitan funciones propias de DuckDB; fechas y otras diferencias pasan por macros de dbt.
3. **Una sola capa de acceso en el panel** (`bi/queries.py`): cambiar de motor toca un archivo.
4. **Datos en Parquet**, legibles directamente por los warehouses en la nube.
5. **La auditoría corre sobre cualquier motor** y debe dar exactamente las mismas cifras antes de cualquier cambio.

El SAD (sección 12) y el ADR-31 dicen en pocas líneas cuándo se justificaría un warehouse en la nube y por qué hoy no; no se escribe una guía de migración detallada para una migración que, en el alcance público, probablemente nunca hará falta.

---

## 5. Plan de la refonte (en ejecución)

La refonte se ejecuta ahora, no es una proyección. Cada paso termina con sus pruebas en verde, su entrada D-xxx en `docs/DECISIONES.md`, el panel funcionando y la validación del autor en local antes de cualquier push.

| Paso | Contenido | Criterio de aceptación | Estado |
|---|---|---|---|
| **0** | Lectura completa y estrategia: se comparan al menos tres estrategias de refonte (con el skill «skills arena» si está disponible) según los criterios de la sección 2.2, y el autor valida la ganadora | Estrategia escrita y validada | En curso |
| **1** | Auditoría de cifras y contradicciones: cada número del panel se recalcula de forma independiente y las páginas coinciden entre sí; se guarda una fotografía de las cifras clave | Informe de diferencias corregidas, con su prueba | Pendiente |
| **2** | Migración a Parquet (bronce), dbt Core (staging → intermedio → marts, reglas como pruebas) y DuckDB, en paralelo a SQLite; el panel cambia de motor solo con cifras idénticas | Auditoría fila a fila y fotografía idénticas; `dbt build` en verde en GitHub Actions | Pendiente |
| **3** | IPC del INE: precios reales junto a los nominales, con regla mes → semana documentada | Selector «Nominal / Real» en Contexto de precios; prueba de auditoría del deflactor | Pendiente |
| **4** | Revisión de páginas «one view»: conservar, fusionar, mover o retirar, con la validación del autor | Cada página en una pantalla de 1440 × 900, simétrica, verificada en capturas | Pendiente |
| **5** | Contexto de precios: búsqueda libre de producto como en el Resumen; sin el menú «Calidad · unidad» | Producto elegido desde la búsqueda o los diagramas | Pendiente |
| **6** | PRD, SAD y ADR premium, descargables (PDF y Markdown), en la sección Documentación, describiendo la arquitectura entregada | Documentos con portada, índice y paginación; el panel y GitHub coinciden | Pendiente |
| **7** | Sección «Escalabilidad»: clima (previsto) y criterios para un warehouse en la nube (ADR-31), como proyección y sin cifras inventadas | Cada extensión con su fuente, su estado y su decisión | Pendiente |

El paso «publicar el estado validado» ya se hizo el 2026-10-19 (21 commits).

### Fuera de alcance

- **Comparación por cadena de supermercados** (Lider, Jumbo, Unimarc): no hay fuente abierta oficial conocida y el scraping contradice D-001. Se documenta en el ADR como opción estudiada y descartada.
- **Vista para el consumidor** («dónde conviene comprar»): no responde a los usuarios de la sección 2.1.
- **Predicción de precios**: el proyecto describe, no pronostica.

---

## 6. Reglas de trabajo

- **Idioma:** todo en español: panel, documentos, decisiones y mensajes de commit.
- **Vocabulario:** pipeline, workflow, ingesta, ETL, staging, data warehouse. Nunca «robot».
- **Autoría:** «el autor» (hombre); ningún nombre personal en la portada ni en los documentos; nada inventado sobre él.
- **Datos:** nunca se borra el histórico; nunca se inventa un precio (sin interpolación); toda cifra del panel debe poder recalcularse desde la fuente.
- **Verificación:** cada cambio de cálculo lleva una prueba en `tests/test_data_audit.py`; ninguna migración se activa sin que la auditoría dé las mismas cifras.
- **Panel:** cada página simétrica y en una pantalla cuando se pueda; ningún espacio en blanco inútil; ningún código visible.
- **Documentación:** cada decisión significativa entra a `docs/DECISIONES.md` (D-xxx) y, si es de arquitectura, al ADR; PRD y SAD se actualizan en la misma fase. Ningún código en los documentos, solo tablas y diagramas.
- **Git:** commits limpios y separados por tema; **push solo después de que el autor revise en local**.

---

## 7. ¿Alcanza?

**Sí, con holgura para un portafolio.** La pila cubre lo que un equipo de datos usa de verdad: ingesta en Python, data lake en Parquet, transformaciones y pruebas en dbt, motor analítico en columnas, orquestación programada y un panel en producción. Todo a costo cero y sin vencimientos.

Lo que el proyecto **no** demuestra, y conviene decirlo en el SAD como límite consciente, es operar un warehouse en la nube con permisos, costos y volumen real. Por eso la portabilidad (sección 4) es parte del diseño: muestra que la migración está pensada, aunque hoy no haga falta.

Por su naturaleza (datos públicos, semanales y pequeños), el proyecto probablemente nunca necesitará la nube. La competencia en un warehouse en la nube se demuestra mejor en otro proyecto del portafolio, donde el volumen la justifique. Si un puesto lo exige, se puede agregar BigQuery como segundo destino del mismo proyecto dbt, sin que el panel dependa de él y declarándolo así en el ADR.
