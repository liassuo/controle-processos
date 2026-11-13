"""Experimento 2: atraso de transporte, tratamento exato (Nyquist) x aproximações de Padé.

Para o Sistema D, calcula o atraso crítico τ_crit:
* exato: pela margem de atraso (Nyquist/Bode, avaliação direta de exp(-jωτ)), com
  verificação independente por bissecção em τ sobre o veredito Z do Nyquist;
* aproximado: por bissecção em τ sobre o veredito de Routh aplicado à equação
  característica racional obtida com Padé de ordem N = 1..12.
"""
from __future__ import annotations

import time

import numpy as np

from comum import CORES, LARGURA, eixo_virgula, num, num_sci, plt, salvar, salvar_json, tabela_latex
from estabilidade import margens, nyquist, tabela_routh
from estabilidade import sistemas as S
from estabilidade.pade import erro_fase
from estabilidade.raizes import raizes_companheira


def bissecao_tau(estavel, a=0.0, b=5.0, tol=1e-9):
    assert estavel(a) and not estavel(b)
    while b - a > tol:
        m = 0.5 * (a + b)
        if estavel(m):
            a = m
        else:
            b = m
    return 0.5 * (a + b)


def main():
    base = S.sistema_d(0.0)
    m0 = margens(base)
    tau_exato = m0.margem_atraso
    t0 = time.perf_counter()
    tau_nyq = bissecao_tau(lambda t: nyquist(S.sistema_d(t)).Z == 0, 0.0, 3.0, 1e-6)
    t_nyq = time.perf_counter() - t0

    linhas, dados = [], []
    taus_grade = np.linspace(0.01, 3.0, 300)
    robustez = []
    for N in range(1, 21):
        def est(t, N=N, esc=True, crit="cancelamento"):
            Lp = S.sistema_d(t).com_pade(N)
            return tabela_routh(Lp.polinomio_caracteristico(), escalonar=esc, criterio_zero=crit).estavel

        def est_r(t, N=N):
            Lp = S.sistema_d(t).com_pade(N)
            return bool(np.all(raizes_companheira(Lp.polinomio_caracteristico()).real < 0))

        # robustez numérica: concordância Routh x raízes em uma grade de τ
        ref = np.array([est_r(t) for t in taus_grade])
        conc_esc = float(np.mean([est(t) == r for t, r in zip(taus_grade, ref)]))
        conc_sem = float(np.mean([est(t, esc=False) == r for t, r in zip(taus_grade, ref)]))
        conc_abs = float(np.mean([est(t, esc=False, crit="absoluta") == r for t, r in zip(taus_grade, ref)]))
        conc_abs_esc = float(np.mean([est(t, esc=True, crit="absoluta") == r for t, r in zip(taus_grade, ref)]))
        p_nom = S.sistema_d(0.5).com_pade(N).polinomio_caracteristico()
        faixa = float(np.abs(p_nom).max() / np.abs(p_nom[p_nom != 0]).min())
        robustez.append(dict(N=N, concordancia_escalonado=conc_esc, concordancia_sem_escalonar=conc_sem,
                             concordancia_absoluta=conc_abs, concordancia_absoluta_escalonada=conc_abs_esc,
                             faixa_dinamica_coef_tau05=faixa))
        if N > 12:
            continue
        t0 = time.perf_counter()
        try:
            tau_N = bissecao_tau(est, 1e-3, 3.0, 1e-9)
        except AssertionError:
            tau_N = np.nan
        dt = time.perf_counter() - t0
        try:
            tau_N_r = bissecao_tau(est_r, 1e-3, 3.0, 1e-9)
        except AssertionError:
            tau_N_r = np.nan
        erro = (tau_N - tau_exato) / tau_exato
        ordem_poli = S.sistema_d(0.5).com_pade(N).den.size - 1
        dados.append(dict(N=N, tau=tau_N, tau_raizes=tau_N_r, erro_rel=erro, tempo_s=dt,
                          grau_eq_caracteristica=ordem_poli))
        linhas.append([N, ordem_poli, num(tau_N, 6), num(tau_N_r, 6), num_sci(abs(erro)),
                       num(dt * 1e3, 1)])
    tabela_latex("pade_atraso_critico",
                 ["Ordem $N$", "Grau eq. caract.", "$\\tau_{crit}$ Routh (s)", "$\\tau_{crit}$ raízes (s)",
                  "Erro relativo", "Tempo (ms)"], linhas)

    # MG e MF do sistema nominal (τ = 0,5 s): exato x Padé
    Lnom = S.sistema_d(0.5)
    mex = margens(Lnom)
    lin2 = [["Exato", num(mex.mg_db, 4), num(mex.mf, 4), num(mex.w_cf, 4)]]
    comp = {"exato": dict(mg_db=mex.mg_db, mf=mex.mf, w_cf=mex.w_cf)}
    for N in (1, 2, 3, 5):
        mp = margens(Lnom.com_pade(N))
        lin2.append([f"Padé {N}", num(mp.mg_db, 4), num(mp.mf, 4), num(mp.w_cf, 4)])
        comp[f"pade{N}"] = dict(mg_db=mp.mg_db, mf=mp.mf, w_cf=mp.w_cf)
    tabela_latex("pade_margens_nominal", ["Modelo", "MG (dB)", "MF (°)", "$\\omega_{cf}$ (rad/s)"], lin2)

    # figura 1: erro de fase de Padé em função de ωτ
    wt = np.logspace(-1, 1.3, 600)
    fig, ax = plt.subplots(1, 2, figsize=(LARGURA, 2.3))
    for N, cor in zip((1, 2, 3, 5, 8), plt.cm.viridis(np.linspace(0, 0.85, 5))):
        e = np.degrees(np.abs(erro_fase(1.0, N, wt)))
        ax[0].loglog(wt, np.maximum(e, 1e-6), color=cor, label=f"$N={N}$")
    ax[0].axvline(m0.w_cg * tau_exato, color="k", ls=":", lw=0.8)
    ax[0].set_xlabel("$\\omega\\tau$ (rad)")
    ax[0].set_ylabel("|erro de fase| (graus)")
    ax[0].set_ylim(1e-4, 400)
    ax[0].legend(fontsize=6, ncol=2)
    Ns = [d["N"] for d in dados]
    ax[1].semilogy(Ns, [abs(d["erro_rel"]) for d in dados], "o-", color=CORES["exato"], ms=3)
    piso = 1e-9 / tau_exato
    ax[1].axhline(piso, color=CORES["ref"], ls=":", lw=0.9)
    ax[1].text(6.5, piso * 4, "tolerância da bissecção ($10^{-9}$ s)", fontsize=7, color=CORES["ref"])
    from matplotlib.ticker import MaxNLocator
    ax[1].xaxis.set_major_locator(MaxNLocator(integer=True))
    ax[1].set_xlabel("ordem de Padé $N$")
    ax[1].set_ylabel("erro relativo em $\\tau_{crit}$")
    fig.tight_layout()
    salvar(fig, "pade_erro")

    # figura 2: Nyquist próximo de -1, exato x Padé 1 x Padé 3 no atraso crítico
    fig, ax = plt.subplots(figsize=(LARGURA * 0.62, 2.8))
    Lc = S.sistema_d(tau_exato)
    w = np.logspace(-2, 2, 6000)
    h = Lc.resposta_frequencia(w)
    ax.plot(h.real, h.imag, color=CORES["exato"], lw=1.4, label="exato $e^{-\\tau s}$")
    for N, ls in ((1, "--"), (3, ":")):
        hp = Lc.com_pade(N).resposta_frequencia(w)
        ax.plot(hp.real, hp.imag, ls=ls, lw=1.1, label=f"Padé $N={N}$")
    ax.plot([-1], [0], "+", color="red", ms=10, mew=1.6)
    ax.set_xlim(-1.6, 0.6)
    ax.set_ylim(-1.2, 0.6)
    ax.set_aspect("equal")
    ax.set_xlabel("Re $L(j\\omega)$")
    ax.set_ylabel("Im $L(j\\omega)$")
    ax.set_title(f"Sistema D com $\\tau = \\tau_{{crit}}$ = {tau_exato:.3f} s".replace(".", ","))
    ax.legend(fontsize=7, loc="lower right")
    eixo_virgula(ax)
    fig.tight_layout()
    salvar(fig, "nyquist_pade_vs_exato")

    lin_r = [[r["N"], num_sci(r["faixa_dinamica_coef_tau05"], 1),
              num(100 * r["concordancia_absoluta"], 1), num(100 * r["concordancia_absoluta_escalonada"], 1),
              num(100 * r["concordancia_sem_escalonar"], 1), num(100 * r["concordancia_escalonado"], 1)]
             for r in robustez if r["N"] in (1, 3, 5, 6, 7, 8, 10, 12, 15, 20)]
    tabela_latex("routh_robustez", ["$N$", "Faixa dinâmica", "Absoluta", "Absoluta + esc.",
                                    "Cancelamento", "Cancel. + esc."], lin_r)
    salvar_json("exp2_atraso_pade", dict(tau_crit_margem=tau_exato, tau_crit_bissecao_nyquist=tau_nyq,
                                         tempo_bissecao_nyquist_s=t_nyq, w_cg=m0.w_cg, mf_sem_atraso=m0.mf,
                                         pade=dados, margens_nominal=comp, robustez_routh=robustez,
                                         tolerancia_bissecao_s=1e-9))
    print(f"tau_crit exato (margem) = {tau_exato:.6f} s; por bissecção Nyquist = {tau_nyq:.6f} s")
    for d in dados:
        print(d)


if __name__ == "__main__":
    main()
