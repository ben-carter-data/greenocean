# Plan de calidad del software (SQAP)

| Campo | Valor |
|---|---|
| Proyecto | GreenOcean |
| Tipo de documento | Plan de calidad del software (SQAP) |
| Versión | 1.2 |
| Fecha | 30-10-2026 |
| Estado | Vigente |
| Responsable | El autor |
| Propósito | Decir qué calidad cuida GreenOcean, cómo la mide, quién decide y qué pasa cuando algo falla. |
| Audiencia | Gerencia, analistas, revisión técnica y quien quiera saber por qué confiar en las cifras. |
| Documentos relacionados | [Documento de requisitos del producto (PRD)](PRD.md) · [Documento de arquitectura de software (SAD)](SAD.md) · [Plan de pruebas y seguridad](PLAN_PRUEBAS.md) · [Manual de operación](MANUAL.md) · [Glosario](GLOSARIO.md) |

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

- **Visión:** Que cualquier persona en Chile sepa, con datos oficiales y confiables, cómo se mueven los precios de los alimentos.
- **Misión:** Publicar cada semana precios verificados, claros y fáciles de leer, y mejorar el proceso de forma continua.

## 3. Qué medimos y por qué

Medimos dos calidades. La primera es la de los datos que publicamos, según la norma ISO/IEC 25012: que nadie vea un precio corrupto, atrasado o mal comparado sin saberlo. La segunda es la del código que trata esos datos, según la norma ISO/IEC 25010: que sea probado, ordenado y seguro.

Cada indicador tiene escrito qué mide, por qué importa, cómo se mide y qué hacer si falla. Todo eso vive en `docs/calidad/metas.json`, y la página «Método y calidad» lo muestra.

[[diagrama:calidades]]

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

## 7. Pruebas que bloquean y pruebas que informan

Una prueba que bloquea detiene la publicación si falla. Así funcionan las pruebas de datos de dbt y las de las cifras del panel. Una prueba que informa solo avisa: nunca debe frenar la publicación.

El ejemplo es F-10 del registro de fallas. Una prueba de velocidad, que era informativa, bloqueaba la carga semanal, y los datos dejaron de actualizarse. La prueba salió de la carga y del CI, y sigue en local como informativa (D-341).

## 8. Informes de calidad

Cada semana se mide todo y se arma un informe numerado. Un informe no se edita después: si algo cambia, sale el informe siguiente. El autor revisa cada informe y lo aprueba antes de que el panel lo muestre (D-331). En el panel, cada informe se abre como presentación y se descarga en PDF (D-333, D-347).

[[diagrama:ciclo_calidad]]

## 9. Registro de fallas

El registro, `docs/calidad/plan_mitigacion.json`, guarda cada falla que el proyecto vivió y cómo se resolvió. Sirve para no repetir errores y para mostrar cómo se corrige cada uno.

Cada falla tiene una categoría (datos, código u operación), una estación del flujo git (el camino de un cambio, de la idea al despliegue) y sus ocurrencias. Lo que falla en GitHub, el CI o el despliegue es de categoría operación.

Cada ocurrencia se escribe en una línea por campo y en lenguaje simple: qué pasó, la causa, qué se hizo y un comentario. El análisis detallado vive en su decisión D-xxx (D-354). El profesional ve qué pasó y cómo se resolvió; el diagnóstico es del autor (D-345). Cada falla diagnosticada se anota antes de publicar el cambio que la corrige (D-342).

## 10. Incidentes de las fuentes de datos

Un incidente externo es una falla de las fuentes de datos: ODEPA o el INE. Por ejemplo, una semana que no se publica o un archivo que cambia de formato. Ante un incidente, la carga no pasa sus controles y el panel conserva la última carga válida, con su fecha a la vista. Los incidentes se anotan en `docs/calidad/incidentes_externos.json`, y su respuesta queda pendiente de aprobación del autor (D-334).

**Fuentes retrasadas (D-356).** Se publica hasta la última semana completa en ambas fuentes, sin rellenar nada: así lo leen el Panorama y los indicadores; la página «Último dato por canal» muestra la última semana de cada fuente, rotulada (D-365). Una semana reciente que una fuente aún no publica no bloquea la carga: queda como incidente externo y la app muestra un aviso discreto. La carga se detiene solo si falta una semana en medio de los datos, o si la fuente lleva más de 2 semanas sin publicar; en ese caso, además, el Autor recibe un aviso urgente.

## 11. Quién decide qué

- **El autor:** fija las metas, los aceptables y los márgenes; aprueba cada informe; decide cada cambio y cada publicación.
- **Las herramientas:** miden, comparan y proponen. Nunca publican ni cambian un umbral por su cuenta.

## 12. Una autoevaluación, no un certificado

Este plan y sus informes son una autoevaluación del autor. Ninguna entidad externa los audita, y no reemplazan una certificación. Su valor está en que cada número se puede comprobar contra el código y los datos.

## 13. Glosario

Las siglas y los términos de este documento se definen en el [Glosario](GLOSARIO.md).

## 14. Historial de versiones

| Versión | Fecha | Cambios |
|---|---|---|
| 1.0 | 30-10-2026 | Primera versión del plan de calidad del software (D-355) |
| 1.1 | 30-10-2026 | Regla de las fuentes retrasadas (D-356) |
| 1.2 | 30-10-2026 | La página «Último dato por canal» muestra la última semana de cada fuente (D-365) |
