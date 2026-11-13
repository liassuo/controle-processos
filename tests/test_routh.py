import numpy as np
import pytest

from estabilidade.polinomios import de_raizes
from estabilidade.routh import tabela_routh, determinantes_hurwitz, faixas_ganho_estavel
from estabilidade import sistemas as S


def contagem_real(raizes, tol=1e-7):
    r = np.asarray(raizes)
    return int(np.sum(r.real > tol)), int(np.sum(np.abs(r.real) <= tol)), int(np.sum(r.real < -tol))


@pytest.mark.parametrize("raizes", [
    [-1, -2, -3],
    [1, -2, -3],
    [1 + 2j, 1 - 2j, -1],
    [0.5, 2, 3, -1 + 1j, -1 - 1j],
    [-0.1 + 5j, -0.1 - 5j, -3, -4, -7],
])
def test_contagem_casos_gerais(raizes):
    r = tabela_routh(de_raizes(raizes))
    spd, eixo, spe = contagem_real(raizes)
    assert (r.n_spd, r.n_eixo, r.n_spe) == (spd, eixo, spe)
    assert not r.casos_especiais


def test_zero_na_primeira_coluna():
    # s^5 + 2s^4 + 2s^3 + 4s^2 + 11s + 10: exemplo clássico (Nise), 2 raízes no SPD
    p = [1, 2, 2, 4, 11, 10]
    r = tabela_routh(p)
    assert any("1ª coluna" in c for c in r.casos_especiais)
    assert r.n_spd == 2
    spd, _, _ = contagem_real(np.roots(p))
    assert r.n_spd == spd


def test_linha_nula_com_raizes_no_eixo():
    # (s^2 + 4)(s + 1)(s + 2): par ±2j sobre o eixo
    p = np.polymul([1, 0, 4], np.polymul([1, 1], [1, 2]))
    r = tabela_routh(p)
    assert any("nula" in c for c in r.casos_especiais)
    assert (r.n_spd, r.n_eixo, r.n_spe) == (0, 2, 2)
    assert not r.estavel


def test_linha_nula_com_pares_simetricos_reais():
    # (s^2 - 4)(s + 3): raízes ±2 e -3 -> linha nula, 1 no SPD
    p = np.polymul([1, 0, -4], [1, 3])
    r = tabela_routh(p)
    assert (r.n_spd, r.n_eixo, r.n_spe) == (1, 0, 2)


def test_raiz_na_origem():
    r = tabela_routh([1, 3, 2, 0])
    assert (r.n_spd, r.n_eixo, r.n_spe) == (0, 1, 2)


def test_hurwitz_consistente_com_routh():
    p = de_raizes([-1, -2, -3, -0.5 + 1j, -0.5 - 1j])
    assert np.all(determinantes_hurwitz(p) > 0)
    p2 = de_raizes([1, -2, -3])
    assert not np.all(determinantes_hurwitz(p2) > 0)


def test_ganho_critico_sistema_a():
    L = S.sistema_a(1.0)
    faixas = faixas_ganho_estavel(L.num, L.den, 1e-3, 1e3)
    assert len(faixas) == 1
    assert faixas[0][1] == pytest.approx(60.0, rel=1e-6)


def test_ganho_minimo_sistema_b():
    L = S.sistema_b(1.0)
    faixas = faixas_ganho_estavel(L.num, L.den, 1e-2, 1e6)
    assert faixas[0][0] == pytest.approx(40000 / 196.2, rel=1e-6)
    assert np.isinf(faixas[0][1])


def test_faixa_sistema_c():
    L = S.sistema_c(1.0)
    faixas = faixas_ganho_estavel(L.num, L.den, 1e-3, 1e3)
    assert faixas[0][1] == pytest.approx(60 / 7, rel=1e-6)


@pytest.mark.parametrize("ordem", [6, 10, 15, 20])
def test_regressao_pade_alta_ordem(ordem):
    """Polinômios com faixa dinâmica de até 1e37 (Padé de ordem alta): o veredito do
    Routh deve coincidir com o das raízes (falhava com tolerância absoluta)."""
    from estabilidade.raizes import raizes_companheira
    for tau in (0.01, 0.5, 1.0, 1.2):
        p = S.sistema_d(tau).com_pade(ordem).polinomio_caracteristico()
        assert tabela_routh(p).estavel == bool(np.all(raizes_companheira(p).real < 0))
