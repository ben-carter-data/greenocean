# GreenOcean · Documento de requisitos del producto (PRD)

Monitor semanal de precios de alimentos en Chile, construido sobre los datos abiertos de ODEPA y el IPC del INE.

| Ficha del documento | |
|---|---|
| Producto | GreenOcean, panel de inteligencia de precios de alimentos |
| Versión | Arquitectura entregada al 19-10-2026 (decisiones hasta D-158) |
| Autoría | El autor, con el registro completo de decisiones en `docs/DECISIONES.md` |
| Documentos hermanos | SAD (cómo está construido) y ADR (por qué se decidió así) |
| Carácter | Reconstruido después de construir el producto: compara lo diseñado al inicio (`docs/DISENO.md`) con lo entregado |

---

## 1. Resumen ejecutivo

GreenOcean reemplaza una tarea manual y repetitiva —bajar dos archivos públicos, convertir unidades distintas y cruzarlos a mano cada semana— por un pipeline que corre solo cada martes. Descarga los precios mayoristas y al consumidor de ODEPA, los guarda tal como llegan en una capa bronce en Parquet, los transforma y prueba con dbt Core sobre DuckDB, y publica el resultado en un panel Streamlit de solo lectura. Desde octubre de 2026 el panel también muestra precios reales, descontada la inflación de alimentos con el IPC oficial del INE.

El producto responde tres preguntas a profesionales que deciden con estos precios: qué se movió esta semana, si el precio de hoy es normal para la temporada y cuánto paga el consumidor sobre el precio mayorista.

| Cifra del data warehouse publicado | Valor |
|---|---|
| Precios semanales | 811.578 |
| Semanas cubiertas | 249, del 03-01-2022 al 05-10-2026 |
| Filas leídas en la última carga | 2.512.298 |
| Filas cargadas · rechazadas | 2.512.097 · 201 |
| Regiones con datos | 9 de 16 |
| Canales | 8 (Mayorista y 7 puntos de venta al consumidor) |
| Claves de producto | 1.609 |
| Meses del IPC de alimentos | 202, de diciembre 2009 a septiembre 2026 |
| Pruebas de datos en dbt | 31, todas en verde en la última construcción |
| Tamaño de la base que lee el panel | unos 13 MB en DuckDB (34 MB en el antiguo SQLite) |

## 2. Problema

Las fuentes existen, pero no son comparables entre sí sin trabajo:

| | Precios mayoristas (ODEPA) | Precios al consumidor (ODEPA) | IPC de alimentos (INE) |
|---|---|---|---|
| Frecuencia | Diaria | Semanal | Mensual |
| Unidad | Caja, bandeja o malla | Kilo, unidad o envase | Índice, base 2023 = 100 |
| Desagregación | Mercado y región | Canal y región | Nacional, división de alimentos |
| Qué exige para cruzarla | Agregar a semana, ponderando por volumen, y llevar la unidad de venta a kilo o unidad | Separar producto, variedad y calidad, y llevar la unidad a kilo, unidad o litro | Asignar a cada semana el mes de su lunes |

Cruzarlas exige una clave de producto común, una unidad común y una semana común. Y comparar un precio de hoy con el de hace tres años sin descontar la inflación lleva a conclusiones equivocadas.

GreenOcean resuelve las tres cosas de forma reproducible: cada cifra del panel se puede reconstruir desde el archivo oficial, con la regla que la produjo y la prueba que la vigila.

## 3. Usuarios y decisiones

El panel sirve a profesionales que toman decisiones con estos precios, no al consumidor final. Los perfiles son **hipótesis de diseño**: el repositorio no registra entrevistas con usuarios reales.

| Usuario | Su decisión | Qué le responde el panel |
|---|---|---|
| Analista de pricing | Ajustar sus precios de venta | ¿El precio de esta semana es normal para la época, en pesos de hoy? |
| Comprador o abastecimiento | Cuándo comprar y qué negociar | ¿Cuánto paga el consumidor sobre el mayorista, y es lo habitual? |
| Gerencia | Dónde mirar esta semana | ¿Qué se movió y qué es inusual? |
| Equipo de datos | Si la carga es confiable | Estado de cada ejecución, rechazos, cobertura del cruce y pruebas |

