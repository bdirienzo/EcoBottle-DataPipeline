import pandas as pd
from etl.transform.utils import write_fact, add_date_sk, CFG, log

def fact_sales_order(ex, dim_channel, dim_customer, dim_address, dim_store):
    so = ex["sales_order"].rename(columns={"order_id": "order_id_src"})
    so = add_date_sk(so, "order_date")
    so["store_id"] = so["store_id"].astype("Int64")

    so = so.merge(dim_channel[["channel_sk", "channel_id_src"]], left_on="channel_id", right_on="channel_id_src", how="left")
    so = so.merge(dim_customer[["customer_sk", "customer_id_src"]], left_on="customer_id", right_on="customer_id_src", how="left")
    so = so.merge(dim_store[["store_id_src", "province_sk"]].rename(columns={"province_sk": "store_province_sk"}),
                  left_on="store_id", right_on="store_id_src", how="left")
    so = so.merge(dim_address[["address_id_src", "province_sk"]].rename(columns={"province_sk": "shipping_province_sk"}),
                  left_on="shipping_address_id", right_on="address_id_src", how="left")

    out = so[[
        "order_id_src", "date_sk", "channel_sk", "customer_sk", "store_id",
        "shipping_province_sk", "subtotal", "tax_amount", "shipping_fee", "total_amount",
        "status", "currency_code"
    ]].rename(columns={
        "order_id_src": "order_id",
        "store_id": "store_id_src",
        "shipping_province_sk": "province_sk"
    })

    write_fact(out, "fact_sales_order.csv")
    return out


def fact_sales_order_item(ex, dim_channel, dim_product):
    oi = ex["sales_order_item"].rename(columns={"order_item_id": "order_item_id_src"})
    so = ex["sales_order"][["order_id", "order_date", "channel_id"]]

    base = oi.merge(so, on="order_id", how="left")
    base = add_date_sk(base, "order_date")
    base = base.merge(dim_channel[["channel_sk", "channel_id_src"]], left_on="channel_id", right_on="channel_id_src", how="left")
    base = base.merge(dim_product[["product_sk", "product_id_src"]], left_on="product_id", right_on="product_id_src", how="left")

    if "line_total" not in base.columns:
        base["line_total"] = base["quantity"] * base["unit_price"] - base.get("discount_amount", 0)

    out = base[[
        "order_item_id_src", "order_id", "date_sk", "channel_sk", "product_sk",
        "quantity", "unit_price", "discount_amount", "line_total"
    ]].rename(columns={"order_item_id_src": "order_item_id"})

    write_fact(out, "fact_sales_order_item.csv")
    return out

def fact_payment(ex, dim_address):
    pay = ex["payment"].rename(columns={"payment_id": "payment_id_src"})
    pay = add_date_sk(pay, "paid_at")

    so_cols = ex["sales_order"].columns.str.lower().tolist()
    candidate_cols = [
        "billing_address_id",
        "billing_adress_id",     # typo común
        "billing_address",       # por si viene sin _id
        "billing_adress"         # otro typo
    ]
    billing_col = next((c for c in candidate_cols if c in so_cols), None)

    if billing_col is not None:
        so_norm = ex["sales_order"][["order_id", billing_col]]
        so_norm = so_norm.rename(columns={billing_col: "billing_address_id"})
        so_norm["billing_address_id"] = (
            pd.to_numeric(so_norm["billing_address_id"], errors="coerce")
              .astype("Int64")
        )
        pay = pay.merge(so_norm, on="order_id", how="left")
    else:
        pay["billing_address_id"] = pd.NA

    dim_addr = dim_address[["address_id_src", "province_sk"]].copy()
    dim_addr["address_id_src"] = (
        pd.to_numeric(dim_addr["address_id_src"], errors="coerce").astype("Int64")
    )
    dim_addr["province_sk"] = (
        pd.to_numeric(dim_addr["province_sk"], errors="coerce").astype("Int64")
    )

    pay["billing_address_id"] = (
        pd.to_numeric(pay["billing_address_id"], errors="coerce").astype("Int64")
    )

    pay = pay.merge(
        dim_addr.rename(columns={"province_sk": "billing_province_sk"}),
        left_on="billing_address_id",
        right_on="address_id_src",
        how="left"
    )

    pay["billing_province_sk"] = (
        pd.to_numeric(pay["billing_province_sk"], errors="coerce").astype("Int64")
    )

    out = pay[[
        "payment_id_src", "order_id", "date_sk",
        "billing_address_id", "billing_province_sk",
        "method", "status", "amount"
    ]].rename(columns={"payment_id_src": "payment_id"})

    write_fact(out, "fact_payment.csv")
    return out


