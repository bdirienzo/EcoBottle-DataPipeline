# 📘 Diccionario de Datos – EcoBottle AR

Este documento describe las tablas, campos y relaciones del **modelo estrella** implementado para el proyecto **EcoBottle AR – Data Warehouse & BI Dashboard**.

---

## 🧠 Tablas de Hechos

### 🧾 FactSalesOrder
Contiene el detalle de cada pedido o venta efectuada, una fila por orden.

![Modelo Estrella](/assets/star/sales_order.png)

| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| order_id | BIGINT | Identificador único del pedido | PK |
| customer_sk | INT | Cliente que realiza la compra | FK |
| channel_sk | INT | Canal de venta (ONLINE/OFFLINE) | FK |
| store_sk | INT | Tienda física (NULL si online) | FK |
| billing_address_sk | INT | Dirección de facturación | FK |
| shipping_address_sk | INT | Dirección de envío | FK |
| date_sk | INT | Fecha del pedido | FK |
| status | VARCHAR(20) | Estado del pedido (CREATED, PAID, FULFILLED, CANCELLED, REFUNDED) | — |
| currency_code | CHAR(3) | Moneda utilizada (ARS) | — |
| subtotal | DECIMAL(12,2) | Monto sin impuestos | — |
| tax_amount | DECIMAL(12,2) | Impuestos aplicados | — |
| shipping_fee | DECIMAL(12,2) | Costo de envío | — |
| total_amount | DECIMAL(12,2) | Monto total de la orden | — |

---

### 📦 FactSalesOrderItem
Detalle por producto dentro de cada orden.

![Modelo Estrella](/assets/star/sales_order_items.png)

| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| order_item_id | BIGINT | Identificador único del ítem | PK |
| order_id | BIGINT | Pedido asociado | FK |
| product_sk | INT | Producto vendido | FK |
| channel_sk | INT | Canal de venta | FK |
| date_sk | INT | Fecha de la venta | FK |
| quantity | INT | Cantidad vendida | — |
| unit_price | DECIMAL(12,2) | Precio unitario | — |
| discount_amount | DECIMAL(12,2) | Descuento aplicado | — |
| line_total | DECIMAL(12,2) | Importe total de la línea (qty × price – discount) | — |

---

### 💳 FactPayment
Registra los pagos efectuados por los clientes.

![Modelo Estrella](/assets/star/payment.png)

| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| payment_id | BIGINT | Identificador del pago | PK |
| order_id | BIGINT | Pedido asociado | FK |
| date_sk | INT | Fecha del pago | FK |
| billing_address_sk | INT | Dirección de facturación | FK |
| billing_province_sk | INT | Provincia asociada | FK |
| method | VARCHAR(20) | Medio de pago (CARD, TRANSFER, GATEWAY, CASH) | — |
| status | VARCHAR(20) | Estado (PAID, PENDING, FAILED, REFUNDED) | — |
| amount | DECIMAL(12,2) | Monto abonado | — |

---

### 🚚 FactShipment
Contiene la trazabilidad de los envíos logísticos.

![Modelo Estrella](/assets/star/shipping.png)

| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| shipment_id | BIGINT | Identificador del envío | PK |
| order_id | BIGINT | Pedido asociado | FK |
| shipped_date_sk | INT | Fecha de despacho | FK |
| delivered_date_sk | INT | Fecha de entrega | FK |
| province_sk | INT | Provincia de destino | FK |
| carrier | VARCHAR(40) | Empresa de transporte | — |
| status | VARCHAR(20) | Estado (READY, SHIPPED, DELIVERED, CANCELLED) | — |
| lead_time_days | DECIMAL(12,2) | Tiempo de entrega (días) | — |

---

### 💻 FactWebSession
Representa las sesiones online registradas por los usuarios.

![Modelo Estrella](/assets/star/web_session.png)

| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| session_id | BIGINT | Identificador único de la sesión | PK |
| customer_sk | INT | Cliente (NULL si anónimo) | FK |
| channel_sk | INT | Canal digital (ONLINE) | FK |
| date_sk | INT | Fecha de inicio de sesión | FK |
| source | VARCHAR(50) | Origen del tráfico (ads, direct, email, etc.) | — |
| device | VARCHAR(30) | Dispositivo (desktop, mobile, tablet) | — |
| started_at | TIMESTAMP | Timestamp de inicio | — |
| ended_at | TIMESTAMP | Timestamp de cierre | — |

---

### 💬 FactNpsResponse
Respuestas de encuestas de satisfacción (NPS).

![Modelo Estrella](/assets/star/nps_response.png)

| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| nps_id | BIGINT | Identificador de respuesta | PK |
| customer_id | INT | Cliente que responde | FK |
| channel_sk | INT | Canal asociado | FK |
| date_sk | INT | Fecha de la respuesta | FK |
| score | SMALLINT | Valor de 0 a 10 | — |
| is_detractor | TINYINT | 1 si score ≤ 6 | — |
| is_passive | TINYINT | 1 si 7 ≤ score ≤ 8 | — |
| is_promoter | TINYINT | 1 si score ≥ 9 | — |
| comment | TEXT | Comentario opcional | — |

---

### 📈 FactMarketingAttribution
Asigna sesiones digitales a resultados comerciales.

![Modelo Estrella](/assets/star/marketing.png)

| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| session_id | BIGINT | Identificador de la sesión (fuente OLTP) | PK |
| customer_sk | INT | Cliente identificado | FK |
| channel_sk | INT | Canal de interacción | FK |
| date_sk | INT | Fecha del evento | FK |
| source | VARCHAR(50) | Fuente (ads, organic, referral) | — |
| device | VARCHAR(30) | Dispositivo (desktop, mobile) | — |
| converted_flag | TINYINT | 1 si la sesión generó compra | — |
| orders_attributed | INT | Número de pedidos atribuidos | — |
| revenue_attributed | DECIMAL(12,2) | Ingreso total atribuido | — |

---

## 🌐 Tablas Dimensión

### 👥 DimCustomer
| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| customer_sk | INT | Clave surrogate del cliente | PK |
| customer_id_src | INT | ID original en sistema fuente | — |
| email | VARCHAR(120) | Correo electrónico | — |
| first_name | VARCHAR(80) | Nombre | — |
| last_name | VARCHAR(80) | Apellido | — |
| status | CHAR(1) | Estado (‘A’ activo / ‘I’ inactivo) | — |
| created_at | TIMESTAMP | Fecha de alta | — |

---

### 📦 DimProduct
| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| product_sk | INT | Clave surrogate del producto | PK |
| product_id_src | INT | ID original del producto | — |
| sku | VARCHAR(40) | Código SKU | — |
| name | VARCHAR(120) | Nombre del producto | — |
| category_name | VARCHAR(80) | Categoría o familia | — |
| list_price | DECIMAL(12,2) | Precio de lista | — |
| status | CHAR(1) | Estado (‘A’ / ‘I’) | — |

---

### 🏬 DimStore
| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| store_sk | INT | Clave surrogate | PK |
| store_id_src | INT | ID fuente | — |
| name | VARCHAR(80) | Nombre de la tienda | — |
| address_sk | INT | Dirección de la tienda | FK |

---

### 🧭 DimChannel
| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| channel_sk | INT | Clave surrogate | PK |
| channel_id_src | INT | ID fuente | — |
| code | VARCHAR(20) | Código (‘ONLINE’, ‘OFFLINE’, etc.) | — |
| name | VARCHAR(50) | Nombre descriptivo del canal | — |

---

### 🗺️ DimAddress
| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| address_sk | INT | Clave surrogate | PK |
| address_id_src | INT | ID original | — |
| city | VARCHAR(80) | Ciudad | — |
| postal_code | VARCHAR(20) | Código postal | — |
| country_code | CHAR(2) | País (‘AR’) | — |
| province_sk | INT | Provincia asociada | FK |

---

### 🏙️ DimProvince
| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| province_sk | INT | Clave surrogate | PK |
| province_id_src | INT | ID fuente | — |
| name | VARCHAR(50) | Nombre de la provincia | — |
| code | VARCHAR(10) | Código corto | — |

---

### 📅 DimCalendar
| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| date_sk | INT | Clave surrogate (YYYYMMDD) | PK |
| date | DATE | Fecha calendario | — |
| year | INT | Año | — |
| quarter | INT | Trimestre (1–4) | — |
| month | INT | Mes (1–12) | — |
| day | INT | Día del mes | — |
| month_name | VARCHAR(20) | Nombre del mes | — |
| is_month_end | TINYINT | 1 si es fin de mes | — |

---

## 🔗 Relaciones Principales (PK–FK)
| Tabla | Relación | Clave Foránea |
|--------|-----------|---------------|
| FactSalesOrder | → DimCustomer | customer_sk |
| FactSalesOrder | → DimChannel | channel_sk |
| FactSalesOrder | → DimStore | store_sk |
| FactSalesOrder | → DimAddress | billing_address_sk / shipping_address_sk |
| FactSalesOrder | → DimCalendar | date_sk |
| FactSalesOrderItem | → DimProduct | product_sk |
| FactSalesOrderItem | → DimChannel | channel_sk |
| FactSalesOrderItem | → DimCalendar | date_sk |
| FactPayment | → DimCalendar | date_sk |
| FactShipment | → DimProvince | province_sk |
| FactShipment | → DimCalendar | shipped_date_sk / delivered_date_sk |
| FactWebSession | → DimChannel | channel_sk |
| FactWebSession | → DimCustomer | customer_sk |
| FactWebSession | → DimCalendar | date_sk |
| FactNpsResponse | → DimChannel | channel_sk |
| FactMarketingAttribution | → DimChannel | channel_sk |
| FactMarketingAttribution | → DimCustomer | customer_sk |
| FactMarketingAttribution | → DimCalendar | date_sk |

---

## 🧩 Supuestos de negocio
- Los pedidos pueden incluir múltiples ítems (`FactSalesOrderItem`).  
- Una sesión puede o no estar asociada a un cliente (clientes anónimos).  
- Los pagos y envíos se asocian 1:1 con órdenes, pero pueden variar en tiempos.  
- Todas las fechas derivan de `DimCalendar` y se identifican con `date_sk`.  
- Las claves *surrogate* (`*_sk`) garantizan integridad entre procesos ETL y modelo BI.  
- Los KPIs de negocio se calculan sobre hechos agregados:  
  - **Ventas Totales**, **Ticket Promedio**, **Usuarios Activos**, **NPS**, **Conversion Rate**, **Tiempo de Entrega**, **Revenue Atribuido**.

---

✳️ *Versión 2.0 — Modelo Estrella Completo (EcoBottle AR, 2025)*