Toda funcionalidad nueva debe responder a una decisión de uno de estos usuarios; si no responde a ninguna, no se construye. No hay inicio de sesión ni datos personales.

Quién usa el sistema, para qué, y de qué sistemas externos depende:

[[diagrama:actores]]

El visitante solo lee. El autor opera: mantiene el código y los secretos y puede lanzar una ejecución manual protegida por clave. ODEPA y el INE entregan los datos; GitHub Actions ejecuta el workflow, el repositorio guarda el código y la base publicada, y Streamlit Community Cloud publica el panel.

## 4. Visión y objetivos

**Visión.** Una base trazable y un seguimiento sostenido que permitan entender las diferencias de precio y señalar qué situaciones merecen una revisión humana.

| # | Objetivo | Cómo se reconoce que se cumple |
|---|---|---|
| O-1 | Reemplazar la consolidación manual por un pipeline semanal automático | El workflow de GitHub Actions corre cada martes sin intervención |
| O-2 | Hacer comparables las dos fuentes | Misma clave, misma unidad, misma semana y misma región |
| O-3 | Comparar precios en el tiempo sin el sesgo de la inflación | Selector Nominal / Real en Contexto de precios |
| O-4 | Entregar evidencia descriptiva, nunca predicciones ni causalidad | Ningún indicador proyecta ni atribuye causas |
| O-5 | Que cada cifra se pueda rastrear | Regla, modelo de dbt y prueba identificados para cada número |

No se fijaron metas numéricas de negocio ni fechas comerciales (D-080).

## 5. Preguntas de negocio

Tras la revisión de pertinencia del 18-10-2026 (D-146), el panel se ordena en torno a tres preguntas centrales:

| Pregunta central | Cómo se responde | Dónde |
|---|---|---|
| ¿Qué se movió esta semana y es inusual? | Variación semanal sobre las mismas regiones en ambas semanas, familia representada por su mediana y alertas K6 | Resumen semanal |
| ¿Es normal el precio de hoy para la temporada? | Rango habitual P25–P75 de las mismas semanas ISO (±1) en años anteriores, en precios nominales o reales | Contexto de precios |
| ¿Cuánto paga el consumidor sobre el precio mayorista? | Margen K1 por canal, frente a su propio rango habitual | Contexto de precios |

Las preguntas del diseño original quedaron así:

| # | Pregunta del diseño | Estado | Dónde, o por qué no | Referencia |
|---|---|---|---|---|
| P1 | Margen entre mayorista y consumidor | Entregada | Contexto de precios, «Sobre el precio mayorista» | D-146 |
| P2 | Diferencia de precio entre canales | Entregada | Brecha Feria libre frente a Supermercado, con su rango habitual | D-094, D-098 |
| P3 | Regiones con precios más altos | Parcial | El mapa muestra hacia dónde se movió cada región (solo si pasa una prueba de signos); el índice K3 se calcula pero no se muestra | D-092, D-146 |
| P4 | Semanas en que sube y baja cada producto | Entregada | Rango habitual y «qué suele pasar», solo si al menos tres años coinciden | D-094, D-146 |
| P5 | Rezago del consumidor frente al mayorista | Retirada | En el 57 % de las 1.215 series no había relación clara | D-146 |
| P6 | Productos fuera de su rango normal | Entregada | Alertas K6 en el Resumen y en Alertas | D-145, D-146 |

## 6. Alcance

**Incluye**

| Ámbito | Detalle |
|---|---|
| Fuentes | Precios mayoristas y al consumidor de ODEPA, 2022 a 2026; IPC de alimentos del INE |
| Productos | Frutas y verduras de ambas fuentes, con margen; carnes, lácteos, huevos, abarrotes y pan solo del consumidor |
| Datos | Ingesta, capa bronce en Parquet, transformaciones y pruebas en dbt, data warehouse en DuckDB |
| Producto | Panel de lectura con precios nominales y reales, calidad de datos, ejecuciones y documentación |
| Operación | Workflow semanal, informe semanal como issue de GitHub y aviso por correo si algo falla |

