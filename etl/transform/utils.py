from pathlib import Path
import pandas as pd
from typing import Dict
import yaml
import logging
import os

# ---- Logging estándar
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("etl")

# ---- Paths RESUELTOS por archivo (no por cwd)
THIS_FILE = Path(__file__).resolve()          # .../etl/transform/utils.py
ETL_DIR   = THIS_FILE.parents[1]              # .../etl
PROJECT   = ETL_DIR.parent                    # raíz del repo: .../mkt_tp_final
CONFIG    = ETL_DIR / "config" / "settings.yaml"

if not CONFIG.exists():
    raise FileNotFoundError(f"No encuentro settings.yaml en: {CONFIG}")

# ---- Config
with open(CONFIG, "r", encoding="utf-8") as f:
    CFG = yaml.safe_load(f)

# Rutas desde PROJECT + lo definido en YAML (raw, warehouse/dim/fact)
RAW  = PROJECT / CFG["paths"]["raw"]
WH   = PROJECT / CFG["paths"]["warehouse"]
DIM  = PROJECT / CFG["paths"]["dim"]
FACT = PROJECT / CFG["paths"]["fact"]

for p in [WH, DIM, FACT]:
    p.mkdir(parents=True, exist_ok=True)

def read_raw(name: str, **kw) -> pd.DataFrame:
    df = pd.read_csv(RAW / name, **kw)
    log.info(f"read_raw: {name} -> {len(df)} rows")
    return df

def write_dim(df: pd.DataFrame, name: str) -> None:
    (DIM / name).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(DIM / name, index=False)
    log.info(f"write_dim: {name} -> {len(df)} rows")

def write_fact(df: pd.DataFrame, name: str) -> None:
    (FACT / name).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(FACT / name, index=False)
    log.info(f"write_fact: {name} -> {len(df)} rows")

def to_dt(s):
    return pd.to_datetime(s, errors="coerce", utc=True).dt.tz_convert(None)

def add_date_sk(df: pd.DataFrame, dt_col: str, out_col="date_sk") -> pd.DataFrame:
    d = pd.to_datetime(df[dt_col], errors="coerce").dt.date
    df[out_col] = pd.to_datetime(d).dt.strftime("%Y%m%d").astype("Int64")
    return df

def make_sk(df: pd.DataFrame, order_by: str, sk_name: str, start: int = 1) -> pd.DataFrame:
    df = df.sort_values(order_by).reset_index(drop=True).copy()
    df[sk_name] = range(start, start + len(df))
    cols = [sk_name] + [c for c in df.columns if c != sk_name]
    return df[cols]

def build_map(df: pd.DataFrame, src_col: str, sk_col: str) -> Dict:
    return dict(zip(df[src_col], df[sk_col]))