# Monitor de precios y márgenes de la cadena alimentaria en Chile

Integración automatizada de datos públicos, del mercado mayorista al consumidor.

Cada semana el sistema descarga los precios mayoristas y los precios al consumidor que publica ODEPA, los limpia, aplica reglas de negocio y actualiza un panel con indicadores para análisis de pricing y abastecimiento.

> Estado al 12-10-2026: ejecución manual semanal comprobada en GitHub, informe automático publicado y panel público funcionando. Pendiente: observar cuatro ejecuciones semanales automáticas consecutivas (T-26).

[**Abrir el panel público**](https://monitor-precios-hito1-d4hfucgaifcebbwahgrzwf.streamlit.app/)

[![pruebas](https://github.com/cben6514-boop/monitor-precios-hito1/actions/workflows/pruebas.yml/badge.svg)](https://github.com/cben6514-boop/monitor-precios-hito1/actions/workflows/pruebas.yml)
[![semanal](https://github.com/cben6514-boop/monitor-precios-hito1/actions/workflows/semanal.yml/badge.svg)](https://github.com/cben6514-boop/monitor-precios-hito1/actions/workflows/semanal.yml)

## Qué responde

- Margen entre precio mayorista y precio al consumidor, por producto y canal.
- Diferencia de precios entre canales (supermercado, feria, carnicería y otros) y entre regiones.
- Estacionalidad de cada producto.
- Rezago con que el precio al consumidor sigue al mayorista (indicador descriptivo).
- Alertas de productos con variaciones fuera de su rango normal.
- Calidad de datos: filas cargadas, rechazadas y motivo.

## Hallazgos

Pendiente. Se publican cuando estén verificados, cada uno con la consulta que lo reproduce.

## Cómo funciona

```
ODEPA (CSV) → agente de descarga → datos crudos → ETL (limpieza y reglas) → SQLite → consultas SQL → panel
```

Un job semanal de GitHub Actions ejecuta todo y guarda la base actualizada.

## Estructura

```
├── README.md
├── LICENSE              licencia MIT del código
├── run_download.command lanzador para macOS: descarga y ETL con doble clic
├── docs/
│   ├── DISENO.md        documento de diseño
│   ├── BACKLOG.md       tareas y criterios de terminado
│   └── DECISIONES.md    registro de decisiones
├── agent/
│   ├── agent.py         descarga y validación de archivos
│   ├── input.csv      recursos a descargar
│   └── logs/
├── etl/
│   ├── etl.py           clean, apply_business_rules, load
│   ├── schema.sql       tablas de datos.db
│   ├── raw_schema.sql   tablas de raw.db
│   ├── raw.db         datos crudos (no se sube; lo genera el ETL)
│   └── datos.db         indicadores semanales
├── bi/
│   ├── queries.sql      una consulta por indicador
│   ├── queries.py       lectura de la base por nombre de consulta
│   ├── alerts.py        alertas de variación (K6)
│   ├── charts.py        gráficos y colores del panel (Altair)
│   ├── control.py       estado y lanzamiento del robot (API de GitHub)
│   ├── dashboard.py     panel Streamlit
│   └── report.py        informe semanal de alertas y estado
├── tests/
└── .github/workflows/   semanal.yml, pruebas.yml
```

## Cómo ejecutarlo

```bash
git clone <url-del-repositorio>
cd <carpeta>
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python agent/agent.py        # descarga
python etl/etl.py             # limpia y carga
streamlit run bi/dashboard.py # abre el panel
python bi/report.py           # imprime el informe semanal
pytest                        # pruebas
```

## Stack

Python (pandas, requests) · SQL (SQLite) · Streamlit · GitHub Actions · pytest

## Alcance y límites

- Frutas y verduras: análisis completo con margen desde el mayorista.
- Carnes, lácteos, huevos, abarrotes y pan: comparación por canal, región y tiempo, sin margen mayorista.
- Precios nominales, sin ajuste por inflación.
- El rezago entre precios es descriptivo y no prueba causalidad.
- No incluye pescados ni mariscos.

## Fuente de los datos

Oficina de Estudios y Políticas Agrarias (ODEPA), Ministerio de Agricultura de Chile, [portal de datos abiertos](https://datos.odepa.gob.cl/), licencia Creative Commons Atribución. Este proyecto no es un producto oficial de ODEPA.

## Licencia

El código está bajo licencia MIT (`LICENSE`). Los datos son de ODEPA y mantienen su licencia Creative Commons Atribución.

## Autor

Jocelyn Ben Yahmed