**No incluye**

| Fuera de alcance | Motivo | Referencia |
|---|---|---|
| Scraping de sitios web | Los datos ya existen como archivo oficial | ADR-01 |
| Comparación por cadena de supermercados | No existe una fuente abierta oficial por cadena | ADR-32 |
| Vista para el consumidor («dónde comprar») | No responde a los usuarios de la sección 3 | ADR-32 |
| Predicción de precios | El producto describe, no pronostica | D-011, D-019 |
| Warehouse en la nube | Sin beneficio con datos públicos, semanales y pequeños | ADR-31 |
| Pescados y mariscos | No están en las fuentes | DISENO.md §4 |
| Comercio exterior | Queda para una etapa posterior | D-002 |

## 7. Requisitos funcionales

| ID | Requisito | Lo satisface |
|---|---|---|
| RF-01 | Descargar cada semana los archivos de ambas fuentes de ODEPA, validar su encabezado y registrar cada resultado | Agente de ingesta |
| RF-02 | No volver a descargar un año cerrado ya disponible | Caché de GitHub Actions (D-047) |
| RF-03 | Conservar las filas tal como llegan en una capa bronce, en un formato estándar | Parquet por fuente y año (D-154) |
| RF-04 | Convertir textos a número y normalizar espacios | Staging de dbt (RN-01, RN-13) |
| RF-05 | Construir una clave común producto + variedad + calidad | Staging de dbt (RN-02) |
| RF-06 | Llevar los precios a kilo, unidad o litro cuando la unidad declara una cantidad | Intermedio de dbt (RN-03 a RN-05) |
| RF-07 | Agregar a precio semanal por lunes, ponderado por volumen en el mayorista | Intermedio de dbt (RN-07 a RN-10) |
| RF-08 | Rechazar con motivo las filas inválidas, sin borrarlas en silencio | Tabla `rejection` (RN-11) |
| RF-09 | Marcar y excluir de los indicadores los precios atípicos, conservándolos | Intermedio de dbt (RN-12) |
| RF-10 | No publicar una carga que no pasó sus pruebas | dbt build y reemplazo atómico de la base (D-154) |
| RF-11 | Cargar de forma idempotente | Reconstrucción completa (RN-14) |
| RF-12 | Mostrar qué se movió esta semana, por familia y por región | Resumen semanal (D-144, D-146) |
| RF-13 | Señalar alertas de precio inusuales y materiales | K6 (D-145, D-146) |
| RF-14 | Mostrar si el precio de esta semana está bajo, dentro o sobre su rango habitual | Contexto de precios (D-094, D-098) |
| RF-15 | Mostrar el margen del consumidor sobre el mayorista por canal | K1 en Contexto de precios |
| RF-16 | Mostrar precios reales en pesos del último mes publicado por el INE, junto a los nominales | Selector Nominal / Real (D-155) |
| RF-17 | Mostrar el estado de cada carga, sus rechazos y la cobertura del cruce | Calidad de datos y Monitoreo (K7, K8) |
| RF-18 | Mostrar el historial de ejecuciones y permitir una ejecución manual protegida | Ejecuciones (D-149) |
| RF-19 | Publicar un informe semanal con estado de la carga y alertas | Issue «Informe semanal» (D-017) |
| RF-20 | Explicar el producto, la arquitectura y las decisiones dentro del panel, descargables en PDF | PRD, SAD y ADR en Documentación (D-151) |

**Las pantallas reales.** Cuatro capturas del panel publicado, con los datos de la carga del 19-10-2026, cada una en un tema de color distinto: el Resumen semanal (RF-12 a RF-14 y RF-17), Precios e inflación con el IPC (RF-16), la página Consultas SQL y el mismo Resumen en un teléfono en horizontal (RNF-07). No son bocetos: son la aplicación tal como la ve un visitante.

[[diagrama:mockups]]

## 8. Requisitos no funcionales

