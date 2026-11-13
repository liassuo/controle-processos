"""Experimento 1: análise dos quatro sistemas pelos quatro métodos + validação cruzada.

Gera: figuras de Nyquist, Bode (exato x assintótico), Lugar das Raízes e resposta
ao degrau; tabelas de resultados por sistema e de concordância entre métodos.
"""
from __future__ import annotations

import numpy as np

from comum import (CORES, LARGURA, ambiente, eixo_virgula, num, plt, salvar, salvar_json,
                   tabela_csv, tabela_latex)
from estabilidade import (FT, bode, bode_assintotico, faixas_ganho_estavel, lugar_raizes,
                          margens, nyquist, tabela_routh)
from estabilidade import sistemas as S
from estabilidade.polinomios import soma
from estabilidade.raizes import raizes_companheira
from estabilidade.simulacao import diverge, resposta_degrau_malha_fechada

ORDEM_PADE_D = 3


def analisa(nome, L):
    r = nyquist(L)
    m = margens(L)
    Lr = L.com_pade(ORDEM_PADE_D) if L.atraso else L
    rt = tabela_routh(Lr.polinomio_caracteristico())
    polos_mf = raizes_companheira(Lr.polinomio_caracteristico())
    t, y = resposta_degrau_malha_fechada(L, 40.0 if nome != "B" else 3.0, 1e-3 if nome != "B" else 1e-4)
    return dict(nome=nome, L=L, ny=r, m=m, routh=rt, polos_mf=polos_mf, t=t, y=y,
                sim_instavel=diverge(t, y))


def fig_nyquist(res, arquivo):
    fig, eixos = plt.subplots(2, 2, figsize=(LARGURA, 5.6))
    for ax, (nome, d) in zip(eixos.ravel(), res.items()):
        Lp = d["ny"].L_positivo
        sel = np.abs(Lp) < 50
        x, y = Lp.real[sel], Lp.imag[sel]
        ax.plot(x, y, color=CORES["exato"], lw=1.1, label="$\\omega>0$")
        ax.plot(x, -y, color=CORES["aprox"], lw=0.9, ls="--", label="$\\omega<0$")
        # setas indicando o sentido de ω crescente
        for frac in (0.25, 0.55):
            i = int(frac * (len(x) - 2))
            ax.annotate("", xy=(x[i + 1], y[i + 1]), xytext=(x[i], y[i]),
                        arrowprops=dict(arrowstyle="-|>", color=CORES["exato"], lw=1.0))
        ax.plot([-1], [0], "+", color="red", ms=9, mew=1.6, label="$-1+j0$")
        lim = {"A": 3.6, "B": 2.5, "C": 1.5, "D": 2.0}[nome]
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect("equal")
        ny = d["ny"]
        ax.set_title(f"Sistema {nome}:  $P={ny.P}$,  $N={ny.N_horario}$,  $Z={ny.Z}$")
        ax.set_xlabel("Re $L(j\\omega)$")
        ax.set_ylabel("Im $L(j\\omega)$")
        eixo_virgula(ax)
    eixos[0, 0].legend(loc="lower left", fontsize=7)
    fig.tight_layout()
    salvar(fig, arquivo)


def fig_bode(res, arquivo):
    w = np.logspace(-2, 3, 2000)
    fig, eixos = plt.subplots(2, 4, figsize=(LARGURA, 3.4), sharex=True)
    for j, (nome, d) in enumerate(res.items()):
        L = d["L"]
        mag, fase = bode(L, w)
        ma, fa = bode_assintotico(L, w)
        # alinha ramos de fase (mesma referência módulo 360°)
        fa = fa + 360 * np.round((fase[0] - fa[0]) / 360)
        eixos[0, j].semilogx(w, mag, color=CORES["exato"], label="exato")
        eixos[0, j].semilogx(w, ma, color=CORES["aprox"], ls="--", label="assintótico")
        eixos[0, j].axhline(0, color="k", lw=0.5)
        eixos[1, j].semilogx(w, fase, color=CORES["exato"])
        eixos[1, j].semilogx(w, fa, color=CORES["aprox"], ls="--")
        eixos[1, j].axhline(-180, color="k", lw=0.5)
        eixos[0, j].set_title(f"Sistema {nome}")
        eixos[1, j].set_xlabel("$\\omega$ (rad/s)")
        eixos[0, j].set_ylim(-100, 40)
        if nome == "D":
            eixos[1, j].set_ylim(-1080, 90)
        for ax in eixos[:, j]:
            eixo_virgula(ax, x=False)
    eixos[0, 0].set_ylabel("$|L|$ (dB)")
    eixos[1, 0].set_ylabel("$\\angle L$ (graus)")
    eixos[0, 0].legend(fontsize=6)
    fig.tight_layout(w_pad=0.4, h_pad=0.4)
    salvar(fig, arquivo)


