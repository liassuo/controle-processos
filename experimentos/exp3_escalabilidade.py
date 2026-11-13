"""Experimento 3: escalabilidade (tempo de CPU) e erro numérico em função da ordem n.

Famílias de teste (raízes conhecidas, semente fixa):
* "aleatória": raízes estáveis aleatórias (reais e pares complexos), Re em [-10, -0,1];
* "Wilkinson": raízes -1, -2, ..., -n (mal condicionadas para n grande [Wilkinson, 1984]).

Para cada n: tempo mediano de Routh, raízes (companheira e Aberth), Nyquist
completo, margens, Bode (1000 pontos) e Lugar das Raízes; erro máximo relativo das
raízes; acerto da classificação de estabilidade por Routh e por Nyquist.
"""
from __future__ import annotations

import time

import numpy as np

from comum import CORES, LARGURA, ambiente, eixo_virgula, num, num_sci, plt, salvar, salvar_json, tabela_latex
from estabilidade import FT, bode, lugar_raizes, margens, nyquist, tabela_routh
from estabilidade.polinomios import de_raizes, soma
from estabilidade.raizes import raizes_aberth, raizes_companheira

ORDENS = [2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30]
DESTAQUE = [5, 10, 20]
REPETICOES = 7
rng = np.random.default_rng(2026)


def raizes_aleatorias(n):
    r = []
    while len(r) < n:
        if n - len(r) >= 2 and rng.random() < 0.5:
            a, b = -rng.uniform(0.1, 10), rng.uniform(0.5, 10)
            r += [a + 1j * b, a - 1j * b]
        else:
            r.append(-rng.uniform(0.1, 10))
    return np.array(r, dtype=complex)


def erro_relativo(calc, verdade):
    calc = list(np.asarray(calc, complex))
    pior = 0.0
    for v in verdade:
        d = [abs(c - v) for c in calc]
        j = int(np.argmin(d))
        pior = max(pior, d[j] / abs(v))
        calc.pop(j)
    return pior


def cronometra(f, rep=REPETICOES):
    tempos = []
    for _ in range(rep):
        t0 = time.perf_counter()
        f()
        tempos.append(time.perf_counter() - t0)
    return float(np.median(tempos))


