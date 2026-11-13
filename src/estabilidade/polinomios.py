"""Operações básicas com polinômios (coeficientes em ordem decrescente de potência).

Convenção usada em todo o pacote: p = [a_n, a_{n-1}, ..., a_0], ou seja,
p(s) = a_n s^n + ... + a_0, a mesma convenção de ``numpy.polyval``.
Apenas NumPy é usado (vetores e aritmética); nenhuma toolbox de controle.
"""
from __future__ import annotations

import numpy as np


def como_poli(p, dtype=float) -> np.ndarray:
    """Converte para vetor 1-D e remove zeros à esquerda (mantém ao menos um termo)."""
    a = np.atleast_1d(np.asarray(p, dtype=dtype)).ravel()
    nz = np.flatnonzero(a != 0)
    if nz.size == 0:
        return np.zeros(1, dtype=dtype)
    return a[nz[0]:].copy()


def grau(p) -> int:
    return como_poli(p).size - 1


def horner(p, x):
    """Avalia p(x) pelo método de Horner (vetorizado em x; x pode ser complexo).

    Custo: n multiplicações e n somas por ponto -> O(n) por avaliação.
    """
    p = np.asarray(p)
    x = np.asarray(x)
    y = np.zeros(np.broadcast(x).shape, dtype=np.result_type(p.dtype, x.dtype, float))
    for c in p:
        y = y * x + c
    return y


def derivada(p) -> np.ndarray:
    p = como_poli(p, np.result_type(np.asarray(p), float))
    n = p.size - 1
    if n == 0:
        return np.zeros(1, dtype=p.dtype)
    return p[:-1] * np.arange(n, 0, -1)


def multiplica(a, b) -> np.ndarray:
    """Produto (convolução dos coeficientes)."""
    return np.convolve(np.atleast_1d(a), np.atleast_1d(b))


def soma(a, b) -> np.ndarray:
    a = np.atleast_1d(np.asarray(a, dtype=np.result_type(a, b, float)))
    b = np.atleast_1d(np.asarray(b, dtype=np.result_type(a, b, float)))
    n = max(a.size, b.size)
    return np.pad(a, (n - a.size, 0)) + np.pad(b, (n - b.size, 0))


def de_raizes(raizes, ganho: float = 1.0) -> np.ndarray:
    """Polinômio mônico (vezes ``ganho``) com as raízes dadas; coeficientes reais
    quando as raízes complexas aparecem em pares conjugados."""
    p = np.array([1.0 + 0j])
    for r in np.atleast_1d(raizes):
        p = np.convolve(p, [1.0, -r])
    if np.allclose(p.imag, 0, atol=1e-12 * max(1.0, np.abs(p).max())):
        p = p.real
    return ganho * p
