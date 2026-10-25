# Plan de capacidad y escalabilidad

| Campo | Valor |
|---|---|
| Proyecto | GreenOcean |
| Tipo de documento | Plan de capacidad y escalabilidad |
| Versión | 2.0 |
| Fecha | 25-10-2026 |
| Estado | Vigente |
| Responsable | El autor |
| Propósito | Medir la capacidad actual, anticipar qué cede primero si el sistema crece y fijar los umbrales que justificarían cambiar la arquitectura. |
| Audiencia | Arquitectura, gerencia y operación. |
| Documentos relacionados | [Documento de arquitectura de software (SAD)](SAD.md) · [Registros de decisiones de arquitectura (ADR)](ADR.md) · [Glosario](GLOSARIO.md) |

## Índice

1. [Capacidad actual](#1-capacidad-actual)
2. [Qué cede primero](#2-qué-cede-primero)
3. [Opciones de crecimiento](#3-opciones-de-crecimiento)
4. [Cuándo se justificaría una nube](#4-cuándo-se-justificaría-una-nube)
5. [Glosario](#5-glosario)
6. [Historial de versiones](#6-historial-de-versiones)

## 1. Capacidad actual

| Medida | Valor | Origen |
|---|---|---|
| Base servida | Unos 14 MB en la base servida | Tamaño de `etl/datos.duckdb` |
| Datos | Volumen y cobertura de la última carga | [PRD, sección 3](PRD.md#3-alcance) |
| Frecuencia | Una carga por semana | [RF-01](PRD.md#6-requisitos) |
| Usuarios | Un panel público de solo lectura | [PRD, sección 4](PRD.md#4-usuarios-y-casos-de-uso) |

## 2. Qué cede primero

| Límite | Situación actual | Respuesta prevista |
|---|---|---|
| Tamaño de la base servida | Una sola copia en un release, reemplazada por cada carga ([ADR-35](ADR.md#adr-35--publicar-la-base-servida-en-un-release-que-cada-carga-reemplaza)); el historial de Git ya no crece con los datos | Un archivo de release admite hasta 2 GB; mucho antes convendría la opción de la sección 4 |
| Duración de la carga | Cada carga rehace la historia completa desde 2022 ([ADR-10](ADR.md#adr-10--reconstruir-todo-en-cada-carga)) y tarda un poco más cada año | Cargas incrementales cuando la duración lo justifique |
| Visitantes simultáneos | Una aplicación gratuita de Streamlit que lee un archivo pequeño en solo lectura | Si varios equipos lo usaran a diario, el plan gratuito sería insuficiente: es uno de los umbrales de la sección 4 |

## 3. Opciones de crecimiento

Una fuente nueva se incorpora como las actuales: una carpeta en el bronce y sus modelos de dbt, sin modificar los existentes.

| Extensión | Estado | Cómo se incorporaría |
|---|---|---|
| Clima por región y semana | Prevista; fuente oficial por definir | Un staging y un mart por semana y región, junto a las alertas de precio, sin afirmar que el clima cause un precio |
| Data warehouse en la nube | No adoptado ([ADR-31](ADR.md#adr-31--no-usar-un-data-warehouse-en-la-nube)) | Un destino nuevo en la configuración de dbt, con los mismos modelos y la misma auditoría |

## 4. Cuándo se justificaría una nube

Con datos públicos, semanales y pequeños, leídos por un solo panel, un data warehouse en la nube agregaría costo, secretos y riesgos de vencimiento sin beneficio ([ADR-31](ADR.md#adr-31--no-usar-un-data-warehouse-en-la-nube)). Se justificaría si una empresa sumara sus propios datos:

| Criterio | Hoy | Umbral |
|---|---|---|
| Volumen | Unos 14 MB | Varios GB: ventas por tienda y día, costos, inventario |
| Usuarios | Un panel de solo lectura | Varios equipos o herramientas de BI sobre los mismos datos |
| Acceso | Público | Permisos por persona o datos sensibles |
| Frescura | Semanal | Varias cargas al día o tiempo real |

## 5. Glosario

Las siglas y los términos de este documento se definen en el [Glosario](GLOSARIO.md).

## 6. Historial de versiones

| Versión | Fecha | Cambios |
|---|---|---|
| 1.0 | 21-10-2026 | Primera versión, como sección del registro de decisiones (D-210) |
| 1.1 | 24-10-2026 | Qué cede primero y qué se agregaría (D-269); base servida en un release (D-270) |
| 2.0 | 25-10-2026 | Documento propio con capacidad actual, límites, opciones y umbrales (D-279, documentación profesional) |
