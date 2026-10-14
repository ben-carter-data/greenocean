# Prompt de revisión de legibilidad y experiencia de usuario

Revisa el Monitor de Precios como si fuera a usarlo una persona de 12 años que
no conoce análisis de datos, programación ni términos internos del proyecto.
Conserva la estructura global y el recorrido cronológico actuales.

## Objetivo

Cada pantalla debe permitir responder en pocos segundos:

1. ¿Qué estoy mirando?
2. ¿Qué significa el número, color o gráfico?
3. ¿Por qué debería importarme?
4. ¿Qué puedo hacer a continuación?

## Reglas obligatorias

- Usa palabras cotidianas y frases cortas. Primero muestra el significado; deja
  el nombre técnico como información secundaria.
- No muestres códigos internos como K1, K6, RN-05 o nombres como
  `k1_margin` en títulos, botones, gráficos ni ayudas dirigidas al público. Si
  son necesarios para auditoría, colócalos dentro de la sección técnica con la
  etiqueta «Nombre usado en el código».
- Explica toda sigla la primera vez que aparezca. Evita la sigla si el nombre
  completo cabe en el espacio disponible.
- Ningún icono o color puede ser la única explicación. Acompáñalo con palabras:
  «Subió», «Bajó», «Dentro de lo habitual», «Conviene revisar» o equivalentes.
- Toda tabla debe tener encabezados visibles, unidad en la columna y una frase
  anterior que diga qué representa cada fila. Evita columnas cuyo significado
  dependa de una leyenda distante.
- Todo gráfico debe tener título descriptivo, unidad, etiquetas legibles y una
  ayuda breve que explique cómo leerlo. El valor exacto debe estar disponible al
  pasar el mouse, pero la idea principal debe entenderse sin hacerlo.
- Mantén los controles antes del contenido que modifican. Muestra primero el
  resumen, después el detalle y al final la explicación técnica.
- El código Python o SQL debe vivir en el flujo normal de la página. No uses
  ventanas flotantes sobre tablas o gráficos. Debe poder copiarse y colapsarse;
  permanece abierto por defecto según la regla general del proyecto.
- Ningún texto, menú, tooltip, código, gráfico o control puede cubrir otro
  componente. En pantallas estrechas, apila elementos antes de reducir el texto
  hasta volverlo ilegible.
- No dupliques información. Enlaza a la sección canónica cuando el detalle ya
  existe en otra parte.
- Conserva el orden cronológico del recorrido y la navegación anterior/siguiente.
- Conserva las paletas Vantablack, Grafito y Corporativo. Asegura contraste de
  lectura en fondo, tarjetas, campos, gráficos, estados, código y tooltips.

## Criterio de aceptación

Para cada cambio, comprueba las tres paletas y al menos una ventana estrecha.
Lee la pantalla sin conocer el proyecto: si un título, símbolo, número o acción
necesita una explicación verbal externa, todavía no está terminado. Verifica que
no haya superposiciones, recortes, desplazamiento horizontal innecesario ni
controles técnicos de Streamlit sobre el contenido.
