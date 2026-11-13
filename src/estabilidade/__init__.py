"""Análise computacional de estabilidade: Nyquist, Routh–Hurwitz, Lugar das Raízes e Bode.

Implementação própria, que usa apenas NumPy para vetores, aritmética complexa e
autovalores. As bibliotecas ``control`` e ``scipy.signal`` são usadas somente nos
testes e scripts de validação cruzada.
"""
from .funcao_transferencia import FT
from .nyquist import nyquist, ResultadoNyquist
from .margens import margens, Margens
from .routh import tabela_routh, faixas_ganho_estavel, determinantes_hurwitz
from .lugar_raizes import lugar_raizes
from .bode import bode, bode_assintotico
from .pade import pade
from .raizes import raizes_companheira, raizes_aberth

__all__ = ["FT", "nyquist", "ResultadoNyquist", "margens", "Margens", "tabela_routh",
           "faixas_ganho_estavel", "determinantes_hurwitz", "lugar_raizes", "bode",
           "bode_assintotico", "pade", "raizes_companheira", "raizes_aberth"]