| ID | Requisito | Cómo se cumple |
|---|---|---|
| RNF-01 | Frescura semanal | El workflow corre cada martes a las 12:00 UTC; el panel lee la base nueva tras el commit |
| RNF-02 | Solo lectura | El panel abre DuckDB en modo de solo lectura, desde un único punto de acceso |
| RNF-03 | Reproducibilidad | Toda cifra se reconstruye desde los archivos oficiales; la auditoría recalcula precios y deflactores sin dbt |
| RNF-04 | Costo cero y sin vencimientos | Parquet, dbt Core, DuckDB, GitHub Actions en repositorio público y Streamlit Community Cloud |
| RNF-05 | Trazabilidad | Leídas = cargadas + rechazadas en cada carga, verificado por una prueba de dbt |
| RNF-06 | Integridad ante fallas | Si un modelo o una prueba falla, la base publicada no cambia y la falla queda registrada |
| RNF-07 | Lectura en una pantalla | Cada vista del Dashboard se lee completa en 1440 × 900 |
| RNF-08 | Accesibilidad de lectura | Paleta apta para daltonismo; números y fechas en formato chileno |
| RNF-09 | Sin tecnología de apariencia | Nada de nube, contenedores ni modelos predictivos que no respondan mejor una pregunta |
| RNF-10 | Portabilidad | El motor se elige en la configuración de dbt; los modelos usan SQL estándar (ADR-30) |

## 9. Indicadores

| ID | Indicador | Definición en palabras | Estado |
|---|---|---|---|
| K1 | Margen mayorista-consumidor | Precio consumidor sobre precio mayorista, misma semana, región, clave y unidad | Vigente |
| K2 | Diferencial entre canales | Precio de un canal sobre el de otro, mismo producto, semana y región | Vigente como brecha Supermercado / Feria libre |
| K3 | Índice regional | Precio de la región sobre el promedio de las regiones con dato | Calculado, no mostrado |
| K4 | Índice estacional | Precio de la semana sobre el promedio de su año | Vigente, con acuerdo de al menos tres años |
| K5 | Rezago | Desfase con mayor correlación entre cambios semanales | Retirado (D-146) |
| K6 | Alerta de variación | Variación sobre las mismas regiones, a más de dos desviaciones estándar de sus 12 anteriores, de al menos 10 % y con al menos 2 cotizaciones en cada semana (D-158) | Vigente |
| K7 | Cobertura del cruce | Claves de frutas y verduras del consumidor con margen sobre el total de esas claves | 219 de 257 |
| K8 | Filas rechazadas | Filas rechazadas sobre filas leídas, por motivo | 201 de 2.512.298, todas por precio no positivo |

**Precio real.** No es un indicador nuevo, sino otra unidad de medida: el precio nominal multiplicado por el cociente entre el IPC de alimentos del último mes publicado y el del mes de la semana. El rango habitual y el estado de la semana se recalculan sobre esa serie.

## 10. Reglas de negocio

| ID | Regla | Dónde vive |
|---|---|---|
| RN-01 | Texto con coma decimal a número; lo ilegible se rechaza | Staging |
| RN-02 | Separar el producto del consumidor en producto, variedad y calidad | Staging |
| RN-03 | Unidad que declara kilos o gramos, a kilo | Intermedio, normalización de unidades |
| RN-04 | Unidad que declara unidades, a unidad | Intermedio, normalización de unidades |
| RN-05 | Unidad sin cantidad o con rango: sin conversión, marcada | Intermedio, normalización de unidades |
| RN-06 | Margen solo con la misma unidad normalizada | Consultas del panel |
| RN-07 | Precio mayorista semanal ponderado por volumen | Intermedio, agregación semanal |
| RN-08 | La semana es el lunes de inicio | Intermedio, agregación semanal |
| RN-09 | Precio al consumidor semanal: promedio por región, canal y clave | Intermedio, agregación semanal |
| RN-10 | «Mercado Mayorista» del consumidor es un canal más | Intermedio, agregación semanal |
| RN-11 | Fila inválida: rechazo con motivo, nunca borrado silencioso | Intermedio, validación |
| RN-12 | Precio cinco veces sobre o bajo la mediana de su fuente: marcado atípico | Intermedio, atípicos |
| RN-13 | Normalizar espacios sin cambiar mayúsculas | Staging |
| RN-14 | Carga idempotente | Reconstrucción completa y prueba de unicidad |

