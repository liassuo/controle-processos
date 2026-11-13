"""Simulação no domínio do tempo, usada como verificação independente dos critérios.

* ``resposta_degrau_malha_fechada``: malha com realimentação negativa unitária
  r -> e -> L(s) -> y, com o atraso aplicado na entrada de L (buffer com
  interpolação linear), integrada por Runge–Kutta de 4ª ordem com passo fixo.
* ``diverge``: classificação empírica da estabilidade pela evolução da envoltória
  do erro.

Realização em espaço de estados na forma canônica controlável (implementação própria).
"""
from __future__ import annotations

import numpy as np

from .funcao_transferencia import FT


def espaco_estados(L: FT):
    """(A, B, C, D) na forma canônica controlável para L racional própria."""
    num = np.asarray(L.num, float)
    den = np.asarray(L.den, float)
    n = den.size - 1
    num = np.pad(num, (n + 1 - num.size, 0)) / den[0]
    den = den / den[0]
    d = num[0]
    c = num[1:] - d * den[1:]
    A = np.zeros((n, n))
    A[0, :] = -den[1:]
    if n > 1:
        A[1:, :-1] = np.eye(n - 1)
    B = np.zeros(n)
    B[0] = 1.0
    return A, B, c, d


def resposta_degrau_malha_fechada(L: FT, t_final: float, dt: float = 1e-3, r: float = 1.0):
    if not L.estritamente_propria:
        raise ValueError("use L estritamente própria (evita laço algébrico)")
    A, B, C, _ = espaco_estados(L)
    n = A.shape[0]
    passos = int(round(t_final / dt))
    atraso_amostras = L.atraso / dt
    x = np.zeros(n)
    t = np.arange(passos + 1) * dt
    y = np.zeros(passos + 1)
    e = np.zeros(passos + 1)

    def entrada(k_float):
        # e(t - τ) com interpolação linear sobre o histórico; e(t<0) = 0
        if k_float < 0:
            return 0.0
        i = int(np.floor(k_float))
        f = k_float - i
        if i + 1 >= len(e) or f == 0:
            return e[min(i, len(e) - 1)]
        return (1 - f) * e[i] + f * e[i + 1]

    def f(xv, u):
        return A @ xv + B * u

    for k in range(passos):
        y[k] = C @ x
        e[k] = r - y[k]
        u0 = entrada(k - atraso_amostras)
        u_meio = entrada(k + 0.5 - atraso_amostras) if atraso_amostras >= 0.5 else u0
        u1 = entrada(k + 1 - atraso_amostras) if atraso_amostras >= 1 else u0
        if L.atraso == 0:
            u_meio = u1 = u0  # sem atraso: e mantido no passo (malha amostrada fina)
        k1 = f(x, u0)
        k2 = f(x + 0.5 * dt * k1, u_meio)
        k3 = f(x + 0.5 * dt * k2, u_meio)
        k4 = f(x + dt * k3, u1)
        x = x + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        if not np.all(np.isfinite(x)) or np.max(np.abs(x)) > 1e12:
            y[k + 1:] = np.nan
            break
    else:
        y[-1] = C @ x
    return t, y


def diverge(t, y, r: float = 1.0) -> bool:
    """Instável se o erro cresce: compara a amplitude do erro no último quarto do
    horizonte com a do segundo quarto."""
    if np.any(~np.isfinite(y)):
        return True
    e = np.abs(r - y)
    n = len(e)
    meio = e[n // 4: n // 2].max()
    fim = e[3 * n // 4:].max()
    return bool(fim > 1.05 * meio and fim > 1e-6)
