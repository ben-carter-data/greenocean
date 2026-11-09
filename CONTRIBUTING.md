# Cómo contribuir a GreenOcean

## Mensajes de commit

Desde D-323, los commits siguen [Conventional Commits](https://www.conventionalcommits.org/es/v1.0.0/), en español, con la decisión entre paréntesis al final:

`tipo(alcance): descripción breve (D-nnn)`

| Tipo | Para qué |
|---|---|
| `feat` | Una función nueva del panel o del pipeline |
| `fix` | Una corrección |
| `refactor` | Un cambio de código que no cambia el comportamiento |
| `test` | Pruebas nuevas o corregidas |
| `docs` | Documentos |
| `style` | Formato, sin cambio de lógica |
| `perf` | Rendimiento |
| `ci` | Workflows de GitHub Actions |
| `chore` | Mantenimiento: dependencias, mediciones, configuración |

Ejemplos: `feat(panel): botón para ampliar la tabla de productos (D-317)`, `fix(accesibilidad): contraste de las etiquetas (D-323)`.

Los commits anteriores a D-323 usan el formato «D-nnn: …» y no se reescriben.

## Antes de cada commit

`pip install pre-commit && pre-commit install` activa Ruff (estilo y formato) y la búsqueda de secretos en cada commit. Cada cambio de comportamiento lleva su entrada en `docs/DECISIONES.md` y sus pruebas en verde.

## Versiones de Python

| Uso | Versiones |
|---|---|
| Pipeline con dbt (`requirements-pipeline.txt`) | 3.12 en el CI de cada push; 3.11 en la carga semanal |
| Panel y pruebas (`requirements.txt`) | 3.12 en el CI; también se usa en 3.14 en local |

## Antes de subir

`python scripts/antes_de_subir.py` revisa sobre el commit que se va a subir lo mismo que el CI, en tres o cuatro minutos: Ruff, mypy, el escáner de secretos y Bandit (en las versiones de `calidad.yml`) y todas las pruebas en una copia aparte, con la base publicada y la hora UTC (D-570). `python scripts/antes_de_subir.py --instalar` lo deja como hook `pre-push` de git: cada `git push` lo corre y no sube si algo está en rojo. `git push --no-verify` lo salta, cuando el autor lo decide.

## Calidad

`python scripts/medir_calidad.py --tools <entorno>/bin --node-path <node_modules>` mide los indicadores y `python scripts/verificar_calidad.py` los compara con `docs/calidad/metas.json`. El workflow `calidad` hace lo mismo en cada push.
