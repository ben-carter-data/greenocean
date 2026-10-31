# Informe de calidad N° 7

| | |
|---|---|
| **Fecha** | 2026-10-31 04:06 UTC |
| **Semana de datos** | 2026-10-26 |
| **Código evaluado** | a6b22af |
| **Informe anterior** | N° 6 |

Autoevaluación automática: 10 de 12 indicadores medidos están dentro de lo aceptable; 2 no conformidades. Los aceptables son los de `metas.json` al crearse el informe; los indicadores de datos van en modo aviso hasta que el autor apruebe que bloqueen la publicación.

| Indicador | Tipo | Falla | Aceptable | Estado | Lectura |
|---|---|---|---|---|---|
| Pruebas que fallan | codigo | 0,53 % | 0 % | Crítico | Supera lo aceptable por mucho: es crítico. Corregir la causa antes de publicar; nunca saltar la prueba. |
| Cobertura total | codigo | 5,50 % | 10 % | Cumple | Dentro de lo aceptable: no afecta. |
| Cobertura del módulo más bajo | codigo | 22,70 % | 30 % | Cumple | Dentro de lo aceptable: no afecta. |
| Avisos de Ruff (E, F y W; el largo de línea, aparte) | codigo | 0 | 0 | Cumple | Dentro de lo aceptable: no afecta. |
| Errores de mypy | codigo | 0 | 0 | Cumple | Dentro de lo aceptable: no afecta. |
| Hallazgos altos de Bandit | codigo | 0 | 0 | Cumple | Dentro de lo aceptable: no afecta. |
| Vulnerabilidades en dependencias | codigo | 0 | 0 | Cumple | Dentro de lo aceptable: no afecta. |
| Posibles secretos sin revisar | codigo | 0 | 0 | Cumple | Dentro de lo aceptable: no afecta. |
| Pruebas de datos dbt superadas | datos | 0 % | 0 % | Cumple | Dentro de lo aceptable: no afecta. |
| Precios con comparación válida | datos | 16,70 % | 10 % | Urgente | Supera lo aceptable por poco: necesita atención. Ver si falta una región o un canal entero; si la causa es la fuente, registrarla como incidente externo. Indicador de datos en modo aviso: todavía no bloquea la publicación. |
| Filas rechazadas | datos | 0,01 % | 1 % | Cumple | Dentro de lo aceptable: no afecta. |
| Días desde la última carga | datos | 0 días | 8 días | Cumple | Dentro de lo aceptable: no afecta. |

Cada informe se guarda en `docs/calidad/informes/` y no se edita: un error se corrige en el informe siguiente.
