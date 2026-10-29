# Informe de calidad N° 4

| | |
|---|---|
| **Fecha** | 2026-10-27 11:37 UTC |
| **Semana de datos** | 2026-10-12 |
| **Código evaluado** | b015e3a |
| **Informe anterior** | N° 3 |

Autoevaluación automática: 10 de 11 indicadores medidos están dentro de lo aceptable; 1 no conformidades. Los aceptables son los de `metas.json` al crearse el informe; los indicadores de datos van en modo aviso hasta que el autor apruebe que bloqueen la publicación.

| Indicador | Tipo | Falla | Aceptable | Estado | Lectura |
|---|---|---|---|---|---|
| Pruebas que fallan | codigo | 0,50 % | 0 % | Crítico | Supera lo aceptable por mucho: es crítico. Corregir la causa antes de publicar; nunca saltar la prueba. |
| Cobertura total | codigo | 5,70 % | 10 % | Cumple | Dentro de lo aceptable: no afecta. |
| Cobertura del módulo más bajo | codigo | 16,90 % | 30 % | Cumple | Dentro de lo aceptable: no afecta. |
| Avisos de Ruff (E, F y W; el largo de línea, aparte) | codigo | 0 | 0 | Cumple | Dentro de lo aceptable: no afecta. |
| Errores de mypy | codigo | 0 | 0 | Cumple | Dentro de lo aceptable: no afecta. |
| Hallazgos altos de Bandit | codigo | 0 | 0 | Cumple | Dentro de lo aceptable: no afecta. |
| Vulnerabilidades en dependencias | codigo | 0 | 0 | Cumple | Dentro de lo aceptable: no afecta. |
| Posibles secretos sin revisar | codigo | 0 | 0 | Cumple | Dentro de lo aceptable: no afecta. |
| Pruebas de datos dbt superadas | datos | 0 % | 0 % | Cumple | Dentro de lo aceptable: no afecta. |
| Precios con comparación válida | datos | 6,90 % | 10 % | Cumple | Dentro de lo aceptable: no afecta. |
| Filas rechazadas | datos | — | — | Sin medición | Sin medición en este informe: no se evalúa; no se inventa un valor. |
| Días desde la última carga | datos | 7 días | 8 días | Cumple | Dentro de lo aceptable: no afecta. |

Cada informe se guarda en `docs/calidad/informes/` y no se edita: un error se corrige en el informe siguiente.
