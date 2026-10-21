# GreenOcean · Plan de pruebas de seguridad

Cómo se buscan los puntos débiles del panel, cómo se corrigen y cómo se comprueba en cada cambio que siguen cerrados. Revisión del 20-10-2026 (D-199 a D-202), usando el OWASP Top 10 (2021) como referencia.

## 1. Objetivo y alcance

El objetivo es comprobar, con pruebas que cualquiera puede repetir, que un visitante no puede leer los secretos, cambiar los datos ni lanzar el pipeline sin la clave de control. La revisión cubre todo lo que se alcanza desde internet: el panel, la página Consultas SQL, la clave de control y el código público. Las cuentas de GitHub y Streamlit quedan fuera, porque las protegen su contraseña y la verificación en dos pasos.

## 2. Puertas y barreras

Cada puerta tiene tres barreras independientes: si una fallara, las otras siguen deteniendo el ataque.

| Puerta | Qué intentaría un atacante | Barreras |
|---|---|---|
| Consultas SQL | Leer secretos, escribir archivos o salir a internet | Filtro de la consulta · motor sin acceso externo y configuración bloqueada · solo lectura con topes de tiempo y filas |
| Clave de control | Adivinar la clave | Comparación en tiempo constante · 5 intentos cada 15 minutos · el botón del pipeline aparece solo tras la clave |
| Código público | Encontrar claves en el repositorio o en los errores | Secretos fuera de git · token nunca en pantalla · permisos mínimos del workflow |

[[diagrama:seguridad]]

## 3. Método

1. **Inventario** de las puertas y de lo que protegen.
2. **Ataque como intruso**, con el código del panel y un secreto falso.
3. **Corrección antes de publicar**, con su entrada en `docs/DECISIONES.md`.
4. **Cada ataque se vuelve una prueba** automática.
5. **Repetición en cada push** en GitHub Actions.

## 4. Casos de prueba

| ID | Ataque | Resultado esperado | OWASP | Prueba |
|---|---|---|---|---|
| S-01 | 19 consultas SQL para leer secretos o escribir archivos | Rechazada; el secreto nunca aparece | A03 | `test_security.py` |
| S-02 | 9 órdenes directas al motor | Error de permiso | A05 | `test_security.py` |
| S-03 | Consultas sin fin o de millones de filas | Cortada a los pocos segundos | A04 | `test_sql_explorer.py` |
| S-04 | Clave con ñ, tildes o emojis | «Clave incorrecta», sin error | A07 | `test_control.py` |
| S-05 | Probar claves sin parar | Bloqueo de 15 minutos tras 5 intentos | A07 | `test_control.py` |
| S-06 | Buscar tokens en el repositorio | Ninguno | A02 | `test_security.py` |
| S-07 | Provocar un error de GitHub | El mensaje nunca muestra el token | A09 | `test_control.py` |
| S-08 | Abusar de los permisos del workflow | Solo contenido e issues | A01 | `test_security.py` |
| S-09 | Afirmar una barrera sin prueba | Cada barrera apunta a una prueba que existe | — | `test_security.py` |
| S-10 | Lanzar el pipeline sin la clave | El botón no existe antes de la clave | A01 | `test_dashboard.py` |

## 5. Resultados y límites

La revisión del 20-10-2026 encontró dos puntos débiles en la clave de control (sin límite de intentos; error con caracteres no ASCII), corregidos en D-199, y una frase inexacta del SAD, corregida en D-200. Para que todo esto se sostenga, la clave de control debe ser larga, el token de GitHub debe tener solo los permisos necesarios y renovarse antes de vencer, y las cuentas de administración deben usar verificación en dos pasos. Los valores secretos y los problemas aún sin corregir nunca se publican.