def fact_shipment(ex, dim_address):
    sh = ex["shipment"].rename(columns={"shipment_id": "shipment_id_src"})
    sh = add_date_sk(sh, "shipped_at", "shipped_date_sk")
    sh = add_date_sk(sh, "delivered_at", "delivered_date_sk")

    so = ex["sales_order"][["order_id", "shipping_address_id"]]
    da = dim_address[["address_id_src", "province_sk"]]
    base = sh.merge(so, on="order_id", how="left").merge(
        da, left_on="shipping_address_id", right_on="address_id_src", how="left"
    )

    from etl.transform.utils import to_dt
    base["shipped_at"] = to_dt(ex["shipment"]["shipped_at"])
    base["delivered_at"] = to_dt(ex["shipment"]["delivered_at"])
    base["lead_time_days"] = (base["delivered_at"] - base["shipped_at"]).dt.total_seconds() / 86400.0

    delta = base["delivered_at"] - base["shipped_at"]
    base["lead_time_days"] = delta.dt.days.astype("Int64")

    out = base[[
        "shipment_id_src", "order_id", "shipped_date_sk", "delivered_date_sk",
        "carrier", "status", "lead_time_days", "province_sk"
    ]].rename(columns={"shipment_id_src": "shipment_id"})

    write_fact(out, "fact_shipment.csv")
    return out


def fact_web_session(ex, dim_channel):
    ws = ex["web_session"].rename(columns={"session_id": "session_id_src"})
    ws = add_date_sk(ws, "started_at")

    ws["customer_id"] = pd.to_numeric(ws["customer_id"], errors="coerce").astype("Int64")

    online_sk = dim_channel.loc[
        dim_channel["code"].str.upper() == "ONLINE", "channel_sk"
    ].iloc[0]
    ws["channel_sk"] = online_sk

    out = ws[
        ["session_id_src", "date_sk", "customer_id", "source", "device", "channel_sk"]
    ].rename(columns={"session_id_src": "session_id"})

    write_fact(out, "fact_web_session.csv")
    return out


def fact_nps_response(ex, dim_channel):
    nps = ex["nps_response"].rename(columns={"nps_id": "nps_id_src"})
    nps = add_date_sk(nps, "responded_at")
    nps = nps.merge(dim_channel[["channel_sk", "channel_id_src"]],
                    left_on="channel_id", right_on="channel_id_src", how="left")

    br = CFG["business_rules"]["nps"]
    nps["is_detractor"] = (nps["score"] <= br["detractor_max"]).astype(int)
    nps["is_passive"] = ((nps["score"] >= br["passive_min"]) & (nps["score"] <= br["passive_max"])).astype(int)
    nps["is_promoter"] = (nps["score"] >= br["promoter_min"]).astype(int)

    out = nps[[
        "nps_id_src", "date_sk", "channel_sk", "customer_id", "score",
        "is_detractor", "is_passive", "is_promoter", "comment"
    ]].rename(columns={"nps_id_src": "nps_id"})

    write_fact(out, "fact_nps_response.csv")
    return out

