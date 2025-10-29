# 📘 Diccionario de Datos – EcoBottle AR

Este documento describe las tablas, campos y relaciones del **modelo estrella** implementado para el proyecto **EcoBottle AR – Data Warehouse & BI Dashboard**.

---

## 🧠 Tabla de Hechos

### FactSalesOrderItem
Contiene el detalle de las líneas de venta por producto, pedido y fecha.

| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| sales_order_item_id | INTEGER | Identificador único de línea de venta | PK |
| sales_order_id | INTEGER | Identificador del pedido | FK |
| product_id | INTEGER | Producto vendido | FK |
| store_id | INTEGER | Tienda asociada a la venta | FK |
| channel_id | INTEGER | Canal de venta (online/offline) | FK |
| customer_id | INTEGER | Cliente que realiza la compra | FK |
| date_id | INTEGER | Fecha de la venta | FK |
| quantity | INTEGER | Cantidad vendida | — |
| unit_price | FLOAT | Precio unitario del producto | — |
| amount | FLOAT | Monto total (quantity × unit_price) | — |

---

### FactPayment
Registra los pagos asociados a pedidos y clientes.

| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| payment_id | INTEGER | Identificador del pago | PK |
| date_id | INTEGER | Fecha del pago | FK |
| customer_id | INTEGER | Cliente que realiza el pago | FK |
| sales_order_id | INTEGER | Pedido asociado al pago | FK |
| method | TEXT | Medio de pago (tarjeta, transferencia, etc.) | — |
| status | TEXT | Estado del pago (aprobado, rechazado, pendiente) | — |
| amount | FLOAT | Monto abonado | — |

---

### FactShipment
Contiene los envíos realizados a clientes.

| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| shipment_id | INTEGER | Identificador del envío | PK |
| ship_date_id | INTEGER | Fecha de envío | FK |
| customer_id | INTEGER | Cliente destinatario | FK |
| store_id | INTEGER | Tienda emisora | FK |
| province_id | INTEGER | Provincia de destino | FK |
| carrier | TEXT | Empresa de transporte | — |
| cost | FLOAT | Costo de envío | — |
| delivery_days | INTEGER | Días de entrega estimados | — |

---

### FactWebSession
Representa la actividad online de los usuarios.

| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| session_id | INTEGER | Identificador de sesión | PK |
| session_date_id | INTEGER | Fecha de la sesión | FK |
| customer_id | INTEGER | Usuario identificado | FK |
| channel_id | INTEGER | Canal digital de acceso | FK |
| duration_seconds | INTEGER | Duración de la sesión en segundos | — |
| device_type | TEXT | Tipo de dispositivo (móvil, desktop, tablet) | — |
| source_medium | TEXT | Fuente o medio de adquisición (orgánico, pago, referido) | — |

---

### FactNpsResponse
Almacena las respuestas de encuestas de satisfacción (NPS).

| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| response_id | INTEGER | Identificador de respuesta | PK |
| response_date_id | INTEGER | Fecha de la respuesta | FK |
| customer_id | INTEGER | Cliente que responde | FK |
| score | INTEGER | Valor NPS (0–10) | — |
| classification | TEXT | Promotor / Neutro / Detractor | — |

---

## 🌐 Tablas Dimensión

### DimCustomer
| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| customer_id | INTEGER | Identificador del cliente | PK |
| customer_code | TEXT | Código de cliente | — |
| full_name | TEXT | Nombre y apellido | — |
| email | TEXT | Correo electrónico | — |
| province_id | INTEGER | Provincia de residencia | FK |
| address_id | INTEGER | Dirección asociada | FK |
| created_at | DATE | Fecha de alta del cliente | — |

---

### DimProduct
| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| product_id | INTEGER | Identificador del producto | PK |
| product_code | TEXT | Código del producto | — |
| product_name | TEXT | Nombre del producto | — |
| category_id | INTEGER | Categoría del producto | FK |
| brand | TEXT | Marca o línea de producto | — |
| unit_price | FLOAT | Precio unitario | — |

---

### DimStore
| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| store_id | INTEGER | Identificador de tienda | PK |
| store_name | TEXT | Nombre de la sucursal o punto de venta | — |
| province_id | INTEGER | Provincia donde opera | FK |

---

### DimChannel
| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| channel_id | INTEGER | Identificador del canal | PK |
| channel_name | TEXT | Canal de venta (Online, Retail, Distribuidor) | — |

---

### DimProvince
| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| province_id | INTEGER | Identificador de provincia | PK |
| province_name | TEXT | Nombre de la provincia | — |
| region | TEXT | Región geográfica (NOA, Cuyo, Patagonia, etc.) | — |

---

### DimAddress
| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| address_id | INTEGER | Identificador de dirección | PK |
| street | TEXT | Calle y número | — |
| city | TEXT | Ciudad o localidad | — |
| postal_code | TEXT | Código postal | — |
| province_id | INTEGER | Provincia correspondiente | FK |

---

### DimCalendar
| Campo | Tipo | Descripción | Clave |
|--------|------|-------------|--------|
| date_id | INTEGER | Identificador de fecha | PK |
| full_date | DATE | Fecha completa | — |
| year | INTEGER | Año | — |
| quarter | INTEGER | Trimestre (1–4) | — |
| month | INTEGER | Mes (1–12) | — |
| month_name | TEXT | Nombre del mes | — |
| day | INTEGER | Día del mes | — |
| weekday | TEXT | Día de la semana | — |
| is_weekend | BOOLEAN | Indica si es fin de semana | — |

---

## 🔗 Relaciones Principales (PK–FK)
| Tabla | Relación | Clave Foránea |
|--------|-----------|---------------|
| FactSalesOrderItem | → DimCustomer | customer_id |
| FactSalesOrderItem | → DimProduct | product_id |
| FactSalesOrderItem | → DimStore | store_id |
| FactSalesOrderItem | → DimChannel | channel_id |
| FactPayment | → DimCustomer | customer_id |
| FactShipment | → DimStore | store_id |
| FactShipment | → DimProvince | province_id |
| FactWebSession | → DimCustomer | customer_id |
| FactNpsResponse | → DimCustomer | customer_id |
| DimCustomer | → DimProvince | province_id |
| DimCustomer | → DimAddress | address_id |

---

## 🧩 Supuestos de negocio
- Cada cliente pertenece a **una provincia y una dirección principal**.  
- Un pedido puede incluir **múltiples productos** (representados en `FactSalesOrderItem`).  
- Los pagos pueden ser **parciales o múltiples** por pedido.  
- Las sesiones web se registran solo para **usuarios logueados o identificables**.  
- Las fechas se gestionan de manera centralizada a través de `DimCalendar`.  
- Los valores NPS se normalizan en una escala de 0 a 10.

---
