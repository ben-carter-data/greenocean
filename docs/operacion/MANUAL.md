# Manual de operación (runbook)

| Campo | Valor |
|---|---|
| Proyecto | GreenOcean |
| Tipo de documento | Manual de operación (runbook) |
| Versión | 3.8 |
| Fecha | 01-11-2026 |
| Estado | Vigente |
| Responsable | El autor |
| Propósito | Indicar qué ocurre de forma automática, qué se revisa y cuándo, y qué hacer ante cada falla. |
| Audiencia | Quien opera el proyecto, también sin formación técnica. |
| Documentos relacionados | [Documento de arquitectura de software (SAD)](../arquitectura/SAD.md) · [Plan de pruebas y seguridad](../calidad/PLAN_PRUEBAS.md) · [Glosario](../negocio/GLOSARIO.md) |

## Índice

1. [En resumen](#1-en-resumen)
2. [Qué ocurre automáticamente](#2-qué-ocurre-automáticamente)
3. [Qué se revisa y cuándo](#3-qué-se-revisa-y-cuándo)
4. [Fallas de la carga semanal](#4-fallas-de-la-carga-semanal)
5. [Fallas del panel publicado](#5-fallas-del-panel-publicado)
6. [Recuperación](#6-recuperación)
7. [Acceso del autor y administración](#7-acceso-del-autor-y-administración)
8. [Guía de GitHub](#8-guía-de-github)
9. [Registro de fallas](#9-registro-de-fallas)
10. [Límites conocidos](#10-límites-conocidos)
11. [Glosario](#11-glosario)
12. [Historial de versiones](#12-historial-de-versiones)

## 1. En resumen

GreenOcean se opera casi solo. Cada martes la carga corre sin intervención. Si algo falla, el panel sigue mostrando la última carga válida: nunca se publica una cifra a medias.

El trabajo de operación se reduce a mirar un resultado por semana, a cuatro tareas del calendario y, si llega el aviso de una falla, a seguir la tabla de la sección 4. El aviso llega por tres vías:

- El correo de GitHub.
- La ejecución en rojo en GitHub.
- Dentro del panel, un aviso rojo arriba del menú en todas las páginas, con un enlace al paso que falló.

[[diagrama:calendario]]

## 2. Qué ocurre automáticamente

El job semanal (`.github/workflows/semanal.yml`) corre cada martes a las 12:00 UTC: las 09:00 en el horario de verano de Chile y las 08:00 en el de invierno. Descarga las fuentes, construye y prueba la base, la publica en el release «base-actual» y crea el informe semanal. La secuencia completa, paso a paso, está en la [secuencia de la carga del SAD](../arquitectura/SAD.md#4-la-carga-de-cada-semana).

También se puede lanzar a mano: desde «Centro de operación», con el botón «Ejecutar pipeline ahora» (requiere la clave de control), o desde la página del workflow en GitHub. La ventana de la ejecución muestra arriba el flujo en vivo, enfocado en la carga: qué pieza trabaja y qué mensaje viaja en cada paso (D-413).

Si un paso falla, los siguientes no se ejecutan y la base servida no cambia ([ADR-11 · Publicar solo si pasan las pruebas](../arquitectura/ADR.md#adr-11--publicar-solo-si-pasan-las-pruebas)).

Después de cada carga, el workflow de calidad mide los 12 indicadores del plan de calidad y propone el informe numerado como pull request «Actualizar medición de calidad». En cada push solo mide, y falla si un indicador de código pasa su aceptable.

## 3. Qué se revisa y cuándo

| Cuándo | Qué se revisa o se hace | Dónde |
|---|---|---|
| Cada martes, después de las 12:00 UTC | Que la ejecución terminó en verde | Pestaña «Operación» de «Centro de operación», o el correo de GitHub si falló |
| Cada martes | Que existe el issue «Informe semanal AAAA-MM-DD» | Issues del repositorio |
| Ante una duda sobre las cifras | El veredicto de calidad y los controles de auditoría | «Calidad y auditoría» |
| Cada enero | Agregar a `agent/input.csv` las dos líneas del año nuevo (mayorista y consumidor), con la URL que publica ODEPA en la página de cada conjunto de datos | `agent/input.csv` |
| Periódicamente | Copiar `agent/downloads` a otro disco: los CSV no se versionan ([ADR-04 · No subir los datos crudos al repositorio](../arquitectura/ADR.md#adr-04--no-subir-los-datos-crudos-al-repositorio)) y la caché de GitHub se borra si no se usa en 7 días | Otro disco del autor |
| Antes de su vencimiento | Renovar los dos tokens de GitHub del panel; «Configuración» los marca en ámbar cuando faltan 15 días o menos, y la alerta «Acción requerida» lo avisa al entrar como Autor (sección 8.1) | Secretos de la app en Streamlit |
| Después de cada carga semanal | El pull request «Actualizar medición de calidad»: fusionarlo o cerrarlo, borrar su rama y hacer `git pull` | Pull requests del repositorio (sección 8) |
| Al entrar como Autor | La alerta «Acción requerida»: primero, cada token a 15 días o menos de vencer; después, los indicadores fuera de su aceptable. Si dice «Última medición del …», el informe tiene más de 8 días y no es el estado de hoy | La ventana que abre el panel |

## 4. Fallas de la carga semanal

[[diagrama:arbol_fallas]]

Cada fila corresponde a un paso del workflow, con su nombre en `semanal.yml`. El aviso llega al autor por el correo «Run failed: semanal» de GitHub y, en el panel, como un aviso rojo arriba del menú de todas las páginas. El paso fallido aparece en rojo en «Centro de operación». La tabla `etl_run` registra solo las cargas publicadas, así que el mensaje de una falla se lee en el log del paso.

| Paso | Síntoma | Causa probable | Acción |
|---|---|---|---|
| Restore the closed-year files | El paso termina con error | Un problema de la caché de GitHub | Volver a lanzar el job; sin caché, la descarga baja todos los años |
| Get the published database | El paso no puede descargar la base o su huella no coincide | El release «base-actual» no está disponible o su archivo cambió | Revisar el release en GitHub; si falta, volver a publicar la base desde una copia local verificada |
| Download the ODEPA files | `DOWNLOAD_ERROR` o `UNEXPECTED_HEADER` en el log | ODEPA no respondió, o cambió las columnas de un archivo | Con `DOWNLOAD_ERROR`, esperar unas horas y volver a lanzar; con `UNEXPECTED_HEADER`, revisar el archivo y adaptar el agente |
| Run the ETL (SQLite backup) | `MISSING_WEEKS`, `UNKNOWN_REGION`, `UNKNOWN_CHANNEL` o `DUPLICATE_KEYS` en el log | Falta una semana fuera de los huecos conocidos, ODEPA agregó una región o un canal, o hay precios repetidos | Revisar el archivo en ODEPA; una región o un canal nuevos se agregan a las listas del ETL; una semana faltante en la fuente se registra como hueco conocido con su decisión |
| Build the data warehouse with dbt | Un modelo o una prueba de dbt falla, o `TOO_FEW_ROWS` | Una regla de negocio no se cumple, o la carga leyó menos del 90 % de la anterior | Leer en el log qué modelo o prueba falló; suele nombrar la tabla y la regla |
| Run the tests against the new database | Una prueba de pytest falla | Los datos nuevos no cumplen algo que el código supone, o el respaldo y la base servida no coinciden | Leer qué prueba falló; suele indicar el producto o la semana |
| Publish the database | GitHub rechaza la subida del archivo o del puntero | Permisos del workflow o un cambio en `main` durante la carga | Revisar Settings → Actions → Workflow permissions («Read and write») y volver a lanzar |
| Publish the weekly report | No se crea el issue | Permisos del workflow | Revisar los permisos; la base ya quedó publicada |

Una semana que una fuente aún no publica no es una falla. La carga publica hasta la última semana completa en ambas fuentes, y el Panorama lo avisa. Sí detienen la carga `MISSING_WEEKS` (falta una semana en medio de los datos) y `LATE_SOURCE` (una fuente lleva más de 2 semanas sin publicar). En esos casos, revisar ODEPA y no rellenar nada: la carga vuelve sola cuando la fuente publica.

Para leer cualquier falla sin copiar a mano, la página «GitHub Actions» del panel, en la vista Autor, muestra el job, el paso, las pruebas que fallan y el final del log, con «Copiar». Para ver en qué paso va una carga, sin logs y en cualquier vista, está el flujo en vivo de «Stack y evidencia» (D-412).

## 5. Fallas del panel publicado

| Síntoma | Causa probable | Acción |
|---|---|---|
| Después de un push, una página muestra `AttributeError` | Streamlit Cloud combinó archivos nuevos con otros que tenía en memoria (ocurrió el 12-10-2026) | En el panel, «Manage app» → ⋮ → **Reboot**, y esperar uno o dos minutos |
| «Centro de operación» indica «GitHub no respondió (…)» | Sin token, GitHub permite 60 consultas por hora, compartidas por las apps del mismo servidor | Ninguna: el panel muestra la última respuesta guardada y vuelve a consultar cada 5 minutos; con el token configurado, el límite sube |
| El panel informa que no tiene la base servida | No pudo descargarla del release al arrancar | Verificar que el release «base-actual» existe; el panel la descarga en la siguiente visita |
| El botón «Ejecutar pipeline ahora» indica que falta el token | El token del panel venció o no está configurado | Crear un token con permiso para lanzar workflows de este repositorio y guardarlo como `GITHUB_TOKEN` en los secretos de la app en Streamlit |

## 6. Recuperación

[[diagrama:secuencia_recuperacion]]

| Situación | Procedimiento |
|---|---|
| Una carga falló | Corregir la causa según la sección 4 y volver a lanzar el job; mientras tanto, el panel muestra la última carga válida |
| Una carga manual se colgó | En la ventana de la ejecución, «Cancelar» y confirmar; si no responde, GitHub la corta a los 20 minutos |
| El release perdió su archivo | Reconstruir la base en un equipo con los datos (`python etl/pipeline.py --local`), verificar que la suite pasa y subir el archivo al release «base-actual» junto con su puntero (`python bi/served_database.py --pointer`) |
| Una copia nueva del repositorio no tiene la base | `python bi/served_database.py` descarga la base de la última carga y verifica su huella |

## 7. Acceso del autor y administración

El panel tiene una sola clave: la de entrar como Autor (secreto `CONTROL_CODE` del panel), en la ventana «Elige tu vista» (D-369, D-421). Con ella aparece la sección «DevOps y seguridad», que solo ve el Autor (D-420): en «Centro de operación», el botón «Ejecutar pipeline ahora», que lanza la carga de inmediato, y el aviso del vencimiento del token; cancelar una carga pide confirmar «¿Seguro?» en la misma ventana. La página «Configuración» está en esa sección. Esa página reúne en una pantalla el estado de los tokens, la última carga, el último informe, las pruebas y las fuentes; qué hacer en cada caso (sección 8.1), y las tareas de mantenimiento. Sin el secreto configurado, por ejemplo en una copia local, el acceso queda cerrado.

La clave evita ejecuciones accidentales; no es la barrera principal. Lo que protege el proyecto es el inicio de sesión del autor en GitHub y en Streamlit (con verificación en dos pasos) y un token con los permisos mínimos. Tras 3 fallos, cada intento espera 2 s, y el doble tras cada nuevo fallo, hasta 15 min; con la clave correcta vuelve a cero (D-393, [Plan de pruebas y seguridad](../calidad/PLAN_PRUEBAS.md#11-riesgos-aceptados-y-límites)). Cada acción del Autor (lanzar, cancelar, recargar los datos) vuelve a comprobar en el servidor que la sesión es del Autor (D-421). Si la espera traba el acceso, la carga se puede lanzar desde GitHub. El panel nunca muestra el token ni una parte de él.

Para entrar: en la ventana «Elige tu vista», el enlace «Acceso del autor», en su esquina, la clave y Enter (D-369). El botón «Vista», debajo del logo, cambia de vista; un clic en el logo hace lo mismo (D-373). Salir de Autor cierra su sesión. Toda recarga de la pestaña (abrir o imprimir un documento, cambiar el tema, un enlace como el del aviso «Acción requerida», F5) conserva la vista, también la del Autor, con un ticket que el servidor emite y comprueba y que vale mientras dure su sesión (D-427, D-428, D-430); solo una pestaña nueva vuelve a pedirla.

El panel usa tres secretos, guardados en Streamlit (sección 8):

- `CONTROL_CODE`: la clave del autor.
- `GITHUB_TOKEN`: lanza la carga, lee su estado y sus logs, y la cancela.
- `GITHUB_READ_TOKEN`: solo lectura, para la página «GitHub Actions». Si falta, la página muestra los estados sin logs y el aviso «Falta el token de solo lectura».

## 8. Guía de GitHub

Los enlaces que se usan para operar el proyecto, agrupados por tarea.

| Tarea | Enlace | Para qué sirve | Cuándo usarlo | En qué hacer clic |
|---|---|---|---|---|
| Revisar fallas | [Actions](https://github.com/ben-carter-data/greenocean/actions) | Ver cada ejecución de los tres workflows y su estado | Cuando llega el correo «Run failed» o el aviso rojo del panel | La ejecución en rojo → el job → el paso en rojo |
| Revisar fallas | [Carga semanal](https://github.com/ben-carter-data/greenocean/actions/workflows/semanal.yml) | Solo las cargas de cada martes y las manuales | Cada martes, después de las 12:00 UTC | La última ejecución → «weekly-load» |
| Revisar fallas | [Pruebas](https://github.com/ben-carter-data/greenocean/actions/workflows/pruebas.yml) | Lint, mypy y pytest de cada push | Después de cada push | La ejecución del commit → «pytest» o «lint» |
| Revisar fallas | [Calidad](https://github.com/ben-carter-data/greenocean/actions/workflows/calidad.yml) | La medición de calidad de cada push y el informe semanal | Si el panel o el correo avisan un indicador fuera de su aceptable | La ejecución → «medir» → el paso en rojo |
| Aprobar un informe | [Pull requests](https://github.com/ben-carter-data/greenocean/pulls) | Revisar el informe de calidad que propone el workflow | Después de cada carga semanal | «Actualizar medición de calidad» → «Files changed» → «Merge pull request», o «Close pull request» |
| Aprobar un informe | [Branches](https://github.com/ben-carter-data/greenocean/branches) | Borrar la rama de un informe ya fusionado o cerrado | Después de fusionar o cerrar el pull request | El ícono de la papelera junto a la rama «informe-calidad/…» |
| Configuración | [Actions · General](https://github.com/ben-carter-data/greenocean/settings/actions) | Permisos del workflow para escribir y abrir pull requests | Si una publicación o un pull request son rechazados | «Workflow permissions» → «Read and write» y «Allow GitHub Actions to create and approve pull requests» |
| Configuración | [Release «base-actual»](https://github.com/ben-carter-data/greenocean/releases/tag/base-actual) | La base servida que lee el panel | Si el panel no encuentra su base | Revisar que el archivo `datos.duckdb` esté en «Assets» |
| Configuración | [Issues](https://github.com/ben-carter-data/greenocean/issues) | El informe semanal de cada carga publicada | Cada martes | «Informe semanal AAAA-MM-DD» |
| La app | [Panel publicado](https://monitor-precios-hito1-d4hfucgaifcebbwahgrzwf.streamlit.app) | La app que ven el Usuario, el Profesional y el Autor | Después de cada push, para confirmar el cambio | Elegir la vista; como Autor, escribir la clave y Enter |
| La app | [Streamlit Community Cloud](https://share.streamlit.io) | Los secretos del panel y su reinicio | Al renovar un token o si el panel muestra un error de módulo | La app → ⋮ → «Settings» → «Secrets», o «Reboot» |
| Tokens | [Tokens de GitHub](https://github.com/settings/personal-access-tokens) | El vencimiento y los permisos de cada token | Cuando «Configuración» marca un token en ámbar o rojo | El token → «Regenerate token»; el valor nuevo se muestra una sola vez |
| Tokens | [Crear un token](https://github.com/settings/personal-access-tokens/new) | Un token nuevo, solo para este repositorio | Si un token falta | «Repository access» → este repositorio; «Permissions» → «Actions» |

**Dos reglas.** No editar archivos desde la web de GitHub: todo cambio se hace en el computador del autor y se sube con push, para que main local y remoto no se separen. Después de fusionar un pull request en la web, traer el cambio con `git pull` antes de trabajar.

### 8.1 Qué hacer en cada caso

Cinco casos, cada uno con sus pasos en orden. Un paso automático lo hace el sistema solo; uno manual lo hace el autor, con el enlace que lleva a ese lugar. La página «Configuración» muestra esta misma tabla.

| Caso | Paso | Tipo | Qué hacer | Enlace |
|---|---|---|---|---|
| La carga falló | 1 | Automático | GitHub detiene los pasos siguientes y el panel sigue mostrando la última carga válida | — |
| La carga falló | 2 | Automático | Llega el correo «Run failed: semanal» y el panel muestra un aviso rojo arriba del menú | — |
| La carga falló | 3 | Manual | Leer qué paso falló y el final de su log | [[vista:GitHub Actions]] |
| La carga falló | 4 | Manual | Corregir la causa según la tabla de la sección 4 | — |
| La carga falló | 5 | Manual | Volver a lanzar la carga con «Ejecutar pipeline ahora», o con «Run workflow» en GitHub | [[vista:Centro de operación]] |
| Llegó un informe | 1 | Automático | Después de cada carga, el workflow de calidad mide los 12 indicadores y abre el pull request «Actualizar medición de calidad» | — |
| Llegó un informe | 2 | Manual | Revisar el informe en «Files changed» | [Pull requests](https://github.com/ben-carter-data/greenocean/pulls) |
| Llegó un informe | 3 | Manual | «Merge pull request», o «Close pull request» si un informe más nuevo lo reemplaza | [Pull requests](https://github.com/ben-carter-data/greenocean/pulls) |
| Llegó un informe | 4 | Manual | Borrar la rama «informe-calidad/…» del informe | [Branches](https://github.com/ben-carter-data/greenocean/branches) |
| Llegó un informe | 5 | Manual | En el computador, traer el cambio con `git pull` | — |
| Un token vence o falta | 1 | Automático | «Configuración» marca el token en ámbar cuando faltan 15 días o menos, y en rojo si venció o falta; la alerta «Acción requerida» lo avisa al entrar como Autor | [[vista:Configuración]] |
| Un token vence o falta | 2 | Manual | En GitHub, regenerar el token o crear uno nuevo, solo para este repositorio: «Actions: Read and write» para `GITHUB_TOKEN` y «Actions: Read» para `GITHUB_READ_TOKEN`. El valor se muestra una sola vez: copiarlo | [Tokens de GitHub](https://github.com/settings/personal-access-tokens) |
| Un token vence o falta | 3 | Manual | En Streamlit Community Cloud: la app → ⋮ → «Settings» → «Secrets» | [Streamlit Community Cloud](https://share.streamlit.io) |
| Un token vence o falta | 4 | Manual | Pegar el valor en `GITHUB_TOKEN` o `GITHUB_READ_TOKEN` y pulsar «Save» | — |
| Un token vence o falta | 5 | Manual | Pulsar «Reboot» y confirmar en «Configuración» la fecha nueva | [[vista:Configuración]] |
| Una fuente se atrasó | 1 | Automático | La carga publica hasta la última semana completa en ambas fuentes y el Panorama avisa «ODEPA aún no publica la semana …» | [[vista:Panorama de precios]] |
| Una fuente se atrasó | 2 | Automático | Si la fuente lleva más de 2 semanas sin publicar, la carga se detiene con `LATE_SOURCE` y llega el aviso de falla | — |
| Una fuente se atrasó | 3 | Manual | Revisar en ODEPA si la semana ya está publicada | [Datos abiertos de ODEPA](https://datos.odepa.gob.cl) |
| Una fuente se atrasó | 4 | Manual | No rellenar nada: la carga vuelve sola cuando la fuente publica | — |
| La app no se actualiza | 1 | Automático | Después de cada push a main, Streamlit Community Cloud vuelve a desplegar la app | — |
| La app no se actualiza | 2 | Manual | Abrir el panel publicado y confirmar que el cambio llegó | [Panel publicado](https://monitor-precios-hito1-d4hfucgaifcebbwahgrzwf.streamlit.app) |
| La app no se actualiza | 3 | Manual | Si una página muestra `AttributeError` o no cambia: la app → ⋮ → «Reboot», y esperar uno o dos minutos | [Streamlit Community Cloud](https://share.streamlit.io) |
| La app no se actualiza | 4 | Manual | Si el panel dice que no tiene la base servida, revisar que `datos.duckdb` esté en el release | [Release «base-actual»](https://github.com/ben-carter-data/greenocean/releases/tag/base-actual) |

## 9. Registro de fallas

Cada falla diagnosticada y resuelta se anota en `docs/calidad/plan_mitigacion.json` antes del push que la corrige. Cada ocurrencia lleva fecha, qué pasó, la causa, qué se hizo y un comentario, en una línea por campo y en lenguaje simple; el análisis largo va en su decisión D-xxx. El registro se lee en «Git workflow» → «Registro de incidentes». La vista Profesional muestra qué pasó y cómo se resolvió; el diagnóstico solo lo ve el Autor.

## 10. Límites conocidos

| Límite | Valor | Fuente |
|---|---|---|
| Tamaño máximo de un archivo de release | 2 GB; la base servida pesa unos 14 MB | Documentación de GitHub sobre releases, consultada el 24-10-2026 |
| Caché de GitHub Actions | Se borra si no se usa en 7 días; esa semana el job descarga todos los años | Documentación de GitHub Actions, consultada el 24-10-2026 |
| Consultas a la API de GitHub sin token | 60 por hora | Documentación de la API de GitHub |
| Arquitectura en la nube | No se adopta mientras los datos sean públicos, semanales y pequeños | [ADR-31 · No usar un data warehouse en la nube](../arquitectura/ADR.md#adr-31--no-usar-un-data-warehouse-en-la-nube) y [Capacidad y crecimiento del SAD](../arquitectura/SAD.md#9-capacidad-y-crecimiento) |

## 11. Glosario

Las siglas y los términos de este documento se definen en el [Glosario](../negocio/GLOSARIO.md).

## 12. Historial de versiones

| Versión | Fecha | Cambios |
|---|---|---|
| 1.0 | 12-10-2026 | Primera versión, como página del proyecto (D-043) |
| 1.1 | 16-10-2026 | Navegación por menú lateral y páginas nuevas (D-090 a D-099) |
| 1.2 | 17-10-2026 | Documentación y fuentes reorganizadas (D-105, D-106, D-110, D-118) |
| 1.3 | 19-10-2026 | Centro de operación y operación de la carga |
| 1.4 | 20-10-2026 | Consultas SQL (D-184, D-185) |
| 1.5 | 21-10-2026 | Calidad y auditoría en una vista (D-220) |
| 1.6 | 23-10-2026 | Seguridad como proceso y monitoreo (D-249); descarga como página impresa (D-248) |
| 1.7 | 24-10-2026 | Despliegue y pipeline (D-251, D-255); Stack y evidencia (D-266); base servida en un release (D-270) |
| 2.0 | 25-10-2026 | Formato de runbook: síntoma, causa, acción, recuperación, tareas periódicas y límites con su fuente (D-279, documentación profesional) |
| 3.0 | 25-10-2026 | Un resumen al inicio, el calendario, el árbol de fallas y la secuencia de recuperación como diagramas (D-290, documentos para todo lector) |
| 3.1 | 30-10-2026 | Guía de GitHub y registro de fallas; fuentes retrasadas, informe de calidad semanal, ventana de la carga manual, acceso como Autor y los tres secretos (D-339 a D-363) |
| 3.2 | 31-10-2026 | Redacción revisada; los 12 indicadores del plan de calidad (2); el token lanza, sigue y cancela la carga (7); las tres vistas (8, 9); el documento pasa a `docs/operacion/` (D-381, D-384, D-388) |
| 3.3 | 01-11-2026 | Qué hacer en cada caso (8.1), que lee la página «Configuración»; los dos tokens en la guía de GitHub (8) y su aviso a 15 días (3, D-409) |
| 3.4 | 01-11-2026 | La alerta «Acción requerida» avisa cada token a 15 días o menos de vencer (3, 8.1, D-410) |
| 3.5 | 01-11-2026 | El flujo en vivo en la ventana de la carga manual (2) y en «Stack y evidencia» (4, D-412, D-413) |
| 3.6 | 01-11-2026 | Una sola clave, la del Autor, y cada acción comprobada en el servidor; las recargas de la app conservan la vista del Autor (7, D-421, D-427) |
| 3.7 | 01-11-2026 | Abrir o imprimir un documento conserva la vista también en Streamlit Community Cloud, que carga la página dos veces (7, D-428) |
| 3.8 | 01-11-2026 | Toda recarga de la pestaña conserva la vista, también F5 y el enlace del aviso «Acción requerida»; solo una pestaña nueva la pide (7, D-430) |
