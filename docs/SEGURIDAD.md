# GreenOcean · Plan de pruebas de seguridad

Cómo se buscan los puntos débiles del panel publicado, cómo se corrigen y cómo se demuestra, en cada cambio del código, que siguen cerradas.

| Ficha del documento | |
|---|---|
| Producto | GreenOcean, panel de inteligencia de precios de alimentos |
| Versión | Revisión del 20-10-2026 (decisiones D-199 a D-202) |
| Autoría | El autor, con el registro completo de decisiones en `docs/DECISIONES.md` |
| Documentos hermanos | PRD (qué resuelve), SAD (cómo está construido) y ADR (por qué se decidió así) |
| Referencia | OWASP Top 10 (2021), la lista estándar de los riesgos más comunes de una aplicación web |
| Vista en el panel | Seguridad · Mapa de seguridad: cada puerta, sus barreras y la prueba de cada una |

---

## 1. Objetivo y alcance

El objetivo es demostrar, con pruebas que cualquiera puede leer y repetir, que un visitante del panel publicado no puede leer los secretos del proyecto, cambiar los datos ni lanzar el pipeline sin la clave del autor.

El alcance es todo lo que un visitante alcanza desde internet: el panel en Streamlit Community Cloud, su página Consultas SQL, la clave de control del Centro de operación y el código público en GitHub. Quedan fuera las cuentas del autor en GitHub y en Streamlit, que se protegen con sus propias contraseñas y su verificación en dos pasos, y los ataques de red contra esas plataformas.

## 2. Activos a proteger

| Activo | Dónde vive | Qué pasaría si se perdiera |
|---|---|---|
| Token de GitHub | Secretos del panel en Streamlit Cloud | Alguien podría usar los permisos del token sobre el repositorio |
| Clave de control | Secretos del panel en Streamlit Cloud | Alguien podría lanzar el pipeline cuando quisiera |
| Base servida `datos.duckdb` | Servidor del panel y repositorio | Cifras alteradas en el panel |
| Pipeline semanal | GitHub Actions | Ejecuciones no pedidas, commits y correos de fallo |

## 3. Superficie de ataque

Un visitante tiene tres puertas. Cada una tiene tres barreras independientes: si una fallara, las otras siguen deteniendo el ataque (defensa en profundidad).

| Puerta | Qué intentaría un atacante | Barreras |
|---|---|---|
| Consultas SQL | Leer el archivo de secretos del servidor, escribir archivos o salir a internet desde el motor | Filtro de la consulta · motor sin acceso externo y con la configuración bloqueada · solo lectura con topes de tiempo, memoria y filas |
| Clave de control | Adivinar la clave probando sin parar | Comparación en tiempo constante · 5 intentos cada 15 minutos para todos los visitantes · una sola puerta: el botón del pipeline y los enlaces aparecen solo tras la clave, y solo en esa sesión |
| Código público | Encontrar claves en el repositorio o en los mensajes de error | Secretos fuera de git · token nunca en pantalla · permisos mínimos del workflow |

## 4. Método

La revisión sigue cinco pasos, siempre en este orden.

1. **Inventario.** Se listan las puertas de entrada de un visitante y lo que hay detrás de cada una (secciones 2 y 3).
2. **Ataque como intruso.** Se ataca cada puerta como lo haría alguien de afuera, con el mismo código que usa el panel y sobre la misma base. El secreto atacado es un archivo falso con un valor de prueba, nunca el real.
3. **Corrección antes de publicar.** Un hallazgo se corrige primero y se documenta después, con su entrada en `docs/DECISIONES.md`. Nunca se publica un problema sin corregir.
4. **Cada ataque se vuelve una prueba.** Cada intento queda escrito como prueba automática, que debe seguir fallando para el atacante.
5. **Repetición en cada cambio.** Las pruebas corren en GitHub Actions en cada push. Un cambio que reabra una puerta deja las pruebas en rojo y no llega a la versión publicada sin que se note.

## 5. Casos de prueba

