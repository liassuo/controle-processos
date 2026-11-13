"""Os quatro sistemas de benchmark do enunciado (Fase 1).

Todos são funções de transferência de malha aberta L(s) = G(s)H(s), com
realimentação negativa unitária. Os parâmetros foram escolhidos pelo grupo para
exercitar cada característica pedida; as hipóteses estão descritas em cada função.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .funcao_transferencia import FT
from .polinomios import multiplica as mul

G = 9.81  # m/s²


def sistema_a(k: float = 20.0) -> FT:
    """Sistema A: estável em malha aberta, 3ª ordem.

    L(s) = K / ((s+1)(s+2)(s+3)), com polos reais em -1, -2 e -3.
    Ganho crítico analítico K = 60 (Routh), com cruzamento em ω = √11 rad/s.
    """
    return FT([k], mul(mul([1, 1], [1, 2]), [1, 3]), nome="Sistema A")


@dataclass
class ParametrosLevitador:
    x0: float = 2 * G / 400.0   # entreferro de equilíbrio (m) -> polo instável em 20 rad/s
    i0: float = 1.0             # corrente de equilíbrio (A)


def planta_levitador(p: ParametrosLevitador = ParametrosLevitador()) -> FT:
    """Levitador magnético linearizado (Sistema B, planta).

    Modelo m ẍ = m g - c i²/x². Linearizado em (x0, i0), com m g = c i0²/x0², dá
    δẍ = (2g/x0) δx - (2g/i0) δi. A saída é medida para cima (y = -δx), o que
    torna o ganho positivo:

        G(s) = (2g/i0) / (s² - 2g/x0),  com polos em ±√(2g/x0).
    """
    a = 2 * G / p.x0
    b = 2 * G / p.i0
    return FT([b], [1.0, 0.0, -a], nome="Levitador")


def controlador_avanco(k: float = 400.0, z: float = 10.0, p: float = 100.0) -> FT:
    """Compensador de avanço de fase C(s) = K (s + z)/(s + p)."""
    return FT(mul([k], [1, z]), [1, p], nome="Avanço")


def sistema_b(k: float = 400.0) -> FT:
    """Sistema B: planta instável em malha aberta (P = 1) com compensador de avanço.

    L(s) = K (s+10) · 19,62 / ((s+100)(s² - 400)). Pelo Routh, a malha fechada é
    estável para K > 203,87 (ganho mínimo, não máximo).
    """
    L = controlador_avanco(k) * planta_levitador()
    L.nome = "Sistema B"
    return L


def sistema_c(k: float = 7.0) -> FT:
    """Sistema C: fase não mínima, com zero no SPD em s = +1.

    L(s) = K (1 - s) / ((s+1)(s+2)(s+3)). Pelo Routh, a malha é estável para
    0 < K < 60/7 ≈ 8,571. O gêmeo de fase mínima K(1+s)/(...) tem o mesmo |L(jω)|
    e é estável para todo K > 0.
    """
    return FT([-k, k], mul(mul([1, 1], [1, 2]), [1, 3]), nome="Sistema C")


def sistema_c_fase_minima(k: float = 7.0) -> FT:
    return FT([k, k], mul(mul([1, 1], [1, 2]), [1, 3]), nome="Sistema C (fase mínima)")


@dataclass
class ParametrosPID:
    kp: float = 2.0
    ki: float = 1.0
    kd: float = 0.5
    tf: float = 0.1     # constante do filtro derivativo (s)


def controlador_pid(p: ParametrosPID = ParametrosPID()) -> FT:
    """C(s) = Kp + Ki/s + Kd s/(Tf s + 1)."""
    num = [p.kp * p.tf + p.kd, p.kp + p.ki * p.tf, p.ki]
    den = mul([1, 0], [p.tf, 1])
    return FT(num, den, nome="PID")


def planta_processo() -> FT:
    """Processo de 2ª ordem G_p(s) = 1 / ((s+1)(0,5 s+1)), constantes de tempo de 1 s e 0,5 s."""
    return FT([1.0], mul([1, 1], [0.5, 1]), nome="Processo")


def sistema_d(tau: float = 0.5, pid: ParametrosPID = ParametrosPID()) -> FT:
    """Sistema D: malha PID sobre rede, com atraso puro de transporte τ.

    L(s) = C_PID(s) G_p(s) exp(-τ s). É o mesmo laço usado na simulação HIL
    (Fase 4, trilha EC), em que τ representa o atraso de comunicação.
    """
    L = controlador_pid(pid) * planta_processo()
    L.atraso = tau
    L.nome = "Sistema D"
    return L


def todos() -> dict:
    return {"A": sistema_a(), "B": sistema_b(), "C": sistema_c(), "D": sistema_d()}
