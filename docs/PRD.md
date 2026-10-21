# GreenOcean · Documento de requisitos del producto (PRD)

Monitor semanal de precios de alimentos en Chile, sobre los datos abiertos de ODEPA y el IPC del INE. Versión del 20-10-2026; el detalle de cada decisión está en `docs/DECISIONES.md`.

## 1. Problema

Los precios mayoristas y al consumidor de ODEPA son públicos, pero no se pueden comparar sin trabajo: uno es diario y por caja o malla, el otro semanal y por kilo o unidad, y ninguno descuenta la inflación. Cruzarlos a mano cada semana es lento y no deja rastro. GreenOcean lo hace solo cada martes y publica un panel de lectura donde cada cifra se puede seguir hasta el archivo oficial.

Hoy la base publicada tiene 814.610 precios semanales en 250 semanas (03-01-2022 a 12-10-2026), 9 regiones, 8 canales, 1.609 claves de producto y 202 meses del IPC de alimentos. La última carga leyó 2.521.012 filas: 2.520.811 cargadas y 201 rechazadas con su motivo.

## 2. Usuarios

Perfiles de diseño, no entrevistas: el panel es para quien decide con estos precios, no para el consumidor final.

| Usuario | Su decisión | Qué le responde el panel |
|---|---|---|
| Analista de pricing | Ajustar precios de venta | ¿El precio de hoy es normal para la época, en pesos de hoy? |
| Compras | Cuándo comprar y qué negociar | ¿Cuánto paga el consumidor sobre el mayorista? |
| Gerencia | Dónde mirar esta semana | ¿Qué se movió y qué es inusual? |
| Revisor técnico | Si el proyecto es confiable | Calidad, pruebas, linaje y documentos |

[[diagrama:actores]]

El visitante solo lee. El autor opera: responde consultas SQL a pedido, mantiene el código y los secretos y puede lanzar una carga manual con clave.

## 3. Preguntas de negocio

| Pregunta | Cómo se responde | Dónde |
|---|---|---|
| ¿Qué se movió esta semana y es inusual? | Variación sobre las mismas regiones y alertas K6 | Resumen semanal |
| ¿Es normal el precio de hoy para la época? | Rango habitual P25–P75 de las mismas semanas en años anteriores, nominal o real | Precios e inflación |
| ¿Cuánto paga el consumidor sobre el mayorista? | Margen K1 por canal frente a su rango habitual | Precios e inflación |

## 4. Requisitos clave

| ID | Requisito | Cómo se cumple |
|---|---|---|
| RF-01 | Cargar ODEPA y el IPC cada semana sin intervención | Workflow de GitHub Actions cada martes |
| RF-02 | Rechazar filas inválidas con motivo, sin borrar nada | Tabla `rejection`; leídas = cargadas + rechazadas |
| RF-03 | No publicar una carga que no pasó sus pruebas | 31 pruebas de dbt y reemplazo atómico de la base |
| RF-04 | Mostrar precios reales junto a los nominales | Selector Nominal / Real con el IPC del INE |
| RF-05 | Mostrar la calidad y el origen de cada cifra | Calidad y auditoría |
| RNF-01 | Costo cero y sin vencimientos | Parquet, dbt Core, DuckDB, GitHub Actions y Streamlit Community Cloud |
| RNF-02 | Solo lectura para el visitante | DuckDB en modo lectura; la carga manual pide clave |
| RNF-03 | Cada vista se lee en una pantalla de 1440 × 900 | Revisado en cada cambio del panel |

## 5. Pantallas reales

Capturas del panel publicado, cada una en un tema distinto. No son bocetos.

[[diagrama:mockups]]
