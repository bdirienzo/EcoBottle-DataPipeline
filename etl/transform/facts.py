import pandas as pd
import numpy as np
from etl.transform.utils import write_fact, add_date_sk, CFG, log, find_ci_col, to_dt
import logging

def fact_sales_order(ex, dim_channel, dim_customer, dim_address, dim_store):
    so = ex["sales_order"].rename(columns={"order_id": "order_id_src"}).copy()

    # --- 1) Generar timestamp de la orden (order_ts)
    # Prioridad: order_ts > order_datetime > (order_date + order_time) > created_at > order_date
    if "order_ts" in so.columns:
        ts = pd.to_datetime(so["order_ts"], errors="coerce")
    elif "order_datetime" in so.columns:
        ts = pd.to_datetime(so["order_datetime"], errors="coerce")
    elif {"order_date", "order_time"}.issubset(so.columns):
        ts = pd.to_datetime(so["order_date"].astype(str) + " " + so["order_time"].astype(str), errors="coerce")
    elif "created_at" in so.columns:
        ts = pd.to_datetime(so["created_at"], errors="coerce")
    elif "order_date" in so.columns:
        ts = pd.to_datetime(so["order_date"], errors="coerce")
    else:
        raise ValueError("No se encontró ninguna columna de fecha/hora válida para construir order_ts")

    # Fallback: completar NaT con medianoche
    ts = ts.fillna(pd.Timestamp("1970-01-01"))
    ts = ts.apply(lambda x: x.replace(microsecond=0) if pd.notna(x) else x)
    so["order_ts"] = ts

    # --- 2) Derivar date_sk y time_sk_order
    so = add_date_sk(so, "order_date") if "order_date" in so.columns else add_date_sk(so, "order_ts")
    so["time_sk_order"] = so["order_ts"].dt.strftime("%H%M%S").astype(int)

    # --- 3) Ajustar IDs y normalizar tipos para los joins
    # Normalizar tipos para que los merges maten bien
    so["channel_id"] = pd.to_numeric(so["channel_id"], errors="coerce").astype("Int64")
    so["customer_id"] = pd.to_numeric(so["customer_id"], errors="coerce").astype("Int64")
    so["store_id"] = pd.to_numeric(so["store_id"], errors="coerce").astype("Int64")
    so["shipping_address_id"] = pd.to_numeric(so["shipping_address_id"], errors="coerce").astype("Int64")

    dc = dim_channel.copy()
    dc["channel_id_src"] = pd.to_numeric(dc["channel_id_src"], errors="coerce").astype("Int64")

    # --- 4) Joins con dimensiones
    so = so.merge(dc[["channel_sk", "channel_id_src"]],
                  left_on="channel_id", right_on="channel_id_src", how="left")

    so = so.merge(dim_customer[["customer_sk", "customer_id_src"]],
                  left_on="customer_id", right_on="customer_id_src", how="left")

    ds = dim_store.copy()
    ds["store_id_src"] = pd.to_numeric(ds["store_id_src"], errors="coerce").astype("Int64")
    so = so.merge(
        ds[["store_id_src", "province_sk"]].rename(columns={"province_sk": "store_province_sk"}),
        left_on="store_id", right_on="store_id_src", how="left"
    )

    da = dim_address.copy()
    da["address_id_src"] = pd.to_numeric(da["address_id_src"], errors="coerce").astype("Int64")
    so = so.merge(
        da[["address_id_src", "province_sk"]].rename(columns={"province_sk": "shipping_province_sk"}),
        left_on="shipping_address_id", right_on="address_id_src", how="left"
    )

    # --- 5) Salida final ordenada (clave → tiempo → atributos → métricas)
    out = so[[
        # Claves
        "order_id_src",
        "customer_sk",
        "channel_sk",
        "store_id",
        "shipping_province_sk",

        # Tiempo
        "date_sk",
        "time_sk_order",
        "order_ts",

        # Atributos
        "status",
        "currency_code",

        # Métricas
        "subtotal",
        "tax_amount",
        "shipping_fee",
        "total_amount"
    ]].rename(columns={
        "order_id_src": "order_id",
        "store_id": "store_id_src",
        "shipping_province_sk": "province_sk"
    })

    # --- 6) Tipos seguros
    # date/time → ok forzar a int (pueden tener 0/Na)
    out["date_sk"] = pd.to_numeric(out["date_sk"], errors="coerce").astype("Int64")
    out["time_sk_order"] = pd.to_numeric(out["time_sk_order"], errors="coerce").astype("Int64")

    # FKs como nullable Int64 (no meter 0 fantasma)
    for col in ["customer_sk", "channel_sk", "store_id_src", "province_sk"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").astype("Int64")

    write_fact(out, "fact_sales_order.csv")
    return out

def fact_sales_order_item(ex, dim_channel, dim_product):
    # origen
    oi = ex["sales_order_item"].rename(columns={"order_item_id": "order_item_id_src"}).copy()
    so = ex["sales_order"][["order_id", "order_date", "channel_id"]].copy()

    # base
    base = oi.merge(so, on="order_id", how="left")

    # normalizar tipos para joins
    base["channel_id"] = pd.to_numeric(base["channel_id"], errors="coerce").astype("Int64")
    base["product_id"] = pd.to_numeric(base["product_id"], errors="coerce").astype("Int64")

    dimc = dim_channel.copy()
    dimc["channel_id_src"] = pd.to_numeric(dimc["channel_id_src"], errors="coerce").astype("Int64")

    dp = dim_product.copy()
    dp["product_id_src"] = pd.to_numeric(dp["product_id_src"], errors="coerce").astype("Int64")

    # date_sk desde order_date
    base = add_date_sk(base, "order_date")

    # joins con dimensiones (una sola vez cada uno)
    base = base.merge(dimc[["channel_sk", "channel_id_src"]],
                      left_on="channel_id", right_on="channel_id_src", how="left")
    base = base.merge(dp[["product_sk", "product_id_src"]],
                      left_on="product_id", right_on="product_id_src", how="left")

    # métrica derivada si falta
    if "line_total" not in base.columns:
        base["line_total"] = base["quantity"] * base["unit_price"] - base.get("discount_amount", 0)

    # salida
    out = base[[
        "order_item_id_src", "order_id", "date_sk", "channel_sk", "product_sk",
        "quantity", "unit_price", "discount_amount", "line_total"
    ]].rename(columns={"order_item_id_src": "order_item_id"})

    write_fact(out, "fact_sales_order_item.csv")
    return out

def fact_payment(ex, dim_address):
    pay = ex["payment"].rename(columns={"payment_id": "payment_id_src"})
    pay = add_date_sk(pay, "paid_at")

    so_df = ex["sales_order"]
    candidates = [
        "billing_address_id",
        "billing_adress_id",
        "billing_address",
        "billing_adress"
    ]
    billing_real = find_ci_col(so_df, candidates)

    if billing_real is not None:
        so_norm = so_df[["order_id", billing_real]].rename(columns={billing_real: "billing_address_id"})
        so_norm["billing_address_id"] = pd.to_numeric(so_norm["billing_address_id"], errors="coerce").astype("Int64")
        pay = pay.merge(so_norm, on="order_id", how="left")
    else:
        pay["billing_address_id"] = pd.NA

    dim_addr = dim_address[["address_id_src", "province_sk"]].copy()
    dim_addr["address_id_src"] = pd.to_numeric(dim_addr["address_id_src"], errors="coerce").astype("Int64")
    dim_addr["province_sk"]   = pd.to_numeric(dim_addr["province_sk"],   errors="coerce").astype("Int64")

    pay["billing_address_id"] = pd.to_numeric(pay["billing_address_id"], errors="coerce").astype("Int64")
    pay = pay.merge(
        dim_addr.rename(columns={"province_sk": "billing_province_sk"}),
        left_on="billing_address_id", right_on="address_id_src", how="left"
    )
    pay["billing_province_sk"] = pd.to_numeric(pay["billing_province_sk"], errors="coerce").astype("Int64")

    out = pay[[
        "payment_id_src","order_id","date_sk",
        "billing_address_id","billing_province_sk",
        "method","status","amount"
    ]].rename(columns={"payment_id_src":"payment_id"})

    write_fact(out, "fact_payment.csv")
    return out

def fact_shipment(ex: dict, dim_address: pd.DataFrame, dim_store: pd.DataFrame) -> pd.DataFrame:
    def norm(s: pd.Series) -> pd.Series:
        return (s.astype(str).str.strip()
                .str.replace(r"\.0$", "", regex=True)
                .str.replace(r"\s+", " ", regex=True))

    # --- SHIPMENT ---
    sh = ex["shipment"].rename(columns={"shipment_id": "shipment_id_src"}).copy()
    sh["shipped_at"]   = to_dt(sh.get("shipped_at"))
    sh["delivered_at"] = to_dt(sh.get("delivered_at"))
    sh = add_date_sk(sh, "shipped_at", "shipped_date_sk")
    sh = add_date_sk(sh, "delivered_at", "delivered_date_sk")
    if "carrier" not in sh.columns: sh["carrier"] = pd.NA
    if "status"  not in sh.columns: sh["status"]  = pd.NA
    sh["order_id"] = norm(sh["order_id"])

    # --- SALES ORDER (normalizamos clave de address) ---
    so = ex["sales_order"][["order_id", "shipping_address_id"]].copy()
    so["order_id"] = norm(so["order_id"])
    so["shipping_address_id_norm"] = norm(so["shipping_address_id"])

    # --- DIM ADDRESS (normalizamos clave y usamos SK si existe) ---
    da = dim_address.copy()
    da["address_id_src_norm"] = norm(da["address_id_src"])

    # columnas para traer desde la address
    take_cols = ["address_id_src_norm", "province_sk"]
    has_addr_sk = "address_sk" in da.columns
    if has_addr_sk:
        take_cols.append("address_sk")

    da_n = da[take_cols].rename(columns={"province_sk": "province_sk_addr"})

    # --- JOIN: shipment -> sales_order -> dim_address(normalizada) ---
    base = sh.merge(so[["order_id","shipping_address_id_norm"]], on="order_id", how="left")
    base = base.merge(
        da_n, left_on="shipping_address_id_norm", right_on="address_id_src_norm", how="left"
    )

    # Provincia desde la address (nullable Int64)
    base["province_sk"] = base["province_sk_addr"].astype("Int64")

    # Detectar PICKUP
    is_pickup = base["carrier"].fillna("").str.lower().str.contains("pickup")

    # --- STORE (solo para pickups; ya te funcionó, lo dejamos igual) ---
    ds = dim_store.copy()
    store_key = "store_sk" if "store_sk" in ds.columns else "store_id_src"
    ds_map = ds[[store_key, "province_sk"]].dropna().drop_duplicates().rename(
        columns={store_key: "pickup_store_key", "province_sk": "province_sk_store"}
    )
    base = base.merge(ds_map, left_on="province_sk", right_on="province_sk_store", how="left")

    # --- LOCATORS ---
    # Delivery: address
    if has_addr_sk:
        base["shipping_address_sk"] = np.where(~is_pickup, base["address_sk"], pd.NA)
    else:
        # Fallback: guardamos el natural key para no perder el link (útil mientras agregás address_sk a la dim)
        base["shipping_address_sk"] = np.where(~is_pickup, base["address_id_src_norm"], pd.NA)

    # Pickup: store
    base["pickup_store_sk"] = np.where(is_pickup, base["pickup_store_key"], pd.NA)
    base["location_type"]   = np.where(is_pickup, "store", "address")

    # Lead time (días)
    delta = base["delivered_at"] - base["shipped_at"]
    base["lead_time_days"] = (delta.dt.total_seconds() / 86400.0).round(3)

    out = base[[
        "shipment_id_src", "order_id", "shipped_date_sk", "delivered_date_sk",
        "carrier", "status", "lead_time_days", "province_sk",
        "location_type", "shipping_address_sk", "pickup_store_sk"
    ]].rename(columns={"shipment_id_src": "shipment_id"})

    for c in ("shipped_date_sk", "delivered_date_sk", "province_sk"):
        out[c] = out[c].astype("Int64")

    write_fact(out, "fact_shipment.csv")
    return out

def fact_web_session(ex, dim_channel, online_code: str = "ONLINE") -> pd.DataFrame:
    # 1) Base raw
    ws = ex["web_session"].rename(columns={"session_id": "session_id_src"}).copy()

    # 2) Timestamps crudos -> datetime (sin imputar acá)
    ws["started_at"] = pd.to_datetime(ws.get("started_at"), errors="coerce")
    if "ended_at" in ws.columns:
        ws["ended_at"] = pd.to_datetime(ws.get("ended_at"), errors="coerce")
    else:
        ws["ended_at"] = pd.NaT

    # 3) date_sk desde started_at (requisito para la atribución por día/cliente)
    ws = add_date_sk(ws, "started_at")

    # 4) Tipos y saneo
    ws["customer_id"] = pd.to_numeric(ws.get("customer_id"), errors="coerce").astype("Int64")
    # Si algún ended_at < started_at (datos sucios), los invertimos
    bad = ws["ended_at"].notna() & ws["started_at"].notna() & (ws["ended_at"] < ws["started_at"])
    if bad.any():
        tmp = ws.loc[bad, "started_at"].copy()
        ws.loc[bad, "started_at"] = ws.loc[bad, "ended_at"]
        ws.loc[bad, "ended_at"] = tmp

    # 5) Canal ONLINE → channel_sk
    dc = dim_channel.copy()
    online_rows = pd.DataFrame()
    if "code" in dc.columns:
        online_rows = dc[dc["code"].astype(str).str.upper() == str(online_code).upper()]
        if online_rows.empty:
            online_rows = dc[dc["code"].astype(str).str.upper().str.contains("ONLINE", na=False)]
    online_sk = online_rows["channel_sk"].iloc[0] if not online_rows.empty else pd.NA
    ws["channel_sk"] = online_sk

    # 6) Salida final (incluye started_at y ended_at)
    out = ws[[
        "session_id_src",
        "date_sk",
        "customer_id",
        "source",
        "device",
        "channel_sk",
        "started_at",
        "ended_at",
    ]].rename(columns={"session_id_src": "session_id"})

    # Tipos “duros” para SKs, pero sin fillna(0)
    out["date_sk"]    = pd.to_numeric(out["date_sk"], errors="coerce").astype("Int64")
    out["channel_sk"] = pd.to_numeric(out["channel_sk"], errors="coerce").astype("Int64")

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
    window_hours: int = 24,                 # ventana para sesión previa
    default_session_minutes: int = 30,      # si no hay ended_at, imputamos duración
    prefer: str = "in_session_then_prev",   # 'in_session_only' | 'prev_only' | 'in_session_then_prev'
) -> pd.DataFrame:

    log.info("=== FACT: Marketing Attribution (hora/ventana) ===")

    # --- 1) Validar columnas mínimas en WEB (acepta customer_id o customer_sk)
    base_ws_needed = {"session_id", "date_sk", "source", "device", "channel_sk", "started_at"}
    missing_ws = base_ws_needed - set(fact_web_session.columns)
    if missing_ws:
        raise ValueError(f"fact_web_session le faltan columnas: {missing_ws}")

    has_cust_sk = "customer_sk" in fact_web_session.columns
    has_cust_id = "customer_id" in fact_web_session.columns
    if not (has_cust_sk or has_cust_id):
        raise ValueError("fact_web_session debe tener 'customer_sk' o 'customer_id'.")

    ws_cols = list(base_ws_needed) + (["customer_sk"] if has_cust_sk else ["customer_id"])
    if "ended_at" in fact_web_session.columns:
        ws_cols.append("ended_at")

    ws = fact_web_session[ws_cols].copy()

    # normalizar a customer_sk (entero)
    if has_cust_sk:
        ws["customer_sk"] = pd.to_numeric(ws["customer_sk"], errors="coerce")
    else:
        ws = ws.rename(columns={"customer_id": "customer_sk"})
        ws["customer_sk"] = pd.to_numeric(ws["customer_sk"], errors="coerce")

    # solo sesiones identificadas
    ws = ws[ws["customer_sk"].notna()].copy()

    for col in ["customer_sk", "date_sk", "channel_sk"]:
        ws[col] = pd.to_numeric(ws[col], errors="coerce").astype("Int64")

    # timestamps de sesión
    ws["started_at"] = pd.to_datetime(ws["started_at"], errors="coerce")
    if "ended_at" in ws.columns:
        ws["ended_at"] = pd.to_datetime(ws["ended_at"], errors="coerce")
    else:
        ws["ended_at"] = pd.NaT

    # imputar ended_at si falta
    missing_end = ws["ended_at"].isna()
    if missing_end.any():
        ws.loc[missing_end, "ended_at"] = ws.loc[missing_end, "started_at"] + pd.to_timedelta(default_session_minutes, unit="m")

    # filtrar sesiones válidas
    ws = ws.dropna(subset=["started_at", "ended_at"]).copy()

    # --- 2) Validar y preparar SALES
    req_so = {"order_id", "customer_sk", "date_sk", "total_amount", "order_ts"}
    missing_so = req_so - set(fact_sales_order.columns)
    if missing_so:
        raise ValueError(f"fact_sales_order le faltan columnas: {missing_so}")

    so = fact_sales_order[list(req_so)].copy()
    so = so[so["customer_sk"].notna()].copy()

    for col in ["customer_sk", "date_sk"]:
        so[col] = pd.to_numeric(so[col], errors="coerce").astype("Int64")

    so["order_ts"] = pd.to_datetime(so["order_ts"], errors="coerce")
    so = so.dropna(subset=["order_ts"]).copy()

    # --- 3) Match “dentro de la sesión” (pre-filtro por cliente y día)
    merged = so.merge(
        ws[["session_id", "customer_sk", "date_sk", "channel_sk", "source", "device", "started_at", "ended_at"]],
        on=["customer_sk", "date_sk"], how="left", suffixes=("_ord", "_sess")
    )

    in_session_mask = (merged["order_ts"] >= merged["started_at"]) & (merged["order_ts"] <= merged["ended_at"])
    in_session = merged[in_session_mask].copy()

    # si una orden cae en múltiples sesiones (solapadas), quedarse con la más cercana al order_ts
    if not in_session.empty:
        in_session["_dist_sec"] = (in_session["order_ts"] - in_session["started_at"]).abs().dt.total_seconds()
        in_session = in_session.sort_values(["order_id", "_dist_sec"], kind="mergesort")
        in_session = in_session.drop_duplicates(subset=["order_id"], keep="first")

    # --- 4) Match “sesión previa” para órdenes no cubiertas (merge_asof por cliente)
    covered = set(in_session["order_id"]) if not in_session.empty else set()
    pending = so[~so["order_id"].isin(covered)].copy()

    # Normalizar tipos para el merge_asof por grupo
    pending["customer_sk"] = pd.to_numeric(pending["customer_sk"], errors="coerce").astype("int64")
    pending["order_ts"] = pd.to_datetime(pending["order_ts"], errors="coerce")

    ws["customer_sk"] = pd.to_numeric(ws["customer_sk"], errors="coerce").astype("int64")
    ws["started_at"] = pd.to_datetime(ws["started_at"], errors="coerce")
    ws["ended_at"] = pd.to_datetime(ws["ended_at"], errors="coerce")

    chunks = []
    for cust, so_c in pending.groupby("customer_sk", sort=False):
        ws_c = ws.loc[ws["customer_sk"] == cust, ["session_id", "customer_sk", "started_at", "ended_at", "channel_sk", "source", "device"]]
        if ws_c.empty:
            continue

        so_c = so_c.dropna(subset=["order_ts"]).sort_values("order_ts", kind="mergesort").reset_index(drop=True)
        ws_c = ws_c.dropna(subset=["started_at"]).sort_values("started_at", kind="mergesort").reset_index(drop=True)

        m = pd.merge_asof(
            so_c,
            ws_c,
            left_on="order_ts",
            right_on="started_at",
            direction="backward",
            allow_exact_matches=True,
        )

        # normalizar customer_sk (evitar customer_sk_x / customer_sk_y)
        if "customer_sk_x" in m.columns:
            m["customer_sk"] = m["customer_sk_x"]
            m = m.drop(columns=[c for c in ["customer_sk_x", "customer_sk_y"] if c in m.columns])

        chunks.append(m)

    prev = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame(columns=[
        "order_id","customer_sk","date_sk","total_amount","order_ts",
        "session_id","started_at","ended_at","channel_sk","source","device"
    ])

    # aplicar ventana
    max_delta = pd.to_timedelta(window_hours, unit="h")
    prev["_delta"] = prev["order_ts"] - prev["started_at"]
    prev_ok = prev[(prev["_delta"].notna()) & (prev["_delta"] >= pd.Timedelta(0)) & (prev["_delta"] <= max_delta)].copy()

    # preferencia de regla
    if prefer == "in_session_only":
        prev_ok = prev_ok.iloc[0:0]
    if prefer == "prev_only":
        in_session = in_session.iloc[0:0]

    # --- 5) Unificar matches (una sesión por orden)
    cols = ["order_id", "customer_sk", "date_sk", "total_amount", "session_id", "channel_sk", "source", "device"]
    a = in_session[cols].copy() if not in_session.empty else pd.DataFrame(columns=cols)
    b = prev_ok[cols].copy() if not prev_ok.empty else pd.DataFrame(columns=cols)

    matched = pd.concat([a, b], ignore_index=True)
    if not matched.empty:
        matched["orders_attributed"] = 1
        matched["revenue_attributed"] = matched["total_amount"].astype(float)

    # --- 6) Agregar al nivel sesión–día
    agg = (
        matched.groupby(["session_id", "customer_sk", "date_sk", "channel_sk", "source", "device"], as_index=False)
               .agg(orders_attributed=("orders_attributed", "sum"),
                    revenue_attributed=("revenue_attributed", "sum"))
        if not matched.empty else
        pd.DataFrame(columns=["session_id", "customer_sk", "date_sk", "channel_sk", "source", "device",
                              "orders_attributed", "revenue_attributed"])
    )

    # --- 7) Salida a grano sesión–día (todas las sesiones identificadas del día)
    base = ws[["session_id", "customer_sk", "date_sk", "channel_sk", "source", "device"]].drop_duplicates().copy()
    out = base.merge(
        agg,
        on=["session_id", "customer_sk", "date_sk", "channel_sk", "source", "device"],
        how="left"
    )

    out["orders_attributed"]  = out["orders_attributed"].fillna(0).astype("int64")
    out["revenue_attributed"] = out["revenue_attributed"].fillna(0.0).astype(float)
    out["converted_flag"]     = (out["orders_attributed"] > 0).astype("int64")

    # SKs como nullable (no introducir 0)
    for col in ["customer_sk", "date_sk", "channel_sk"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").astype("Int64")

    # Métricas / flags con default 0
    out["orders_attributed"] = pd.to_numeric(out["orders_attributed"], errors="coerce").fillna(0).astype("int64")
    out["revenue_attributed"] = pd.to_numeric(out["revenue_attributed"], errors="coerce").fillna(0.0).astype(float)
    out["converted_flag"] = (out["orders_attributed"] > 0).astype("int64")

    # --- 8) Persistencia + log
    out = out[[
        "session_id",
        "customer_sk",
        "channel_sk",
        "source",
        "device",
        "date_sk",
        "converted_flag",
        "orders_attributed",
        "revenue_attributed",
    ]]

    write_fact(out, "fact_marketing_attribution.csv")
    return out