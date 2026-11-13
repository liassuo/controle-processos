"""Gêmeo digital da simulação Hardware-in-the-Loop (trilha EC, Fase 4).

Reproduz, passo a passo e em ponto flutuante de 32 bits (como no Arduino Uno),
o algoritmo dos dois microcontroladores do circuito no Tinkercad:

* **Arduino "Planta + Rede"** (relógio mestre, período Ts): integra a planta
  G_p(s) discretizada por segurador de ordem zero (ZOH) e mantém uma fila FIFO
  de ``d`` amostras com os comandos recebidos, o que emula o atraso de rede τ = d·Ts.
* **Arduino "Controlador"**: recebe y[k], calcula u[k] com PID discreto e devolve u[k].

Sequência em cada período k (idêntica à dos sketches em ``hil/``):
    1. planta envia y[k]
    2. controlador calcula u[k] = PID(r - y[k]) e envia
    3. planta insere u[k] na fila e aplica u[k-d] durante [k, k+1)
    4. planta atualiza o estado: x[k+1] = Ad x[k] + Bd u[k-d]

O PID discreto usa integração retangular para trás e derivada filtrada
discretizada por Euler para trás, com antiwindup por saturação condicional.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .funcao_transferencia import FT
from .simulacao import espaco_estados
from .sistemas import ParametrosPID


def expm(M: np.ndarray) -> np.ndarray:
    """Exponencial de matriz por escalonamento e quadratura com série de Taylor."""
    norma = np.linalg.norm(M, 1)
    s = max(0, int(np.ceil(np.log2(norma))) + 1) if norma > 0 else 0
    X = M / 2 ** s
    E = np.eye(M.shape[0])
    termo = np.eye(M.shape[0])
    for k in range(1, 30):
        termo = termo @ X / k
        E = E + termo
    for _ in range(s):
        E = E @ E
    return E


def discretiza_zoh(G: FT, ts: float):
    """(Ad, Bd, C, D) do equivalente ZOH de G(s) racional."""
    A, B, C, D = espaco_estados(G)
    n = A.shape[0]
    M = np.zeros((n + 1, n + 1))
    M[:n, :n] = A
    M[:n, n] = B
    E = expm(M * ts)
    return E[:n, :n], E[:n, n], C, D


@dataclass
class ConfigHIL:
    ts: float = 0.02          # período de amostragem (s)
    u_max: float = 10.0       # saturação do atuador
    r: float = 1.0            # referência (degrau)
    t_final: float = 60.0
    float32: bool = True


def simula_hil(G: FT, pid: ParametrosPID, d, cfg: ConfigHIL = ConfigHIL()):
    """Simula o laço HIL. ``d`` é o atraso em amostras: um inteiro fixo ou uma
    função k -> d[k] (atraso variável). Retorna (t, r, y, u, d_efetivo).

    Atraso variável: em cada período a planta aplica o comando mais recente já
    "entregue" pela rede, índice j[k] = max(j[k-1], k - d[k]). Assim os pacotes
    nunca são reordenados, como em um enlace serial.
    """
    tipo = np.float32 if cfg.float32 else np.float64
    Ad, Bd, C, D = (np.asarray(v, dtype=tipo) for v in discretiza_zoh(G, cfg.ts))
    ts = tipo(cfg.ts)
    kp, ki, kd, tf = (tipo(v) for v in (pid.kp, pid.ki, pid.kd, pid.tf))
    a_d = tipo(tf / (tf + cfg.ts))            # filtro derivativo (Euler para trás)
    b_d = tipo(kd / (tf + cfg.ts))
    n = int(round(cfg.t_final / cfg.ts))
    x = np.zeros(Ad.shape[0], dtype=tipo)
    atraso_k = d if callable(d) else (lambda k, d=int(d): d)
    hist_u = np.zeros(n, dtype=tipo)             # comandos enviados pelo controlador
    j_ant = -1                                   # índice do último comando aplicado
    d_ef = np.zeros(n, dtype=int)
    integ = tipo(0.0)
    deriv = tipo(0.0)
    e_ant = tipo(0.0)
    t = np.arange(n) * cfg.ts
    ys = np.zeros(n)
    us = np.zeros(n)
    umax = tipo(cfg.u_max)
    for k in range(n):
        y = tipo(C @ x)                          # 1. planta envia y[k]
        e = tipo(cfg.r) - y                      # 2. controlador
        deriv = a_d * deriv + b_d * (e - e_ant)
        integ_nova = integ + ki * ts * e
        u = kp * e + integ_nova + deriv
        if -umax < u < umax:                     # antiwindup condicional
            integ = integ_nova
        else:
            u = kp * e + integ + deriv
        u = tipo(min(max(u, -umax), umax))
        e_ant = e
        hist_u[k] = u                            # 3. rede: entrega com atraso d[k]
        j = max(j_ant, k - int(atraso_k(k)))
        u_aplicado = hist_u[j] if j >= 0 else tipo(0.0)
        j_ant = j
        d_ef[k] = k - j
        x = (Ad @ x + Bd * u_aplicado).astype(tipo)  # 4. planta
        ys[k] = y
        us[k] = u
        if not np.isfinite(y):
            ys[k:] = np.nan
            break
    return t, np.full(n, cfg.r), ys, us, d_ef


def taxa_crescimento(t, y, r: float = 1.0) -> float:
    """Taxa exponencial (1/s) da envoltória do erro na segunda metade do horizonte,
    obtida por mínimos quadrados sobre log dos picos locais de |r - y|.
    Positiva = oscilação crescente (instável)."""
    if np.any(~np.isfinite(y)):
        return np.inf
    e = np.abs(r - np.asarray(y, float))
    meio = len(e) // 2
    seg, ts = e[meio:], t[meio:]
    picos = np.flatnonzero((seg[1:-1] > seg[:-2]) & (seg[1:-1] >= seg[2:])) + 1
    # piso de ruído: em float32 o erro estabiliza em ~1e-7 e oscila por arredondamento
    picos = picos[seg[picos] > 1e-4]
    if picos.size < 3:
        return -np.inf          # sem oscilação mensurável: convergiu
    a, _ = np.polyfit(ts[picos], np.log(seg[picos]), 1)
    return float(a)


def instavel_hil(t, y, r: float = 1.0) -> bool:
    return taxa_crescimento(t, y, r) > 0


def atraso_critico_hil(G: FT, pid: ParametrosPID, cfg: ConfigHIL = ConfigHIL(), d_max: int = 200):
    """Menor número de amostras d que torna o laço instável.

    Para isolar a estabilidade do laço linear, a busca é feita sem saturação do
    atuador (com saturação, a instabilidade vira um ciclo-limite de amplitude
    limitada, o que também é reportado nas figuras)."""
    from dataclasses import replace
    cfg_lin = replace(cfg, u_max=1e30)
    for d in range(d_max + 1):
        t, _, y, _, _ = simula_hil(G, pid, d, cfg_lin)
        if instavel_hil(t, y, cfg.r):
            return d
    return None
