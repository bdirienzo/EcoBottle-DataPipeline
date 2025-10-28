import pandas as pd
from etl.transform.utils import (
    write_dim, make_sk, to_dt, CFG
)

def build_dim_calendar(extracts) -> pd.DataFrame:
    dates = []
    for name, col in [
        ("sales_order","order_date"),
        ("payment","paid_at"),
        ("shipment","shipped_at"),
        ("shipment","delivered_at"),
        ("web_session","started_at"),
        ("nps_response","responded_at"),
    ]:
        if name in extracts and col in extracts[name].columns:
            dates.append(pd.to_datetime(extracts[name][col], errors="coerce"))

    s = pd.concat(dates).dropna()
    min_d, max_d = s.min().date(), s.max().date()
    cal = pd.DataFrame({"date": pd.date_range(min_d, max_d, freq="D")})
    cal["date_sk"] = cal["date"].dt.strftime("%Y%m%d").astype(int)
    cal["year"] = cal["date"].dt.year
    cal["quarter"] = cal["date"].dt.quarter
    cal["month"] = cal["date"].dt.month
    cal["day"] = cal["date"].dt.day
    cal["month_name"] = cal["date"].dt.month_name()
    cal["is_month_end"] = cal["date"].dt.is_month_end
    write_dim(cal[["date_sk","date","year","quarter","month","day","month_name","is_month_end"]],
              "dim_calendar.csv")
    return cal

def build_dim_channel(extracts) -> pd.DataFrame:
    ch = extracts["channel"].rename(columns={"channel_id":"channel_id_src"})
    ch = make_sk(ch, order_by="code", sk_name="channel_sk")
    write_dim(ch[["channel_sk","channel_id_src","code","name"]], "dim_channel.csv")
    return ch

def build_dim_province(extracts) -> pd.DataFrame:
    pr = extracts["province"].rename(columns={"province_id":"province_id_src"})
    pr = make_sk(pr, order_by="name", sk_name="province_sk")
    write_dim(pr[["province_sk","province_id_src","name","code"]], "dim_province.csv")
    return pr

def build_dim_address(extracts, dim_province) -> pd.DataFrame:
    ad = extracts["address"].rename(columns={"address_id":"address_id_src"})
    out = ad.merge(dim_province[["province_sk","province_id_src"]],
                   left_on="province_id", right_on="province_id_src", how="left")
    write_dim(out[["address_id_src","line1","line2","city","postal_code","country_code","province_id","province_sk"]],
              "dim_address.csv")
    return out

def build_dim_store(extracts, dim_address) -> pd.DataFrame:
    st = extracts["store"].rename(columns={"store_id":"store_id_src"})
    st = st.merge(dim_address[["address_id_src","province_sk"]],
                  left_on="address_id", right_on="address_id_src", how="left")
    write_dim(st[["store_id_src","name","address_id","province_sk"]], "dim_store.csv")
    return st

def build_dim_product(extracts) -> pd.DataFrame:
    pr = extracts["product"].rename(columns={"product_id":"product_id_src"})
    cat = extracts["product_category"].rename(columns={"category_id":"category_id_src"})
    pr = pr.merge(cat[["category_id_src","name"]].rename(columns={"name":"category_name"}),
                  left_on="category_id", right_on="category_id_src", how="left")
    pr = make_sk(pr, order_by="sku", sk_name="product_sk")
    write_dim(pr[["product_sk","product_id_src","sku","name","category_id","category_name","list_price","status","created_at"]],
              "dim_product.csv")
    return pr

def build_dim_customer(extracts) -> pd.DataFrame:
    cu = extracts["customer"].rename(columns={"customer_id":"customer_id_src"})
    cu["created_at"] = to_dt(cu["created_at"])
    cu = make_sk(cu, order_by="customer_id_src", sk_name="customer_sk")
    write_dim(cu[["customer_sk","customer_id_src","email","first_name","last_name","phone","status","created_at"]],
              "dim_customers.csv")
    return cu
