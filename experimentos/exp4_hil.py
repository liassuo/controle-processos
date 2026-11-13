"""Experimento 4: gêmeo digital do HIL (trilha EC).

Previsão pelo critério de Nyquist (tempo contínuo) do atraso crítico do laço PID
do Sistema D, confrontada com a simulação passo a passo do algoritmo que roda nos
dois Arduinos (float32, ZOH, PID discreto, buffer de atraso).

Os valores aqui são de SIMULAÇÃO em Python. As medições no Tinkercad são feitas
pelo grupo e registradas à parte (results/tinkercad/).
"""
from __future__ import annotations

import numpy as np

from comum import CORES, LARGURA, eixo_virgula, num, plt, salvar, salvar_json, tabela_latex
from estabilidade import margens
from estabilidade import sistemas as S
from estabilidade.hil import ConfigHIL, atraso_critico_hil, discretiza_zoh, simula_hil


def main():
    G = S.planta_processo()
    pid = S.ParametrosPID()
    m = margens(S.sistema_d(0.0))
    tau_pred = m.margem_atraso

    # 1) atraso crítico em função do período de amostragem
    linhas, dados_ts = [], []
    for ts in (0.005, 0.01, 0.02, 0.05):
        cfg = ConfigHIL(ts=ts, t_final=80.0)
        d = atraso_critico_hil(G, pid, cfg, d_max=int(2.0 / ts))
        tau_sim = d * ts if d is not None else np.nan
        pred_zoh = tau_pred - ts / 2               # o ZOH equivale a ~Ts/2 de atraso
        dados_ts.append(dict(ts=ts, d_crit=d, tau_sim=tau_sim, tau_pred=tau_pred, tau_pred_zoh=pred_zoh))
        linhas.append([num(ts * 1e3, 0), d, num(tau_sim, 3), num(tau_pred, 3), num(pred_zoh, 3),
                       num(100 * (tau_sim - tau_pred) / tau_pred, 2)])
    tabela_latex("hil_atraso_critico",
                 ["$T_s$ (ms)", "$d_{crit}$ (amostras)", "$\\tau$ simulado (s)", "$\\tau$ Nyquist (s)",
                  "$\\tau$ Nyquist $- T_s/2$ (s)", "Desvio (\\%)"], linhas)

    # 2) respostas para o período adotado nos sketches (Ts = 20 ms)
    cfg = ConfigHIL(ts=0.02, t_final=30.0)
    casos = [(0, "sem atraso"), (25, "$\\tau = 0{,}50$ s (nominal)"), (50, "$\\tau = 1{,}00$ s"),
             (60, "$\\tau = 1{,}20$ s")]
    fig, ax = plt.subplots(2, 1, figsize=(LARGURA, 3.6), sharex=True)
    respostas = {}
    for d, rot in casos:
        t, r, y, u, _ = simula_hil(G, pid, d, cfg)
        ax[0].plot(t, y, lw=1, label=rot)
        ax[1].plot(t, u, lw=0.9)
        respostas[d] = dict(y_max=float(np.nanmax(y)), y_final=float(y[-1]))
    ax[0].axhline(1.0, color="k", lw=0.5, ls=":")
    ax[0].set_ylabel("$y$")
    ax[0].set_ylim(-0.5, 2.5)
    ax[0].legend(fontsize=7, ncol=2, loc="upper right")
    ax[1].set_ylabel("$u$")
    ax[1].set_xlabel("$t$ (s)")
    for a in ax:
        eixo_virgula(a)
    fig.tight_layout()
    salvar(fig, "hil_respostas")

    # 3) atraso variável (jitter): uniforme em faixas, semente fixa
    rng = np.random.default_rng(7)
    faixas = [(15, 35), (40, 60), (50, 70), (56, 76)]
    jitter = []
    fig, ax = plt.subplots(1, 1, figsize=(LARGURA, 2.2))
    cfg_j = ConfigHIL(ts=0.02, t_final=120.0)
    n = int(round(cfg_j.t_final / cfg_j.ts))
    from dataclasses import replace
    from estabilidade.hil import taxa_crescimento
    for (a, b) in faixas:
        seq = rng.integers(a, b + 1, size=n)
        # classificação no laço linear (sem saturação), como no caso de atraso constante
        tl, _, yl, _, d_ef = simula_hil(G, pid, lambda k, seq=seq: seq[k], replace(cfg_j, u_max=1e30))
        taxa = taxa_crescimento(tl, yl)
        inst = bool(taxa > 0)
        t, r, y, u, _ = simula_hil(G, pid, lambda k, seq=seq: seq[k], cfg_j)
        jitter.append(dict(faixa_amostras=[a, b], faixa_s=[a * 0.02, b * 0.02], d_medio=float(d_ef.mean()),
                           tau_medio=float(d_ef.mean() * 0.02), d_ef_max=int(d_ef.max()),
                           d_ef_min=int(d_ef[100:].min()), taxa_1_s=taxa, instavel=inst))
        ax.plot(t, y, lw=0.9, label=f"$d \\in [{a}, {b}]$: $\\bar d_{{ef}}$={d_ef.mean():.1f} "
                                    f"({'instável' if inst else 'estável'})".replace(".", ","))
    ax.axhline(1.0, color="k", lw=0.5, ls=":")
    ax.set_xlim(0, 60)
    ax.set_ylim(-0.5, 2.5)
    ax.set_xlabel("$t$ (s)")
    ax.set_ylabel("$y$")
    ax.legend(fontsize=7)
    eixo_virgula(ax)
    fig.tight_layout()
    salvar(fig, "hil_jitter")

    Ad, Bd, C, D = discretiza_zoh(G, 0.02)
    salvar_json("exp4_hil", dict(tau_crit_nyquist=tau_pred, w_cg=m.w_cg, mf_sem_atraso=m.mf,
                                 por_ts=dados_ts, respostas=respostas, jitter=jitter,
                                 zoh_ts20ms=dict(Ad=Ad, Bd=Bd, C=C)))
    print("tau_crit Nyquist:", tau_pred)
    for d in dados_ts:
        print(d)
    print(jitter)


if __name__ == "__main__":
    main()