| ID | Puerta | Ataque | Resultado esperado | Riesgo OWASP | Prueba |
|---|---|---|---|---|---|
| S-01 | Consultas SQL | 19 consultas para leer secretos o escribir archivos: `read_text`, `glob`, rutas como tabla, `query()` armado por partes, comentarios entre letras, `COPY`, `getenv` | Rechazada o vacía; el secreto nunca aparece y no se crea ningún archivo | A03 Inyección | `test_security.py` |
| S-02 | Consultas SQL | 9 órdenes directas al motor, como si el filtro no existiera: leer archivos, reactivar el acceso externo, `COPY`, `ATTACH`, instalar extensiones, crear o borrar tablas | El motor responde con un error de permiso | A05 Configuración insegura | `test_security.py` |
| S-03 | Consultas SQL | Consultas que no terminan o devuelven millones de filas | Cortada a los pocos segundos, con filas limitadas | A04 Diseño inseguro | `test_sql_explorer.py` |
| S-04 | Clave de control | Clave con ñ, tildes o emojis | «Clave incorrecta», sin error de la aplicación | A07 Fallas de autenticación | `test_control.py` |
| S-05 | Clave de control | Probar claves sin parar | Tras 5 intentos, bloqueo de 15 minutos incluso para la clave correcta | A07 Fallas de autenticación | `test_control.py` y `test_dashboard.py` |
| S-06 | Código público | Buscar tokens en cada archivo versionado | Ninguno; `secrets.toml` ignorado por git | A02 Fallas criptográficas (secretos expuestos) | `test_security.py` |
| S-07 | Código público | Provocar un error de GitHub para leer el token | El mensaje dice el código y la causa, nunca el token | A09 Fallas de registro | `test_control.py` |
| S-08 | Código público | Abusar de los permisos del workflow semanal | Solo puede escribir contenido y crear issues | A01 Control de acceso | `test_security.py` |
| S-09 | Vista Seguridad | Afirmar una barrera sin prueba | Cada barrera de la vista apunta a una prueba que existe | Rigor del método | `test_security.py` |
| S-10 | Clave de control | Lanzar el pipeline sin la clave | El botón no existe antes de la clave; la ventana de ejecución vuelve a pedirla | A01 Control de acceso | `test_dashboard.py` |

## 6. Criterios de aceptación

- Todas las pruebas de la sección 5 pasan en GitHub Actions en cada push.
- Ningún valor secreto aparece en el repositorio, en el panel, en los errores ni en este documento.
- Cada barrera que muestra la vista Seguridad tiene su prueba automática.
- Un hallazgo nuevo se corrige antes de publicarse y deja su decisión escrita.

## 7. Resultados de la revisión del 20-10-2026

| Hallazgo | Gravedad | Estado |
|---|---|---|
| La clave de control no tenía límite de intentos: un script podía probar claves sin parar | Media | Corregido en D-199 |
| Una clave con caracteres no ASCII hacía fallar la comparación y mostraba un error | Baja | Corregido en D-199 |
| El SAD decía que el panel no ejecuta texto de un visitante, y la página Consultas SQL sí lo hace | Documental | Corregido en D-200 |

Lo que la revisión confirmó que ya estaba bien: el SQL resistió todos los ataques con sus dos barreras, ningún secreto está en el historial de git, el token nunca se muestra y el desbloqueo vive solo en la sesión del navegador.

## 8. Límites y responsabilidades del autor

- **Fuerza de la clave de control.** Las pruebas limitan los intentos, pero la clave debe ser larga: cuatro o cinco palabras, o más de 16 caracteres.
- **Permisos del token de GitHub.** Conviene un token de grano fino, solo para este repositorio y solo con permiso sobre Actions, y renovarlo antes de que venza; el Centro de operación avisa cuando faltan menos de 14 días.
- **Bloqueo compartido.** Quien pruebe claves a propósito bloquea también al autor durante 15 minutos. Es el costo aceptado: el pipeline sigue corriendo cada martes y desde GitHub.
- **Cuentas del autor.** La seguridad de GitHub y de Streamlit depende de sus contraseñas y de la verificación en dos pasos.

## 9. Divulgación

El código es público, y este documento no le da a un atacante nada que no pueda leer en él: un sistema debe seguir siendo seguro aunque se sepa cómo está hecho (principio de Kerckhoffs). Lo que nunca se publica son los valores secretos, la configuración de las cuentas del autor y un hallazgo todavía sin corregir.

La revisión se repite cuando aparece una nueva puerta de entrada (una página que reciba texto de un visitante, un nuevo secreto o un nuevo permiso) y, en todo caso, antes de cada cambio grande de arquitectura.