def fig_lugar(res, arquivo):
    fig, eixos = plt.subplots(1, 4, figsize=(LARGURA, 1.9))
    janelas = {"A": (-8, 3, -6, 6), "B": (-120, 30, -100, 100), "C": (-8, 4, -6, 6), "D": (-25, 10, -12, 12)}
    for ax, (nome, d) in zip(eixos, res.items()):
        L = d["L"]
        Lr = (L.com_pade(ORDEM_PADE_D) if L.atraso else L)
        Lr = FT(Lr.num / Lr.num[0] * np.sign(Lr.num[0]), Lr.den)  # K varre o ganho de L
        lr = lugar_raizes(Lr)
        for i in range(lr.raizes.shape[1]):
            ax.plot(lr.raizes[:, i].real, lr.raizes[:, i].imag, color=CORES["exato"], lw=0.9)
        p = Lr.polos()
        z = Lr.zeros()
        ax.plot(p.real, p.imag, "x", color="k", ms=5)
        ax.plot(z.real, z.imag, "o", mfc="none", color="k", ms=4)
        pm = d["polos_mf"]
        ax.plot(pm.real, pm.imag, "s", color=CORES["aprox"], ms=3, label="MF nominal")
        ax.axvline(0, color="k", lw=0.5)
        x0, x1, y0, y1 = janelas[nome]
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ax.set_title(f"Sistema {nome}" + (f" (Padé {ORDEM_PADE_D})" if L.atraso else ""))
        ax.set_xlabel("Re $s$")
        eixo_virgula(ax)
    eixos[0].set_ylabel("Im $s$")
    eixos[0].legend(fontsize=6, loc="lower left")
    fig.tight_layout(w_pad=0.5)
    salvar(fig, arquivo)


def fig_degrau(res, arquivo):
    fig, eixos = plt.subplots(1, 4, figsize=(LARGURA, 1.7))
    for ax, (nome, d) in zip(eixos, res.items()):
        ax.plot(d["t"], d["y"], color=CORES["exato"])
        ax.set_title(f"Sistema {nome}")
        ax.set_xlabel("$t$ (s)")
        eixo_virgula(ax)
    eixos[0].set_ylabel("$y(t)$")
    fig.tight_layout(w_pad=0.5)
    salvar(fig, arquivo)


def ganho_critico_por_metodo(nome, L):
    """Fronteira de estabilidade em K (multiplicador do ganho nominal) por método."""
    Lr = L.com_pade(ORDEM_PADE_D) if L.atraso else L
    faixas = faixas_ganho_estavel(Lr.num, Lr.den, 1e-3, 1e3)
    m = margens(L)
    lr = lugar_raizes(Lr, k_max=1e3)
    k_lr = sorted(k for k, _ in lr.cruzamentos_jw)
    return dict(routh=faixas, nyquist_mg=m.mg, lugar=k_lr)


