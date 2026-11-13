"""Cálculo de raízes de polinômios (polos e zeros), implementado sem toolbox de controle.

Dois algoritmos independentes, usados também na análise de custo e erro numérico:

* ``raizes_companheira``: autovalores da matriz companheira (Frobenius). É o mesmo
  princípio de ``numpy.roots`` [Edelman e Murakami, 1995]. Custo O(n^3); o
  autovalor é obtido com ``numpy.linalg.eigvals`` (LAPACK, com balanceamento).
* ``raizes_aberth``: iteração simultânea de Aberth–Ehrlich, implementada do zero,
  só com aritmética complexa. Custo O(n^2) por iteração, com convergência cúbica
  para raízes simples.
"""
from __future__ import annotations

import numpy as np

from .polinomios import como_poli, derivada, horner


def _remove_raizes_nulas(p):
    p = como_poli(p, np.result_type(np.asarray(p), float))
    k = 0
    while p.size > 1 and p[-1] == 0:
        p = p[:-1]
        k += 1
    return p, k


def matriz_companheira(p) -> np.ndarray:
    p = como_poli(p)
    n = p.size - 1
    c = np.zeros((n, n), dtype=np.result_type(p.dtype, float))
    c[0, :] = -p[1:] / p[0]
    if n > 1:
        c[1:, :-1] = np.eye(n - 1)
    return c


def raizes_companheira(p) -> np.ndarray:
    p, k = _remove_raizes_nulas(p)
    n = p.size - 1
    r = np.linalg.eigvals(matriz_companheira(p)) if n > 0 else np.array([], dtype=complex)
    return np.concatenate([np.asarray(r, dtype=complex), np.zeros(k, dtype=complex)])


def raizes_aberth(p, tol: float = 1e-14, max_iter: int = 500, retorna_iter: bool = False):
    """Método de Aberth–Ehrlich.

    Estimativas iniciais distribuídas em um círculo de raio dado pela cota de
    Fujiwara, com rotação para evitar simetrias exatas.
    """
    p, k = _remove_raizes_nulas(p)
    p = p.astype(complex)
    n = p.size - 1
    if n == 0:
        z = np.zeros(k, dtype=complex)
        return (z, 0) if retorna_iter else z
    a = p / p[0]
    # cota de Fujiwara para o módulo das raízes
    termos = [abs(a[i]) ** (1.0 / i) for i in range(1, n)] + [abs(a[n] / 2) ** (1.0 / n)]
    raio = 2.0 * max(termos) if max(termos) > 0 else 1.0
    ang = 2 * np.pi * np.arange(n) / n + 0.4
    z = raio * 0.5 * np.exp(1j * ang)
    dp = derivada(a)
    a_abs = np.abs(a)
    u = np.finfo(float).eps
    ativo = np.ones(n, bool)
    it = 0
    for it in range(1, max_iter + 1):
        pz = horner(a, z)
        # critério de parada por erro regressivo: |p(z)| no nível do erro de
        # arredondamento da avaliação de Horner, u·Σ|a_k||z|^k. Limiares mais
        # frouxos (4nu) pioram o erro direto em polinômios mal condicionados;
        # mais rígidos (0,1u) podem nunca ser atingidos (testado com Wilkinson n = 5..20).
        ativo &= ~(np.abs(pz) <= u * horner(a_abs, np.abs(z)))
        if not ativo.any():
            break
        dpz = horner(dp, z)
        with np.errstate(divide="ignore", invalid="ignore"):
            razao = pz / dpz
            dif = z[:, None] - z[None, :]
            np.fill_diagonal(dif, 1.0)
            soma_inv = (1.0 / dif).sum(axis=1) - 1.0  # remove o termo diagonal (1/1)
            passo = razao / (1.0 - razao * soma_inv)
        passo = np.where(np.isfinite(passo) & ativo, passo, 0.0)
        z = z - passo
        if np.max(np.abs(passo) / np.maximum(1.0, np.abs(z))) < tol:
            break
    z = np.concatenate([z, np.zeros(k, dtype=complex)])
    return (z, it) if retorna_iter else z


def ordena_raizes(r) -> np.ndarray:
    """Ordenação canônica (parte real, depois imaginária) para comparar conjuntos."""
    r = np.asarray(r, dtype=complex)
    return r[np.lexsort((np.round(r.imag, 9), np.round(r.real, 9)))]


def distancia_conjuntos(a, b) -> float:
    """Maior distância após emparelhamento guloso de raízes (métrica de erro)."""
    a = list(np.asarray(a, dtype=complex))
    b = list(np.asarray(b, dtype=complex))
    if len(a) != len(b):
        raise ValueError("conjuntos de tamanhos diferentes")
    pior = 0.0
    for x in a:
        d = [abs(x - y) for y in b]
        j = int(np.argmin(d))
        pior = max(pior, d[j])
        b.pop(j)
    return pior
