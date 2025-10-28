# 🧩 EcoBottle AR – Data Warehouse & BI Dashboard

## 📊 Descripción general
Este proyecto implementa un **mini–ecosistema de datos comercial (online + offline)** para la empresa **EcoBottle AR**, con el objetivo de desarrollar un **pipeline ETL reproducible en Python** y un **dashboard analítico en Looker Studio** que permita monitorear ventas, usuarios activos, ticket promedio, NPS y desempeño por provincia y producto.

El flujo completo sigue buenas prácticas de ingeniería de datos y se basa en un **modelo estrella (Kimball)**.

---

## 🧱 Estructura del proyecto


---

## 🧩 Esquema Estrella

### 🧠 Tabla de Hechos
**FactSales**
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
python -m etl.extract´´´

### 2️⃣ Transform
Limpieza, estandarización de campos y creación de nuevas métricas derivadas.  
Incluye:
- Conversión de tipos y manejo de valores nulos  
- Integración de tablas (joins entre productos, tiendas y canales)  
- Cálculo de métricas base: monto, cantidad y fecha de venta  
- Normalización de provincias y canales  

```bash
python -m etl.transform
