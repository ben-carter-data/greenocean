# GreenOcean · Documento de requisitos del producto (PRD)

Monitor semanal de precios de alimentos en Chile, construido sobre los datos abiertos de ODEPA.

> Este PRD se reconstruyó después de construir el producto. Parte del documento de diseño escrito al inicio (`docs/DISENO.md`) y lo contrasta con lo que se entregó, según el registro de decisiones (`docs/DECISIONES.md`). Donde lo planificado y lo entregado difieren, se muestran las dos cosas.

---

## 1. Resumen

GreenOcean descarga cada semana los dos conjuntos de datos públicos de ODEPA (precios mayoristas de frutas y hortalizas, y precios al consumidor), los limpia con reglas de negocio explícitas, revisa su calidad y los carga en un data warehouse SQLite con modelo estrella. Un panel público en Streamlit responde tres preguntas sobre esos precios. Todo el proceso corre solo, cada martes, en GitHub Actions.

| Cifra de la base actual | Valor |
|---|---|
| Precios semanales cargados | 811.578 |
| Semanas cubiertas | 249, del 03-01-2022 al 05-10-2026 |
| Filas leídas en la última carga | 2.512.298 |
| Filas cargadas · rechazadas | 2.512.097 · 201 |
| Regiones con datos | 9 de 16 |
| Canales | 8 (Mayorista y 7 puntos de venta del consumidor) |
| Claves de producto | 1.609 |

## 2. Problema y usuario

Quien quiere seguir hoy los precios de los alimentos en Chile debe bajar archivos de dos fuentes, convertir unidades distintas (cajas, bandejas y mallas contra kilos) y cruzarlas a mano cada semana. Las fuentes existen, pero no son comparables entre sí sin ese trabajo.

El diseño definió cuatro perfiles. Son **hipótesis de diseño**: el repositorio no registra entrevistas ni usuarios reales que las validen.

| Perfil (hipótesis) | Necesidad prevista | Prioridad en el diseño | Qué quedó |
|---|---|---|---|
| Analista de pricing, compras o abastecimiento | Márgenes, diferencias por canal y región, alertas | 1 | Usuario principal del Dashboard |
| Equipo de datos | Saber si la carga funcionó y qué se descartó | 1 | Páginas Calidad de datos y Ejecuciones |
| Gerencia | Pocos indicadores y tendencias | 2 | Cubierta por el Resumen semanal, que se lee en una pantalla |
| Consumidor | Dónde y cuándo conviene comprar | 3 | No se construyó una vista propia (mejora T-34 del backlog) |

El selector de perfil obligatorio del diseño (D-005) dejó de abrir el panel: desde D-078 la entrada directa abre el Dashboard. No hay inicio de sesión ni datos personales.

## 3. Visión y objetivos

**Visión.** Una base trazable y un seguimiento sostenido que permitan entender las diferencias de precio y señalar qué situaciones merecen revisión humana (`docs/PROYECTO.md`, Marco de negocio).

**Objetivos.**

1. Reemplazar la consolidación manual de dos fuentes por un pipeline semanal automático.
2. Hacer comparables las dos fuentes: misma clave de producto, misma unidad, misma semana y región.
3. Entregar evidencia descriptiva, nunca predicciones ni causalidad.
4. Que cada cifra del panel pueda rastrearse hasta su regla, su consulta y su prueba.

No se fijaron metas numéricas de negocio ni fechas objetivo; el registro lo dice expresamente (D-080).

## 4. Preguntas de negocio

El diseño planteó seis preguntas. Tras la revisión de pertinencia del 18-10-2026 (D-146), el panel se ordena en torno a tres preguntas centrales:

1. **¿Qué se movió esta semana y es inusual?** Variación semanal sobre las mismas regiones en ambas semanas; familia representada por su mediana; alertas K6.
2. **¿Es normal el precio de hoy para la temporada?** Rango habitual P25–P75 de las mismas semanas ISO (±1) en años anteriores, sobre las regiones con precio esta semana.
3. **¿Cuánto paga el consumidor sobre el precio mayorista?** K1, con su propio rango habitual.

