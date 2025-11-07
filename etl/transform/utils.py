#Importamos lo necesario
from pathlib import Path
import pandas as pd
from typing import Dict
import yaml
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s") #Configura un log con formato estandar
log = logging.getLogger("etl") #Se configura para todos los archivos del etl

THIS_FILE = Path(__file__).resolve() #Guarda el path del archivo actual y resolve lo convierte en una ruta absoluta y normalizada
ETL_DIR   = THIS_FILE.parents[1] #Sirve para ubicar en cualquier archivo la carpeta etl
PROJECT   = ETL_DIR.parent #Ubicar en cualquier momento el project
CONFIG    = ETL_DIR / "config" / "settings.yaml" #Ubicar la carpeta de settings

if not CONFIG.exists():
    raise FileNotFoundError(f"No encuentro settings.yaml en: {CONFIG}")

with open(CONFIG, "r", encoding="utf-8") as f:
    CFG = yaml.safe_load(f) #Convierte settings en un dict (CFG) para poder acceder a la info

#Acceder a las rutas del proyectos desde el yaml
RAW  = PROJECT / CFG["paths"]["raw"]
WH   = PROJECT / CFG["paths"]["warehouse"]
DIM  = PROJECT / CFG["paths"]["dim"]
FACT = PROJECT / CFG["paths"]["fact"]

#Revisamos que existan las carpetas
for p in [WH, DIM, FACT]:
    p.mkdir(parents=True, exist_ok=True)

#Creamos las funciones del etl
def read_raw(name: str, **kw) -> pd.DataFrame:
    df = pd.read_csv(RAW / name, **kw) #Usa función de pandas para leer un .csv, kw= parámetros adicionales ej: encoding
    log.info(f"read_raw: {name} -> {len(df)} rows")
    return df

def write_dim(df: pd.DataFrame, name: str) -> None:
    (DIM / name).parent.mkdir(parents=True, exist_ok=True) #Revisa que existan las carpetas necesarias
    df.to_csv(DIM / name, index=False) #Crea el .csv sin índice
    log.info(f"write_dim: {name} -> {len(df)} rows")

def write_fact(df: pd.DataFrame, name: str) -> None:
    (FACT / name).parent.mkdir(parents=True, exist_ok=True) #Revisa que existan las carpetas necesarias
    df.to_csv(FACT / name, index=False) #Crea el .csv sin índice
    log.info(f"write_fact: {name} -> {len(df)} rows")

def to_dt(s):
    return pd.to_datetime(s, errors="coerce", utc=True).dt.tz_convert(None) #Convierte una celda en formato DATETIME en UTC Ej: (2025-11-07 16:00:00=

def add_date_sk(df: pd.DataFrame, dt_col: str, out_col="date_sk") -> pd.DataFrame: #Permite hacer joins con dim_Calendar
    d = pd.to_datetime(df[dt_col], errors="coerce").dt.date #Convierte a date
    df[out_col] = pd.to_datetime(d).dt.strftime("%Y%m%d").astype("Int64") #Se le da formato y queda como entero
    return df

def make_sk(df: pd.DataFrame, order_by: str, sk_name: str, start: int = 1) -> pd.DataFrame:
    df = df.sort_values(order_by).reset_index(drop=True).copy() #Ordena la tabla con alguna referencia estable, reinicia el índice y duplica
    df[sk_name] = range(start, start + len(df)) #Asigna números consecutivos empezando por start
    cols = [sk_name] + [c for c in df.columns if c != sk_name]  #Reordena las columnas para que sk sea la primera
    return df[cols]

def build_map(df: pd.DataFrame, src_col: str, sk_col: str) -> Dict:
    return dict(zip(df[src_col], df[sk_col])) #Mapea el id original de la tabla con su respectivo sk
#Conectar las fact con sus dimensiones, ahí hay mucho mapeo

def read_warehouse_table(subfolder: str, filename: str) -> pd.DataFrame: #La usamos para la de marketing, carga en memoria la tablas
    path = Path("warehouse") / subfolder / filename
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {path}")
    return pd.read_csv(path)

def find_ci_col(df, candidates): #Evita errores
    lowmap = {c.lower(): c for c in df.columns} #crea un dict donde el valor es el nombre real y la clave nombre en minúscula
    for c in candidates: #Permite posibilidades de nombres, por si haya lgun error en el archivo
        if c in lowmap:
            return lowmap[c]
    return None
