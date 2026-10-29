# Calidad de GreenOcean

Dos calidades, medidas con herramientas reales y juzgadas contra un aceptable fijado por el autor:

- **Los datos que publicamos:** pruebas de dbt superadas, precios con comparación válida, filas rechazadas y días desde la última carga.
- **El código que los trata:** pruebas que fallan, cobertura total y del módulo más bajo, Ruff, mypy, hallazgos altos de Bandit, vulnerabilidades de pip-audit y posibles secretos.

Las fuentes externas (ODEPA, INE) no se miden: si una falla o se retrasa, se registra como incidente externo.

## Los archivos

| Archivo | Qué contiene | Quién lo cambia |
|---|---|---|
| `metas.json` | Los 12 indicadores: aceptable, meta, margen crítico, qué mide, por qué importa, cómo se mide, acción y frecuencia | el autor |
| `politica.json` | Los textos fijos de los informes, las plantillas de los insights y el modo de los indicadores de datos | el autor |
| `informes/informe-NNN.json` | Un informe por medición, congelado: no se edita, un error se corrige en el siguiente | el workflow «calidad», una vez |
| `medicion.json` | La última medición, de la que sale el siguiente informe | el workflow «calidad» |
| `no_conformidades.json` | Cada indicador fuera de su aceptable, con su causa; la acción y el estado los escribe el autor | el autor |
| `plan_mitigacion.json` | Las fallas previstas y reales, su detección, su causa, la contención y la acción correctiva | el autor |
| `incidentes_externos.json` | Incidentes de una fuente o de un tercero, y las respuestas por defecto | el autor |
| `INFORME.md` | El último informe, en texto | el workflow «calidad» |
| `linea_base.json`, `historial.json`, `rubrica.json` | Registros de las mediciones anteriores y de la rúbrica ISO en borrador; ya no se muestran | — |

## Cómo se lee un indicador

- **Aceptable:** lo peor que se tolera. **Meta:** lo que se aspira. **Falla:** el valor leído contra el aceptable.
- **Estados:** cumple · aviso (peor que la meta, dentro de lo aceptable) · urgente (pasa lo aceptable por poco) · crítico (por mucho, según el margen del indicador).
- Un indicador de código fuera de su aceptable hace fallar el CI. Los de datos están en modo aviso hasta que el autor apruebe que bloqueen la publicación.

## Cómo reproducir

- `python scripts/medir_calidad.py --tools <entorno>/bin` escribe `medicion.json`.
- `python scripts/verificar_calidad.py` la compara con los aceptables.
- `python scripts/informe_calidad.py` crea el informe siguiente.

Las herramientas (Ruff, mypy, Bandit, pip-audit, detect-secrets) viven en un entorno aparte; sus versiones están en `.github/workflows/calidad.yml`.