def main():
    import control

    resultados = []
    for familia in ("aleatória", "Wilkinson"):
        for n in ORDENS:
            verdade = raizes_aleatorias(n) if familia == "aleatória" else -np.arange(1, n + 1, dtype=complex)
            p = de_raizes(verdade).real
            # L(s) = K / p(s) com K = p(0)/2: estável em MF, com cruzamentos
            L = FT([p[-1] * 0.5], p)
            reg = dict(familia=familia, n=n)
            reg["t_routh"] = cronometra(lambda: tabela_routh(p))
            reg["t_companheira"] = cronometra(lambda: raizes_companheira(p))
            reg["t_aberth"] = cronometra(lambda: raizes_aberth(p))
            reg["t_nyquist"] = cronometra(lambda: nyquist(L), rep=3)
            reg["t_margens"] = cronometra(lambda: margens(L), rep=3)
            w = np.logspace(-2, 3, 1000)
            reg["t_bode"] = cronometra(lambda: bode(L, w))
            reg["t_lugar"] = cronometra(lambda: lugar_raizes(L, max_pontos=4000), rep=1)
            reg["t_np_roots"] = cronometra(lambda: np.roots(p))
            Lc = control.tf(L.num, L.den)
            reg["t_ctrl_margin"] = cronometra(lambda: control.margin(Lc), rep=3)
            reg["t_ctrl_nyquist"] = cronometra(lambda: control.nyquist_response(Lc), rep=3)
            # erros numéricos
            reg["erro_companheira"] = erro_relativo(raizes_companheira(p), verdade)
            ab, it = raizes_aberth(p, retorna_iter=True)
            reg["erro_aberth"] = erro_relativo(ab, verdade)
            reg["iter_aberth"] = it
            rt = tabela_routh(p)
            reg["routh_correto"] = bool(rt.n_spd == 0 and rt.n_eixo == 0)
            col = np.abs(rt.primeira_coluna)
            reg["routh_faixa_dinamica"] = float(col.max() / col.min())
            # malha fechada: verdade = Routh no polinômio exato? usamos o veredito por raízes
            # do polinômio característico como referência e checamos concordância
            car = soma(L.den, L.num)
            spd_raizes = int(np.sum(raizes_companheira(car).real > 0))
            ny = nyquist(L)
            reg["nyquist_Z"] = ny.Z
            reg["routh_mf_spd"] = tabela_routh(car).n_spd
            reg["raizes_mf_spd"] = spd_raizes
            reg["pontos_nyquist"] = ny.n_pontos
            resultados.append(reg)
            print(familia, n, {k: (f"{v:.2e}" if isinstance(v, float) else v) for k, v in reg.items()
                               if k not in ("familia", "n")})

    # tabela (n = 5, 10, 20)
    linhas = []
    for fam in ("aleatória", "Wilkinson"):
        for r in [r for r in resultados if r["familia"] == fam and r["n"] in DESTAQUE]:
            linhas.append([fam, r["n"], num(r["t_routh"] * 1e6, 1), num(r["t_companheira"] * 1e6, 1),
                           num(r["t_aberth"] * 1e6, 1), num(r["t_nyquist"] * 1e3, 2),
                           num(r["t_margens"] * 1e3, 1), num(r["t_lugar"] * 1e3, 0),
                           num_sci(r["erro_companheira"], 1), num_sci(r["erro_aberth"], 1),
                           "sim" if r["routh_correto"] else "não"])
    tabela_latex("escalabilidade",
                 ["Família", "$n$", "Routh ($\\mu$s)", "Compan. ($\\mu$s)", "Aberth ($\\mu$s)",
                  "Nyquist (ms)", "Margens (ms)", "Lugar (ms)", "Erro compan.", "Erro Aberth", "Routh ok"],
                 linhas, "llccccccccc")

    # figuras
    fig, ax = plt.subplots(1, 2, figsize=(LARGURA, 2.5))
    al = [r for r in resultados if r["familia"] == "aleatória"]
    ns = [r["n"] for r in al]
    for chave, rot, est in (("t_routh", "Routh", "o-"), ("t_companheira", "Raízes (companheira)", "s-"),
                            ("t_aberth", "Raízes (Aberth)", "^-"), ("t_nyquist", "Nyquist (contorno)", "d-"),
                            ("t_margens", "Margens (200 mil pts)", "v-"), ("t_lugar", "Lugar das Raízes", "x-")):
        ax[0].loglog(ns, [r[chave] for r in al], est, ms=3, lw=1, label=rot)
    from matplotlib.ticker import FixedLocator, NullFormatter, NullLocator
    ax[0].xaxis.set_major_locator(FixedLocator([2, 5, 10, 20, 30]))
    ax[0].xaxis.set_minor_locator(NullLocator())
    ax[0].xaxis.set_minor_formatter(NullFormatter())
    ax[0].set_xticklabels(["2", "5", "10", "20", "30"])
    ax[0].set_xlabel("ordem $n$")
    ax[0].set_ylabel("tempo mediano (s)")
    ax[0].set_ylim(5e-6, 300)
    ax[0].legend(fontsize=6, ncol=2, loc="upper left")
    for fam, cor in (("aleatória", CORES["exato"]), ("Wilkinson", CORES["aprox"])):
        rr = [r for r in resultados if r["familia"] == fam]
        ax[1].semilogy([r["n"] for r in rr], [max(r["erro_companheira"], 1e-17) for r in rr], "o-",
                       color=cor, ms=3, label=f"companheira – {fam}")
        ax[1].semilogy([r["n"] for r in rr], [max(r["erro_aberth"], 1e-17) for r in rr], "^--",
                       color=cor, ms=3, label=f"Aberth – {fam}")
    ax[1].set_xlabel("ordem $n$")
    ax[1].set_ylabel("erro relativo máximo das raízes")
    ax[1].legend(fontsize=6)
    eixo_virgula(ax[1], y=False)
    fig.tight_layout()
    salvar(fig, "escalabilidade")

    salvar_json("exp3_escalabilidade", dict(ambiente=ambiente(), repeticoes=REPETICOES,
                                            ordens=ORDENS, resultados=resultados))


if __name__ == "__main__":
    main()
