"""Aproximação de Padé [N/N] para o atraso exp(-tau s) [Padé, 1892].

    exp(-tau s) ≈ sum_k c_k (-tau s)^k / sum_k c_k (tau s)^k,
    c_k = (2N - k)! N! / ((2N)! k! (N - k)!)

A aproximação tem módulo unitário em s = jω (é passa-tudo), portanto só erra
na fase, e o erro cresce com ω·tau.
"""
from __future__ import annotations

from math import factorial

import numpy as np


def coeficientes(ordem: int) -> np.ndarray:
    n = ordem
    return np.array([factorial(2 * n - k) * factorial(n)
                     / (factorial(2 * n) * factorial(k) * factorial(n - k))
                     for k in range(n + 1)])


def pade(tau: float, ordem: int):
    """Retorna (num, den) em potências decrescentes de s."""
    if ordem < 1:
        raise ValueError("ordem >= 1")
    c = coeficientes(ordem)
    k = np.arange(ordem + 1)
    num = c * (-tau) ** k
    den = c * tau ** k
    return num[::-1].astype(float), den[::-1].astype(float)


def erro_fase(tau: float, ordem: int, w) -> np.ndarray:
    """Erro de fase (rad) da aproximação em relação a -ω·tau, com desdobramento."""
    from .polinomios import horner
    w = np.asarray(w, dtype=float)
    num, den = pade(tau, ordem)
    h = horner(num, 1j * w) / horner(den, 1j * w)
    fase = np.unwrap(np.angle(h))
    return fase - (-w * tau)
