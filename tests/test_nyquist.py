import numpy as np
import pytest

from estabilidade import FT, nyquist, sistemas as S
from estabilidade.nyquist import voltas_soma_angulos, voltas_cruzamentos
from estabilidade.polinomios import multiplica as mul, soma
from estabilidade.raizes import raizes_companheira


def spd_malha_fechada(L):
    return int(np.sum(raizes_companheira(soma(L.den, L.num)).real > 1e-9))


def test_winding_circulo():
    th = np.linspace(0, 2 * np.pi, 400, endpoint=False)
    c = -1 + 0.5 * np.exp(1j * th)                    # anti-horário em torno de -1
    assert round(voltas_soma_angulos(c)) == 1
    assert voltas_cruzamentos(c) == 1
    assert voltas_cruzamentos(c[::-1]) == -1
    duas = -1 + 0.5 * np.exp(2j * th)
    assert voltas_cruzamentos(duas) == 2
    fora = 2 + 0.5 * np.exp(1j * th)
    assert voltas_cruzamentos(fora) == 0


@pytest.mark.parametrize("L", [
    S.sistema_a(20), S.sistema_a(70), S.sistema_b(400), S.sistema_b(150),
    S.sistema_c(7), S.sistema_c(10),
    FT([3], mul([1, 0], mul([1, 1], [1, 2]))),          # tipo 1, estável
    FT([10], mul([1, 0], mul([1, 1], [1, 2]))),         # tipo 1, instável
    FT([1, 1], mul([1, 0, 0], [1, 10])),                # tipo 2: dupla integração
    FT([5], mul([1, 0, 4], [1, 1])),                    # polos em ±2j (indentação)
    FT([1, 2], mul([1, -1], [1, 3])),                   # P = 1
])
def test_z_igual_polos_spd_malha_fechada(L):
    r = nyquist(L)
    assert r.N_horario == r.N_cruzamentos
    assert abs(r.voltas_float - round(r.voltas_float)) < 1e-6
    assert r.Z == spd_malha_fechada(L)


def test_sistema_b_envolve_anti_horario():
    r = nyquist(S.sistema_b())
    assert r.P == 1 and r.N_horario == -1 and r.Z == 0


@pytest.mark.parametrize("tau,estavel", [(0.5, True), (1.0, True), (1.1, True), (1.15, False), (2.0, False)])
def test_sistema_d_com_atraso(tau, estavel):
    # limite analítico calculado pelas margens: τ_crit ≈ 1.122 s
    r = nyquist(S.sistema_d(tau))
    assert r.estavel_malha_fechada == estavel
    assert r.N_horario == r.N_cruzamentos


def test_primeira_ordem_com_atraso_limite_analitico():
    # L = 2 e^{-τ s}/(s+1): ω = √3, τ_crit = (π - atan √3)/√3 = 2π/(3√3)
    tau_c = 2 * np.pi / (3 * np.sqrt(3))
    assert nyquist(FT([2], [1, 1], tau_c * 0.98)).Z == 0
    assert nyquist(FT([2], [1, 1], tau_c * 1.02)).Z == 2


def test_rejeita_impropria():
    with pytest.raises(ValueError):
        nyquist(FT([1, 0, 0], [1, 1]))
