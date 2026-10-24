# Etapa 10 · Qué sobraba, qué faltaba y dónde vive cada cosa

Cada documento cumple su función y ninguna otra; cada afirmación se apoya en el código o en una prueba.

| Documento | Función | Sobraba (se quitó o se movió) | Faltaba (se agregó) | Discrepancias corregidas |
|---|---|---|---|---|
| PRD | Problema, usuarios y requisitos medibles | «Visión y misión» (no es problema, usuarios ni requisitos); el diagrama de actores (pasó al SAD como contexto) | Casos de uso (D2); P-4; trazabilidad pregunta → pantalla → prueba; criterio medible y evidencia por requisito; capturas reales de hoy, una por tema | P-2 y P-3 apuntaban a «Precios e inflación», que responde otra pregunta; «Compras» decía «por canal»; la captura M-2 usaba el tema «Claro», que ya no existe |
| SAD | Arquitectura por vistas | Copias del pipeline, la plataforma y la estrella (ahora enlaza a su página) | Contenedores (C4 nivel 2); datos, despliegue y seguridad como enlaces; componentes omitidos con su motivo | El contexto mezclaba contexto y flujo de entrega; copiaba la cifra viva «665 MB» |
| ADR | Una decisión por entrada | — | Formato estándar: estado, contexto, decisión, alternativas y consecuencias, con su D-xxx | ADR-04 decía «hasta 46 MB» por CSV; el mayor pesa unos 65 MB |
| Plan de pruebas de seguridad | Procedimiento con resultado esperado | (El mapa repetido sale en la Etapa 8, tras la aprobación) | (El SOP llega en la Etapa 8) | — |
| Escalabilidad | Qué se agregaría y cuándo | — | — | Sin cambios; una prueba verifica que «Unos 14 MB» sea el tamaño real |
| MANUAL | Operación para quien no es técnico | Guías de páginas retiradas (Histórico, Contexto del precio, cabecera vieja); la recomendación de pasar a PostgreSQL, contraria a ADR-31 | Los nueve pasos reales del job, con dbt; la falla de dbt; el límite de intentos de la clave; el menú actual | Llamaba «bronce» a `raw.db` y «data warehouse» a `datos.db`; la hora del job en invierno |
| PROYECTO (textos del panel) | Glosario y cuadros de seguridad, DevOps, observabilidad e informes | — | dbt en el workflow; el bloqueo de la clave | `datos.db` como base servida; «tres dimensiones»; la clave en `bi/dashboard.py` (está en `bi/control.py`); nombres de páginas antiguos |

**Descargas:** el PDF es la página impresa por el navegador (botón «Imprimir o guardar como PDF»). `tests/medicion/imprimir.cjs` imprime los cinco documentos con Chrome y comprueba que lleven los mismos títulos de sección y los mismos diagramas, en el mismo orden, que la página y que su `.md`: los cinco dan OK.
