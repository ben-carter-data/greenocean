# Revisión GreenOcean · 15-10-2026

La aplicación se revisó localmente en `http://127.0.0.1:8612`. Las imágenes son
capturas reales de la interfaz; se recortó únicamente la barra del navegador en
las capturas de escritorio. Las capturas de pantalla estrecha muestran una
ventana de aproximadamente 574 px CSS; la captura móvil clara usa 390 × 844 px.

| Vista | Captura | Qué permite comprobar |
| --- | --- | --- |
| Dashboard Corporativo | [Ver](dashboard-corporativo.png) | Jerarquía y precios por producto |
| Dashboard Blue Light | [Ver](dashboard-blue-light.png) | Contraste en tema claro alternativo |
| Dashboard Dark Grey | [Ver](dashboard-dark-grey.png) | Contraste en gris oscuro |
| Dashboard Vantablack | [Ver](dashboard-vantablack.png) | Contraste en negro |
| Ranking y detalle Dark Grey | [Ver](dashboard-dark-grey-detalle.png) | Producto, mercado, precios, cambio y curva |
| Dashboard móvil claro | [Ver](dashboard-movil-claro.png) | Disposición a 390 × 844 px |
| Dashboard estrecho oscuro | [Ver](dashboard-estrecho-oscuro.png) | Cabecera y filtros adaptados |
| Tabla estrecha al desplazar | [Ver](dashboard-estrecho-tabla.png) | Cabecera fija opaca y tabla contenida |
| Datos del producto | [Ver](datos-producto.png) | Filtros heredados, periodo, tabla y estado de comparación |
| Histórico | [Ver](historico.png) | Evolución antes del análisis estacional |
| Pipeline | [Inicio anterior](pipeline.png) · [recorridos](pipeline-recorridos.png) | El mini recorrido ODEPA → Panel vuelve a encabezar la página con cifras y estados reales |
| Diagramas originales recuperados | [Ver](pipeline-diagramas-restaurados.png) | Debajo del mini recorrido siguen el diagrama por capas y la arquitectura por plataformas |
| Modelo | [Ver](modelo.png) | Qué representa cada registro antes de las relaciones |
| DevOps | [Ver](devops.png) | Responsabilidades y diagrama técnico |

Comprobaciones de datos: en la semana del 05-10-2026, Manzana · Cripps Pink ·
Calibre 80, Mayorista, promedio nacional por kilo muestra $1.000 el 28-09-2026
y $1.556 el 05-10-2026; el cambio es +$556 y +55,6 % antes del redondeo de
presentación. La comparación usa exactamente siete días antes. Los ensayos
automatizados verifican otros precios nacionales y regionales contra consultas
independientes, semanas anteriores ausentes, precio anterior cero, orden Top N,
selección y conservación del contexto al entrar en Datos. La media nacional
incluye las regiones disponibles en cada semana; 230 comparaciones de la vista
capturada cambiaron de cobertura regional. Ese número depende de la base local.

Se probaron los cuatro temas en la interfaz y la vista estrecha clara y oscura.
La tabla HTML del Dashboard mantiene su anchura legible dentro de un contenedor
con desplazamiento horizontal. En la pantalla estrecha verificada, la cabecera
fija ya tiene fondo opaco y no deja ver texto por detrás. La inspección visual
se limita a los tamaños y estados capturados; no es una certificación de todos
los dispositivos.

Limitación visible: la cuadrícula nativa de Streamlit puede mostrar `None` en
una celda numérica sin dato, aunque el formato use «Sin comparación». La primera
columna aclara ese estado y los números se conservan como números para ordenar
y descargar con precisión. No se reemplazó un faltante por cero.

Validación automatizada de esta revisión: `154 passed` en
`tests/test_home_mockup.py`, `tests/test_dashboard.py`,
`tests/test_architecture.py` y `tests/test_data_browser.py`. Compilación de los
módulos modificados y `git diff --check` correctos. No se modificaron los datos
fuente, la base, el ETL ni las fórmulas SQL canónicas.
