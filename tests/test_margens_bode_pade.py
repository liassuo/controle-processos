import numpy as np
import pytest

from estabilidade import FT, margens, bode, bode_assintotico, pade, sistemas as S
from estabilidade.pade import erro_fase
from estabilidade.polinomios import horner


def test_margens_sistema_a_analiticas():
    m = margens(S.sistema_a(20))
    assert m.w_cf == pytest.approx(np.sqrt(11), rel=1e-6)
    assert m.mg == pytest.approx(3.0, rel=1e-6)                     # 60/20


def test_margem_atraso_primeira_ordem():
    # L = 2/(s+1): ω_cg = √3, MF = 180 - 60 = 120°
    m = margens(FT([2], [1, 1]))
    assert m.w_cg == pytest.approx(np.sqrt(3), rel=1e-6)
    assert m.mf == pytest.approx(120.0, rel=1e-6)
    assert m.margem_atraso == pytest.approx(2 * np.pi / (3 * np.sqrt(3)), rel=1e-6)


def test_margem_ganho_sistema_b_em_w0():
    m = margens(S.sistema_b())
    assert m.w_cf == 0.0
    assert m.mg == pytest.approx(203.87359836901122 / 400, rel=1e-9)


def test_atraso_reduz_margem_de_fase():
    m0 = margens(S.sistema_d(0.0))
    m1 = margens(S.sistema_d(0.5))
    assert m1.w_cg == pytest.approx(m0.w_cg, rel=1e-9)               # módulo não muda
    assert m0.mf - m1.mf == pytest.approx(np.degrees(0.5 * m0.w_cg), rel=1e-6)


def test_bode_assintotico_baixa_e_alta_frequencia():
    L = S.sistema_a(20)
    w = np.array([1e-3, 1e3])
    exato, _ = bode(L, w)
    ass, _ = bode_assintotico(L, w)
    assert np.allclose(exato, ass, atol=0.01)


@pytest.mark.parametrize("ordem", [1, 2, 3, 5, 8])
def test_pade_passa_tudo_e_baixa_frequencia(ordem):
    num, den = pade(0.7, ordem)
    w = np.logspace(-3, 2, 50)
    h = horner(num, 1j * w) / horner(den, 1j * w)
    assert np.allclose(np.abs(h), 1.0, atol=1e-9)
    assert abs(erro_fase(0.7, ordem, [1e-3])[0]) < 1e-9


def test_pade_erro_diminui_com_ordem():
    e = [abs(erro_fase(1.0, n, [2.0])[0]) for n in (1, 2, 3, 4)]
    assert all(a > b for a, b in zip(e, e[1:]))
