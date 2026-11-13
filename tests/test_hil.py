"""Coerência entre os sketches do Tinkercad (hil/*.ino) e o gêmeo digital em Python."""
import re
from pathlib import Path

import numpy as np
import pytest

from estabilidade import margens, sistemas as S
from estabilidade.hil import ConfigHIL, atraso_critico_hil, discretiza_zoh, simula_hil

RAIZ = Path(__file__).resolve().parents[1]
PLANTA = (RAIZ / "hil" / "planta_rede" / "planta_rede.ino").read_text(encoding="utf-8")
CTRL = (RAIZ / "hil" / "controlador_pid" / "controlador_pid.ino").read_text(encoding="utf-8")


def const(src, nome):
    # apenas declarações "const <tipo> ... NOME = valor" (ignora comentários)
    m = re.search(rf"^\s*const\s+\w+[^;\n]*\b{nome}\s*=\s*(-?[0-9.eE+-]+)f?", src, re.M)
    assert m, nome
    return float(m.group(1))


def test_matrizes_zoh_do_sketch():
    Ad, Bd, C, _ = discretiza_zoh(S.planta_processo(), const(PLANTA, "TS"))
    esperado = {"AD00": Ad[0, 0], "AD01": Ad[0, 1], "AD10": Ad[1, 0], "AD11": Ad[1, 1],
                "BD0": Bd[0], "BD1": Bd[1], "C0": C[0], "C1": C[1]}
    for nome, v in esperado.items():
        assert const(PLANTA, nome) == pytest.approx(v, rel=1e-7, abs=1e-9), nome


def test_parametros_pid_do_sketch():
    p = S.ParametrosPID()
    assert const(CTRL, "KP") == p.kp
    assert const(CTRL, "KI") == p.ki
    assert const(CTRL, "KD") == p.kd
    assert const(CTRL, "TF") == p.tf
    assert const(CTRL, "TS") == const(PLANTA, "TS") == ConfigHIL().ts
    assert const(CTRL, "UMAX") == ConfigHIL().u_max


def test_buffer_comporta_atraso_critico():
    """O atraso máximo do sketch (DMAX·TS) precisa exceder o atraso crítico previsto."""
    tau_crit = margens(S.sistema_d(0.0)).margem_atraso
    assert const(PLANTA, "DMAX") * const(PLANTA, "TS") > 1.2 * tau_crit


def test_gemeo_converge_sem_atraso_e_no_nominal():
    for d in (0, 25):
        _, _, y, _, _ = simula_hil(S.planta_processo(), S.ParametrosPID(), d, ConfigHIL(t_final=40))
        assert abs(y[-1] - 1.0) < 1e-3


def test_atraso_critico_gemeo_proximo_do_nyquist():
    tau_crit = margens(S.sistema_d(0.0)).margem_atraso
    cfg = ConfigHIL(ts=0.02, t_final=200)
    d = atraso_critico_hil(S.planta_processo(), S.ParametrosPID(), cfg, 80)
    assert abs(d * cfg.ts - tau_crit) <= 2 * cfg.ts
