# Hito 3 · Indicadores y panel mínimo

Cierre del 11-10-2026. Datos: archivos 2026 descargados ese día.

## Qué se construyó

| Tarea | Resultado |
|---|---|
| T-15 | `bi/queries.sql`: una consulta con nombre por indicador (K1, K2, K3, K4, K8) y tres para la vista de calidad |
| T-16 | `bi/dashboard.py`: selector «¿Quién consulta?» con dos perfiles de prioridad 1 |
| T-17 | Vista Márgenes (K1): filtros de grupo, producto, variedad y calidad, región y canal; margen y precios por semana |
| T-18 | Vista Canales y regiones (K2, K3): todos los grupos, con o sin precio mayorista |
| T-19 | Vista Estacionalidad (K4): curva por producto y canal |
| T-20 | Vista Calidad de datos: última ejecución, K7, K8, precios marcados y lista de atípicos |
| T-21 | Atribución a ODEPA al pie de todas las vistas |

Perfiles y vistas:

| Perfil | Vistas |
|---|---|
| Analista de pricing / compras | Márgenes, Canales y regiones, Estacionalidad |
| Equipo de datos | Calidad de datos |

## Cómo comprobarlo

1. `pytest -q` → 67 pruebas en verde. Las del panel (`tests/test_dashboard.py`) dibujan cada vista con la base real y necesitan `etl/datos.db`.
2. `streamlit run bi/dashboard.py` → se abre el panel en el navegador.
3. Cambiar «¿Quién consulta?» a «Equipo de datos»: la lista de vistas pasa a tener solo «Calidad de datos».
4. Vista Márgenes con la selección inicial (Tomate · Larga vida · Primera · $/kilo, Región Metropolitana): la tabla inferior debe mostrar los valores de «Resultados reales».
5. Comprobar una cifra sin el panel: copiar la consulta `k1_margin` de `bi/queries.sql` y ejecutarla con `sqlite3 etl/datos.db`.

## Resultados reales

| Consulta | Filas | Alcance |
|---|---|---|
| `k1_margin` | 24.169 | 36 productos de frutas y verduras |
| `k2_channel_gap` | 84.008 | 7 grupos |
| `k3_regional_index` | 128.971 | 7 grupos |
| `k4_seasonal_index` | 34.269 | 7 grupos, solo año 2026 |
| `k8_rejected_rows` | 0 | la última ejecución no rechazó filas |

Tomate Larga vida Primera, por kilo, Región Metropolitana, 41 semanas de 2026:

| Canal | Margen mediano sobre el mayorista (K1) |
|---|---|
| Feria libre | 60,1 % |
| Supermercado | 144,7 % |
| Supermercado en Línea | 147,8 % |

Mismo producto, todas las regiones, diferencial promedio contra la feria libre (K2): supermercado +62,7 %, supermercado en línea +51,0 %, mercado minorista +4,0 %.

Estas cifras son resultados de las consultas, no hallazgos publicados: la verificación de hallazgos es el hito 6 (D-018).

Productos de la prueba: K2, K3 y K4 devuelven filas para los cinco. K1 las devuelve para tomate, limón, palta y cebolla; no para la papa (D-030).

## Qué quedó pendiente

- **K1 de la papa**: sin margen por la diferencia de calidades entre fuentes (D-030, mejora T-37). El criterio de T-15 se cumple para cuatro de los cinco productos.
- **K4 con un solo año**: muestra la variación dentro de 2026. La estacionalidad se confirma con el histórico (hito 5); el panel lo dice en la vista.
- **Perfiles de gerencia y consumidor**: no están en el selector; son T-31 y T-34.
- **Panel sin publicar**: funciona en local. El enlace público es T-24 (hito 4).
- **Probado con Python 3.10 y Streamlit 1.65** en el entorno del asistente. Falta ejecutarlo en el computador del autor (Python 3.14) y en GitHub Actions (Python 3.11).
- **Nombres de región largos**: en los gráficos de barras se cortan con «…».
