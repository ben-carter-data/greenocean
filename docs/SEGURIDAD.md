# GreenOcean · Plan de pruebas de seguridad

Cómo se verifica, paso a paso, que los controles de seguridad del panel siguen cerrados. Revisión del 20-10-2026 (D-199 a D-202), actualizada el 23-10-2026 (D-249), con el OWASP Top 10 (2021) como referencia.

## 1. Objetivo y alcance

El objetivo es comprobar, con pruebas que cualquiera puede repetir, que un visitante no puede leer los secretos, cambiar los datos ni lanzar el pipeline sin la clave de control. La revisión cubre todo lo que se alcanza desde internet: el panel, el estudio de Consultas SQL (abierto a cualquier visitante, porque los datos son públicos), la clave de control y el código público. Las cuentas de GitHub y de Streamlit Cloud quedan fuera: las protege su propio inicio de sesión, que es una configuración de cada plataforma y no se puede verificar desde el repositorio.

## 2. Amenazas y controles

Las seis amenazas, el control que mitiga cada una, la prueba que lo verifica, el activo que protege y el ciclo de mejora continua que los mantiene están en [[vista:Arquitectura de seguridad]]. Aquí no se repiten: este documento dice cómo comprobarlos.

## 3. Procedimiento

[[diagrama:sop]]

Cada paso se puede repetir en cualquier computador con Python 3.11 o 3.12. En GitHub, el workflow `pruebas.yml` ejecuta las mismas pruebas en cada push y pull request.

## 4. Casos de prueba

Los diez casos, de S-01 a S-10, están en el esquema de abajo, alrededor del candado del plan. Cada caso se abre con un clic y muestra su ataque, su resultado esperado, su categoría del OWASP Top 10, la amenaza que cubre y la prueba que lo verifica. Una prueba exige que cada una de esas pruebas exista.

[[diagrama:pruebas]]

## 5. Resultados y límites

La revisión del 20-10-2026 encontró un error de la clave de control con caracteres no ASCII, corregido en D-199, y una frase inexacta del SAD, corregida en D-200. **Sin límite de intentos de la clave:** riesgo aceptado por el autor (D-249), porque la clave solo evita que alguien pulse «Ejecutar pipeline ahora» por accidente y, con ese botón, lo máximo que se puede hacer es lanzar el workflow. Para que todo esto se sostenga, la clave de control debe ser larga, el token de GitHub debe tener solo los permisos necesarios y renovarse antes de vencer, y las cuentas de administración deben usar verificación en dos pasos; esto último lo declara el autor y no se puede comprobar desde el repositorio. Los valores secretos y los problemas aún sin corregir nunca se publican.
