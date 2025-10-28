# Diccionario de datos – EcoBottle AR

## DimDate
| Campo | Tipo | Descripción | Reglas / Dominio / Supuestos |
|---|---|---|---|
| date_id | INTEGER | Clave surrogate | Única, generada en ETL |
| full_date | DATE | Fecha calendario ISO | Única, formato YYYY-MM-DD |
| year | INTEGER | Año | 4 dígitos |
| quarter | INTEGER | Trimestre | 1–4 |
| month | INTEGER | Mes | 1–12 |
| is_weekend | INTEGER | 0 = no, 1 = sí | Derivado de la fecha |

## DimProduct
| Campo | Tipo | Descripción | Reglas / Dominio / Supuestos |
|---|---|---|---|
| product_id | INTEGER | Clave surrogate | Única |
| product_code | TEXT | Código natural | Único si existe |
| product_name | TEXT | Nombre | Trim, no nulo |
| category | TEXT | Categoría comercial | Dominio controlado |
| unit_price | REAL | Precio unitario | ≥ 0 |

## DimChannel
| Campo | Tipo | Descripción | Reglas / Dominio / Supuestos |
|---|---|---|---|
| channel_id | INTEGER | Clave surrogate | Única |
| channel_name | TEXT | Nombre del canal | Dominio: Online, Offline, … |

## DimStore
| Campo | Tipo | Descripción | Reglas / Dominio / Supuestos |
|---|---|---|---|
| store_id | INTEGER | Clave surrogate | Única |
| store_name | TEXT | Nombre tienda | Único |
| province_id | INTEGER | FK a DimProvince | 0 si desconocido |

## DimProvince
| Campo | Tipo | Descripción | Reglas / Dominio / Supuestos |
|---|---|---|---|
| province_id | INTEGER | Clave surrogate | Única |
| province_name | TEXT | Provincia | Dominio: AR provinc. normales |
| region | TEXT | Región | Opcional |

## DimCustomer
| Campo | Tipo | Descripción | Reglas / Dominio / Supuestos |
|---|---|---|---|
| customer_id | INTEGER | Clave surrogate | Única |
| customer_code | TEXT | ID natural | Único si existe |
| full_name | TEXT | Nombre completo | Opcional si no está |
| email | TEXT | Correo | Formato válido (si aplica) |
| province_id | INTEGER | FK a DimProvince | 0 si desconocido |
| created_at | DATE | Alta de cliente | ISO |

## FactSales
| Campo | Tipo | Descripción | Reglas / Dominio / Supuestos |
|---|---|---|---|
| sales_line_id | INTEGER | Clave surrogate | Única |
| date_id | INTEGER | FK DimDate | Requerido |
| customer_id | INTEGER | FK DimCustomer | 0 si desconocido |
| product_id | INTEGER | FK DimProduct | Requerido |
| store_id | INTEGER | FK DimStore | Requerido |
| channel_id | INTEGER | FK DimChannel | Requerido |
| quantity | INTEGER | Ítems vendidos | ≥ 1 |
| unit_price | REAL | Precio unitario | ≥ 0 |
| amount | REAL | Importe | quantity*unit_price |

## FactNPS (si aplica)
| Campo | Tipo | Descripción | Reglas / Dominio / Supuestos |
|---|---|---|---|
| nps_id | INTEGER | Clave surrogate | Única |
| date_id | INTEGER | FK DimDate | Requerido |
| customer_id | INTEGER | FK DimCustomer | Opcional |
| score | INTEGER | Puntaje NPS | 0–10 |
| classification | TEXT | Clase NPS | {Detractor, Neutral, Promoter}
