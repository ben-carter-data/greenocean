# GreenOcean · Documento de requisitos del producto (PRD)

Versión 20-10-2026. Define el propósito, los usuarios y los requisitos verificables de GreenOcean. Las decisiones de detalle se registran en `docs/DECISIONES.md`.

## 1. Propósito y problema

GreenOcean es un sistema de monitoreo semanal de precios de alimentos en Chile. Integra dos fuentes oficiales de datos abiertos: los precios mayoristas y al consumidor de ODEPA y el IPC de alimentos del INE.

Las series de ODEPA no son comparables de forma directa: difieren en frecuencia (diaria y semanal), en unidad de venta (caja, bandeja o malla frente a kilo o unidad) y en desagregación (mercado y canal), y ninguna está ajustada por inflación. La consolidación manual es lenta, propensa a errores y no trazable. El sistema la reemplaza por un pipeline semanal automatizado que normaliza unidades, semanas y claves de producto, valida la calidad y publica un panel de consulta de solo lectura con trazabilidad de cada cifra hasta su archivo de origen.

Volumen a la fecha: 814.610 precios semanales en 250 semanas (03-01-2022 a 12-10-2026), 9 regiones, 8 canales, 1.609 claves de producto y 202 meses del IPC. Última carga: 2.521.012 filas leídas, 2.520.811 cargadas y 201 rechazadas con motivo.

## 2. Partes interesadas

Perfiles de diseño (hipótesis, sin entrevistas). El sistema no está dirigido al consumidor final.

| Perfil | Decisión que apoya | Información entregada |
|---|---|---|
| Analista de pricing | Fijación de precios | Precio actual frente a su rango estacional, nominal y real |
| Compras y abastecimiento | Oportunidad de compra | Diferencia consumidor–mayorista por canal |
| Gerencia | Priorización semanal | Variaciones y alertas de la semana |
| Revisor técnico | Confiabilidad del sistema | Calidad, pruebas, linaje y documentación |

[[diagrama:actores]]

Los usuarios acceden en modo de solo lectura. El autor opera el sistema: atiende consultas SQL a pedido, mantiene código y secretos, y ejecuta cargas manuales con clave de control.

## 3. Preguntas de negocio

| ID | Pregunta | Método | Vista |
|---|---|---|---|
| P-1 | ¿Qué precios variaron esta semana y cuáles son atípicos? | Variación sobre las mismas regiones; alertas K6 | Resumen semanal |
| P-2 | ¿El precio actual es normal para la temporada? | Rango P25–P75 de las mismas semanas ISO en años anteriores | Precios e inflación |
| P-3 | ¿Cuál es el margen consumidor sobre mayorista? | Indicador K1 por canal frente a su rango habitual | Precios e inflación |

## 4. Requisitos

| ID | Requisito | Criterio de verificación |
|---|---|---|
| RF-01 | Carga semanal automática de ODEPA e INE | Workflow de GitHub Actions programado los martes |
| RF-02 | Rechazo con motivo, sin pérdida de filas | Filas leídas = cargadas + rechazadas, probado en dbt |
| RF-03 | Publicación solo de cargas válidas | 31 pruebas de dbt; reemplazo atómico de la base |
| RF-04 | Precios reales junto a los nominales | Deflactor del IPC recalculado en la auditoría |
| RF-05 | Trazabilidad de cada cifra | Página Calidad y auditoría |
| RNF-01 | Costo cero, sin vencimientos | Solo servicios gratuitos permanentes |
| RNF-02 | Solo lectura para usuarios | DuckDB en modo lectura; carga manual con clave |
| RNF-03 | Legibilidad en 1440 × 900 | Revisión visual en cada cambio del panel |

## 5. Pantallas

Capturas del panel en producción, en cuatro temas de color.

[[diagrama:mockups]]