def main():
    sistemas = S.todos()
    res = {n: analisa(n, L) for n, L in sistemas.items()}

    fig_nyquist(res, "nyquist_sistemas")
    fig_bode(res, "bode_sistemas")
    fig_lugar(res, "lugar_raizes_sistemas")
    fig_degrau(res, "degrau_sistemas")

    # validação cruzada com python-control
    import control
    linhas_val, val = [], {}
    for nome, d in res.items():
        L = d["L"]
        Lr = L.com_pade(ORDEM_PADE_D) if L.atraso else L
        gm, pm, w180, wc = control.margin(control.tf(L.num, L.den))
        if L.atraso:
            pm = pm - np.degrees(L.atraso * wc)   # atraso só altera a fase
            gm, w180 = np.nan, np.nan             # control.margin não aceita atraso exato
        ref_polos = control.poles(control.feedback(control.tf(Lr.num, Lr.den), 1))
        from estabilidade.raizes import distancia_conjuntos
        erro_polos = distancia_conjuntos(d["polos_mf"], ref_polos)
        cnt = control.nyquist_response(control.tf(L.num, L.den)).count if not L.atraso else None
        val[nome] = dict(mf_nosso=d["m"].mf, mf_ctrl=pm, mg_nosso=d["m"].mg, mg_ctrl=gm,
                         N_nosso=d["ny"].N_horario, N_ctrl=cnt, erro_polos=erro_polos)
        linhas_val.append([nome, num(d["m"].mf, 4), num(pm, 4),
                           num(d["m"].mg, 4) if np.isfinite(gm) else num(d["m"].mg, 4),
                           num(gm, 4) if np.isfinite(gm) else "--",
                           d["ny"].N_horario, cnt if cnt is not None else "--",
                           f"{erro_polos:.1e}".replace(".", "{,}")])
    tabela_latex("validacao_cruzada",
                 ["Sist.", "MF própria (°)", "MF python-control (°)", "MG própria", "MG python-control",
                  "$N$ própria", "$N$ python-control", "erro polos MF"], linhas_val)

    # tabela principal
    linhas, csv_l, dados = [], [], {}
    for nome, d in res.items():
        m, ny, rt = d["m"], d["ny"], d["routh"]
        criterio = ganho_critico_por_metodo(nome, d["L"])
        dados[nome] = dict(P=ny.P, N=ny.N_horario, N_cruz=ny.N_cruzamentos, Z=ny.Z,
                           mg=m.mg, mg_db=m.mg_db, w_cf=m.w_cf, mf=m.mf, w_cg=m.w_cg,
                           margem_atraso=m.margem_atraso, routh_spd=rt.n_spd,
                           routh_casos=rt.casos_especiais, polos_mf=d["polos_mf"],
                           sim_instavel=d["sim_instavel"], pontos_contorno=ny.n_pontos,
                           ganho_critico=criterio, todos_cf=m.todos_cf, todos_cg=m.todos_cg,
                           routh_primeira_coluna=rt.primeira_coluna)
        linhas.append([nome, ny.P, ny.N_horario, ny.Z, num(m.mg_db, 2), num(m.w_cf, 3),
                       num(m.mf, 2), num(m.w_cg, 3), num(m.margem_atraso, 3),
                       rt.n_spd, "instável" if d["sim_instavel"] else "estável"])
        csv_l.append([nome, ny.P, ny.N_horario, ny.Z, m.mg_db, m.w_cf, m.mf, m.w_cg,
                      m.margem_atraso, rt.n_spd, d["sim_instavel"]])
    cab = ["Sist.", "$P$", "$N$", "$Z$", "MG (dB)", "$\\omega_{cf}$", "MF (°)", "$\\omega_{cg}$",
           "MA (s)", "Routh SPD", "Simulação"]
    tabela_latex("resultados_sistemas", cab, linhas)
    tabela_csv("resultados_sistemas", ["sistema", "P", "N", "Z", "MG_dB", "w_cf", "MF_graus", "w_cg",
                                       "margem_atraso_s", "routh_spd", "sim_instavel"], csv_l)

    # concordância da fronteira de ganho (multiplicador de K nominal)
    linhas_k = []
    for nome, dd in dados.items():
        g = dd["ganho_critico"]
        faixa = g["routh"][0] if g["routh"] else (np.nan, np.nan)
        lim_routh = faixa[1] if np.isfinite(faixa[1]) else faixa[0]
        lim_lugar = g["lugar"][0] if g["lugar"] else np.nan
        linhas_k.append([nome, num(lim_routh, 5), num(lim_lugar, 5), num(g["nyquist_mg"], 5),
                         "mínimo" if not np.isfinite(faixa[1]) else "máximo"])
    tabela_latex("ganho_critico_metodos",
                 ["Sist.", "Routh", "Lugar das Raízes", "Nyquist/Bode (MG)", "Tipo de limite"], linhas_k)

    salvar_json("exp1_sistemas", dict(ambiente=ambiente(), sistemas=dados, validacao=val,
                                      ordem_pade_D=ORDEM_PADE_D))
    print("Experimento 1 concluído")
    for nome, dd in dados.items():
        print(nome, {k: dd[k] for k in ("P", "N", "Z", "mg_db", "mf", "margem_atraso", "routh_spd", "sim_instavel")},
              dd["ganho_critico"])


if __name__ == "__main__":
    main()
