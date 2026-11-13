"""Gera results/tabelas/numeros.tex: macros LaTeX com os números citados no texto do
artigo, lidos dos JSON dos experimentos (nenhum número é digitado à mão)."""
from __future__ import annotations

import json

import numpy as np

from comum import RESULTADOS, TAB


def f(x, casas=2):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "\\infty"
    return f"{x:.{casas}f}".replace(".", "{,}")


def sci(x, casas=1):
    e = int(np.floor(np.log10(abs(x))))
    return f"{x / 10 ** e:.{casas}f}".replace(".", "{,}") + f"\\times 10^{{{e}}}"


def main():
    e1 = json.loads((RESULTADOS / "exp1_sistemas.json").read_text(encoding="utf-8"))
    e2 = json.loads((RESULTADOS / "exp2_atraso_pade.json").read_text(encoding="utf-8"))
    e3 = json.loads((RESULTADOS / "exp3_escalabilidade.json").read_text(encoding="utf-8"))
    e4 = json.loads((RESULTADOS / "exp4_hil.json").read_text(encoding="utf-8"))
    m = {}
    for s, d in e1["sistemas"].items():
        m[f"MG{s}"] = f(d["mg_db"], 2)
        m[f"MGlin{s}"] = f(d["mg"], 3)
        m[f"MF{s}"] = f(d["mf"], 1)
        m[f"Wcg{s}"] = f(d["w_cg"], 3)
        m[f"Wcf{s}"] = f(d["w_cf"], 3)
        m[f"MA{s}"] = f(d["margem_atraso"], 3)
        m[f"N{s}"] = str(d["N"])
        m[f"P{s}"] = str(d["P"])
        m[f"Pts{s}"] = str(d["pontos_contorno"])
    # ganhos críticos absolutos = ganho nominal x margem (linear)
    m["KcritA"] = f(20.0 * e1["sistemas"]["A"]["mg"], 2)
    m["KminB"] = f(400.0 * e1["sistemas"]["B"]["mg"], 2)
    m["KcritC"] = f(7.0 * e1["sistemas"]["C"]["mg"], 3)
    m["TauCrit"] = f(e2["tau_crit_margem"], 4)
    m["TauCritBis"] = f(e2["tau_crit_bissecao_nyquist"], 4)
    m["MFsemAtraso"] = f(e2["mf_sem_atraso"], 2)
    m["WcgD"] = f(e2["w_cg"], 3)
    pade = {p["N"]: p for p in e2["pade"]}
    for n in (1, 2, 3, 4, 5):
        m[f"TauPade{'ABCDE'[n - 1]}"] = f(pade[n]["tau"], 4)
        m[f"ErroPade{'ABCDE'[n - 1]}"] = sci(abs(pade[n]["erro_rel"]))
    m["ErroPadeApct"] = f(100 * abs(pade[1]["erro_rel"]), 1)
    rob = {r["N"]: r for r in e2["robustez_routh"]}
    m["RobAbsMin"] = f(100 * min(r["concordancia_absoluta"] for r in rob.values()), 1)
    m["RobAbsErro"] = f(100 * (1 - min(r["concordancia_absoluta"] for r in rob.values())), 1)
    m["FaixaDinMax"] = sci(rob[20]["faixa_dinamica_coef_tau05"])
    res = {(r["familia"], r["n"]): r for r in e3["resultados"]}
    for fam, tag in (("aleatória", "Al"), ("Wilkinson", "Wi")):
        for n in (5, 10, 20):
            r = res[(fam, n)]
            m[f"ErroComp{tag}{n}"] = sci(max(r["erro_companheira"], 1e-17))
            m[f"ErroAb{tag}{n}"] = sci(max(r["erro_aberth"], 1e-17))
            m[f"TRouth{tag}{n}"] = f(r["t_routh"] * 1e6, 0)
            m[f"TNyq{tag}{n}"] = f(r["t_nyquist"] * 1e3, 2)
            m[f"TLugar{tag}{n}"] = f(r["t_lugar"] * 1e3, 0)
            m[f"TComp{tag}{n}"] = f(r["t_companheira"] * 1e6, 0)
            m[f"TAb{tag}{n}"] = f(r["t_aberth"] * 1e6, 0)
    m["CPU"] = e3["ambiente"]["processador"].replace("_", " ")
    m["VerPython"] = e3["ambiente"]["python"]
    m["VerNumpy"] = e3["ambiente"]["numpy"]
    m["VerControl"] = e3["ambiente"].get("control", "?")
    m["VerScipy"] = e3["ambiente"].get("scipy", "?")
    por_ts = {round(p["ts"], 3): p for p in e4["por_ts"]}
    m["DcritHil"] = str(por_ts[0.02]["d_crit"])
    m["TauHil"] = f(por_ts[0.02]["tau_sim"], 2)
    m["DcritHilFino"] = str(por_ts[0.005]["d_crit"])
    m["TauHilFino"] = f(por_ts[0.005]["tau_sim"], 3)
    arq5 = RESULTADOS / "exp5_tinkercad.json"
    if arq5.exists():
        e5 = json.loads(arq5.read_text(encoding="utf-8"))["ensaios"]
        erros = [v["erro_max_gemeo"] for v in e5.values() if "erro_max_gemeo" in v and not v["variavel"]]
        if erros:
            m["ErroTinkMax"] = sci(max(erros))
        for k, v in e5.items():
            tag = k.replace("T", "Tk")
            m[f"{tag}Pico"] = f(v["pico"], 3)
            m[f"{tag}D"] = str(v["d_medido"])
            if "erro_max_gemeo" in v:
                m[f"{tag}Erro"] = sci(v["erro_max_gemeo"])
            if np.isfinite(v["taxa_tinkercad"]):
                m[f"{tag}Taxa"] = sci(v["taxa_tinkercad"]) if abs(v["taxa_tinkercad"]) < 0.01 else f(v["taxa_tinkercad"], 3)
    linhas = ["% Gerado por experimentos/gera_macros.py -- não editar à mão"]
    for k, v in sorted(m.items()):
        # LaTeX não aceita dígitos em nomes de macro: 10 -> UmZero, T4a -> TkQuatroa
        digitos = ["Zero", "Um", "Dois", "Tres", "Quatro", "Cinco", "Seis", "Sete", "Oito", "Nove"]
        nome = "".join(digitos[int(c)] if c.isdigit() else c for c in k)
        linhas.append(f"\\newcommand{{\\{nome}}}{{{v}}}")
    (TAB / "numeros.tex").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"{len(m)} macros em {TAB / 'numeros.tex'}")


if __name__ == "__main__":
    main()