**Regla del deflactor (D-155).** Cada semana toma el IPC del mes de su lunes. Los precios reales quedan en pesos del último mes publicado por el INE. Una semana cuyo mes aún no se publica usa ese último mes y se marca como provisional: nunca se inventa un índice.

## 11. Criterios de aceptación

| # | Criterio | Estado | Evidencia o motivo |
|---|---|---|---|
| 1 | El workflow semanal corre solo cuatro semanas seguidas | Pendiente | Revisiones previstas hasta el 03-11-2026 (T-26) |
| 2 | Dos ejecuciones de la misma semana dejan las mismas filas | Cumplido | Las dos últimas cargas registran las mismas cifras |
| 3 | Leídas = cargadas + rechazadas | Cumplido | 2.512.298 = 2.512.097 + 201, verificado por dbt y por la auditoría |
| 4 | K7 medido y publicado | Cumplido | Calidad de datos |
| 5 | Los cinco productos de prueba muestran margen | Cumplido en parte | Cuatro de cinco: la papa no tiene margen por la clave exacta (D-030) |
| 6 | Cada regla RN tiene al menos una prueba y corren en cada cambio | Cumplido | Pruebas de Python y de dbt en el workflow de pruebas |
| 7 | El panel carga en un enlace público | Cumplido | Streamlit Community Cloud |
| 8 | Cada ejecución publica un informe y una falla genera aviso | Cumplido | Issue semanal y correo de GitHub |
| 9 | La migración a DuckDB no cambia ninguna cifra | Cumplido | Paridad fila a fila: 811.578 precios, diferencia máxima 4,9 × 10⁻¹⁶ (D-154) |
| 10 | El deflactor se puede recalcular sin dbt | Cumplido | Auditoría del IPC con diferencia relativa menor a 10⁻¹² (D-155) |

## 12. Limitaciones conocidas

| Limitación | Efecto |
|---|---|
| ODEPA publica 9 de las 16 regiones | Los promedios nacionales y el mapa cubren solo esas 9 |
| La semana del 02-05-2022 no existe en la fuente consumidor | Esa semana no tiene precio al consumidor ni margen (D-042) |
| El margen exige la misma clave y unidad | Solo frutas y verduras tienen K1; la papa no |
| Unidades sin cantidad declarada no se convierten | 12.472 precios semanales quedan sin precio comparable |
| El IPC es nacional y de toda la división de alimentos | El precio real descuenta la inflación general de alimentos, no la de cada producto o región |
| El INE publica con un mes de rezago | La semana más reciente suele quedar marcada como provisional |
| ODEPA es la única fuente oficial de estos precios | No hay contraste con una segunda fuente |

## 13. Riesgos

| Riesgo | Efecto | Mitigación |
|---|---|---|
| ODEPA cambia columnas o direcciones | La carga falla | Validación de encabezado; la base publicada no cambia |
| Archivo truncado o semana faltante | Datos incompletos | Control del 90 % de filas y pruebas de dbt de semanas y claves |
| El INE no responde o cambia sus archivos | Sin IPC nuevo | Se usa el bronce previo o las filas del INE guardadas en la base publicada |
| Lectura causal de los indicadores | Conclusiones erróneas | Indicadores descriptivos; K5 retirado |
| Cambio de regiones entre semanas | Variaciones que no ocurrieron | Comparación sobre las mismas regiones (D-144) |
| Vencimiento del token de la ejecución manual | El botón deja de funcionar | Aviso en la administración (D-053) |

## 14. Evolución y escalabilidad

| Extensión | Para qué usuario | Estado | Decisión |
|---|---|---|---|
| Parquet, dbt Core y DuckDB | Equipo de datos | Entregada | ADR-30 |
| IPC del INE y precios reales | Pricing, compras | Entregada | ADR-33 |
| Clima por región y semana, junto a las alertas, sin afirmar causalidad | Pricing, gerencia | Prevista | D-152 |
| Warehouse en la nube | Solo si una empresa suma sus propios datos | No adoptada | ADR-31 |
| Retiro del respaldo SQLite | Equipo de datos | Pendiente de la decisión del autor | D-154 |
