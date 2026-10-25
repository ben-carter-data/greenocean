# Manual de operación (runbook)

| Campo | Valor |
|---|---|
| Proyecto | GreenOcean |
| Tipo de documento | Manual de operación (runbook) |
| Versión | 2.0 |
| Fecha | 25-10-2026 |
| Estado | Vigente |
| Responsable | El autor |
| Propósito | Indicar qué ocurre de forma automática, qué se revisa y cuándo, y qué hacer ante cada falla. |
| Audiencia | Operación del proyecto, también sin formación técnica. |
| Documentos relacionados | [Documento de arquitectura de software (SAD)](SAD.md) · [Plan de pruebas de seguridad](SEGURIDAD.md) · [Glosario](GLOSARIO.md) |

## Índice

1. [Qué ocurre automáticamente](#1-qué-ocurre-automáticamente)
2. [Qué se revisa y cuándo](#2-qué-se-revisa-y-cuándo)
3. [Fallas de la carga semanal](#3-fallas-de-la-carga-semanal)
4. [Fallas del panel publicado](#4-fallas-del-panel-publicado)
5. [Recuperación](#5-recuperación)
6. [Tareas periódicas](#6-tareas-periódicas)
7. [Acceso del autor y administración](#7-acceso-del-autor-y-administración)
8. [Límites conocidos](#8-límites-conocidos)
9. [Glosario](#9-glosario)
10. [Historial de versiones](#10-historial-de-versiones)

## 1. Qué ocurre automáticamente

El job semanal (`.github/workflows/semanal.yml`) corre cada martes a las 12:00 UTC: las 09:00 en el horario de verano de Chile y las 08:00 en el de invierno. Descarga las fuentes, construye y prueba la base, la publica en el release «base-actual» y crea el informe semanal. La secuencia completa, paso a paso, está en la [vista de ejecución del SAD](SAD.md#6-vista-de-ejecución).

También se puede lanzar a mano: desde «Centro de operación», con el botón «Ejecutar pipeline ahora» (requiere la clave de control), o desde la página del workflow en GitHub.

Si un paso falla, los siguientes no se ejecutan y la base servida no cambia ([ADR-11 · Publicar solo si pasan las pruebas](ADR.md#adr-11--publicar-solo-si-pasan-las-pruebas)).

## 2. Qué se revisa y cuándo

| Cuándo | Qué se revisa | Dónde |
|---|---|---|
| Cada martes, después de las 12:00 UTC | Que la ejecución terminó en verde | Pestaña «Operación» de «Centro de operación», o el correo de GitHub si falló |
| Cada martes | Que existe el issue «Informe semanal AAAA-MM-DD» | Issues del repositorio |
| Ante una duda sobre las cifras | El veredicto de calidad y los controles de auditoría | «Calidad y auditoría» |

## 3. Fallas de la carga semanal

Cada fila corresponde a un paso del workflow, con su nombre en `semanal.yml`. El aviso llega al autor por el correo «Run failed: semanal» de GitHub, y el paso fallido aparece en rojo en «Centro de operación». La tabla `etl_run` registra solo las cargas publicadas: el mensaje de una falla se lee en el log del paso.

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

## 4. Fallas del panel publicado

| Síntoma | Causa probable | Acción |
|---|---|---|
| Después de un push, una página muestra `AttributeError` | Streamlit Cloud combinó archivos nuevos con otros que tenía en memoria (ocurrió el 12-10-2026) | En el panel, «Manage app» → ⋮ → **Reboot**, y esperar uno o dos minutos |
| «Centro de operación» indica «GitHub no respondió (…)» | Sin token, GitHub permite 60 consultas por hora, compartidas por las apps del mismo servidor | Ninguna: el panel muestra la última respuesta guardada y vuelve a consultar cada 5 minutos; con el token configurado, el límite sube |
| El panel informa que no tiene la base servida | No pudo descargarla del release al arrancar | Verificar que el release «base-actual» existe; el panel la descarga en la siguiente visita |
| El botón «Ejecutar pipeline ahora» indica que falta el token | El token del panel venció o no está configurado | Crear un token con permiso para lanzar workflows de este repositorio y guardarlo como `GITHUB_TOKEN` en los secretos de la app en Streamlit |

## 5. Recuperación

| Situación | Procedimiento |
|---|---|
| Una carga falló | Corregir la causa según la sección 3 y volver a lanzar el job; mientras tanto, el panel muestra la última carga válida |
| El release perdió su archivo | Reconstruir la base en un equipo con los datos (`python etl/pipeline.py --local`), verificar que la suite pasa y subir el archivo al release «base-actual» junto con su puntero (`python bi/served_database.py --pointer`) |
| Una copia nueva del repositorio no tiene la base | `python bi/served_database.py` descarga la base de la última carga y verifica su huella |

## 6. Tareas periódicas

| Frecuencia | Tarea |
|---|---|
| Cada martes | Revisar «Centro de operación» o el correo; si está en verde, no hay nada que hacer |
| Cada enero | Agregar a `agent/input.csv` las dos líneas del año nuevo (mayorista y consumidor), con la URL que publica ODEPA en la página de cada conjunto de datos |
| Periódicamente | Copiar `agent/downloads` a otro disco: los CSV no se versionan ([ADR-04 · No subir los datos crudos al repositorio](ADR.md#adr-04--no-subir-los-datos-crudos-al-repositorio)) y la caché de GitHub se borra si no se usa en 7 días |
| Antes de su vencimiento | Renovar el token de GitHub del panel; el panel avisa cuando faltan menos de 14 días |

## 7. Acceso del autor y administración

En «Centro de operación», «Acceso del autor» pide la clave de control (secreto `CONTROL_CODE` del panel) y se abre con Enter. Con la clave correcta aparecen el botón «Ejecutar pipeline ahora», el aviso del vencimiento del token y los enlaces de administración (tokens de GitHub, ejecuciones y administración de la app en Streamlit). Sin el secreto configurado, por ejemplo en una copia local, el acceso permanece cerrado.

La clave evita ejecuciones accidentales; no es la barrera principal. Lo que protege el proyecto es el inicio de sesión del autor en GitHub y en Streamlit (con verificación en dos pasos) y un token con los permisos mínimos. No hay límite de intentos de la clave: es un riesgo aceptado, descrito en el [Plan de pruebas de seguridad](SEGURIDAD.md). El panel nunca muestra el token ni una parte de él.

## 8. Límites conocidos

| Límite | Valor | Fuente |
|---|---|---|
| Tamaño máximo de un archivo de release | 2 GB; la base servida pesa unos 14 MB | Documentación de GitHub sobre releases, consultada el 24-10-2026 |
| Caché de GitHub Actions | Se borra si no se usa en 7 días; esa semana el job descarga todos los años | Documentación de GitHub Actions, consultada el 24-10-2026 |
| Consultas a la API de GitHub sin token | 60 por hora | Documentación de la API de GitHub |
| Arquitectura en la nube | No se adopta mientras los datos sean públicos, semanales y pequeños | [ADR-31 · No usar un data warehouse en la nube](ADR.md#adr-31--no-usar-un-data-warehouse-en-la-nube) y [Plan de capacidad y escalabilidad](ESCALABILIDAD.md) |

## 9. Glosario

Las siglas y los términos de este documento se definen en el [Glosario](GLOSARIO.md).

## 10. Historial de versiones

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
