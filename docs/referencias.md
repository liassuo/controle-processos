# Levantamento de referências

Levantamento feito em 11/11/2026. Os dados bibliográficos foram conferidos em fontes indexadas (IEEE Xplore, Numdam, AMS, PubMed/Nature, editoras). O arquivo BibTeX correspondente é `report/referencias.bib`.

Legenda: ✅ dados conferidos em fonte indexada · ⚠️ requer conferência manual antes da entrega · 📘 indicada pelo professor

## Livros-texto (base teórica)

| Chave | Referência | Uso no trabalho | Status |
|---|---|---|---|
| `ogata2010` | OGATA, K. *Engenharia de Controle Moderno*. 5. ed. São Paulo: Pearson, 2010. | Nyquist, Routh, Lugar das Raízes, Bode e margens | 📘 ⚠️ conferir capítulos e páginas no exemplar |
| `nise2017` | NISE, N. S. *Engenharia de Sistemas de Controle*. 7. ed. Rio de Janeiro: LTC, 2017. | Casos especiais de Routh (zero na 1ª coluna, linha nula) e regras do Lugar das Raízes | 📘 ⚠️ conferir capítulos e páginas |
| `astrom2008` | ÅSTRÖM, K. J.; MURRAY, R. M. *Feedback Systems*. Princeton University Press, 2008. | Princípio do argumento, contorno de Nyquist com desvio de polos em jω, atraso | 📘 ✅ (cap. 9, "Frequency Domain Analysis", na 1ª ed.) |
| `skogestad2005` | SKOGESTAD, S.; POSTLETHWAITE, I. *Multivariable Feedback Control*. 2. ed. Wiley, 2005. | Limitações impostas por zeros no SPD (Sistema C) e por atraso (Sistema D), seç. 5.7 | ✅ |

## Fontes primárias dos métodos

| Chave | Referência | Uso | Status |
|---|---|---|---|
| `nyquist1932` | NYQUIST, H. Regeneration Theory. *Bell System Technical Journal*, v. 11, n. 1, p. 126–147, 1932. DOI 10.1002/j.1538-7305.1932.tb02344.x | Origem do critério | ✅ |
| `routh1877` | ROUTH, E. J. *A Treatise on the Stability of a Given State of Motion*. London: Macmillan, 1877. | Origem do critério de Routh | ✅ |
| `hurwitz1895` | HURWITZ, A. Über die Bedingungen... *Mathematische Annalen*, v. 46, p. 273–284, 1895. | Origem do critério de Hurwitz | ⚠️ volume e páginas vêm de fonte secundária; conferir o DOI 10.1007/BF01446812 |
| `evans1948` | EVANS, W. R. Graphical Analysis of Control Systems. *Trans. AIEE*, v. 67, n. 1, p. 547–551, 1948. | Origem do Lugar das Raízes | ✅ (há divergência histórica sobre qual artigo de Evans introduz o nome "root locus"; citar como origem do método gráfico) |
| `bode1945` | BODE, H. W. *Network Analysis and Feedback Amplifier Design*. New York: Van Nostrand, 1945. | Origem do diagrama de Bode e das margens | ✅ |
| `pade1892` | PADÉ, H. Sur la représentation approchée d'une fonction par des fractions rationnelles. *Ann. Sci. ÉNS*, 3e série, t. 9, suppl. p. 3–93, 1892. | Origem da aproximação de Padé | ✅ |

## Atraso e sistemas controlados via rede

| Chave | Referência | Uso | Status |
|---|---|---|---|
| `zhang2001` | ZHANG, W.; BRANICKY, M. S.; PHILLIPS, S. M. Stability of Networked Control Systems. *IEEE Control Systems Magazine*, v. 21, n. 1, p. 84–99, 2001. | Motivação do Sistema D (atraso induzido pela rede) | ✅ |

## Algoritmos numéricos

| Chave | Referência | Uso | Status |
|---|---|---|---|
| `hormann2001` | HORMANN, K.; AGATHOS, A. The point in polygon problem for arbitrary polygons. *Computational Geometry*, v. 20, n. 3, p. 131–144, 2001. | *Winding number* em torno de (−1, 0), com complexidade O(n) | ✅ |
| `edelman1995` | EDELMAN, A.; MURAKAMI, H. Polynomial roots from companion matrix eigenvalues. *Math. Comp.*, v. 64, n. 210, p. 763–776, 1995. | Cálculo de polos pela matriz companheira e sua estabilidade numérica | ✅ |
| `wilkinson1984` | WILKINSON, J. H. The perfidious polynomial. In: GOLUB, G. H. (ed.). *Studies in Numerical Analysis*. MAA, 1984. p. 1–28. | Mau condicionamento das raízes em ordens altas (n = 20) | ✅ |

## Ferramentas de software (validação cruzada)

| Chave | Referência | Status |
|---|---|---|
| `harris2020` | HARRIS, C. R. et al. Array programming with NumPy. *Nature*, v. 585, p. 357–362, 2020. | ✅ |
| `virtanen2020` | VIRTANEN, P. et al. SciPy 1.0... *Nature Methods*, v. 17, p. 261–272, 2020. | ✅ |
| `fuller2021` | FULLER, S. et al. The Python Control Systems Library (python-control). In: *60th IEEE CDC*, 2021. p. 4875–4881. | ✅ |

## Observações que entram no texto

- **Padé:** a aproximação vale em baixas frequências e se degrada quando τ/T cresce. A documentação do MATLAB desaconselha ordens N > 10, porque os polos ficam agrupados e sensíveis a perturbações. Essas afirmações serão **medidas** no Sistema D, e não apenas citadas.
- **Raízes de polinômios:** `numpy.roots` usa os autovalores da matriz companheira (Edelman e Murakami, 1995). O polinômio de Wilkinson motiva a análise de erro para n = 20.
- **Modelo do levitador magnético (Sistema B):** a forma linearizada usual é G(s) = −k_i/(s² − k_x), com polos em ±√k_x. Os parâmetros numéricos virão de fonte a ser citada no artigo.
- **Template do artigo:** formato SBC, com o modelo `sbc-template.sty` (Overleaf "SBC Conferences") ou o novo modelo SBC OpenLib (2025).
