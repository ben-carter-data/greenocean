# Plan de calidad del software (SQAP)

| Campo | Valor |
|---|---|
| Proyecto | GreenOcean |
| Tipo de documento | Plan de calidad del software (SQAP) |
| Versión | 1.13 |
| Fecha | 03-11-2026 |
| Estado | Vigente |
| Responsable | El autor |
| Propósito | Decir qué calidad cuida GreenOcean, cómo la mide, quién decide y qué pasa cuando algo falla. |
| Audiencia | Gerencia, analistas, revisores técnicos y quien quiera saber por qué fiarse de las cifras. |
| Documentos relacionados | [Documento de requisitos del producto (PRD)](../negocio/PRD.md) · [Documento de arquitectura de software (SAD)](../arquitectura/SAD.md) · [Plan de pruebas y seguridad](PLAN_PRUEBAS.md) · [Manual de operación](../operacion/MANUAL.md) · [Glosario](../negocio/GLOSARIO.md) |

## Índice

1. [Por qué existe este plan](#1-por-qué-existe-este-plan)
2. [Visión y misión](#2-visión-y-misión)
3. [Qué medimos y por qué](#3-qué-medimos-y-por-qué)
4. [Cómo lo medimos](#4-cómo-lo-medimos)
5. [Qué no medimos y por qué](#5-qué-no-medimos-y-por-qué)
6. [Cómo se lee un indicador](#6-cómo-se-lee-un-indicador)
7. [Pruebas que bloquean y pruebas que informan](#7-pruebas-que-bloquean-y-pruebas-que-informan)
8. [Informes de calidad](#8-informes-de-calidad)
9. [Registro de fallas](#9-registro-de-fallas)
10. [Incidentes de las fuentes de datos](#10-incidentes-de-las-fuentes-de-datos)
11. [Quién decide qué](#11-quién-decide-qué)
12. [Una autoevaluación, no un certificado](#12-una-autoevaluación-no-un-certificado)
13. [Glosario](#13-glosario)
14. [Historial de versiones](#14-historial-de-versiones)

## 1. Por qué existe este plan

Este plan dice qué calidad cuida el proyecto, cómo la mide y quién decide. Así la calidad no depende de la memoria de nadie. Sigue la estructura del estándar IEEE 730, adaptada a un proyecto de un solo autor.

## 2. Visión y misión

- **Visión:** que cualquier persona en Chile sepa, con datos oficiales, cómo se mueven los precios de los alimentos.
- **Misión:** publicar cada semana precios revisados y fáciles de leer, y mejorar el proceso con cada carga.

## 3. Qué medimos y por qué

Medimos dos calidades. La primera es la de los datos que publicamos, según la norma ISO/IEC 25012: que nadie vea un precio corrupto, atrasado o mal comparado sin saberlo. La segunda es la del código que trata esos datos, según la norma ISO/IEC 25010: que sea probado, ordenado y seguro.

[[diagrama:calidades]]

Son los 14 indicadores del plan de calidad: 8 del código y 6 de los datos. Cada uno tiene escrito qué mide, por qué importa, cómo se mide y qué hacer si falla. Todo eso vive en `docs/calidad/metas.json`, y la página «Plan de calidad» lo muestra.

No hay que confundirlos con los 11 indicadores de calidad de los datos, que se miden en cada carga sobre la base publicada y se ven en «Controles de datos». Esos protegen cada publicación; los del plan miden el proyecto semana a semana.

Así se ven los 11 indicadores de los datos en [[vista:Controles de datos]], cada uno bajo la parada del pipeline donde se vigila:

[[diagrama:calidad]]

## 4. Cómo lo medimos

Lo miden pruebas automáticas, es decir, programas que revisan el trabajo sin intervención. Corren en el CI, el servidor de GitHub que prueba cada cambio, y en la carga de cada martes. Cada indicador tiene un umbral, un límite que el autor fijó. Un umbral nunca se baja para que una prueba pase, y una prueba nunca se salta: se corrige la causa.

## 5. Qué no medimos y por qué

- **Tiempo de respuesta:** el servidor de GitHub es compartido y su velocidad cambia de un día a otro, así que no sirve para medir. Las pruebas de velocidad siguen corriendo en el computador del autor como informativas (D-341).
- **Navegadores:** salieron de la medición porque el plan mide lo mínimo que prueba la calidad: los datos y el código (D-330). El workflow de calidad ya no instala navegadores.
- **Accesibilidad:** se revisó una vez y quedó sin fallas (D-323). Salió de la medición semanal por la misma razón (D-330).

## 6. Cómo se lee un indicador

Cada indicador tiene una meta (el valor deseado), un aceptable (el peor valor que se tolera) y un margen crítico (cuánto más allá del aceptable se puede llegar antes de actuar de inmediato). Con esos tres valores, un indicador queda en uno de cuatro estados.

[[diagrama:estados_calidad]]

Los valores de cada indicador están en `docs/calidad/metas.json`, y los nombres de los estados, en `docs/calidad/politica.json`.

El aceptable de un indicador de datos se calibra con la historia de la fuente, no a ojo: marca lo que es raro en esos datos. El de los precios con comparación válida es 97 %, el percentil 5 de 251 semanas, igual que su meta ([ADR-36](../arquitectura/ADR.md#adr-36--calibrar-el-aceptable-de-los-precios-comparables-con-la-historia-de-los-datos), D-433). Se mide sobre los precios que también tenían precio la semana anterior; los que reaparecen tras un hueco se cuentan aparte y no alertan (D-475). El de los precios atípicos de la semana es 0,25 %, el percentil 95 de 252 semanas. Una región o un canal con precios en cada una de las 8 semanas anteriores que falta en la última es una ausencia, y el aceptable es 0 (D-475). Un cambio de aceptable vale desde el informe siguiente: los informes ya escritos guardan el aceptable con que se midieron.

## 7. Pruebas que bloquean y pruebas que informan

Una prueba que bloquea detiene la publicación si falla. Así funcionan las pruebas de datos de dbt y las de las cifras del panel. Una prueba que informa solo avisa: nunca debe frenar la publicación.

La carga semanal corre solo las pruebas que bloquean por los datos: las de datos y del pipeline. Las de pantalla (páginas, traducciones, documentos) corren en el CI de cada push; una falla de pantalla nunca detiene la publicación de datos (D-366).

El ejemplo es F-10 del registro de fallas. Una prueba de velocidad, que era informativa, bloqueaba la carga semanal, y los datos dejaron de actualizarse. La prueba salió de la carga y del CI, y sigue en local como informativa (D-341).

## 8. Informes de calidad

Hay un solo informe numerado: el informe semanal de calidad, uno por semana de datos (D-431). El workflow de calidad lo genera solo cuando la carga semanal terminó en verde, con sus pruebas pasadas y la base publicada, y lo propone como pull request (D-363). Mide los 5 indicadores de datos de cada carga: pruebas de datos dbt superadas, precios con comparación válida, filas rechazadas, regiones o canales ausentes y precios atípicos de la semana (D-475). Los 8 indicadores de código se verifican en el CI de cada push: pasan o fallan en GitHub Actions, sin informe. Los días desde la última carga se ven en el panel, no en el informe.

El informe tiene cuatro páginas: la portada, con la versión de este plan con que se midió; los resultados; la comparación con otro informe, que avisa si los dos no miden los mismos indicadores; y una sola tabla de no conformidades e incidencias, con las abiertas y las de esa semana. La metodología vive solo en este plan. Un informe no se edita después: si algo cambia, sale el informe siguiente. Si los indicadores de código están en su aceptable, el pull request se fusiona solo y el panel muestra el informe; si no, queda abierto y lo revisa el autor; si sigue abierto a la semana siguiente, el informe nuevo lo reemplaza con el mismo número (D-436). En el panel, cada informe se abre como presentación y se descarga en PDF (D-333, D-347).

Una no conformidad de la serie semanal se cierra sola cuando un informe siguiente devuelve su indicador al aceptable, con el estado «resuelta automáticamente, informe N° x»; la causa y la acción que escribió el autor se conservan (D-437).

Los informes C-1 a C-7, del 26 al 31 de octubre de 2026, son la serie de construcción: mezclan código y datos, se midieron en cada push y no se editan. El panel los muestra aparte y no los compara con la serie semanal.


## 9. Registro de fallas

El registro, `docs/calidad/plan_mitigacion.json`, guarda cada falla que el proyecto vivió y cómo se resolvió. Sirve para no repetir errores y para mostrar cómo se corrige cada uno.

Cada falla tiene una categoría (datos, código u operación), una estación del flujo git (el camino de un cambio, de la idea al despliegue) y sus ocurrencias. Lo que falla en GitHub, el CI o el despliegue es de categoría operación.

Cada ocurrencia se escribe en una línea por campo y en lenguaje simple: qué pasó, la causa, qué se hizo y un comentario. El análisis detallado vive en su decisión D-xxx (D-354). La vista Profesional muestra qué pasó y cómo se resolvió; el diagnóstico solo lo ve el Autor (D-345). Cada falla diagnosticada se anota antes de publicar el cambio que la corrige (D-342).

## 10. Incidentes de las fuentes de datos

Un incidente externo es una falla de las fuentes de datos: ODEPA o el INE. Por ejemplo, una semana que no se publica o un archivo que cambia de formato. Ante un incidente, la carga no pasa sus controles y el panel conserva la última carga válida, con su fecha a la vista. Los incidentes se anotan en `docs/calidad/incidentes_externos.json`, y su respuesta queda pendiente de aprobación del autor (D-334).

**Fuentes retrasadas (D-356).** Se publica hasta la última semana completa en ambas fuentes, sin rellenar nada. Así lo leen el dashboard Semanal y los indicadores. Al elegir un canal en el paso 2 de Semanal se ve la última semana de esa fuente, rotulada (D-365, D-494). Una semana reciente que una fuente aún no publica no bloquea la carga: queda como incidente externo y la app muestra un aviso discreto. La carga se detiene solo si falta una semana en medio de los datos, o si la fuente lleva más de 2 semanas sin publicar. En ese caso, además, el Autor recibe un aviso urgente.

## 11. Quién decide qué

- **El autor:** fija las metas, los aceptables y los márgenes; aprueba el informe que no se fusiona solo; decide cada cambio y cada publicación.
- **Las herramientas:** miden, comparan y proponen. Nunca publican ni cambian un umbral por su cuenta.

## 12. Una autoevaluación, no un certificado

Este plan y sus informes son una autoevaluación del autor. Ninguna entidad externa los audita, y no reemplazan una certificación. Su valor está en que cada número se puede comprobar contra el código y los datos.

## 13. Glosario

Las siglas y los términos de este documento se definen en el [Glosario](../negocio/GLOSARIO.md).

## 14. Historial de versiones

| Versión | Fecha | Cambios |
|---|---|---|
| 1.0 | 30-10-2026 | Primera versión del plan de calidad del software (D-355) |
| 1.1 | 30-10-2026 | Regla de las fuentes retrasadas (D-356) |
| 1.2 | 30-10-2026 | La página «Último dato por canal» muestra la última semana de cada fuente (D-365) |
| 1.3 | 30-10-2026 | La carga semanal corre solo las pruebas de datos y del pipeline (D-366) |
| 1.4 | 31-10-2026 | Los 12 indicadores del plan de calidad, distintos de los 11 indicadores de calidad de los datos (3); el informe se propone como pull request después de cada carga (8); visión y misión como en el PRD; el documento pasa a `docs/calidad/` (D-381, D-384, D-388) |
| 1.5 | 01-11-2026 | Un solo informe numerado, el semanal de los datos, en cuatro páginas y solo tras una carga en verde; el código se verifica en el CI; la serie de construcción C-1 a C-7 (8, D-431) |
| 1.6 | 01-11-2026 | El aceptable y la meta de los precios comparables se calibran al percentil 5 de la historia, 81 % (6, ADR-36, D-433) |
| 1.7 | 01-11-2026 | El pull request del informe se fusiona solo si el código está en su aceptable; uno abierto lo reemplaza el informe siguiente (8, 11, D-436) |
| 1.8 | 01-11-2026 | Una no conformidad de la serie semanal se cierra sola cuando su indicador vuelve al aceptable (8, D-437) |
| 1.9 | 02-11-2026 | «Panorama de precios» pasa a llamarse «Dashboard» y encabeza el menú (D-442) |
| 1.10 | 02-11-2026 | Los 11 indicadores de los datos se dibujan con el flujo de «Controles de datos» (3), en vez de «El ciclo de cada semana» (D-455) |
| 1.11 | 02-11-2026 | El dashboard de la semana se llama «Semanal» (10, D-459) |
| 1.12 | 03-11-2026 | Los precios comparables se miden sobre los que tenían precio la semana anterior, con aceptable 97 %; dos indicadores nuevos de datos: regiones o canales ausentes y precios atípicos de la semana (3, 6, 8, ADR-36, D-475) |
| 1.13 | 03-11-2026 | La última semana de cada fuente se ve al elegir su canal en Semanal (D-494) |
