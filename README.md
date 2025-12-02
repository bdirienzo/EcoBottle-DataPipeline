# ♻️ EcoBottle AR – Data Warehouse & BI Dashboard

## 📊 1. Descripción general

**EcoBottle AR** es un proyecto académico de **Data Warehouse & Business Intelligence** que implementa un mini–ecosistema de datos comercial **(online + offline)** para una empresa ficticia dedicada a la venta de botellas reutilizables.

El objetivo principal es diseñar e implementar un **pipeline ETL reproducible en Python**, construir un **modelo estrella (Kimball)**, y desarrollar un **dashboard analítico en Power BI** que permita monitorear los indicadores clave del negocio.

El proyecto integra múltiples fuentes de información (ventas, pagos, envíos, sesiones web y encuestas NPS) para generar una vista consolidada del desempeño comercial y de la experiencia del cliente.  

Este repositorio contiene el código, los datos y la documentación necesaria para reproducir todo el flujo, desde la extracción de archivos CSV hasta la visualización final de métricas y KPIs.

---

## 🧱 2. Estructura del proyecto

El repositorio sigue una arquitectura modular de tipo **Data Warehouse Pipeline**, organizada por etapas y responsabilidades, para facilitar la trazabilidad, mantenimiento y escalabilidad del flujo de datos.

```text
EcoBottle-AR/
│
├── assets/             → Recursos gráficos (diagramas, capturas, íconos)
│   ├── star/           → Diagramas de estrella
│
├── docs/               → Documentación técnica
│   └── data_dictionary.md
│
├── etl/                → Scripts del proceso ETL (Extract, Transform, Load)
│   ├── config/         → Parámetros, rutas y variables globales
│   ├── extract/        → Lectura de fuentes RAW (.csv)
│   ├── transform/      → Limpieza, joins y creación de dimensiones/hechos
│   ├── load/           → Carga al Data Warehouse (SQLite)
│   ├── __init__.py
│   └── run_pipeline.py → Script principal del pipeline
│
├── raw/                → Archivos fuente (.csv) del ecosistema de datos
│
├── warehouse/          → Resultado final del ETL
│   ├── dim/            → Tablas de dimensiones transformadas
│   ├── fact/           → Tablas de hechos transformadas
│
├── requirements.txt    → Dependencias del entorno Python
├── LICENSE             → Licencia del proyecto (MIT)
└── README.md           → Documentación principal del repositorio
```
---

## 🌟 3. Modelo de Datos

El proyecto se estructura en dos niveles de modelado complementarios:

### 🔹 3.1 Modelo Entidad–Relación (DER)
Representa el **modelo lógico original** de las fuentes de datos operacionales, con todas las entidades del ecosistema comercial (clientes, pedidos, productos, pagos, envíos, sesiones, etc.).  
Este modelo fue el punto de partida para comprender las relaciones entre las tablas y definir las claves de negocio.

![DER original](assets/DER.png)

> *El diagrama DER muestra las entidades base y sus relaciones antes de la transformación hacia el modelo dimensional.*


### 🔹 3.2 Modelo Estrella (Data Warehouse)
A partir del DER, se construyó el **modelo dimensional** siguiendo la metodología de **Ralph Kimball**, diseñado para optimizar la consulta analítica y la agregación de métricas.

El **esquema estrella** consolida los procesos clave del negocio en varias *fact tables*, conectadas a dimensiones comunes como tiempo, cliente, producto, tienda y canal.

**Hechos principales:**
- `fact_sales_order` – detalle de ventas.
- `fact_sales_order_item` – detalle de ventas por producto y fecha.
- `fact_payment` – pagos realizados por cliente.
- `fact_shipment` – envíos procesados y costos asociados.
- `fact_web_session` – sesiones web de usuarios.
- `fact_marketing_attribution` – atribución de conversiones.
- `fact_nps_response` – respuestas de encuestas de satisfacción (NPS).

**Dimensiones comunes:**
- `DimCalendar`, `DimCustomer`, `DimProduct`, `DimStore`, `DimChannel`, `DimProvince`, `DimAddress`, entre otras.

```Todos los detalles técnicos del modelo (campos, tipos, claves y reglas de negocio) se documentan en el docs/data_dictionary.md, junto con los esquemas visuales individuales de cada proceso.```

---

## 📘 4. Documentación Técnica Complementaria

Toda la estructura de tablas, claves y relaciones del modelo estrella se encuentra descrita en detalle en el [`docs/data_dictionary.md`](docs/data_dictionary.md).

El documento incluye:
- Diagramas individuales (*star schemas*) de cada proceso.  
- Definición de todas las tablas de hechos y dimensiones.  
- Campos, tipos de datos, claves (PK/FK) y descripciones funcionales.  
- Reglas de negocio aplicadas en la etapa de transformación.

> Este **Data Dictionary** actúa como la pieza central de gobernanza de datos del proyecto, permitiendo la trazabilidad entre los datos crudos, el modelo dimensional y los KPIs analíticos.

---

## ⚙️ 5. Pipeline ETL

El proceso ETL de **EcoBottle AR** automatiza la creación del Data Warehouse a partir de los archivos fuente en formato `.csv`.  
Está desarrollado en **Python** y estructurado en módulos independientes que reflejan las tres fases clásicas del pipeline: **Extract**, **Transform** y **Load**.

