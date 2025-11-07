from pathlib import Path #Importamos pathlib (sirve para trabajar con rutas de archivos).
import logging as log #Nos permite hacer el logging por consola.

def load() -> bool:
    base = Path("warehouse") #/warehouse es el path base.
    if not base.exists():
        log.warning("[LOAD] No existe la carpeta 'warehouse/'.") #Si no existe cancelamos y tiramos error.
        return False

    total = 0 #Inicia el contador en cero.
    for sub in ("dim", "fact"): #Iteramos sobre los archivos de /warehouse.
        subdir = base / sub
        if not subdir.exists():
            log.warning(f"[LOAD] Carpeta faltante: {subdir}") #Si no aparece la carpeta error.
            continue
        for csv in subdir.glob("*.csv"):
            n = sum(1 for _ in open(csv, encoding="utf-8")) - 1 #Contamos filas en .csv menos encabezado.
            total += n
            log.info(f"[LOAD] {sub}/{csv.name} -> {n} filas")

    log.info(f"[LOAD] Total de filas cargadas: {total}") #Total final de filas cargadas.
    return True