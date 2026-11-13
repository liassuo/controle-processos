"""Reproduz todos os resultados do artigo (figuras em results/figuras, tabelas em
results/tabelas e dados brutos em results/*.json)."""
import runpy
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent

for nome in ("exp1_sistemas", "exp2_atraso_pade", "exp3_escalabilidade", "exp4_hil",
             "exp5_tinkercad", "gera_macros"):
    t0 = time.perf_counter()
    print(f"== {nome} ==", flush=True)
    runpy.run_path(str(AQUI / f"{nome}.py"), run_name="__main__")
    print(f"   ({time.perf_counter() - t0:.1f} s)", flush=True)
