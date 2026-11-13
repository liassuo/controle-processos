"""Validação cruzada com bibliotecas consolidadas (python-control e SciPy).

Essas bibliotecas são usadas somente aqui, como referência externa.
"""
import numpy as np
import pytest

from estabilidade import margens, nyquist, pade, sistemas as S
from estabilidade.raizes import raizes_companheira, distancia_conjuntos
from estabilidade.polinomios import soma

control = pytest.importorskip("control")
signal = pytest.importorskip("scipy.signal")


def tf_ctrl(L):
    return control.tf(L.num, L.den)


@pytest.mark.parametrize("nome", ["A", "B", "C"])
def test_margens_vs_python_control(nome):
    L = S.todos()[nome]
    gm, pm, wcg_ctrl, wcp_ctrl = control.margin(tf_ctrl(L))   # (gm, pm, w_180, w_cg)
    m = margens(L)
    assert m.mf == pytest.approx(pm, rel=1e-5)
    assert m.w_cg == pytest.approx(wcp_ctrl, rel=1e-5)
    if np.isfinite(gm) and wcg_ctrl > 0:
        assert m.mg == pytest.approx(gm, rel=1e-5)


@pytest.mark.parametrize("nome", ["A", "B", "C"])
def test_encirclements_vs_python_control(nome):
    L = S.todos()[nome]
    resp = control.nyquist_response(tf_ctrl(L))
    assert nyquist(L).N_horario == resp.count


@pytest.mark.parametrize("nome", ["A", "B", "C"])
def test_polos_malha_fechada_vs_control(nome):
    L = S.todos()[nome]
    ref = control.poles(control.feedback(tf_ctrl(L), 1))
    nosso = raizes_companheira(soma(L.den, L.num))
    assert distancia_conjuntos(nosso, ref) < 1e-8


@pytest.mark.parametrize("ordem", [1, 3, 5])
def test_pade_vs_python_control(ordem):
    n_ref, d_ref = control.pade(0.5, ordem)
    n, d = pade(0.5, ordem)
    # normaliza pelo coeficiente líder do denominador
    assert np.allclose(np.asarray(n) / d[0], np.asarray(n_ref) / d_ref[0])
    assert np.allclose(np.asarray(d) / d[0], np.asarray(d_ref) / d_ref[0])


def test_resposta_frequencia_vs_scipy():
    L = S.sistema_a()
    w = np.logspace(-2, 2, 200)
    _, h_ref = signal.freqs(L.num, L.den, worN=w)
    assert np.allclose(L.resposta_frequencia(w), h_ref, rtol=1e-12)


def test_margem_atraso_sistema_d_vs_python_control():
    L = S.sistema_d(0.0)
    _, pm, _, wcp = control.margin(tf_ctrl(L))
    m = margens(S.sistema_d(0.5))
    assert m.margem_atraso == pytest.approx(np.radians(pm) / wcp - 0.5, rel=1e-5)