def fact_marketing_attribution(
    ex,
    fact_web_session: pd.DataFrame,
    fact_sales_order: pd.DataFrame,
    method: str = "last_touch_of_day",  # 'first_touch_of_day' | 'last_touch_of_day'
) -> pd.DataFrame:
    """
    Grain: 1 fila por sesión web identificada (session_id) y día (date_sk).
    Atribuye TODO el revenue/órdenes del día a UNA sola sesión del cliente (entera),
    evitando fracciones en orders_attributed. Acepta customer_id o customer_sk.
    """

    log.info("=== FACT: Marketing Attribution (día de sesión) ===")

    # --- 1) Validar columnas mínimas en WEB, aceptar id o sk
    base_ws_needed = {"session_id", "date_sk", "source", "device", "channel_sk"}
    missing_ws = base_ws_needed - set(fact_web_session.columns)
    if missing_ws:
        raise ValueError(f"fact_web_session le faltan columnas: {missing_ws}")

    has_cust_sk = "customer_sk" in fact_web_session.columns
    has_cust_id = "customer_id" in fact_web_session.columns
    if not (has_cust_sk or has_cust_id):
        raise ValueError("fact_web_session debe tener 'customer_sk' o 'customer_id'.")

    ws_cols = list(base_ws_needed) + (["customer_sk"] if has_cust_sk else ["customer_id"])
    ws = fact_web_session[ws_cols].copy()

    # normalizar a customer_sk (entero)
    if has_cust_sk:
        ws["customer_sk"] = pd.to_numeric(ws["customer_sk"], errors="coerce")
    else:
        ws = ws.rename(columns={"customer_id": "customer_sk"})
        ws["customer_sk"] = pd.to_numeric(ws["customer_sk"], errors="coerce")

    # solo sesiones identificadas
    ws = ws[ws["customer_sk"].notna()].copy()

    # tipificación estricta (IDs como enteros)
    for col in ["customer_sk", "date_sk", "channel_sk"]:
        ws[col] = pd.to_numeric(ws[col], errors="coerce").fillna(0).astype("int64")

    # --- 2) Validar y preparar SALES
    req_so = {"order_id", "customer_sk", "date_sk", "total_amount"}
    missing_so = req_so - set(fact_sales_order.columns)
    if missing_so:
        raise ValueError(f"fact_sales_order le faltan columnas: {missing_so}")

    so = fact_sales_order[list(req_so)].copy()
    so = so[so["customer_sk"].notna()]
    so["customer_sk"] = pd.to_numeric(so["customer_sk"], errors="coerce").fillna(0).astype("int64")
    so["date_sk"] = pd.to_numeric(so["date_sk"], errors="coerce").fillna(0).astype("int64")

    # ventas por cliente + día (maneja múltiples pedidos ese día)
    so_day = (
        so.groupby(["customer_sk", "date_sk"], as_index=False)
          .agg(orders_count=("order_id", "count"),
               revenue=("total_amount", "sum"))
    )

    # --- 3) Join sesiones ↔ pedidos por (cliente, día)
    conv = ws.merge(so_day, on=["customer_sk", "date_sk"], how="left", validate="m:1")
    conv["orders_count"] = conv["orders_count"].fillna(0).astype("int64")
    conv["revenue"] = conv["revenue"].fillna(0.0).astype(float)

    # flag de conversión por sesión (entero)
    conv["converted_flag"] = (conv["orders_count"] > 0).astype("int64")

    # --- 4) Elegir sesión ganadora (primera o última) para asignar TODO sin fracciones
    key = ["customer_sk", "date_sk"]

    # clave de orden única para evitar columnas duplicadas
    if "started_at" in fact_web_session.columns:
        order_map = (
            fact_web_session[["session_id", "started_at"]]
            .drop_duplicates("session_id")
            .rename(columns={"started_at": "_order_key"})
        )
        conv = conv.merge(order_map, on="session_id", how="left")
    else:
        conv["_order_key"] = conv["session_id"]

    if method == "first_touch_of_day":
        conv["_rank"] = conv.groupby(key)["_order_key"].rank(method="first", ascending=True)
    elif method == "last_touch_of_day":
        conv["_rank"] = conv.groupby(key)["_order_key"].rank(method="first", ascending=False)
    else:
        raise ValueError("method inválido. Usa: 'first_touch_of_day' o 'last_touch_of_day'.")

    is_winner = (conv["_rank"] == 1) & (conv["orders_count"] > 0)
    conv["orders_attributed"]  = (is_winner.astype("int64") * conv["orders_count"]).astype("int64")
    conv["revenue_attributed"] = (is_winner.astype(int) * conv["revenue"]).astype(float)

    # --- 5) Salida final, sin decimales donde no corresponde
    out = conv[[
        "session_id",
        "customer_sk",
        "channel_sk",
        "source",
        "device",
        "date_sk",
        "converted_flag",
        "orders_attributed",
        "revenue_attributed",
    ]].copy()

    for col in ["customer_sk", "channel_sk", "date_sk", "converted_flag", "orders_attributed"]:
        out[col] = out[col].astype("int64")

    # --- 6) Persistencia + log
    write_fact(out, "fact_marketing_attribution.csv")
    log.info(
        f"FactMarketingAttribution: sesiones={len(out)}, "
        f"convertidas={int(out['converted_flag'].sum())}, "
        f"orders_attr={int(out['orders_attributed'].sum())}, "
        f"revenue_attr={float(out['revenue_attributed'].sum()):.2f}"
    )
    return out
