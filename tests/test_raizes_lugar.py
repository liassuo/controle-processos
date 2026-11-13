import numpy as np
import pytest

from estabilidade import lugar_raizes, sistemas as S
from estabilidade.polinomios import de_raizes
from estabilidade.raizes import raizes_companheira, raizes_aberth, distancia_conjuntos


@pytest.mark.parametrize("raizes", [
    [-1, -2, -3],
    [0.5 + 1j, 0.5 - 1j, -4, 2],
    list(-np.arange(1, 9)),
])
def test_raizes_conhecidas(raizes):
    p = de_raizes(raizes)
    assert distancia_conjuntos(raizes_companheira(p), raizes) < 1e-8
    assert distancia_conjuntos(raizes_aberth(p), raizes) < 1e-8


def test_raizes_na_origem():
    r = raizes_aberth([1, 3, 2, 0, 0])
    assert np.sum(np.abs(r) < 1e-12) == 2


def test_lugar_sistema_a():
    lr = lugar_raizes(S.sistema_a(1.0))
    assert lr.centroide == pytest.approx(-2.0)
    assert np.allclose(lr.angulos_assintotas, [60, 180, 300])
    (k, w), = lr.cruzamentos_jw
    assert k == pytest.approx(60.0, rel=1e-6)
    assert w == pytest.approx(np.sqrt(11), rel=1e-6)
    # separação entre -1 e -2: raiz de 3s² + 12s + 11 = 0
    s_sep = [s for s, _ in lr.separacao]
    assert any(abs(s - (-2 + 1 / np.sqrt(3))) < 1e-9 for s in s_sep)


def test_lugar_sistema_b_ganho_minimo():
    lr = lugar_raizes(S.sistema_b(1.0))
    ks = sorted(k for k, _ in lr.cruzamentos_jw)
    assert ks[0] == pytest.approx(40000 / 196.2, rel=1e-6)


def test_lugar_rejeita_atraso():
    with pytest.raises(ValueError):
        lugar_raizes(S.sistema_d())
