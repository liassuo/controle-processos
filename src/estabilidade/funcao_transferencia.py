"""Função de transferência racional com atraso de transporte opcional:

    L(s) = N(s)/D(s) * exp(-tau * s)

A avaliação em s é exata (o termo exponencial é calculado diretamente), o que
permite ao critério de Nyquist e ao diagrama de Bode tratar o atraso sem
aproximação. Métodos no plano s (Routh, Lugar das Raízes) exigem uma forma
racional: ver ``com_pade``.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .polinomios import como_poli, horner, multiplica, soma
from .raizes import raizes_companheira


@dataclass
class FT:
    num: np.ndarray
    den: np.ndarray
    atraso: float = 0.0
    nome: str = field(default="", compare=False)

    def __post_init__(self):
        self.num = como_poli(self.num)
        self.den = como_poli(self.den)
        if self.den.size == 1 and self.den[0] == 0:
            raise ValueError("denominador nulo")
        if self.atraso < 0:
            raise ValueError("atraso deve ser não negativo")

    # --- propriedades -----------------------------------------------------
    @property
    def ordem(self) -> int:
        return self.den.size - 1

    @property
    def estritamente_propria(self) -> bool:
        return self.num.size < self.den.size

    @property
    def propria(self) -> bool:
        return self.num.size <= self.den.size

    def polos(self) -> np.ndarray:
        return raizes_companheira(self.den)

    def zeros(self) -> np.ndarray:
        return raizes_companheira(self.num) if self.num.size > 1 else np.array([], dtype=complex)

    # --- avaliação --------------------------------------------------------
    def __call__(self, s):
        s = np.asarray(s, dtype=complex)
        val = horner(self.num, s) / horner(self.den, s)
        if self.atraso:
            val = val * np.exp(-self.atraso * s)
        return val

    def racional(self, s):
        """Parte racional N/D (sem o atraso)."""
        s = np.asarray(s, dtype=complex)
        return horner(self.num, s) / horner(self.den, s)

    def resposta_frequencia(self, w):
        return self(1j * np.asarray(w, dtype=float))

    # --- álgebra ------------------------------------------------------------
    def __mul__(self, outra):
        if isinstance(outra, (int, float, np.floating)):
            return FT(self.num * outra, self.den, self.atraso, self.nome)
        return FT(multiplica(self.num, outra.num), multiplica(self.den, outra.den),
                  self.atraso + outra.atraso)

    __rmul__ = __mul__

    def sem_atraso(self) -> "FT":
        return FT(self.num, self.den, 0.0, self.nome)

    def polinomio_caracteristico(self, k: float = 1.0) -> np.ndarray:
        """D(s) + k N(s): equação característica de 1 + k L(s) = 0 (realimentação
        negativa unitária). Só é definida para L racional."""
        if self.atraso:
            raise ValueError("L(s) com atraso não é racional; use com_pade(N) antes")
        return soma(self.den, k * self.num)

    def com_pade(self, ordem: int) -> "FT":
        from .pade import pade
        if not self.atraso:
            return self.sem_atraso()
        pn, pd = pade(self.atraso, ordem)
        return FT(multiplica(self.num, pn), multiplica(self.den, pd), 0.0,
                  f"{self.nome} (Padé {ordem})")

    def __repr__(self):
        atr = f" * exp(-{self.atraso:g} s)" if self.atraso else ""
        return f"FT(num={self.num.tolist()}, den={self.den.tolist()}{atr})"
