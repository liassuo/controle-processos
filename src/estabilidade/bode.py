"""Diagrama de Bode [Bode, 1945]: curva exata e aproximação assintótica.

A curva exata usa L(jω) diretamente (inclusive exp(-jωτ), cuja contribuição é
apenas de fase, -ωτ). A aproximação assintótica usa as retas clássicas
(±20 dB/década por raiz real, ±40 dB/década por par complexo, a partir da
frequência de quebra |raiz|) e serve para medir o erro do traçado manual.
"""
from __future__ import annotations

import numpy as np

from .funcao_transferencia import FT
from .margens import fase_desdobrada


def bode(L: FT, w):
    w = np.asarray(w, dtype=float)
    mag_db = 20 * np.log10(np.abs(L.racional(1j * w)))
    fase_deg = np.degrees(fase_desdobrada(L, w))
    return mag_db, fase_deg


def _fatores(raizes, tol=1e-9):
    """Agrupa raízes em fatores: ('real', ω_q, sinal) e ('par', ω_n, sinal)."""
    usadas = np.zeros(len(raizes), bool)
    fat = []
    for i, r in enumerate(raizes):
        if usadas[i]:
            continue
        usadas[i] = True
        if abs(r.imag) <= tol * max(1, abs(r)):
            fat.append(("real", abs(r.real), np.sign(r.real) if r.real != 0 else 0.0))
        else:
            for j in range(i + 1, len(raizes)):
                if not usadas[j] and abs(raizes[j] - np.conj(r)) <= 1e-6 * max(1, abs(r)):
                    usadas[j] = True
                    break
            fat.append(("par", abs(r), np.sign(r.real)))
    return fat


def bode_assintotico(L: FT, w):
    """Magnitude assintótica (dB) e fase aproximada (graus, regra da década)."""
    w = np.asarray(w, dtype=float)
    z, p = L.zeros(), L.polos()
    # ganho de "baixa frequência" na forma de Bode: K * s^{tipo}
    nz0 = int(np.sum(np.abs(z) < 1e-12))
    np0 = int(np.sum(np.abs(p) < 1e-12))
    z_nz = z[np.abs(z) >= 1e-12]
    p_nz = p[np.abs(p) >= 1e-12]
    k_bode = abs(L.num[0] / L.den[0]) * np.prod(np.abs(z_nz)) / np.prod(np.abs(p_nz))
    tipo = nz0 - np0
    mag = 20 * np.log10(k_bode) + 20 * tipo * np.log10(w)
    # sinal de K na forma de Bode (fase 0 ou 180 em baixa frequência)
    sinal_k = np.sign(np.real(L.num[0] / L.den[0] * np.prod(-z_nz) / np.prod(-p_nz)))
    fase = np.full_like(w, 0.0 if sinal_k >= 0 else -180.0) + 90.0 * tipo

    def contrib(fatores, s_exp):
        nonlocal mag, fase
        for tipo_f, wq, sinal in fatores:
            ordem = 1 if tipo_f == "real" else 2
            mag = mag + s_exp * 20 * ordem * np.maximum(0.0, np.log10(w / wq))
            # fase: 0 abaixo de wq/10, ±90·ordem acima de 10·wq, reta no meio
            frac = np.clip((np.log10(w / wq) + 1) / 2, 0, 1)
            # zero no SPE soma fase; zero no SPD subtrai; polos SPE subtraem; polos SPD somam
            sentido = s_exp * (-1 if sinal > 0 else 1)
            fase = fase + sentido * 90.0 * ordem * frac

    contrib(_fatores(z_nz), +1)
    contrib(_fatores(p_nz), -1)
    fase = fase - np.degrees(w * L.atraso)
    return mag, fase