| # | Pregunta del diseño | Estado final | Dónde o por qué | Referencia |
|---|---|---|---|---|
| P1 | Margen entre precio mayorista y al consumidor, y su evolución | Entregada | Contexto de precios, tarjeta «Sobre el precio mayorista», por canal y frente a su rango habitual | D-146 |
| P2 | Diferencia de precio entre canales | Cubierta por Contexto de precios | Brecha Feria libre frente a Supermercado, con su rango habitual | D-094, D-098, D-146 |
| P3 | Regiones con precios más altos | Parcial | El mapa del Resumen muestra hacia dónde se movieron los precios de cada región (coloreada solo si pasa una prueba de signos, p < 0,05), no qué región es más cara; el índice regional K3 se calcula pero el panel no lo muestra | D-092, D-146 |
| P4 | Semanas en que sube y baja cada producto | Entregada | Contexto de precios: rango habitual y «qué suele pasar», mostrado solo si al menos tres años coinciden | D-094, D-146 |
| P5 | Semanas con que el consumidor sigue al mayorista | Retirada | En el 57 % de las 1.215 series no hay relación clara y el 18 % da «la misma semana», que datos semanales no pueden separar | D-146 |
| P6 | Productos que se movieron fuera de su rango normal | Entregada | Alertas K6 en el Resumen y en «Alerta de precio» | D-145, D-146 |

## 5. Alcance

**Incluye**

- Las dos fuentes de ODEPA, años 2022 a 2026 (D-009, D-047).
- Frutas y verduras presentes en ambas fuentes, con margen (K1).
- Carnes, lácteos, huevos, abarrotes y pan, solo de la fuente consumidor, sin margen.
- Ingesta, capa bronce, limpieza, normalización de unidades, controles de calidad, modelo estrella, indicadores, panel y automatización semanal.
- Informe semanal publicado como issue de GitHub y aviso por correo si el job falla (D-017).

**No incluye**

| Fuera de alcance | Motivo | Referencia |
|---|---|---|
| Scraping de sitios web | Los datos ya existen como archivo oficial | D-001 |
| Pescados y mariscos | No están en las fuentes | DISENO.md §4 |
| Predicción y modelos estadísticos | No responden mejor ninguna pregunta | D-011, D-019 |
| Ajuste por inflación | Los indicadores comparan precios de la misma semana | D-010; mejora T-32 |
| Comercio exterior | Etapa 2 | D-002; mejora T-35 |
| Recomendar compras de forma automática | El proyecto entrega evidencia para decisión humana | PROYECTO.md |

## 6. Requisitos funcionales

| ID | Requisito | Lo satisface |
|---|---|---|
| RF-01 | Descargar cada semana los CSV de ambas fuentes, validar tamaño, encabezado y filas, y registrar cada resultado | Agente de ingesta; motivo `UNEXPECTED_HEADER`; T-03 a T-05 |
| RF-02 | No volver a descargar un año cerrado ya disponible; descargar siempre el año en curso | D-047, caché de GitHub Actions |
| RF-03 | Conservar los archivos tal como llegan en una capa bronce | `raw.db`, D-020 |
| RF-04 | Convertir textos a número y normalizar espacios | RN-01, RN-13 |
| RF-05 | Construir una clave común producto + variedad + calidad | RN-02, D-007 |
| RF-06 | Llevar los precios a kilo, unidad o litro cuando la unidad declara una cantidad; conservar sin precio comparable las que no | RN-03 a RN-05, D-026 |
| RF-07 | Agregar a precio semanal por lunes de inicio, ponderado por volumen en el mayorista | RN-07 a RN-09, D-006, D-027 |
| RF-08 | Rechazar con motivo las filas inválidas, sin borrarlas en silencio | RN-11, tabla `rejection` |
| RF-09 | Marcar y excluir de los indicadores los precios atípicos, conservándolos | RN-12, D-028 |
| RF-10 | Detener la carga si los controles de calidad fallan y conservar la última base válida | D-029, D-034, D-042, D-046 |
| RF-11 | Cargar de forma idempotente | RN-14, D-024 |
| RF-12 | Mostrar qué se movió esta semana, por familia (mediana) y por región, comparando solo regiones presentes en ambas semanas | Resumen semanal; D-144, D-146; `tests/test_data_audit.py` |
| RF-13 | Señalar alertas de precio inusuales y materiales | K6; Resumen y «Alerta de precio»; D-145, D-146 |
| RF-14 | Mostrar si el precio de esta semana está bajo, dentro o sobre su rango habitual de temporada | Contexto de precios; D-094, D-098, D-146 |
| RF-15 | Mostrar el margen del consumidor sobre el mayorista por canal, con su rango habitual | K1; Contexto de precios; D-146 |
| RF-16 | Mostrar el estado de cada carga, sus rechazos y la cobertura del cruce | Calidad de datos; K7, K8 |
| RF-17 | Mostrar el historial de ejecuciones y permitir una ejecución manual protegida | Ejecuciones; D-038, D-149 |
| RF-18 | Publicar un informe semanal con estado de la carga y alertas | Issue «Informe semanal AAAA-MM-DD»; D-017, D-034 |
| RF-19 | Explicar la arquitectura, el modelo de datos y la operación dentro del panel | Arquitectura: Pipeline, Modelo de datos, DevOps y seguridad |
| RF-20 | Enlazar las fuentes oficiales y el código | Fuentes (dos enlaces de ODEPA); página GitHub; D-143, D-148 |

