"""Margens de ganho e de fase, extraídas da resposta em frequência L(jω).

* Frequência de cruzamento de ganho ω_cg: |L(jω)| = 1. Margem de fase
  MF = 180° + ∠L(jω_cg), com a fase desdobrada continuamente em ω.
* Frequência de cruzamento de fase ω_cf: ∠L(jω) = -180° + k·360°. Margem de ganho
  MG = 1/|L(jω_cf)|, também expressa em dB.
* Margem de atraso: MA = MF[rad] / ω_cg, o maior atraso adicional tolerado.

As raízes das condições acima são isoladas em uma grade logarítmica densa e
refinadas por bissecção. A interpretação das margens pressupõe P = 0; para
P > 0 a estabilidade deve ser decidida pelo critério de Nyquist completo.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .funcao_transferencia import FT


@dataclass
class Margens:
    mg: float                 # margem de ganho (linear); inf se não houver ω_cf
    mg_db: float
    w_cf: float               # frequência de cruzamento de fase (rad/s)
    mf: float                 # margem de fase (graus); inf se não houver ω_cg
    w_cg: float               # frequência de cruzamento de ganho (rad/s)
    margem_atraso: float      # s
    todos_cg: list = field(default_factory=list)   # (ω, MF)
    todos_cf: list = field(default_factory=list)   # (ω, MG)


def _bissecao(f, a, b, tol=1e-13, max_iter=200):
    fa = f(a)
    for _ in range(max_iter):
        m = 0.5 * (a + b)
        fm = f(m)
        if np.sign(fm) == np.sign(fa):
            a, fa = m, fm
        else:
            b = m
        if (b - a) <= tol * max(1.0, b):
            break
    return 0.5 * (a + b)


def fase_desdobrada(L: FT, w):
    """Fase contínua (rad) ao longo de ω crescente. A parte racional é desdobrada
    numericamente e o atraso é somado de forma exata (-ωτ)."""
    w = np.asarray(w, dtype=float)
    fase_rac = np.unwrap(np.angle(L.racional(1j * w)))
    return fase_rac - w * L.atraso


def margens(L: FT, w_min: float = 1e-4, w_max: float = 1e4, pontos: int = 200_000) -> Margens:
    w = np.geomspace(w_min, w_max, pontos)
    mag = np.abs(L.racional(1j * w))          # |exp(-jωτ)| = 1
    fase = fase_desdobrada(L, w)

    def fase_em(x, i):
        # fase em x dentro do intervalo [w[i], w[i+1]], ancorada em w[i]
        rel = np.angle(L.racional(1j * x) / L.racional(1j * w[i]))
        return fase[i] + rel - (x - w[i]) * L.atraso

    # cruzamentos de ganho: log|L| = 0
    lm = np.log(mag)
    cg = []
    for i in np.flatnonzero(np.sign(lm[:-1]) != np.sign(lm[1:])):
        wc = _bissecao(lambda x: np.log(np.abs(L.racional(1j * x))), w[i], w[i + 1])
        ph = np.degrees(fase_em(wc, i))
        mf = (ph + 180.0 + 180.0) % 360.0 - 180.0   # (-180, 180]
        cg.append((wc, mf))

    # cruzamentos de fase: fase = -180° + k·360°
    cf = []
    # caso ω = 0: L(0) real e negativo (típico com P > 0) é um cruzamento de fase
    d0 = L.den[-1]
    if d0 != 0:
        l0 = L.num[-1] / d0
        if l0 < 0:
            cf.append((0.0, 1.0 / abs(l0)))
    g = (fase + np.pi) / (2 * np.pi)          # inteiro nos cruzamentos
    k_ = np.floor(g)
    for i in np.flatnonzero(k_[:-1] != k_[1:]):
        alvo = max(k_[i], k_[i + 1])           # nível inteiro atravessado
        wf = _bissecao(lambda x, i=i, alvo=alvo: (fase_em(x, i) + np.pi) / (2 * np.pi) - alvo,
                       w[i], w[i + 1])
        cf.append((wf, 1.0 / np.abs(L.racional(1j * wf))))

    if cg:
        w_cg, mf = min(cg, key=lambda t: abs(t[1]))
        # margem de atraso: o menor atraso que leva algum cruzamento de ganho a -180°
        ma = min((np.radians(f) / wc for wc, f in cg if f > 0), default=0.0)
        if any(f <= 0 for _, f in cg):
            ma = 0.0
    else:
        w_cg, mf, ma = np.nan, np.inf, np.inf
    if cf:
        w_cf, mg = min(cf, key=lambda t: abs(np.log(t[1])))
    else:
        w_cf, mg = np.nan, np.inf
    return Margens(mg=mg, mg_db=20 * np.log10(mg) if np.isfinite(mg) else np.inf, w_cf=w_cf,
                   mf=mf, w_cg=w_cg, margem_atraso=ma, todos_cg=cg, todos_cf=cf)
