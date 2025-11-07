from etl.transform.utils import read_raw #-> Importamos read_raw para utilizar

# - Se define la función extract() para extraer los datos de los .csv.
# - Se le da estructura de diccionario, para poder acceder a un df usando una key, ej: data["channel"].
# - Las keys son los nombres de las tablas y los valores son df obtenidos con read_raw.
# - read_raw es una función en utils que estandariza la lectura de .csv con pandas y utiliza una ruta preestablecida con settings.yaml.

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
    # - Devuelve un diccionario completo.