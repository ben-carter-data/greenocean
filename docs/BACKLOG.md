# Backlog

Orden de arriba hacia abajo. Cada tarea indica cuándo se considera terminada. Las referencias RN, K y D apuntan a `DISENO.md` y `DECISIONES.md`.

## Hito 1 · Datos crudos

| ID | Tarea | Terminado cuando |
|---|---|---|
| T-01 | Crear repositorio público con estructura, `requirements.txt`, licencia y README | La estructura coincide con el README y `pytest` corre sin pruebas |
| T-02 | `input.csv` con fuente, año y URL de los recursos 2026 | Dos filas, una por fuente |
| T-03 | `agent.py`: `load_input_resources`, `download_all_resources`, `download_file`, `validate_downloaded_file`, log | Descarga los dos archivos 2026 y deja un log con una línea por recurso |
| T-04 | Reintentos y umbrales | Con una URL inválida el agente reintenta, registra la falla y termina con error |
| T-05 | Validación de encabezado | Con un archivo de columnas alteradas registra `UNEXPECTED_HEADER` y no carga |
| T-06 | Tablas `raw_wholesale` y `raw_consumer` con año y hash | Filas en la tabla = filas del CSV |
| T-06b | Workflow de pruebas: `pytest` corre en cada cambio subido al repositorio, con su sello de estado en el README | Un cambio que rompe una prueba deja el sello en rojo |

## Hito 2 · ETL y reglas

| ID | Tarea | Terminado cuando |
|---|---|---|
| T-07 | `schema.sql` con dimensiones, `precio_semanal`, `ejecucion`, `rechazo` | La base se crea desde cero con un comando |
| T-08 | `clean()`: RN-01, RN-02, RN-13 | Pruebas con casos de coma decimal, producto con y sin `\|` |
| T-09 | Validación RN-11 con tabla de rechazos | leídas = cargadas + rechazadas |
| T-10 | Unidades RN-03, RN-04, RN-05 | Prueba con las 147 unidades del archivo 2026; informe de cuántas filas quedan en kilo, en unidad y sin convertir |
| T-11 | Agregación semanal RN-07, RN-08, RN-09 | Un valor semanal de tomate en la RM se reproduce a mano desde el CSV |
| T-12 | Atípicos RN-12 | Las filas marcadas aparecen en la vista de calidad; umbral revisado con los datos |
| T-13 | Carga idempotente RN-14 | Dos ejecuciones seguidas dejan el mismo número de filas |
| T-14 | Medir K7 (cobertura del cruce) | Cifra documentada en DISENO.md, sección 10 |
| T-14b | Controles de calidad en cada carga: número de filas dentro de un rango esperado, semanas sin huecos, regiones y canales conocidos | Un archivo con la mitad de las filas hace fallar la carga con un mensaje claro |

## Hito 3 · Indicadores y panel mínimo

| ID | Tarea | Terminado cuando |
|---|---|---|
| T-15 | `queries.sql`: K1, K2, K3, K4 | Cada consulta devuelve resultados para los 5 productos de la prueba |
| T-16 | Panel: selector de perfil | Cambiar de perfil cambia las vistas visibles |
| T-17 | Vista Márgenes (K1) | Filtro por producto, región y canal; gráfico histórico |
| T-18 | Vista Canales y regiones (K2, K3) | Incluye los grupos sin precio mayorista |
| T-19 | Vista Estacionalidad (K4) | Curva por producto |
| T-20 | Vista Calidad de datos (K7, K8, última ejecución) | Muestra motivos de rechazo |
| T-21 | Atribución a ODEPA visible en el panel | Pie de página en todas las vistas |

## Hito 4 · Automatización y publicación

| ID | Tarea | Terminado cuando |
|---|---|---|
| T-22 | Workflow semanal: agente + ETL + guardar base | Una ejecución manual termina en verde y actualiza la base |
| T-23 | El job falla de forma visible ante un error | Una falla forzada deja el job en rojo y no modifica la base |
| T-24 | Publicar el panel | Enlace público funcionando |
| T-25 | Enlace del panel en el README y en el CV | Hecho |
| T-25b | K6 alertas con los datos disponibles y vista en el panel | Lista de productos fuera de rango en la semana |
| T-25c | Informe semanal automático: el job publica un resumen en el repositorio (issue) con las alertas de la semana y el estado de la carga | Aparece un informe nuevo tras cada ejecución, sin intervención |
| T-25d | Aviso de falla: si el job falla, GitHub notifica por correo al autor | Una falla forzada genera el aviso |
| T-26 | Observar cuatro ejecuciones semanales | Cuatro semanas en verde sin intervención |

## Hito 5 · Histórico e indicadores avanzados

| ID | Tarea | Terminado cuando |
|---|---|---|
| T-27 | Validar formato de los archivos 2022-2025 | Lista de diferencias de columnas por año |
| T-28 | Cargar histórico | K4 calculado con varios años |
| T-29 | K5 rezago, con nota de que es descriptivo | Visible solo con 26 semanas o más |
| T-30 | Recalibrar el umbral de K6 con el histórico | Umbral documentado con su justificación |
| T-31 | Perfil gerencia: resumen ejecutivo | Una pantalla, sin filtros obligatorios |

## Hito 6 · Hallazgos

| ID | Tarea | Terminado cuando |
|---|---|---|
| T-31b | Explorar los datos limpios y elegir de uno a tres hallazgos | Cada hallazgo se dice en una frase con su cifra |
| T-31c | Verificar cada hallazgo: misma variedad y calidad, suficientes semanas, sin atípicos, y revisión a mano de una muestra | La consulta SQL que lo produce está en el repositorio y cualquiera la puede repetir |
| T-31d | Publicar los hallazgos en el README y en el resumen del panel, con sus límites | Sección «Hallazgos» visible |
| T-31e | Opcional: mostrar el panel a una persona de compras o pricing y registrar qué cambió por su comentario | Entrada nueva en DECISIONES.md |

## Mejoras

| ID | Tarea |
|---|---|
| T-32 | Ajuste por inflación con IPC |
| T-33 | Tabla de equivalencias para atados y docenas |
| T-34 | Perfil consumidor |
| T-35 | Tercera fuente: comercio exterior de ODEPA |
| T-36 | Migración opcional a PostgreSQL gestionado |
| T-37 | Tabla de equivalencia de calidades entre fuentes (papa: «Primera» contra «1a (cosecha)», etc.), ver D-030 |
| T-38 | Panel con aspecto de producto: modo oscuro y claro beige, tarjetas, cifras clave y gráficos con colores fijos por canal (D-037) |
| T-39 | Centro de control: estado e historial del robot y botón «Ejecutar ahora» con código de acceso (D-038) |
| T-40 | Página «Pipeline»: recorrido de los datos con el estado real de cada paso (D-039) |
| T-41 | Explicaciones al pasar el mouse en cada gráfico y página «El proyecto» con la idea de negocio (D-040) |
| T-42 | Página «Consultas»: constructor de consultas por clics (vista, agrupación, filtros y medida), con tabla, gráfico, CSV y «Ver SQL» (D-041) |
