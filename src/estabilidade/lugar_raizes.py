"""Lugar das Raízes [Evans, 1948], implementado do zero.

Para L(s) = K N(s)/D(s), o lugar é o conjunto das raízes de D(s) + K N(s) = 0,
com K variando de 0 a ∞. Implementação:

* passo adaptativo em K: o passo é reduzido quando alguma raiz se desloca mais
  que uma fração da escala do problema e ampliado quando o movimento é pequeno;
* continuidade dos ramos por emparelhamento ao vizinho mais próximo;
* elementos analíticos das regras de construção: assíntotas (centroide e
  ângulos), pontos de separação/chegada (raízes reais de N'D - N D' = 0 com K > 0)
  e cruzamentos do eixo jω (ganho crítico, por bissecção na parte real máxima).

L(s) com atraso não é racional: neste caso o lugar deve ser traçado sobre a
aproximação de Padé (``FT.com_pade``), o que é justamente uma limitação do
método no plano s.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .funcao_transferencia import FT
from .polinomios import derivada, multiplica, soma
from .raizes import raizes_companheira


@dataclass
class LugarRaizes:
    k: np.ndarray                  # ganhos amostrados
    raizes: np.ndarray             # (len(k), n) ramos ordenados por continuidade
    centroide: float
    angulos_assintotas: np.ndarray # graus
    separacao: list                # (s, K) pontos de separação/chegada no eixo real
    cruzamentos_jw: list           # (K, ω) cruzamentos do eixo imaginário


def _emparelha(ant, novas):
    novas = list(novas)
    saida = np.empty_like(ant)
    for i in np.argsort(-np.abs(ant.imag)):          # ordem estável
        d = [abs(ant[i] - x) for x in novas]
        j = int(np.argmin(d))
        saida[i] = novas.pop(j)
    return saida


def _max_real(num, den, k):
    return np.max(raizes_companheira(soma(den, k * num)).real)


def lugar_raizes(L: FT, k_max: float | None = None, max_pontos: int = 20000,
                 desloc_max: float = 0.02) -> LugarRaizes:
    if L.atraso:
        raise ValueError("Lugar das Raízes exige L(s) racional; use L.com_pade(N)")
    num, den = L.num, L.den
    n, m = den.size - 1, num.size - 1
    polos, zeros = L.polos(), L.zeros()
    escala = max(1.0, np.max(np.abs(np.concatenate([polos, zeros]))))
    if k_max is None:
        k_max = 1e3 * max(1.0, abs(den[0] / num[0])) * escala ** max(n - m, 1)

    ks = [0.0]
    rs = [polos.copy()]
    k, dk = 0.0, k_max * 1e-9
    while k < k_max and len(ks) < max_pontos:
        k_novo = min(k + dk, k_max)
        r = _emparelha(rs[-1], raizes_companheira(soma(den, k_novo * num)))
        mov = np.max(np.abs(r - rs[-1])) / escala
        if mov > desloc_max and dk > 1e-14 * max(1.0, k):
            dk *= 0.5
            continue
        ks.append(k_novo)
        rs.append(r)
        k = k_novo
        if mov < desloc_max / 4:
            dk *= 2.0

    # regras de construção
    q = n - m
    if q > 0:
        centroide = float((np.sum(polos).real - np.sum(zeros).real) / q)
        angulos = np.array([(2 * i + 1) * 180.0 / q for i in range(q)])
    else:
        centroide, angulos = np.nan, np.array([])

    # pontos de separação: d/ds [ -D/N ] = 0  <=>  N D' - N' D = 0
    eq = soma(multiplica(num, derivada(den)), -multiplica(derivada(num), den))
    separacao = []
    for s0 in raizes_companheira(eq):
        if abs(s0.imag) < 1e-7 * max(1, abs(s0)):
            s0 = s0.real
            nv = np.polyval(num, s0)
            if nv != 0:
                k0 = -np.polyval(den, s0) / nv
                if k0 > 0:
                    separacao.append((float(s0), float(k0)))

    # cruzamentos do eixo jω: mudança de sinal de max Re(raízes) ao longo de K
    cruz = []
    ks_arr = np.array(ks)
    mr = np.array([np.max(r.real) for r in rs])
    tol_re = 1e-9 * escala
    sinal = np.where(np.abs(mr) <= tol_re, 0, np.sign(mr))
    # polos de malha aberta sobre o eixo (ex.: integrador) não são cruzamentos:
    # propaga o primeiro sinal não nulo para trás
    nz = np.flatnonzero(sinal != 0)
    if nz.size:
        sinal[: nz[0]] = sinal[nz[0]]
    for i in np.flatnonzero(sinal[:-1] * sinal[1:] < 0):
        a, b = ks_arr[i], ks_arr[i + 1]
        fa = _max_real(num, den, a)
        for _ in range(200):
            c = 0.5 * (a + b)
            fc = _max_real(num, den, c)
            if np.sign(fc) == np.sign(fa):
                a, fa = c, fc
            else:
                b = c
            if b - a < 1e-13 * max(1.0, b):
                break
        kc = 0.5 * (a + b)
        r = raizes_companheira(soma(den, kc * num))
        w = float(np.max(np.abs(r[np.argsort(np.abs(r.real))[:2]].imag)))
        cruz.append((float(kc), w))

    return LugarRaizes(k=ks_arr, raizes=np.array(rs), centroide=centroide,
                       angulos_assintotas=angulos, separacao=separacao, cruzamentos_jw=cruz)
