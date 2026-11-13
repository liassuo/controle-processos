"""Critério de Routh–Hurwitz [Routh, 1877; Hurwitz, 1895], implementado do zero.

Trata os dois casos especiais clássicos [Nise, 2017; Ogata, 2010]:

1. **Zero na primeira coluna** (linha não nula): o zero é substituído por um
   ε > 0 pequeno e o sinal é analisado no limite ε → 0+.
2. **Linha inteira nula**: indica raízes simétricas em relação à origem. A linha
   é substituída pelos coeficientes da derivada do polinômio auxiliar formado
   pela linha anterior. As raízes do polinômio auxiliar são raízes do polinômio
   original; as que estão sobre o eixo jω são contadas como
   ``grau(A) - 2 * (trocas de sinal da tabela a partir da linha auxiliar)``.

Raízes na origem (coeficiente independente nulo) são removidas antes da tabela
e contadas como raízes sobre o eixo imaginário.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .polinomios import como_poli


@dataclass
class ResultadoRouth:
    polinomio: np.ndarray
    tabela: list                      # linhas (np.ndarray), da potência s^n até s^0
    primeira_coluna: np.ndarray
    trocas_sinal: int
    n_spd: int                        # raízes com parte real > 0
    n_eixo: int                       # raízes sobre o eixo imaginário (inclui origem)
    n_spe: int                        # raízes com parte real < 0
    casos_especiais: list = field(default_factory=list)
    polinomios_auxiliares: list = field(default_factory=list)

    @property
    def estavel(self) -> bool:
        """Estabilidade assintótica: todas as raízes no semiplano esquerdo."""
        return self.n_spd == 0 and self.n_eixo == 0


def _trocas_sinal(v: np.ndarray) -> int:
    s = np.sign(v)
    s = s[s != 0]
    return int(np.sum(s[1:] != s[:-1]))


def escalona(p) -> tuple[np.ndarray, float]:
    """Escalonamento de frequência s -> α s, com α = |a_0/a_n|^(1/n), que equilibra
    a faixa dinâmica dos coeficientes. Como α > 0, a localização das raízes em
    relação ao eixo imaginário não muda."""
    p = np.asarray(p, float)
    n = p.size - 1
    if n < 1 or p[-1] == 0:
        return p / np.max(np.abs(p)), 1.0
    alfa = abs(p[-1] / p[0]) ** (1.0 / n)
    q = p * alfa ** np.arange(n, -1, -1)
    return q / np.max(np.abs(q)), alfa


def tabela_routh(p, eps_rel: float = 1e-8, tol_cancel: float | None = None,
                 escalonar: bool = True, criterio_zero: str = "cancelamento") -> ResultadoRouth:
    """Monta a tabela de Routh e conta as raízes por região.

    ``criterio_zero``:
      * ``"cancelamento"`` (padrão): um elemento é zero numérico quando
        |b_j| <= tol · (|b_0 a_{j+1}| + |a_0 b_{j+1}|)/|b_0|.
      * ``"absoluta"``: critério ingênuo da primeira versão do código,
        |b_j| <= 1e-12 · max|p|. Mantido apenas para o estudo de ablação (exp. 2),
        porque falha quando os coeficientes têm grande faixa dinâmica.
    """
    p = como_poli(p, float)
    if p[0] < 0:
        p = -p
    original = p.copy()

    # raízes na origem
    n_origem = 0
    while p.size > 1 and p[-1] == 0:
        p = p[:-1]
        n_origem += 1

    n = p.size - 1
    casos, auxiliares = [], []
    if n == 0:
        return ResultadoRouth(original, [p.copy()], p.copy(), 0, 0, n_origem, 0, casos, auxiliares)
    if escalonar:
        p, _ = escalona(p)
    if tol_cancel is None:
        tol_cancel = 64 * n * np.finfo(float).eps

    largura = n // 2 + 1
    linhas = [np.zeros(largura), np.zeros(largura)]
    refs = [np.zeros(largura), np.zeros(largura)]   # magnitude dos termos que geraram cada elemento
    linhas[0][: len(p[0::2])] = p[0::2]
    linhas[1][: len(p[1::2])] = p[1::2]
    refs[0][:] = np.abs(linhas[0])
    refs[1][:] = np.abs(linhas[1])
    linha_aux_idx = None   # índice da primeira linha substituída por derivada

    escala_abs = np.max(np.abs(p))

    def _zero(v, r):
        """Zero numérico: |v| desprezível diante dos termos que o produziram
        (cancelamento catastrófico), e não diante do maior valor da tabela."""
        if criterio_zero == "absoluta":
            return np.abs(v) <= 1e-12 * escala_abs
        return np.abs(v) <= tol_cancel * r

    # a linha s^(n-1) também pode ser inteiramente nula (ex.: s^4 + 2s^2 + 1)
    for i in range(1, n + 1):
        if i >= 2:
            a, b = linhas[i - 2], linhas[i - 1]
            nova = np.zeros(largura)
            ref = np.zeros(largura)
            for j in range(largura - 1):
                t1, t2 = b[0] * a[j + 1], a[0] * b[j + 1]
                nova[j] = (t1 - t2) / b[0]
                ref[j] = (abs(t1) + abs(t2)) / abs(b[0])
            nova[_zero(nova, ref)] = 0.0
            linhas.append(nova)
            refs.append(ref)
        atual = linhas[i]
        if np.all(atual == 0):
            # caso especial 2: polinômio auxiliar com a linha anterior (potência n-i+1)
            ordem_aux = n - i + 1
            ant = linhas[i - 1]
            aux = np.zeros(ordem_aux + 1)
            aux[0::2] = ant[: ordem_aux // 2 + 1]
            auxiliares.append(aux)
            deriv = aux[:-1] * np.arange(ordem_aux, 0, -1)
            nova = np.zeros(largura)
            coef = deriv[0::2]
            nova[: len(coef)] = coef
            linhas[i] = nova
            refs[i] = np.abs(nova)
            casos.append(f"linha s^{n - i} nula: polinômio auxiliar de grau {ordem_aux}")
            if linha_aux_idx is None:
                linha_aux_idx = i
            atual = nova
        if atual[0] == 0 and i < n:
            # caso especial 1: zero na primeira coluna (linha não nula)
            if criterio_zero == "absoluta":
                atual[0] = 1e-9 * escala_abs
            else:
                atual[0] = eps_rel * max(np.max(np.abs(atual)), np.max(np.abs(linhas[i - 1])))
            casos.append(f"zero na 1ª coluna na linha s^{n - i}: substituído por ε")

    col = np.array([l[0] for l in linhas])
    trocas = _trocas_sinal(col)

    n_eixo_aux = 0
    if auxiliares:
        # raízes do primeiro auxiliar (maior grau) contêm todas as simétricas
        grau_aux = auxiliares[0].size - 1
        trocas_abaixo = _trocas_sinal(col[linha_aux_idx - 1:])
        n_eixo_aux = grau_aux - 2 * trocas_abaixo
    n_spd = trocas
    n_eixo = n_eixo_aux + n_origem
    n_spe = (original.size - 1) - n_spd - n_eixo
    return ResultadoRouth(original, linhas, col, trocas, n_spd, n_eixo, n_spe, casos, auxiliares)


def matriz_hurwitz(p) -> np.ndarray:
    """Matriz de Hurwitz H (n x n) do polinômio a_n s^n + ... + a_0."""
    p = como_poli(p, float)
    if p[0] < 0:
        p = -p
    n = p.size - 1
    h = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            k = 2 * (j + 1) - (i + 1)   # índice do coeficiente a_{n-k}
            if 0 <= k <= n:
                h[i, j] = p[k]
    return h


def determinantes_hurwitz(p) -> np.ndarray:
    h = matriz_hurwitz(p)
    return np.array([np.linalg.det(h[:k, :k]) for k in range(1, h.shape[0] + 1)])


def faixas_ganho_estavel(num, den, k_min=1e-6, k_max=1e6, pontos=4000, tol=1e-10):
    """Intervalos de K > 0 em que 1 + K N/D = 0 é estável, via Routh.

    Varre K em escala logarítmica e refina as fronteiras por bissecção.
    """
    from .polinomios import soma

    def estavel(k):
        return tabela_routh(soma(den, k * np.asarray(num, float))).estavel

    ks = np.logspace(np.log10(k_min), np.log10(k_max), pontos)
    est = np.array([estavel(k) for k in ks])
    fronteiras = []
    for i in range(len(ks) - 1):
        if est[i] != est[i + 1]:
            a, b = ks[i], ks[i + 1]
            while (b - a) > tol * b:
                m = 0.5 * (a + b)
                if estavel(m) == est[i]:
                    a = m
                else:
                    b = m
            fronteiras.append(0.5 * (a + b))
    intervalos = []
    inicio = k_min if est[0] else None
    for f in fronteiras:
        if inicio is None:
            inicio = f
        else:
            intervalos.append((inicio, f))
            inicio = None
    if inicio is not None:
        intervalos.append((inicio, np.inf))
    return intervalos
