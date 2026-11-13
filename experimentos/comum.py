"""Utilitários comuns aos experimentos: caminhos, estilo de gráficos e formatação pt-BR."""
from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402
import numpy as np  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
RESULTADOS = RAIZ / "results"
FIG = RESULTADOS / "figuras"
TAB = RESULTADOS / "tabelas"
for d in (FIG, TAB):
    d.mkdir(parents=True, exist_ok=True)

LARGURA = 6.3  # polegadas (coluna única do modelo SBC)
CORES = {"exato": "#1f4e79", "aprox": "#c55a11", "ref": "#7f7f7f", "destaque": "#2e8b57"}

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.titlesize": 9,
    "axes.labelsize": 9,
    "legend.fontsize": 8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "lines.linewidth": 1.2,
    "savefig.bbox": "tight",
    "savefig.dpi": 300,
    "axes.formatter.use_mathtext": True,
})


def _virgula(x, _pos=None):
    s = f"{x:g}"
    return s.replace(".", ",")


VIRGULA = FuncFormatter(_virgula)


def eixo_virgula(ax, x=True, y=True):
    if x and ax.get_xscale() == "linear":
        ax.xaxis.set_major_formatter(VIRGULA)
    if y and ax.get_yscale() == "linear":
        ax.yaxis.set_major_formatter(VIRGULA)


def salvar(fig, nome):
    fig.savefig(FIG / f"{nome}.pdf")
    fig.savefig(FIG / f"{nome}.png")
    plt.close(fig)


def num(x, casas=3):
    """Número em notação pt-BR para tabelas (vírgula decimal)."""
    if x is None:
        return "--"
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    if not np.isfinite(x):
        return "$\\infty$" if x > 0 else "$-\\infty$"
    return f"{x:.{casas}f}".replace(".", "{,}")


def num_sci(x, casas=2):
    if x == 0:
        return "0"
    e = int(np.floor(np.log10(abs(x))))
    m = x / 10 ** e
    return f"${m:.{casas}f} \\times 10^{{{e}}}$".replace(".", "{,}")


def tabela_latex(nome, cabecalho, linhas, alinhamento=None):
    alinhamento = alinhamento or "l" + "c" * (len(cabecalho) - 1)
    corpo = [f"\\begin{{tabular}}{{{alinhamento}}}", "\\hline",
             " & ".join(cabecalho) + " \\\\", "\\hline"]
    corpo += [" & ".join(str(c) for c in l) + " \\\\" for l in linhas]
    corpo += ["\\hline", "\\end{tabular}"]
    (TAB / f"{nome}.tex").write_text("\n".join(corpo) + "\n", encoding="utf-8")


def tabela_csv(nome, cabecalho, linhas):
    import csv
    with open(TAB / f"{nome}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cabecalho)
        w.writerows(linhas)


def ambiente():
    import matplotlib as mpl
    info = {"python": sys.version.split()[0], "numpy": np.__version__,
            "matplotlib": mpl.__version__, "plataforma": platform.platform(),
            "processador": platform.processor()}
    try:
        import control
        import scipy
        info["control"] = control.__version__
        info["scipy"] = scipy.__version__
    except ImportError:
        pass
    return info


def salvar_json(nome, dados):
    def conv(o):
        if isinstance(o, (np.floating, np.integer)):
            return o.item()
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, complex):
            return [o.real, o.imag]
        return str(o)
    (RESULTADOS / f"{nome}.json").write_text(json.dumps(dados, indent=2, default=conv,
                                                         ensure_ascii=False), encoding="utf-8")