### 1️⃣ 5.1 Extract
En esta etapa se realiza la **lectura de las fuentes RAW** desde la carpeta `/raw`, aplicando validaciones básicas de formato y consistencia (por ejemplo: columnas esperadas, tipos de datos, duplicados y valores nulos críticos).  

Los datos se cargan en estructuras temporales de listas para ser transformadas.

```bash
python -m etl.extract
```

### 2️⃣ 5.2 Transform
Aquí se lleva a cabo la limpieza, estandarización e integración de todas las tablas.
Se generan las claves sustitutas (surrogate keys), se aplican normalizaciones de texto y se unifican los dominios de provincias, canales, productos y fechas.
También se construyen las tablas de dimensiones y hechos a partir de las relaciones del modelo DER.
```bash
python -m etl.transform 
```
Principales transformaciones:
- Conversión de tipos y manejo de nulos
- Creación de claves primarias y foráneas
- Join entre pedidos, clientes, productos, canales y envíos
- Cálculo de métricas derivadas (monto, cantidad, ticket promedio, etc.)
- Normalización de fechas en una DimCalendar reutilizable

### 3️⃣ 5.3 Load
Los datos finales se cargan en la carpeta /warehouse.
El proceso asegura la integridad referencial entre dimensiones y hechos, y deja el dataset listo para conectarse a Looker Studio o cualquier herramienta BI.
```bash
python -m etl.load
```

### ▶️ 5.4 Ejecución completa del pipeline
Ejecuta los tres pasos anteriores en secuencia, registrando logs del proceso:
```bash
python -m etl.run_pipeline
```

> *Este script orquesta todas las fases del ETL en orden secuencial y deja registrada la trazabilidad en consola (logging).*

---

## 📊 6. KPIs Principales

El modelo estrella permite calcular y analizar indicadores clave del negocio, combinando información de ventas, pagos, envíos, sesiones web y encuestas NPS.

Los siguientes **KPIs** se utilizan en el dashboard analítico para evaluar el rendimiento comercial y la satisfacción del cliente:

| KPI | Fórmula / Fuente | Descripción |
|-----|------------------|--------------|
| **Ventas Totales** | `SUM(amount)` en `FactSalesOrderItem` | Valor total vendido en un período. |
| **Usuarios Activos** | `COUNT(DISTINCT customer_id)` | Número de clientes que realizaron al menos una compra. |
| **Ticket Promedio** | `SUM(amount) / COUNT(DISTINCT sales_order_id)` | Valor promedio por pedido. |
| **Costo de Envíos** | `SUM(cost)` en `FactShipment` | Gasto total asociado a entregas. |
| **NPS (Net Promoter Score)** | %Promotores − %Detractores | Nivel de satisfacción y lealtad del cliente. |

> *Estos indicadores se visualizan en el dashboard de Power BI para monitorear tendencias de ventas, desempeño logístico y comportamiento del cliente.*

---

## 📈 7. Dashboard Analítico

A partir del modelo estrella almacenado en `warehouse/`, se desarrolló un **dashboard interactivo** en **Power BI**, que consolida los KPIs del negocio y permite explorar los datos desde distintas perspectivas: comercial, logística, digital y de experiencia del cliente.

El tablero integra información de todas las *fact tables* (ventas, pagos, envíos, sesiones y NPS) y ofrece una visión unificada del desempeño general de **EcoBottle AR**.

### 🎯 7.1 Objetivo
Brindar una herramienta de análisis que permita:
- Monitorear el cumplimiento de objetivos comerciales.
- Analizar el comportamiento de clientes y productos.
- Identificar patrones de compra y eficiencia logística.
- Evaluar la satisfacción del cliente mediante NPS.

### 🧭 7.2 Principales vistas
- **Ventas por provincia y canal**  
- **Ranking mensual de productos**  
- **Evolución del ticket promedio y volumen de ventas**  
- **Tiempos y costos de envío por zona**  
- **Actividad de usuarios en canales online**  
- **Distribución de NPS (Promotores / Neutros / Detractores)**  

📊 **Herramienta:** [Power BI](https://app.powerbi.com/view?r=eyJrIjoiNzhhNTM4ZDQtYThjOS00Yjg2LWE1NWMtYWM5YjI3Njg5ZjUyIiwidCI6IjNlMDUxM2Q2LTY4ZmEtNDE2ZS04ZGUxLTZjNWNkYzMxOWZmYSIsImMiOjR9&pageName=f058cc2ec84f9d72e255)

---

## 🧾 8. Licencia y reconocimiento

Este proyecto fue desarrollado por **Bernardo Di Rienzo** en el marco de la Licenciatura en Ciencia de Datos de la Universidad Austral (2025).

Los archivos originales de datos (`/raw`) y el diagrama entidad–relación (`DER`) provienen del repositorio académico base del profesor **Augusto Carmona**, utilizados únicamente como punto de partida para la práctica de modelado y análisis.

> © 2025 Bernardo Di Rienzo – MIT License. Todos los derechos reservados sobre los desarrollos y documentación propios.

