"""Experimento 5: análise dos ensaios executados no Tinkercad Circuits (HIL simulado).

Lê as séries temporais capturadas do Monitor Serial da placa "Planta"
(results/tinkercad/bruto_*.txt, linhas "y tau u k", t = k·Ts) e as confronta com:
* o gêmeo digital em Python (mesmo algoritmo, float32) -> erro amostra a amostra;
* a previsão do critério de Nyquist para o atraso crítico.

Os arquivos brutos são produzidos no Tinkercad (ver hil/README.md); este script
apenas os analisa. Ensaios ausentes são ignorados.
"""
from __future__ import annotations

import json

import numpy as np

from comum import CORES, LARGURA, RESULTADOS, eixo_virgula, num, num_sci, plt, salvar, salvar_json, tabela_latex
from estabilidade import margens
from estabilidade import sistemas as S
from estabilidade.hil import ConfigHIL, simula_hil, taxa_crescimento

PASTA = RESULTADOS / "tinkercad"
TS = 0.02

# ensaio -> (descrição, d nominal em amostras, atraso variável?)
ENSAIOS = {
    "T1": ("sem atraso", 0, False),
    "T2": ("nominal", 25, False),
    "T3": ("atraso elevado", 50, False),
    "T4a": ("limite (estável previsto)", 54, False),
    "T4b": ("limite (instável previsto)", 55, False),
    "T4c": ("acima do limite", 56, False),
    "T5": ("bem acima do limite", 60, False),
    "T6": ("atraso variável", 40, True),
}


def carrega(nome):
    arq = PASTA / f"bruto_{nome}.txt"
    if not arq.exists():
        return None
    txt = arq.read_text(encoding="utf-8")
    try:
        txt = json.loads(txt)
    except json.JSONDecodeError:
        pass
    dados = np.array([[float(v) for v in l.split()] for l in txt.split("\n") if l.strip()])
    k = dados[:, 3].astype(int)
    if k[0] != 0 or np.any(np.diff(k) != 1):
        raise ValueError(f"{arq.name}: série com lacunas ou fora de ordem")
    return dict(t=k * TS, y=dados[:, 0], tau=dados[:, 1], u=dados[:, 2])


def main():
    G, pid = S.planta_processo(), S.ParametrosPID()
    tau_crit = margens(S.sistema_d(0.0)).margem_atraso
    res, linhas = {}, []
    for nome, (desc, d, variavel) in ENSAIOS.items():
        s = carrega(nome)
        if s is None:
            continue
        n = len(s["t"])
        d_med = int(round(np.median(s["tau"][n // 2:]) / TS))
        r = dict(descricao=desc, d_nominal=d, d_medido=d_med, n=n, duracao_s=n * TS,
                 tau_min=float(s["tau"][100:].min()), tau_max=float(s["tau"].max()),
                 pico=float(s["y"].max()), t_pico=float(s["t"][s["y"].argmax()]),
                 taxa_tinkercad=taxa_crescimento(s["t"], s["y"]), variavel=variavel)
        # gêmeo digital: atraso fixo d, ou (atraso variável) a mesma sequência de
        # atrasos efetivos registrada pelo Tinkercad, tau[k] = (k - j[k])·Ts
        if variavel:
            seq = np.rint(s["tau"] / TS).astype(int)
            d_arg = lambda kk, seq=seq: seq[kk]          # noqa: E731
        else:
            d_arg = d_med
        _, _, yg, _, _ = simula_hil(G, pid, d_arg, ConfigHIL(ts=TS, t_final=n * TS))
        dy = np.abs(s["y"] - yg[:n])
        r["erro_max_gemeo"] = float(np.nanmax(dy))
        r["taxa_gemeo"] = taxa_crescimento(s["t"], yg[:n])
        r["instavel_tinkercad"] = bool(r["taxa_tinkercad"] > 0)
        res[nome] = r
        taxa = r["taxa_tinkercad"]
        linhas.append([nome, num(d_med * TS, 2) if not variavel else f"{num(r['tau_min'], 2)}--{num(r['tau_max'], 2)}",
                       num(r["pico"], 3),
                       "--" if not np.isfinite(taxa) else num(taxa, 4),
                       "instável" if r["instavel_tinkercad"] else "estável",
                       num_sci(r["erro_max_gemeo"], 1) if "erro_max_gemeo" in r else "--"])
    if not res:
        print("nenhum ensaio do Tinkercad encontrado em", PASTA)
        return
    tabela_latex("tinkercad_ensaios",
                 ["Ensaio", "$\\tau$ (s)", "Pico de $y$", "Taxa (1/s)", "Veredito", "Erro máx. x gêmeo"], linhas)

    # figura: respostas medidas no Tinkercad
    fig, ax = plt.subplots(2, 1, figsize=(LARGURA, 3.8), sharex=False)
    for nome in ("T1", "T2", "T3", "T5"):
        if nome in res:
            s = carrega(nome)
            ax[0].plot(s["t"], s["y"], lw=1, label=f"{nome}: $\\tau$ = {num(res[nome]['d_medido'] * TS, 2).replace('{,}', ',')} s")
    ax[0].axhline(1, color="k", lw=0.5, ls=":")
    ax[0].set_ylabel("$y$ (Tinkercad)")
    ax[0].set_xlim(0, 30)
    ax[0].set_ylim(-1.5, 3.5)
    ax[0].legend(fontsize=7, ncol=2)
    for nome, cor in (("T4a", CORES["exato"]), ("T4b", CORES["aprox"]), ("T4c", CORES["destaque"])):
        if nome in res:
            s = carrega(nome)
            ax[1].plot(s["t"], s["y"] - 1, lw=0.8, color=cor,
                       label=f"{nome}: $d$ = {res[nome]['d_medido']} ({'instável' if res[nome]['instavel_tinkercad'] else 'estável'})")
    ax[1].set_ylabel("$y - r$ (Tinkercad)")
    ax[1].set_xlabel("$t$ (s, tempo simulado)")
    ax[1].legend(fontsize=7)
    for a in ax:
        eixo_virgula(a)
    fig.tight_layout()
    salvar(fig, "tinkercad_respostas")

    salvar_json("exp5_tinkercad", dict(tau_crit_nyquist=tau_crit, ts=TS, ensaios=res))
    for k, v in res.items():
        print(k, v)


if __name__ == "__main__":
    main()
