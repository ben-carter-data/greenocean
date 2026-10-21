# GreenOcean · Documento de requisitos del producto (PRD)

Versión del 20-10-2026. El registro completo de decisiones está en `docs/DECISIONES.md`.

## 1. Contexto

ODEPA publica cada semana los precios mayoristas y al consumidor de frutas, verduras y otros alimentos, y el INE publica el IPC de alimentos. Los datos son abiertos, pero cada serie viene en su propia frecuencia, unidad de venta y nivel de detalle, y ninguna descuenta la inflación. Para compararlos hay que cruzarlos a mano todas las semanas.

## 2. Visión y misión

**Visión:** que cualquier persona que trabaje con precios de alimentos en Chile pueda compararlos en el tiempo, entre canales y entre regiones, con datos en los que puede confiar.

**Misión:** cargar cada martes las fuentes oficiales, dejarlas en una misma unidad y una misma semana, revisar su calidad y publicar un panel donde cada cifra se puede seguir hasta el archivo original.

## 3. Alcance

| Hace | No hace |
|---|---|
| Integra los precios de ODEPA desde 2022 y el IPC de alimentos del INE | Comparar cadenas de supermercados o tiendas |
| Convierte unidades, agrega por semana y calcula precios reales | Predecir precios o explicar sus causas |
| Rechaza filas inválidas con su motivo y audita cada cifra | Orientar al consumidor sobre dónde comprar |
| Publica un panel de solo lectura con su documentación | Permitir que los usuarios modifiquen datos |

Hoy la base tiene 814.610 precios semanales en 250 semanas (03-01-2022 a 12-10-2026), 9 regiones, 8 canales, 1.609 claves de producto y 202 meses del IPC. La última carga leyó 2.521.012 filas: 2.520.811 cargadas y 201 rechazadas con su motivo.

## 4. Usuarios

| Perfil | Para qué lo usa |
|---|---|
| Analista de pricing | Saber si el precio de hoy es normal para la época, en pesos de hoy |
| Compras y abastecimiento | Ver cuánto paga el consumidor sobre el precio mayorista, por canal |
| Gerencia | Revisar qué se movió en la semana y qué está fuera de lo habitual |
| Revisor técnico | Comprobar la calidad, las pruebas, el linaje y la documentación |

[[diagrama:actores]]

El panel es de consulta. El administrador mantiene el código y los secretos, responde consultas SQL puntuales y puede lanzar una carga manual con la clave de control.

## 5. Preguntas de negocio

| ID | Pregunta | Dónde se responde |
|---|---|---|
| P-1 | ¿Qué precios cambiaron esta semana y cuáles son inusuales? | Resumen semanal |
| P-2 | ¿El precio de hoy es normal para la temporada? | Precios e inflación |
| P-3 | ¿Cuánto paga el consumidor sobre el mayorista? | Precios e inflación |

## 6. Requisitos

| ID | Requisito | Cómo se verifica |
|---|---|---|
| RF-01 | Carga semanal automática | Workflow de GitHub Actions cada martes |
| RF-02 | Ninguna fila se pierde | Filas leídas = cargadas + rechazadas, probado en dbt |
| RF-03 | Solo se publica una carga válida | 31 pruebas de dbt antes de reemplazar la base |
| RF-04 | Precios reales junto a los nominales | Deflactor del IPC recalculado en la auditoría |
| RNF-01 | Costo cero y sin vencimientos | Solo servicios gratuitos permanentes |
| RNF-02 | Cada vista se lee en una pantalla de 1440 × 900 | Revisión visual en cada cambio |

## 7. Pantallas

[[diagrama:mockups]]
