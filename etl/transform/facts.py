import pandas as pd
from etl.transform.utils import write_fact, add_date_sk, CFG

def fact_sales_order(ex, dim_channel, dim_customer, dim_address, dim_store):
    so = ex["sales_order"].rename(columns={"order_id": "order_id_src"})
    so = add_date_sk(so, "order_date")

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


def fact_payment(ex):
    pay = ex["payment"].rename(columns={"payment_id": "payment_id_src"})
    pay = add_date_sk(pay, "paid_at")

    out = pay[["payment_id_src", "order_id", "date_sk", "method", "status", "amount"]].rename(columns={"payment_id_src": "payment_id"})
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

    out = base[[
        "shipment_id_src", "order_id", "shipped_date_sk", "delivered_date_sk",
        "carrier", "status", "lead_time_days", "province_sk"
    ]].rename(columns={"shipment_id_src": "shipment_id"})

    write_fact(out, "fact_shipment.csv")
    return out


def fact_web_session(ex, dim_channel):
    ws = ex["web_session"].rename(columns={"session_id": "session_id_src"})
    ws = add_date_sk(ws, "started_at")

    online_sk = dim_channel.loc[dim_channel["code"].str.upper() == "ONLINE", "channel_sk"].iloc[0]
    ws["channel_sk"] = online_sk

    out = ws[["session_id_src", "date_sk", "customer_id", "source", "device", "channel_sk"]].rename(
        columns={"session_id_src": "session_id"}
    )
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
