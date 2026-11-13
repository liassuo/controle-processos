"""Critério de estabilidade de Nyquist [Nyquist, 1932], implementado do zero.

Procedimento (Princípio do Argumento de Cauchy):

1. Contorno de Nyquist Γ no plano s, percorrido no sentido horário: sobe o eixo
   imaginário de -jR a +jR, contornando por semicírculos de raio r à direita os
   polos de L(s) sobre o eixo jω (inclusive a origem), e fecha pelo semicírculo de
   raio R no semiplano direito.
2. Mapeamento L(Γ), com avaliação exata de exp(-τ s).
3. Número de envoltórios de -1 + j0: o número de voltas (``winding number``) de
   L(Γ) + 1 em torno da origem, calculado por dois métodos independentes:
   soma de ângulos e cruzamentos com sinal de uma semirreta [Hormann e Agathos, 2001].
4. Z = N + P, em que N é o número de envoltórios no sentido horário, P o número de
   polos de L(s) no SPD e Z o número de polos de malha fechada no SPD.

Amostragem: a frequência é refinada adaptativamente sempre que a variação do
ângulo de L+1 entre amostras vizinhas excede um limiar, garantindo a contagem
correta mesmo quando o atraso faz o diagrama espiralar. Onde |L| < 1/2, L + 1
fica no semiplano Re > 0 e não contribui com voltas, o que justifica truncar o
refinamento nas altas frequências (ver ``_raio_externo``).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .funcao_transferencia import FT


@dataclass
class ResultadoNyquist:
    s: np.ndarray                 # pontos do contorno no plano s
    L: np.ndarray                 # L(s) nos pontos do contorno
    w_positivo: np.ndarray        # frequências do ramo ω > 0 (para gráficos)
    L_positivo: np.ndarray
    P: int
    polos_eixo: np.ndarray
    N_horario: int                # envoltórios horários de -1 (soma de ângulos)
    N_cruzamentos: int            # mesmo valor por cruzamentos com sinal
    Z: int
    voltas_float: float           # valor real antes do arredondamento (diagnóstico)
    n_pontos: int

    @property
    def estavel_malha_fechada(self) -> bool:
        return self.Z == 0


def _classifica_polos(L: FT, tol_eixo: float):
    polos = L.polos()
    escala = max(1.0, np.max(np.abs(polos))) if polos.size else 1.0
    tol = tol_eixo * escala
    no_eixo = polos[np.abs(polos.real) <= tol]
    P = int(np.sum(polos.real > tol))
    # frequências (ω >= 0) dos polos no eixo, sem repetição
    w_eixo = np.unique(np.round(np.abs(no_eixo.imag), 10))
    return P, w_eixo, polos


def _raio_externo(L: FT, w_eixo) -> float:
    """Raio R a partir do qual |parte racional de L| < 1/2 em todo o semicírculo e
    no eixo imaginário além de R (cota de módulo sobre raízes). Com atraso,
    |exp(-τ s)| <= 1 no SPD, logo a mesma cota vale para L."""
    if not L.estritamente_propria:
        return np.nan
    z = L.zeros()
    p = L.polos()
    m, n = z.size, p.size
    lead = abs(L.num[0] / L.den[0])
    rz = np.abs(z).max() if m else 0.0
    rp = np.abs(p).max() if n else 0.0
    R = max(2.0 * rp, 2.0 * rz, 1.0, 2.0 * (np.max(w_eixo) if len(w_eixo) else 0.0))
    for _ in range(200):
        cota = lead * np.prod(R + np.abs(z)) / np.prod(R - np.abs(p)) if n else np.inf
        if cota < 0.5:
            return R
        R *= 2.0
    raise RuntimeError("não foi possível determinar R")


def _ramo_eixo(L: FT, w_ini, w_fim, n_ini, lim_ang, max_pontos, tau_passo):
    """Amostras adaptativas de s = jω em [w_ini, w_fim] (log quando possível)."""
    if w_ini > 0:
        w = np.geomspace(w_ini, w_fim, n_ini)
    else:
        w = np.concatenate([[0.0], np.geomspace(max(w_fim * 1e-6, 1e-9), w_fim, n_ini - 1)])
    if tau_passo:
        # garante Δω·τ <= 0.2 rad onde |L| ainda pode envolver -1
        dw_max = 0.2 / tau_passo
        extras = []
        for a, b in zip(w[:-1], w[1:]):
            if b - a > dw_max and np.abs(L(1j * a)) >= 0.5:
                extras.append(np.arange(a, b, dw_max)[1:])
        if extras:
            w = np.unique(np.concatenate([w] + extras))
    for _ in range(40):
        z = L(1j * w) + 1.0
        dang = np.abs(np.angle(z[1:] / z[:-1]))
        relevante = np.minimum(np.abs(z[1:] - 1.0), np.abs(z[:-1] - 1.0)) >= 0.5  # |L| >= 1/2
        ruim = np.flatnonzero((dang > lim_ang) & relevante)
        if ruim.size == 0 or w.size > max_pontos:
            break
        novos = 0.5 * (w[ruim] + w[ruim + 1])
        w = np.unique(np.concatenate([w, novos]))
    return w


def contorno_nyquist(L: FT, r_indent: float = 1e-4, n_ini: int = 2000,
                     lim_ang: float = np.pi / 12, max_pontos: int = 2_000_000,
                     tol_eixo: float = 1e-9, w_min: float | None = None):
    """Constrói o contorno de Nyquist e retorna (s, w_pos, P, w_eixo)."""
    if not L.propria:
        raise ValueError("L(s) imprópria: critério não aplicável diretamente")
    if L.atraso and not L.estritamente_propria:
        raise ValueError("L(s) com atraso precisa ser estritamente própria")
    P, w_eixo, polos = _classifica_polos(L, tol_eixo)
    R = _raio_externo(L, w_eixo)
    if np.isnan(R):  # bipróprio sem atraso: L(∞) constante, semicírculo trivial
        R = 1e3 * max(1.0, np.abs(polos).max() if polos.size else 1.0, np.abs(L.zeros()).max() if L.num.size > 1 else 1.0)

    # ramo ω >= 0, com pontos de quebra nos polos sobre o eixo
    quebras = [w for w in w_eixo if w > 0]
    inicio_em_zero = 0.0 in w_eixo
    pedacos_s = []
    w_pos_lista = []
    w_inf = r_indent if inicio_em_zero else 0.0
    if w_min is not None:
        w_inf = max(w_inf, w_min) if inicio_em_zero else w_inf
    limites = [w_inf]
    for wq in quebras:
        limites += [wq - r_indent, wq + r_indent]
    limites.append(R)
    for k in range(0, len(limites), 2):
        a, b = limites[k], limites[k + 1]
        w = _ramo_eixo(L, a, b, n_ini, lim_ang, max_pontos, L.atraso)
        w_pos_lista.append(w)
        pedacos_s.append(1j * w)
        if k + 2 < len(limites):
            # semicírculo à direita em torno de j*wq, de θ=-π/2 a +π/2
            wq = quebras[k // 2]
            th = np.linspace(-np.pi / 2, np.pi / 2, 721)[1:-1]
            pedacos_s.append(1j * wq + r_indent * np.exp(1j * th))
    s_pos = np.concatenate(pedacos_s)
    w_pos = np.concatenate(w_pos_lista)

    # semicírculo grande, de +jR a -jR passando por +R (horário)
    th = np.linspace(np.pi / 2, -np.pi / 2, 2001)[1:-1]
    arco = R * np.exp(1j * th)

    # ramo ω <= 0 por simetria conjugada do contorno
    s_neg = np.conj(s_pos[::-1])
    if inicio_em_zero:
        # semicírculo em torno da origem: de -j r a +j r passando por +r
        th0 = np.linspace(-np.pi / 2, np.pi / 2, 721)[1:-1]
        origem = r_indent * np.exp(1j * th0)
        s = np.concatenate([origem, s_pos, arco, s_neg])
    else:
        s = np.concatenate([s_pos, arco, s_neg])
        if s[0] == 0 and s[-1] == 0:
            s = s[:-1]
    return s, w_pos, P, w_eixo


def voltas_soma_angulos(z: np.ndarray, ponto: complex = -1.0) -> float:
    """Número de voltas anti-horárias da poligonal fechada z em torno de ``ponto``."""
    d = z - ponto
    d = np.append(d, d[0])
    return float(np.sum(np.angle(d[1:] / d[:-1])) / (2 * np.pi))


def voltas_cruzamentos(z: np.ndarray, ponto: complex = -1.0) -> int:
    """Cruzamentos com sinal da semirreta horizontal à esquerda de ``ponto``
    (algoritmo de Sunday / Hormann e Agathos). Retorna voltas anti-horárias."""
    d = z - ponto
    d = np.append(d, d[0])
    x0, y0 = d[:-1].real, d[:-1].imag
    x1, y1 = d[1:].real, d[1:].imag
    desce = (y0 > 0) & (y1 <= 0)
    sobe = (y0 <= 0) & (y1 > 0)
    cruza = desce | sobe
    with np.errstate(divide="ignore", invalid="ignore"):
        xc = x0 + (0 - y0) * (x1 - x0) / (y1 - y0)
    esquerda = cruza & (xc < 0)
    return int(np.sum(desce & esquerda) - np.sum(sobe & esquerda))


def nyquist(L: FT, **kw) -> ResultadoNyquist:
    s, w_pos, P, w_eixo = contorno_nyquist(L, **kw)
    z = L(s)
    if np.any(np.abs(z + 1) < 1e-12):
        raise ValueError("L(Γ) passa sobre -1: sistema no limite de estabilidade")
    voltas = voltas_soma_angulos(z)
    n_ah = int(round(voltas))
    n_cr = voltas_cruzamentos(z)
    N = -n_ah                       # horário positivo
    Z = N + P
    return ResultadoNyquist(s=s, L=z, w_positivo=w_pos, L_positivo=L(1j * w_pos), P=P,
                            polos_eixo=w_eixo, N_horario=N, N_cruzamentos=-n_cr, Z=Z,
                            voltas_float=voltas, n_pontos=s.size)
