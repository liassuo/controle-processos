# Análise Computacional e Comparativa de Critérios de Estabilidade em Sistemas Dinâmicos

Projeto de pesquisa aplicada da disciplina de Controle de Processos, na trilha de Engenharia da Computação. O enunciado está em [`docs/enunciado/`](docs/enunciado/).

A ferramenta, escrita em Python, analisa a estabilidade de sistemas lineares invariantes no tempo pelo **critério de Nyquist** e compara os resultados, as limitações e o custo computacional com os métodos de **Routh-Hurwitz**, **Lugar das Raízes** e **Diagrama de Bode**. Os algoritmos foram implementados do zero, usando o NumPy apenas para vetores, aritmética complexa e autovalores. As bibliotecas `python-control` e `scipy` entram **somente** na validação cruzada.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `src/estabilidade/` | Núcleo: Nyquist (contorno, envoltórios, Z = N + P), margens, Routh-Hurwitz, raízes, Lugar das Raízes, Bode, Padé, simulação e gêmeo digital do HIL |
| `tests/` | Testes unitários, validação cruzada (python-control e SciPy) e coerência dos sketches |
| `experimentos/` | Scripts que geram **todas** as figuras e tabelas do artigo |
| `results/` | Saídas: `figuras/` (PDF e PNG), `tabelas/` (LaTeX e CSV), `*.json` (dados brutos e ambiente) e `tinkercad/` (ensaios do grupo) |
| `hil/` | Sketches dos dois Arduinos e guia de montagem no Tinkercad |
| `report/` | Artigo no formato SBC (LaTeX) e referências (`referencias.bib`) |
| `docs/` | Enunciado, modelo de referência e levantamento bibliográfico |

## Reprodução

```bash
python -m pip install -r requirements.txt
python -m pytest                      # suíte de testes
python experimentos/executar_tudo.py  # regenera results/ (cerca de 1 min)
```

Para rodar um único teste: `python -m pytest tests/test_nyquist.py::test_sistema_b_envolve_anti_horario`.

## Uso rápido

```python
from estabilidade import FT, nyquist, margens, tabela_routh

L = FT([20], [1, 6, 11, 6])           # 20 / ((s+1)(s+2)(s+3))
r = nyquist(L)                         # r.P, r.N_horario, r.Z
m = margens(L)                         # m.mg_db, m.mf, m.margem_atraso
t = tabela_routh(L.polinomio_caracteristico())

Ld = FT([1], [1, 1], atraso=0.8)       # atraso tratado de forma exata
nyquist(Ld).Z
```

## Sistemas de benchmark

Os sistemas estão definidos em `src/estabilidade/sistemas.py`.

| Sistema | L(s) | Característica |
|---|---|---|
| A | 20 / ((s+1)(s+2)(s+3)) | estável em malha aberta, 3ª ordem |
| B | 400(s+10)/(s+100) · 19,62/(s² − 400) | levitador magnético linearizado (P = 1) com compensador de avanço |
| C | 7(1 − s) / ((s+1)(s+2)(s+3)) | fase não mínima (zero em s = +1) |
| D | PID · 1/((s+1)(0,5s+1)) · e^(−0,5s) | atraso de rede; é o mesmo laço da simulação HIL |

## Simulação HIL (Tinkercad)

Veja [`hil/README.md`](hil/README.md). Os resultados no Tinkercad são registrados pelo grupo em `results/tinkercad/`.
