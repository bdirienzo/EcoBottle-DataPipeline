# etl/run_pipeline.py
"""
Orquestador estándar ETL: Extract -> Transform -> Load -> Data Quality
Correr desde la raíz del proyecto:
    python -m etl.run_pipeline
"""
from .extract.extract_raw import extract
from .transform.dims import (
    build_dim_calendar, build_dim_channel, build_dim_province,
    build_dim_address, build_dim_store, build_dim_product, build_dim_customer
)
from .transform.facts import (
    fact_sales_order, fact_sales_order_item, fact_payment,
    fact_shipment, fact_web_session, fact_nps_response
)
from .load.load_to_warehouse import load
from .quality.dq_checks import run_basic_checks
from .transform.utils import log

def main():
    log.info("=== EXTRACT ===")
    ex = extract()

    log.info("=== TRANSFORM (DIM) ===")
    dim_calendar  = build_dim_calendar(ex)
    dim_channel   = build_dim_channel(ex)
    dim_province  = build_dim_province(ex)
    dim_address   = build_dim_address(ex, dim_province)
    dim_store     = build_dim_store(ex, dim_address)
    dim_product   = build_dim_product(ex)
    dim_customer  = build_dim_customer(ex)

    log.info("=== TRANSFORM (FACT) ===")
    fact_sales_order(ex, dim_channel, dim_customer, dim_address, dim_store)
    fact_sales_order_item(ex, dim_channel, dim_product)
    fact_payment(ex)
    fact_shipment(ex, dim_address)
    fact_web_session(ex, dim_channel)
    fact_nps_response(ex, dim_channel)

    log.info("=== LOAD ===")
    load()   # (placeholder: ya escribimos CSV en /warehouse)

    log.info("=== DATA QUALITY ===")
    run_basic_checks()

    log.info("🎯 Pipeline ETL completo.")

if __name__ == "__main__":
    main()

