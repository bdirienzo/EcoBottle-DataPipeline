# 🧩 EcoBottle AR – Data Warehouse & BI Dashboard

## 📊 Descripción general
Este proyecto implementa un **mini–ecosistema de datos comercial (online + offline)** para la empresa **EcoBottle AR**, con el objetivo de desarrollar un **pipeline ETL reproducible en Python** y un **dashboard analítico en Looker Studio** que permita monitorear ventas, usuarios activos, ticket promedio, NPS y desempeño por provincia y producto.

El flujo completo sigue buenas prácticas de ingeniería de datos y se basa en un **modelo estrella (Kimball)**.

---

## 🧱 Estructura del proyecto

```text
RAW (CSV, fuentes simuladas)
   └── Extract  (etl/extract.py)
         ↓
       Transform (etl/transform.py)
         ↓
       Load      (etl/load.py)  →  Data Warehouse (SQLite/PostgreSQL)
                                     └── Modelo Estrella (DDL/star_schema.sql)
                                              ↓
                                       Dashboard (Looker Studio)

```
---

Esa sección describe el flujo lógico del proyecto desde la ingesta de archivos CSV hasta la visualización final en Looker Studio, manteniendo el formato limpio y consistente con el resto del README.

---

## 🧩 Esquema Estrella

```
```mermaid
erDiagram
  %% ============================
  %% RELACIONES PRINCIPALES
  %% ============================
  DimDate ||--o{ FactSales : "date_id"
  DimCustomer ||--o{ FactSales : "customer_id"
  DimProduct ||--o{ FactSales : "product_id"
  DimStore ||--o{ FactSales : "store_id"
  DimChannel ||--o{ FactSales : "channel_id"

  DimDate ||--o{ FactNPS : "date_id"
  DimCustomer ||--o{ FactNPS : "customer_id"

  %% Relaciones con provincias
  DimProvince ||--o{ DimStore : "province_id"
  DimProvince ||--o{ DimCustomer : "province_id"

  %% ============================
  %% TABLAS DIMENSIÓN
  %% ============================
  DimDate {
    INTEGER date_id PK
    DATE full_date
    INTEGER year
    INTEGER quarter
    INTEGER month
    TEXT month_name
    INTEGER day
    INTEGER is_weekend
  }

  DimProvince {
    INTEGER province_id PK
    TEXT province_name
    TEXT region
  }

  DimChannel {
    INTEGER channel_id PK
    TEXT channel_name
  }

  DimStore {
    INTEGER store_id PK
    TEXT store_name
    INTEGER province_id FK
  }

  DimProduct {
    INTEGER product_id PK
    TEXT product_code
    TEXT product_name
    TEXT category
    TEXT brand
    REAL unit_price
  }

  DimCustomer {
    INTEGER customer_id PK
    TEXT customer_code
    TEXT full_name
    TEXT email
    INTEGER province_id FK
    DATE created_at
  }

  %% ============================
  %% TABLAS DE HECHOS
  %% ============================
  FactSales {
    INTEGER sales_line_id PK
    INTEGER date_id FK
    INTEGER customer_id FK
    INTEGER product_id FK
    INTEGER store_id FK
    INTEGER channel_id FK
    INTEGER quantity
    REAL unit_price
    REAL amount
  }

  FactNPS {
    INTEGER nps_id PK
    INTEGER date_id FK
    INTEGER customer_id FK
    INTEGER score
    TEXT classification
  }
```

### 🧠 Tabla de Hechos
| Campo | Descripción | Tipo |
|-------|--------------|------|
| sale_id | Identificador de la venta | INTEGER |
| date_id | FK a DimDate | INTEGER |
| customer_id | FK a DimCustomer | INTEGER |
| product_id | FK a DimProduct | INTEGER |
| store_id | FK a DimStore | INTEGER |
| channel_id | FK a DimChannel | INTEGER |
| amount | Monto total de la venta | FLOAT |
| quantity | Cantidad de ítems | INTEGER |

### 🌐 Tablas Dimensión
| Dimensión | Descripción |
|------------|--------------|
| **DimDate** | Fechas normalizadas (año, mes, trimestre, día, etc.) |
| **DimCustomer** | Clientes con datos demográficos y de ubicación |
| **DimProduct** | Productos con categoría, precio y marca |
| **DimStore** | Tiendas físicas o sucursales |
| **DimProvince** | Provincias argentinas de operación |
| **DimChannel** | Canal de venta (online/offline) |

---

## 🧮 KPIs Principales

| KPI | Fórmula / Fuente | Descripción |
|-----|------------------|--------------|
| **Ventas Totales** | SUM(amount) | Monto total vendido |
| **Usuarios Activos** | COUNT(DISTINCT customer_id) | Clientes con al menos una compra |
| **Ticket Promedio** | SUM(amount) / COUNT(DISTINCT sale_id) | Valor promedio por transacción |
| **NPS (Net Promoter Score)** | %Promotores - %Detractores | Nivel de satisfacción y lealtad del cliente |
| **Ventas por Provincia** | SUM(amount) GROUP BY province | Distribución geográfica |
| **Ranking de Productos** | SUM(amount) GROUP BY product | Identificación de productos top |

---

## ⚙️ Pipeline ETL

### 1️⃣ Extract
Lectura de archivos `.csv` desde la carpeta `RAW`:
```bash
python -m etl.extract
```

### 2️⃣ Transform
Limpieza, estandarización de campos y creación de nuevas métricas derivadas.  
Incluye:
- Conversión de tipos y manejo de valores nulos  
- Integración de tablas (joins entre productos, tiendas y canales)  
- Cálculo de métricas base: monto, cantidad y fecha de venta  
- Normalización de provincias y canales
```bash
python -m etl.transform 
```

### 3️⃣ Load
Carga de los datos transformados en el modelo estrella definido en SQL.
Se utiliza una base local (por defecto SQLite), aunque el diseño es compatible con PostgreSQL.
```bash
python -m etl.load
```

### ▶️ Ejecución completa del pipeline
Ejecuta los tres pasos anteriores en secuencia, registrando logs del proceso:
```bash
python -m etl.run_pipeline
```
---
Los logs de ejecución se almacenan en /logs/pipeline.log e incluyen el conteo de filas procesadas por tabla.