## 7. Requisitos no funcionales

| ID | Requisito | Cómo se cumple | Referencia |
|---|---|---|---|
| RNF-01 | Frescura semanal | El workflow corre cada martes a las 12:00 UTC (09:00 en Chile en horario de verano); el panel lee la base nueva uno o dos minutos después del commit | `semanal.yml`, MANUAL.md |
| RNF-02 | Solo lectura | El panel abre `datos.db` en modo de solo lectura; ninguna página puede escribir | PROYECTO.md, Seguridad |
| RNF-03 | Reproducibilidad | Toda cifra se reconstruye desde los CSV de ODEPA; la auditoría recalcula precios desde las filas crudas en cada ejecución de las pruebas | D-018, D-144 |
| RNF-04 | Coste cero | SQLite, GitHub Actions en repositorio público y Streamlit Community Cloud, sin servicios de pago | D-012 |
| RNF-05 | Trazabilidad | Leídas = cargadas + rechazadas en cada carga; cada rechazo guarda su motivo y la fila original | RN-11, D-144 |
| RNF-06 | Integridad ante fallas | Si un paso falla, los siguientes no corren y la base del repositorio no cambia | D-034 |
| RNF-07 | Lectura en una pantalla | Cada vista del Dashboard se lee completa sin desplazarse en 1440 × 900 y 1920 × 1080; en pantallas menores la grilla se apila | D-067, D-092, D-094 |
| RNF-08 | Accesibilidad de lectura | Paleta de canales comprobada para daltonismo; números y fechas en formato chileno; ayudas ⓘ en cada tarjeta | D-037, D-040 |
| RNF-09 | Sin tecnologías de apariencia | No se agregan nube, contenedores ni modelos predictivos que no respondan mejor una pregunta | D-019 |

## 8. Indicadores

| ID | Indicador | Fórmula en palabras | Estado | Página |
|---|---|---|---|---|
| K1 | Margen mayorista-consumidor | (precio consumidor − precio mayorista) / precio mayorista, misma semana, región, clave y unidad | Vigente | Contexto de precios |
| K2 | Diferencial entre canales | precio de un canal / precio de otro − 1, mismo producto, semana y región | Vigente como brecha Supermercado / Feria libre | Contexto de precios |
| K3 | Índice regional | precio de la región / promedio simple de las regiones con dato esa semana | Calculado; el panel no lo muestra (el mapa del Resumen muestra la dirección del cambio por región, no este índice) | — |
| K4 | Índice estacional | precio de la semana / promedio de su año (100 = promedio) | Vigente; el patrón de meses siguientes se muestra solo si al menos tres años coinciden | Contexto de precios |
| K5 | Rezago | desfase de 0 a 8 semanas con mayor correlación entre cambios semanales | Retirado del producto (D-146) | — |
| K6 | Alerta de variación | variación semanal, sobre las mismas regiones, a más de 2 desviaciones estándar de sus 12 variaciones anteriores **y** con cambio de al menos 10 % | Vigente | Resumen y «Alerta de precio» |
| K7 | Cobertura del cruce | claves de frutas y verduras del consumidor con margen / claves de frutas y verduras del consumidor | Vigente: 219 de 257 en la base actual | Calidad de datos |
| K8 | Filas rechazadas | filas rechazadas / filas leídas, por motivo | Vigente: 201 de 2.512.298, todas `NON_POSITIVE_PRICE` del mayorista | Calidad de datos |

## 9. Reglas de negocio

