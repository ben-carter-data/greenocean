# Reglas de trabajo con Claude

Cómo trabaja Claude en este repositorio. Complementa a `CLAUDE.md`; no lo reemplaza.

## 1. Solo lo necesario

Claude hace lo que se pidió y nada más. Si una tarea no es necesaria para el resultado pedido, no la hace. Ante la duda sobre si hace falta, no la hace y lo dice en una línea.

## 2. Tres tamaños de tarea

| Tamaño | Qué es | Qué hace Claude |
|---|---|---|
| **Pesada** (energívora) | Tarda más de unos 2 minutos o gasta mucho: suite completa repetida, medición de calidad, navegadores, descargas, auditorías de todas las páginas, cambios en muchos archivos, subagentes | **Avisa antes** en una línea (qué, cuánto tarda más o menos y por qué hace falta) y espera el visto bueno |
| **Normal** | Editar, leer, probar un módulo, un commit | La hace y sigue, sin pedir permiso |
| **Liviana** | Lectura, una búsqueda, un chequeo corto | La hace **en paralelo** mientras corre otra cosa, si no toca los mismos archivos ni altera lo que se está midiendo |

Una tarea liviana nunca se convierte en pesada: si crece, Claude se detiene y avisa.

## 3. Cómo informa

Al terminar, **un párrafo**: qué hizo, qué verificó y con qué resultado, y qué decide el autor. Sin listas largas ni explicaciones que nadie pidió.

## 4. Siempre igual

Sin push, sin forzar y sin borrar ramas ni archivos sin aprobación explícita del autor. Los pasos de aprobación que el autor define en cada pedido se respetan.

## 5. Pruebas según el tipo de cambio

- Textos, nombres, traducciones, estilos o documentos: solo lint y las pruebas del archivo tocado. Sin suite completa y sin revisión con agentes.
- Lógica del panel (filtros, tablas, descargas): las pruebas de ese módulo.
- Pipeline, reglas de datos o cualquier cosa que cambie cifras: suite completa con las dos bases (la publicada y la reconstruida, D-527). Revisión con agentes solo si el cambio es grande.
- Antes de correr algo que tarde más de 5 minutos, Claude pregunta.
- Claude no vigila el CI después de subir; el autor revisa Actions.
- Reportes de máximo 5 líneas: qué hizo, qué falta, qué decide el autor.
