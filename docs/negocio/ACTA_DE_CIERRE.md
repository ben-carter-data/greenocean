# Acta de cierre del proyecto

| Campo | Valor |
|---|---|
| Proyecto | GreenOcean |
| Tipo de documento | Acta de cierre del proyecto |
| Versión | 1.2 |
| Fecha | 08-11-2026 |
| Estado | Vigente |
| Responsable | El autor |
| Propósito | Dejar escrito cómo empezó el proyecto, qué se quiso demostrar, qué se encontró en los datos, qué se aprendió y a quién sirve, ahora que queda en mantenimiento. |
| Audiencia | Reclutadores y revisores técnicos, profesionales de datos y de negocio, y el autor. |
| Documentos relacionados | [Documento de requisitos del producto (PRD)](PRD.md) · [Documento de arquitectura de software (SAD)](../arquitectura/SAD.md) · [Plan de calidad del software (SQAP)](../calidad/PLAN_DE_CALIDAD.md) · [Glosario](GLOSARIO.md) |

## Índice

1. [En resumen](#1-en-resumen)
2. [Cómo empezó](#2-cómo-empezó)
3. [Lo que se esperaba y lo que se encontró](#3-lo-que-se-esperaba-y-lo-que-se-encontró)
4. [Cómo se trabajó](#4-cómo-se-trabajó)
5. [Los roles](#5-los-roles)
6. [Lo que se aprendió](#6-lo-que-se-aprendió)
7. [Sorpresas en los datos](#7-sorpresas-en-los-datos)
8. [Puntos fuertes y menos fuertes](#8-puntos-fuertes-y-menos-fuertes)
9. [A quién sirve](#9-a-quién-sirve)
10. [Qué queda](#10-qué-queda)
11. [Glosario](#11-glosario)
12. [Historial de versiones](#12-historial-de-versiones)

## 1. En resumen

GreenOcean cierra como proyecto de portafolio el 04-11-2026, tres semanas y media después de su primer commit. Queda andando solo: cada martes descarga los precios de ODEPA y el IPC de alimentos del INE, los revisa y publica un panel en dos idiomas. Esta acta cuenta cómo empezó, qué se quiso demostrar, qué se encontró en los datos y qué se aprendió.

- **Qué quedó:** un pipeline semanal con 69 reglas de transformación explicadas, 20 controles, 1.505 pruebas automáticas que recalculan las cifras, 14 indicadores de calidad, 9 documentos en español e inglés y 519 decisiones registradas.
- **Qué se demostró:** que una fuente pública «sencilla» esconde trabajo de ingeniería de datos, y que ese trabajo se puede dejar a la vista: cada cifra del panel se sigue hasta la fila de ODEPA que la originó.
- **Estado:** cerrado y en mantenimiento. No hay funciones pendientes; quedan deudas técnicas conocidas, listadas en la sección 10.

## 2. Cómo empezó

El proyecto nació el 11-10-2026 como un ejercicio de portafolio con un objetivo concreto: construir de punta a punta un pipeline de datos sobre una fuente pública chilena y mostrar cómo se trabaja, no solo qué se sabe. En los dos primeros días se cerraron cuatro hitos: la descarga de los archivos y su carga cruda, el ETL con sus reglas, un panel mínimo con indicadores y la carga automática de cada martes.

- **Visión:** que cualquier persona en Chile sepa, con datos oficiales, cómo se mueven los precios de los alimentos.
- **Misión:** publicar cada semana precios revisados y fáciles de leer, y mejorar el proceso con cada carga.
- **Qué se quiso mostrar:** las cuatro competencias que el autor quería consolidar: ingeniería de datos, análisis de sistemas de negocio (BSA), inteligencia de negocios (BI) y operación (DevOps), más una quinta que atraviesa a las demás: trabajar con un asistente de inteligencia artificial bajo reglas escritas.

[[diagrama:linea_proyecto]]

## 3. Lo que se esperaba y lo que se encontró

Al empezar, las tres fuentes parecían sencillas: archivos CSV públicos, con columnas claras, que bastaba descargar, normalizar y cruzar. La realidad apareció en la última semana, cuando las pruebas de datos empezaron a fallar.

- **Las unidades de venta.** ODEPA escribe la unidad de cada precio a mano: «$/bandeja 18 kilos», «$/cien», «$/12 canastillos 125/170 gramos», «$/kilo (en caja de 17 kilos)». Unas 200 formas distintas, que se revisaron una por una; 12.185 filas quedaron sin unidad legible y se publican sin precio por kilo, nunca con uno adivinado.
- **El volumen.** La columna de volumen cuenta envases, no kilos: lo dice el boletín de ODEPA y lo confirman los datos (el 99,997 % de las filas calza). Con esa lectura, el precio semanal mayorista pasó a pesar los kilos o unidades que trae cada envase.
- **Los envases que cambian.** Un producto que una semana se vende en bandeja de 18 kilos y la siguiente en bandeja de 10 parece subir o bajar de precio sin que nada haya pasado. Desde entonces toda variación compara solo el mismo envase (RN-15); 1.003 cambios quedaron fuera de la comparación.
- **Las fuentes que se atrasan.** Una fuente puede publicar días después que la otra. El panel publica hasta la última semana completa en ambas, sin rellenar nada.

Cómo se abordó: con pruebas que recalculan cada cifra desde las filas crudas, no con pruebas que solo comprueban que la regla se aplicó; con una regla escrita por cada transformación, que dice qué problema resuelve y qué pasaría sin ella ([[vista:Reglas de transformación]]); y marcando como inferencia lo que la fuente no confirma.

[[diagrama:esperado_real]]

## 4. Cómo se trabajó

El trabajo avanzó en etapas cortas, cada una cerrada con pruebas en verde y una decisión escrita. Después de los hitos vinieron el panel con sus diagramas, los documentos (PRD, SAD, ADR, SQAP, plan de pruebas y manual), el plan de calidad con sus informes semanales, la versión en inglés de toda la app, el dashboard Semanal en cuatro pasos y, al final, la revisión de fondo de los datos.

- **Criterios de aceptación.** Los definió el autor y no cambiaron: comparaciones solo entre semana, región y unidad compatibles; reglas y rechazos explicados; indicadores trazables a su consulta; cargas auditables; y una carga con errores nunca llega al panel.
- **Gestión de calidad.** Un plan de calidad (SQAP) con 14 indicadores, 8 de código y 6 de datos, medidos en cada push; 42 fallas diagnosticadas y resueltas, cada una con su causa, su contención y su acción correctiva ([[vista:Cambios e incidentes]]); y pruebas que recorren todas las páginas en los dos idiomas.
- **Reglas de trabajo con la inteligencia artificial.** El asistente ejecutó bajo reglas escritas en el repositorio: solo lo necesario, aviso antes de lo pesado, informes de un párrafo, nunca inventar una cifra, nunca subir sin aprobación. Cada cambio de comportamiento quedó en una decisión numerada; hoy son 519.

## 5. Los roles

- **El autor, como ingeniero de datos:** diseñó el flujo (ingesta, aterrizaje en SQLite, bronce en Parquet, dbt sobre DuckDB y la base publicada en un release), decidió qué se prueba y exigió que las pruebas recalculen las cifras, no que solo apliquen la regla.
- **El autor, como analista de sistemas de negocio (BSA):** definió los criterios de aceptación, los nombres oficiales de cada cosa, qué bloquea una publicación y qué solo avisa, y revisó la app en local antes de cada subida. Encontró contradicciones entre diagramas mirando la app y pidió que las pruebas las impidieran.
- **El asistente de inteligencia artificial:** escribió código, pruebas y documentos; midió el impacto de cada regla de datos antes de aplicarla y propuso opciones con sus consecuencias. Las decisiones fueron del autor.

## 6. Lo que se aprendió

- **De ingeniería de datos:** que la regla correcta nace de mirar las filas, no de suponerlas; que un cambio de composición (regiones que entran o salen, envases que cambian) se confunde con un cambio de precio si no se compara lo mismo con lo mismo; y que una tolerancia temporal se anota con su fecha de salida.
- **Del negocio:** cómo publica ODEPA y qué significa cada columna; que una alerta de precio solo sirve si descuenta la estacionalidad y el envase; y que la pregunta de negocio manda sobre la técnica: el panel empieza por la región, el canal y la familia porque así compra y vende la gente.
- **De DevOps**, que no era la especialidad del autor: automatizar la carga en GitHub Actions con reintentos, publicar la base en un release, correr las pruebas en dos versiones de Python en cada push, medir la calidad del código en el mismo CI, rotar secretos y, la lección más cara, probar antes de subir con la misma base que usa el CI.
- **Del uso de la inteligencia artificial:** que rinde cuando tiene reglas escritas, criterios de aceptación y a alguien que revisa; y que su mejor aporte fue medir y proponer, no decidir.

## 7. Sorpresas en los datos

- **El salto de 2022.** Según el IPC de alimentos del INE, los alimentos subieron un 24,7 % en 2022, el mayor salto desde 2010. Desde 2023 suben entre 3,6 % y 5,2 % al año: el alza se moderó, pero los precios no volvieron atrás ([[vista:Análisis]]).
- **El kiwi del Maule.** La alerta de kiwi Hayward Especial mayorista marcaba un alza de 25,6 % en una semana. Al comparar solo el mismo envase, la subida fue de 8,8 % y la alerta desapareció: el Maule había pasado de bandeja de 18 kilos a bandeja de 10.
- **Lo que no se publica.** 12.185 cotizaciones no tienen una unidad que se pueda leer; antes, algunas se leían mal. Hoy quedan fuera del precio por kilo y a la vista en el catálogo de controles.

## 8. Puntos fuertes y menos fuertes

Fuertes:

- Trazabilidad completa: de la cifra del panel a la fila de ODEPA, pasando por una regla escrita y una prueba que la recalcula.
- Calidad medida, no declarada: 14 indicadores en cada push, informes semanales y un registro de fallas con antes y después.
- Documentación viva: nueve documentos que leen sus cifras de la base y se imprimen desde la página, en español e inglés.

Menos fuertes:

- El panel era un solo archivo de casi 10.000 líneas; después del cierre se dividió en archivos por responsabilidad (D-541), pero sigue siendo grande y algunas funciones son largas.
- La suite completa tarda unos 15 minutos en el CI; en local, cinco.
- Tres lecturas de los datos siguen siendo inferencias sin confirmación de ODEPA, marcadas como tales.
- Un solo despliegue, en Streamlit Community Cloud, sin un contenedor que lo reproduzca en otra parte.

## 9. A quién sirve

- **Al autor:** para consolidar, con un caso real, ingeniería de datos, BSA, BI, DevOps y el trabajo con inteligencia artificial bajo reglas.
- **A reclutadores y revisores técnicos:** como evidencia de cómo trabaja el autor: decisiones escritas, pruebas, calidad medida y fallas reconocidas.
- **A profesionales de datos:** como ejemplo de lo que hay que hacerle a una fuente pública antes de publicar una cifra.
- **A quien investiga o enseña:** como una base revisada de precios de alimentos en Chile, con cada regla a la vista y los archivos originales al alcance.

[[diagrama:para_quien]]

## 10. Qué queda

- Publicar el proyecto en una comunidad de ingeniería de datos y recibir la revisión de profesionales con más experiencia; esta acta es la primera pieza para esa conversación.
- Pagar las deudas de la sección 8 si el proyecto sigue creciendo: acortar las funciones más largas del panel, acortar la suite y empaquetar el despliegue.
- Seguir profundizando donde el autor se sintió menos firme: DevOps más allá de GitHub Actions, estadística para las alertas y diseño de pruebas de datos a gran escala.

## 11. Glosario

Las siglas y los términos de este documento se definen en el [Glosario](GLOSARIO.md).

## 12. Historial de versiones

| Versión | Fecha | Cambios |
|---|---|---|
| 1.0 | 04-11-2026 | Primera versión, al cerrar el proyecto como portafolio (D-529) |
| 1.1 | 07-11-2026 | Sin consulta pendiente a ODEPA: las tres inferencias quedan como tales (D-534) |
| 1.2 | 08-11-2026 | El panel ya está dividido por responsabilidad: se actualizan sus puntos menos fuertes y lo que queda (D-548) |