| ID | Regla | Precisión posterior |
|---|---|---|
| RN-01 | Texto con coma decimal a número | Ilegible → rechazo `UNREADABLE_VALUE` (D-025) |
| RN-02 | Separar el producto del consumidor en producto, variedad y calidad | Sin separador: «Sin especificar» |
| RN-03 | Unidad mayorista a kilo cuando declara kilos | Se aplica a ambas fuentes; gramos a kilo (D-026) |
| RN-04 | Unidad mayorista a unidad cuando declara unidades | Igual que RN-03 (D-026) |
| RN-05 | Unidades con rango o sin cantidad no se convierten; motivo `UNIDAD_NO_CONVERTIBLE` | Se agrega ml y litros a litro (D-026) |
| RN-06 | Margen solo con la misma unidad normalizada | — |
| RN-07 | Precio mayorista semanal ponderado por volumen | Volumen tal como se publica (D-027) |
| RN-08 | Semana = lunes de inicio | — |
| RN-09 | Precio al consumidor semanal = promedio por región, canal y clave | — |
| RN-10 | «Mercado Mayorista» del consumidor es un canal más | — |
| RN-11 | Fila inválida → rechazo con motivo, nunca borrado silencioso | Semana del archivo si toca su año; motivo `NON_POSITIVE_VOLUME` (D-025) |
| RN-12 | Atípico (más de 5 veces o menos de 1/5 de la mediana) → marca `ATIPICO`, fuera de indicadores | Mediana por producto, unidad, semana y fuente (D-028) |
| RN-13 | Normalizar espacios sin cambiar mayúsculas | — |
| RN-14 | Carga idempotente | Reconstrucción completa en una transacción (D-024) |

## 10. Criterios de aceptación

Los nueve criterios de `DISENO.md` §11, con su estado según el repositorio.

| # | Criterio | Estado | Evidencia o motivo |
|---|---|---|---|
| 1 | El job semanal corre solo cuatro semanas seguidas | Pendiente | T-26: revisiones previstas 13-10, 20-10, 27-10 y 03-11-2026 (`docs/hito-4.md`) |
| 2 | Dos ejecuciones de la misma semana dejan las mismas filas | Cumplido | RN-14, D-024; las dos últimas cargas registran las mismas cifras |
| 3 | Leídas = cargadas + rechazadas | Cumplido | 2.512.298 = 2.512.097 + 201; prueba en `tests/test_data_audit.py` |
| 4 | K7 medido y publicado | Cumplido | Calidad de datos |
| 5 | Los cinco productos de prueba muestran margen y un valor se reproduce a mano | Cumplido en parte | Cuatro de cinco: la papa no tiene margen por la clave exacta (D-030) |
| 6 | Cada regla RN tiene al menos una prueba automática y las pruebas corren en cada cambio | Cumplido | Cada regla RN-01 a RN-14 da nombre a una prueba como mínimo; `pruebas.yml` las corre en cada push y pull request |
| 7 | El panel carga en un enlace público con los perfiles de prioridad 1 | Cumplido | Streamlit Community Cloud (T-24) |
| 8 | Cada ejecución publica un informe y una falla genera aviso | Cumplido | Issue semanal (T-25c) y correo de GitHub (T-25d) |
| 9 | El README presenta al menos un hallazgo verificado | Pendiente | El README dice «Pendiente» en Hallazgos |

## 11. Limitaciones conocidas

| Limitación | Efecto |
|---|---|
| ODEPA publica 9 de las 16 regiones | El mapa y los promedios nacionales cubren solo esas 9 |
| La semana del 02-05-2022 no existe en la fuente consumidor | Esa semana no tiene precio al consumidor ni margen (D-042) |
| Algunas series tienen una sola cotización por semana | Su cambio va al final del orden con la marca «1 cotización» (D-146) |
| El margen solo existe para frutas y verduras con la misma clave y unidad | Las demás familias no tienen K1; la papa no tiene margen (D-007, D-030) |
| Unidades sin cantidad declarada (atados, matas, rangos) no se convierten | 12.472 precios semanales quedan sin precio comparable (D-008, D-026) |
| Precios nominales | Las comparaciones entre años no descuentan inflación (D-010) |
| ODEPA es la única fuente oficial de estos precios | No hay contraste con una segunda fuente (D-146) |

## 12. Riesgos

| Riesgo | Efecto | Mitigación |
|---|---|---|
| ODEPA cambia columnas o URL | El job falla | Validación de encabezado; falla visible, sin carga parcial (D-034) |
| Archivo truncado o semana faltante | Datos incompletos | Controles de filas, semanas, regiones, canales y duplicados antes de cargar (D-029, D-046) |
| Lectura causal de los indicadores | Conclusiones incorrectas | Indicadores descriptivos; K5 retirado (D-011, D-146) |
| Cambio de composición regional entre semanas | Variaciones que no ocurrieron | Comparación sobre las mismas regiones (D-144, D-145) |
| Crecimiento de `datos.db` y del historial de Git | Límites de tamaño de GitHub | Sin índice único y compactación tras cada carga (D-046) |
| Vencimiento del token de la ejecución manual | El botón deja de funcionar | Aviso de vencimiento en la administración (D-053) |
| Caché de Actions vencida | Descarga completa algunas semanas | Comportamiento previsto, sin falla (D-047) |
