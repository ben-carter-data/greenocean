# Informe de calidad N° 6

| | |
|---|---|
| **Fecha** | 2026-10-30 23:18 UTC |
| **Semana de datos** | 2026-10-12 |
| **Código evaluado** | 5f6ca81 |
| **Informe anterior** | N° 5 |

Autoevaluación automática: 9 de 12 indicadores medidos están dentro de lo aceptable; 3 no conformidades. Los aceptables son los de `metas.json` al crearse el informe; los indicadores de datos van en modo aviso hasta que el autor apruebe que bloqueen la publicación.

| Indicador | Tipo | Falla | Aceptable | Estado | Lectura |
|---|---|---|---|---|---|
| Pruebas que fallan | codigo | 1,24 % | 0 % | Crítico | Supera lo aceptable por mucho: es crítico. Corregir la causa antes de publicar; nunca saltar la prueba. |
| Cobertura total | codigo | 5,60 % | 10 % | Cumple | Dentro de lo aceptable: no afecta. |
| Cobertura del módulo más bajo | codigo | 55,60 % | 30 % | Crítico | Supera lo aceptable por mucho: es crítico. Probar primero ese módulo. |
| Avisos de Ruff (E, F y W; el largo de línea, aparte) | codigo | 0 | 0 | Cumple | Dentro de lo aceptable: no afecta. |
| Errores de mypy | codigo | 0 | 0 | Cumple | Dentro de lo aceptable: no afecta. |
| Hallazgos altos de Bandit | codigo | 0 | 0 | Cumple | Dentro de lo aceptable: no afecta. |
| Vulnerabilidades en dependencias | codigo | 0 | 0 | Cumple | Dentro de lo aceptable: no afecta. |
| Posibles secretos sin revisar | codigo | 0 | 0 | Cumple | Dentro de lo aceptable: no afecta. |
| Pruebas de datos dbt superadas | datos | 0 % | 0 % | Cumple | Dentro de lo aceptable: no afecta. |
| Precios con comparación válida | datos | 6,90 % | 10 % | Cumple | Dentro de lo aceptable: no afecta. |
| Filas rechazadas | datos | 0,01 % | 1 % | Cumple | Dentro de lo aceptable: no afecta. |
| Días desde la última carga | datos | 10 días | 8 días | Urgente | Supera lo aceptable por poco: necesita atención. Revisar la ejecución del workflow semanal; si la fuente se retrasó, registrarlo como incidente externo. Indicador de datos en modo aviso: todavía no bloquea la publicación. |

Cada informe se guarda en `docs/calidad/informes/` y no se edita: un error se corrige en el informe siguiente.
