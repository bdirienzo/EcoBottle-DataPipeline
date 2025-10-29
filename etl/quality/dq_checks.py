import pandas as pd
from etl.transform.utils import DIM, FACT, CFG, log

def _has_rows(path):
    try:
        return pd.read_csv(path).shape[0] > 0
    except Exception:
        return False

def run_basic_checks():
    for f in ["dim_calendar.csv","dim_channel.csv","dim_province.csv","dim_address.csv","dim_store.csv","dim_product.csv","dim_customers.csv"]:
        ok = _has_rows(DIM / f)
        log.info(f"DQ dim {f}: {'OK' if ok else 'EMPTY'}")
        assert ok, f"Dim vacía: {f}"

    for f in ["fact_sales_order.csv","fact_sales_order_item.csv","fact_payment.csv","fact_shipment.csv","fact_web_session.csv","fact_nps_response.csv"]:
        ok = _has_rows(FACT / f)
        log.info(f"DQ fact {f}: {'OK' if ok else 'EMPTY'}")
        assert ok, f"Fact vacía: {f}"

    o = pd.read_csv(FACT / "fact_sales_order.csv")
    included = CFG["business_rules"]["sales_status_included"]
    kpi_rows = o[o["status"].isin(included)]
    log.info(f"DQ ventas incluidas (status in {included}): {len(kpi_rows)} filas")
    assert len(kpi_rows) > 0, "No hay ventas con status permitidos"

    nps = pd.read_csv(FACT / "fact_nps_response.csv")
    nps["sum_flags"] = nps[["is_detractor","is_passive","is_promoter"]].sum(axis=1)
    bad = nps[nps["sum_flags"] != 1]
    log.info(f"DQ NPS flags mal clasificados: {len(bad)}")
    assert len(bad) == 0, "Hay respuestas NPS con flags inconsistentes"

    log.info("✅ Data Quality: checks básicos OK")
