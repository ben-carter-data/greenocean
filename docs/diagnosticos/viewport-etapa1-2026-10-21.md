# Etapa 1 · El contenido cabe por construcción

D-226 · 21 de octubre de 2026.

**138/138 comprobaciones aprobadas.** Las 15 páginas principales, ocho variantes, tres tamaños y dos temas. Ningún `stMain` tiene desplazamiento vertical; zoom calculado 1. La auditoría no encontró texto recortado, superpuesto ni por debajo de 11 px. Los iframes de contenido también caben en su celda. Una segunda ejecución de 12 casos verificó además que los rótulos del Centro de operación no colisionan con sus íconos.

**640 pruebas Python aprobadas, 3 omitidas** por fuentes crudas no incluidas en el checkout. Las pruebas de cifras y PDF siguen aprobadas.

## Medidas por página

Cada celda muestra `stMain.scrollHeight / stMain.clientHeight`, en píxeles. El resultado es el mismo en **Vantablack y Blue Light**.

| Página | 1440 × 700 | 1440 × 900 | 1920 × 1080 |
|---|---:|---:|---:|
| Resumen semanal | 700 / 700 | 900 / 900 | 1080 / 1080 |
| Precios e inflación | 700 / 700 | 900 / 900 | 1080 / 1080 |
| Pipeline y linaje | 700 / 700 | 900 / 900 | 1080 / 1080 |
| Modelo de datos | 700 / 700 | 900 / 900 | 1080 / 1080 |
| Calidad y auditoría | 700 / 700 | 900 / 900 | 1080 / 1080 |
| Consultas SQL | 700 / 700 | 900 / 900 | 1080 / 1080 |
| SAD · Arquitectura | 700 / 700 | 900 / 900 | 1080 / 1080 |
| Mapa de seguridad | 700 / 700 | 900 / 900 | 1080 / 1080 |
| Plan de pruebas de seguridad | 700 / 700 | 900 / 900 | 1080 / 1080 |
| Stack y evidencia | 700 / 700 | 900 / 900 | 1080 / 1080 |
| PRD · Requisitos del producto | 700 / 700 | 900 / 900 | 1080 / 1080 |
| ADR · Decisiones de arquitectura | 700 / 700 | 900 / 900 | 1080 / 1080 |
| Escalabilidad | 700 / 700 | 900 / 900 | 1080 / 1080 |
| GitHub | 700 / 700 | 900 / 900 | 1080 / 1080 |
| Centro de operación | 700 / 700 | 900 / 900 | 1080 / 1080 |

## Variantes y desplazamiento interno

También pasan los seis escenarios de tamaño y tema de cada variante:

- Precios sin inflación y una familia ampliada.
- Linaje dbt.
- Modelo estrella, Entidad-relación y Cruces entre bases.
- SQL con una consulta de más de 70 líneas y un resultado de 5.000 filas.
- Plataforma del Centro de operación.

En seis pruebas de interacción, la tabla de productos llega a su última fila y el índice del SAD desplaza el documento. En todos los casos, `stMain.scrollTop` permanece en cero. El código SQL, las listas de modelos y columnas y la documentación tienen sus propios paneles con desplazamiento.

## Qué cambió

La ventana contiene una grilla con cabecera, una fila flexible para la página y pie. Se retiraron `FIT_SCREEN_SCRIPT`, `TILE_HEIGHT` y los altos fijos de los iframes. Los gráficos y el estudio SQL reciben la altura de su celda.

Los diagramas densos tienen vistas resumidas legibles y conservan sus diagramas completos en paneles ampliados. El linaje mantiene todos los modelos reales y sus pruebas por capa. Los documentos conservan el texto y el PDF y tienen un índice al lado de la hoja.

El menú conserva el diseño anterior: la etapa 2 requiere otra aprobación.

## Método reproducible

Playwright y Chromium 155.0.8059.85. La ruta `/opt/pw-browsers/chromium` no existe en este Mac; se usó el Chrome instalado. No se agregaron dependencias de producción. El código se mantuvo sin cambios durante cada ejecución y las dos huellas quedan en los metadatos; la ejecución puntual reemplaza los 12 casos del Centro de operación en la matriz consolidada.

La app se abre dentro de un iframe del mismo origen, como en Cloud, cuyo padre no tiene `stMain`. Se espera a que cada página termine de renderizar y luego se cambia el tamaño. La auditoría comprueba altura, zoom, presencia de contenido, recortes, superposición y tamaño efectivo de texto SVG. Las listas y documentos se verifican considerando el recorte propio de sus paneles con desplazamiento.

Desde la raíz del repositorio, con Playwright disponible en Node:

- `VIEWPORT_VARIANTS=1 CLOUD_WRAPPER=1 node tests/viewport.cjs`
- `node tests/viewport_interactions.cjs`

El primer ejecutor admite `APP_URL`, `CHROMIUM_EXECUTABLE` y `VIEWPORT_OUTPUT`; el segundo comprueba la app local en el puerto 8511. Alcance: navegación actual y sus variantes indicadas; las direcciones históricas y los teléfonos quedan fuera de esta matriz de escritorio.

Las medidas, los metadatos y los resultados de interacción acompañan este informe. La captura de producción y la CI del commit se comprueban al publicarlo.
