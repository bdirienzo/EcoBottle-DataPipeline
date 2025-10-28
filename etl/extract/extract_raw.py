# En este TP, "Extract" = leer CSV de /raw y retornar dataframes (sin modificar).
# Si mañana traés APIs o DBs, expandís este módulo.

from etl.transform.utils import read_raw

def extract():
    data = {
        "channel": read_raw("channel.csv"),
        "province": read_raw("province.csv"),
        "address": read_raw("address.csv"),
        "store": read_raw("store.csv"),
        "product": read_raw("product.csv"),
        "product_category": read_raw("product_category.csv"),
        "customer": read_raw("customer.csv"),
        "sales_order": read_raw("sales_order.csv"),
        "sales_order_item": read_raw("sales_order_item.csv"),
        "payment": read_raw("payment.csv"),
        "shipment": read_raw("shipment.csv"),
        "web_session": read_raw("web_session.csv"),
        "nps_response": read_raw("nps_response.csv"),
    }
    return data
    