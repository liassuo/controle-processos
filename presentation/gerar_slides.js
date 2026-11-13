// Gera presentation/Apresentacao_Nyquist.pptx a partir dos resultados em results/.
// Uso: node presentation/gerar_slides.js   (requer pptxgenjs)
// Todos os números vêm dos JSON gerados pelos experimentos (mesma fonte do artigo).
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");

const RAIZ = path.resolve(__dirname, "..");
const FIG = path.join(RAIZ, "results", "figuras");
const TK = path.join(RAIZ, "results", "tinkercad");
// os JSON do Python podem conter Infinity/NaN, que não são JSON padrão
const J = (n) => JSON.parse(fs.readFileSync(path.join(RAIZ, "results", n), "utf8")
  .replace(/-Infinity/g, "-1e999").replace(/\bInfinity\b/g, "1e999").replace(/\bNaN\b/g, "null"));
const e1 = J("exp1_sistemas.json"), e2 = J("exp2_atraso_pade.json"), e3 = J("exp3_escalabilidade.json");
const e4 = J("exp4_hil.json"), e5 = J("exp5_tinkercad.json");

const br = (x, c = 2) => x.toFixed(c).replace(".", ",");
const pct = (x, c = 1) => br(100 * x, c) + "%";
// notação científica com expoente sobrescrito (ex.: 6×10⁻¹⁴)
const SUP = { "-": "⁻", "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹" };
const cient = (x, c = 0) => { const [m, e] = x.toExponential(c).split("e"); return m.replace(".", ",") + "×10" + String(+e).split("").map((ch) => SUP[ch]).join(""); };
const ERRO_ROUTH = pct(1 - Math.min(...e2.robustez_routh.map((d) => d.concordancia_absoluta)));
const ERRO_PADE1 = pct(Math.abs(e2.pade[0].erro_rel));

// ---------- tema ----------
const COR = { navy: "14213D", azul: "2B4C7E", gelo: "E8EEF6", laranja: "E4572E", cinza: "5B6575", branco: "FFFFFF", texto: "1F2933" };
const FONTE = "Calibri";
const W = 13.333, H = 7.5;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Davi Valério de Oliveira, Luiz Iassuoo Yabagata Neto, Samuel André Lopes Furtado";
pres.title = "Análise Computacional e Comparativa de Critérios de Estabilidade";
pres.theme = { headFontFace: FONTE, bodyFontFace: FONTE };

const RODAPE = "PUC Goiás · Engenharia da Computação · Controle de Processos";
pres.defineSlideMaster({
  title: "CONTEUDO",
  background: { color: COR.branco },
  objects: [
    { text: { text: RODAPE, options: { x: 0.6, y: 7.0, w: 8, h: 0.3, fontSize: 10, color: COR.cinza, fontFace: FONTE } } },
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.9, fontSize: 34, bold: true, color: COR.navy, fontFace: FONTE, valign: "middle", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: 12.2, y: 6.95, w: 0.6, h: 0.35, fontSize: 11, color: COR.cinza, fontFace: FONTE, align: "right" },
});
pres.defineSlideMaster({
  title: "ESCURO",
  background: { color: COR.navy },
  objects: [],
  slideNumber: { x: 12.2, y: 6.95, w: 0.6, h: 0.35, fontSize: 11, color: "AFC3DD", fontFace: FONTE, align: "right" },
});

// ---------- utilitários ----------
function tamPng(arq) {
  const b = fs.readFileSync(arq);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}
let nFig = 0;
function figura(slide, arq, box, legenda, fonte = "elaborada pelos autores (2026)") {
  const t = tamPng(arq);
  const r = Math.min(box.w / t.w, (box.h - 0.45) / t.h);
  const w = t.w * r, h = t.h * r;
  const x = box.x + (box.w - w) / 2;
  slide.addImage({ path: arq, x, y: box.y, w, h, altText: legenda });
  nFig += 1;
  slide.addText([
    { text: `Figura ${nFig} – ${legenda}`, options: { breakLine: true } },
    { text: `Fonte: ${fonte}.` },
  ], { x: box.x, y: box.y + h + 0.05, w: box.w, h: 0.42, fontSize: 10, color: COR.cinza, align: "center", isTextBox: true, margin: 0 });
}
function bullets(slide, itens, box, size = 20) {
  slide.addText(itens.map((t, i) => ({ text: t, options: { bullet: { indent: 18 }, breakLine: i < itens.length - 1 } })),
    { ...box, fontSize: size, color: COR.texto, paraSpaceAfter: 10, valign: "top", isTextBox: true, margin: 0 });
}
function cartao(slide, x, y, w, h, titulo, corpo, opt = {}) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: opt.fundo || COR.gelo }, line: { color: opt.fundo || COR.gelo } });
  slide.addText(titulo, { x: x + 0.2, y: y + 0.15, w: w - 0.4, h: 0.5, fontSize: opt.tt || 20, bold: true, color: opt.corTitulo || COR.navy, isTextBox: true, margin: 0, valign: "top" });
  slide.addText(corpo, { x: x + 0.2, y: y + 0.7, w: w - 0.4, h: h - 0.85, fontSize: opt.tc || 16, color: opt.corTexto || COR.texto, isTextBox: true, margin: 0, valign: "top" });
}
function destaque(slide, x, y, w, valor, rotulo, cor = COR.laranja) {
  slide.addText(valor, { x, y, w, h: 1.0, fontSize: 54, bold: true, color: cor, isTextBox: true, margin: 0, align: "left" });
  slide.addText(rotulo, { x, y: y + 1.0, w, h: 0.8, fontSize: 16, color: COR.cinza, isTextBox: true, margin: 0, valign: "top" });
}
function conteudo(titulo, notas) {
  const s = pres.addSlide({ masterName: "CONTEUDO" });
  s.addText(titulo, { placeholder: "title" });
  if (notas) s.addNotes(notas);
  return s;
}

// ======================================================================
// 1. Capa
{
  const s = pres.addSlide({ masterName: "ESCURO" });
  s.addText("Seminário · Controle de Processos", { x: 0.8, y: 0.8, w: 11.5, h: 0.5, fontSize: 18, color: "AFC3DD", isTextBox: true, margin: 0 });
  s.addText("Análise Computacional e Comparativa de Critérios de Estabilidade em Sistemas Dinâmicos",
    { x: 0.8, y: 1.5, w: 11.5, h: 1.9, fontSize: 40, bold: true, color: COR.branco, isTextBox: true, margin: 0, valign: "top" });
  s.addText("Critério de Nyquist comparado a Routh-Hurwitz, Lugar das Raízes e Diagrama de Bode",
    { x: 0.8, y: 3.45, w: 11.5, h: 0.6, fontSize: 22, color: COR.laranja, isTextBox: true, margin: 0 });
  s.addText([
    { text: "Davi Valério de Oliveira · Luiz Iassuoo Yabagata Neto · Samuel André Lopes Furtado", options: { breakLine: true, bold: true } },
    { text: "Orientador: Prof. Dr. Nilson Cardoso Amaral", options: { breakLine: true } },
    { text: "Engenharia da Computação · Pontifícia Universidade Católica de Goiás · Goiânia, 2026" },
  ], { x: 0.8, y: 4.7, w: 11.5, h: 1.5, fontSize: 18, color: COR.branco, isTextBox: true, margin: 0, paraSpaceAfter: 6, valign: "top" });
  s.addNotes("Apresentação do grupo e do tema: análise de estabilidade com foco no critério de Nyquist, implementado do zero, e comparação com Routh-Hurwitz, Lugar das Raízes e Bode.");
}

// 2. Contexto e problema
{
  const s = conteudo("Quanto atraso um laço de controle tolera?",
    "Contextualização: em sistemas controlados via rede, o atraso de comunicação é intrínseco. A pergunta central do trabalho é prever, antes de construir, quanto atraso o laço suporta sem perder a estabilidade.");
  const ex = [
    ["Redes industriais", "Sensores, CLP e válvulas conversando por Profinet, EtherCAT ou Modbus"],
    ["Teleoperação", "Cirurgia robótica, drones e robôs de inspeção controlados a distância"],
    ["Redes elétricas", "Controle de frequência e tensão com medições de subestações remotas"],
    ["Veículos", "Freio, motor e direção trocando dados pelo barramento CAN"],
  ];
  ex.forEach(([t, c], i) => cartao(s, 0.6 + i * 3.08, 1.6, 2.85, 2.6, t, c, { tc: 18 }));
  s.addText([
    { text: "Problema: ", options: { bold: true, color: COR.laranja } },
    { text: "o atraso e^(−τs) não é um polinômio. Métodos algébricos precisam aproximá-lo; o critério de Nyquist o trata de forma exata." },
  ], { x: 0.6, y: 4.6, w: 12.1, h: 1.2, fontSize: 22, color: COR.texto, isTextBox: true, margin: 0 });
  s.addText("Fonte: Zhang, Branicky e Phillips (2001).", { x: 0.6, y: 6.2, w: 12, h: 0.3, fontSize: 11, color: COR.cinza, isTextBox: true, margin: 0 });
}

// 3. Objetivos
{
  const s = conteudo("Objetivos",
    "Objetivo geral e específicos, conforme o enunciado. Destacar que os algoritmos foram implementados do zero, sem bibliotecas de controle, e que as bibliotecas consolidadas foram usadas apenas para validação.");
  cartao(s, 0.6, 1.5, 5.4, 4.9, "Objetivo geral",
    "Desenvolver uma ferramenta em Python que analise a estabilidade de sistemas lineares pelo critério de Nyquist e compare resultados, limitações e custo com Routh-Hurwitz, Lugar das Raízes e Bode.",
    { fundo: COR.navy, corTitulo: COR.laranja, corTexto: COR.branco, tc: 24, tt: 26 });
  bullets(s, [
    "Implementar Nyquist pelo Princípio do Argumento",
    "Extrair margens de ganho e de fase automaticamente",
    "Implementar Routh-Hurwitz e Lugar das Raízes do zero",
    "Comparar atraso exato × aproximação de Padé",
    "Medir tempo e erro numérico para n = 5, 10 e 20",
    "Prever o atraso crítico de um PID em HIL (trilha EC)",
  ], { x: 6.5, y: 1.6, w: 6.2, h: 4.8 }, 20);
}

// 4. Fundamentação: Princípio do argumento e Z = N + P
{
  const s = conteudo("Fundamentação: do Princípio do Argumento a Z = N + P",
    "O contorno de Nyquist envolve todo o semiplano direito. Mapeado por L(s), conta-se quantas vezes a curva envolve o ponto −1. Z é o número de polos instáveis de malha fechada; P, os de malha aberta; N, os envoltórios horários. Estável se, e somente se, Z = 0.");
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 1.6, w: 5.6, h: 2.3, rectRadius: 0.12, fill: { color: COR.navy }, line: { color: COR.navy } });
  s.addText("Z = N + P", { x: 0.6, y: 1.75, w: 5.6, h: 1.3, fontSize: 60, bold: true, color: COR.branco, align: "center", isTextBox: true, margin: 0 });
  s.addText("estável  ⇔  Z = 0  ⇔  N = −P", { x: 0.6, y: 3.05, w: 5.6, h: 0.6, fontSize: 22, color: COR.laranja, align: "center", isTextBox: true, margin: 0 });
  const defs = [
    ["Z", "polos de malha fechada no semiplano direito"],
    ["N", "envoltórios horários de L(jω) em torno de −1 + j0"],
    ["P", "polos de malha aberta no semiplano direito"],
  ];
  defs.forEach(([l, t], i) => {
    s.addShape(pres.shapes.OVAL, { x: 0.6, y: 4.3 + i * 0.75, w: 0.55, h: 0.55, fill: { color: COR.laranja }, line: { color: COR.laranja } });
    s.addText(l, { x: 0.6, y: 4.3 + i * 0.75, w: 0.55, h: 0.55, fontSize: 20, bold: true, color: COR.branco, align: "center", valign: "middle", isTextBox: true, margin: 0 });
    s.addText(t, { x: 1.35, y: 4.3 + i * 0.75, w: 4.9, h: 0.55, fontSize: 18, color: COR.texto, valign: "middle", isTextBox: true, margin: 0 });
  });
  bullets(s, [
    "Contorno sobe o eixo jω e fecha pelo semiplano direito",
    "Polos sobre o eixo jω: desvio por semicírculos à direita",
    "Atraso e^(−jωτ): só gira a fase, |e^(−jωτ)| = 1",
    "Margens: MG = 1/|L(jω_cf)|,  MF = 180° + ∠L(jω_cg)",
    "Margem de atraso: MA = MF / ω_cg",
  ], { x: 6.8, y: 1.6, w: 5.9, h: 4.9 }, 20);
  s.addText("Fonte: Nyquist (1932); Åström e Murray (2008).", { x: 6.8, y: 6.3, w: 5.9, h: 0.3, fontSize: 11, color: COR.cinza, isTextBox: true, margin: 0 });
}

// 5. Métodos comparados
{
  const s = conteudo("Os quatro métodos comparados",
    "Cada método responde a uma pergunta diferente e exige uma entrada diferente. Routh e Lugar das Raízes operam sobre polinômios em s, logo precisam aproximar o atraso; Nyquist e Bode avaliam a resposta em frequência e tratam o atraso exatamente.");
  const m = [
    ["Nyquist", "Plano complexo (polar)", "Estabilidade e margens; aceita P > 0 e atraso exato"],
    ["Routh-Hurwitz", "Coeficientes do polinômio", "Nº de raízes instáveis; atraso exige Padé"],
    ["Lugar das Raízes", "Plano s (geométrico)", "Polos em função do ganho K; atraso exige Padé"],
    ["Diagrama de Bode", "Módulo e fase em log", "Margens; leitura difícil quando P > 0"],
  ];
  m.forEach(([t, d, r], i) => {
    const x = 0.6 + i * 3.08;
    cartao(s, x, 1.6, 2.85, 4.6, t, "", { tt: 22 });
    s.addText("Domínio", { x: x + 0.2, y: 2.35, w: 2.45, h: 0.35, fontSize: 14, bold: true, color: COR.azul, isTextBox: true, margin: 0 });
    s.addText(d, { x: x + 0.2, y: 2.7, w: 2.45, h: 0.9, fontSize: 17, color: COR.texto, isTextBox: true, margin: 0, valign: "top" });
    s.addText("O que entrega", { x: x + 0.2, y: 3.75, w: 2.45, h: 0.35, fontSize: 14, bold: true, color: COR.azul, isTextBox: true, margin: 0 });
    s.addText(r, { x: x + 0.2, y: 4.1, w: 2.45, h: 1.9, fontSize: 17, color: COR.texto, isTextBox: true, margin: 0, valign: "top" });
  });
  s.addText("Fonte: Routh (1877); Hurwitz (1895); Evans (1948); Bode (1945).", { x: 0.6, y: 6.4, w: 12, h: 0.3, fontSize: 11, color: COR.cinza, isTextBox: true, margin: 0 });
}

// 6. Metodologia / arquitetura
{
  const s = conteudo("Metodologia e arquitetura computacional",
    "Pipeline: definição dos 4 sistemas; núcleo implementado do zero com NumPy; validação em três níveis (testes analíticos, python-control/SciPy e simulação temporal); experimentos que geram todas as figuras e tabelas; aplicação HIL no Tinkercad.");
  const etapas = [
    ["1", "Sistemas A–D", "Modelagem dos 4 benchmarks"],
    ["2", "Núcleo próprio", "Nyquist, margens, Routh, raízes, Lugar, Bode, Padé"],
    ["3", "Validação", `${74} testes · python-control · simulação`],
    ["4", "Experimentos", "Figuras e tabelas geradas por script"],
    ["5", "HIL Tinkercad", "2 Arduinos: PID + planta com atraso"],
  ];
  etapas.forEach(([n, t, d], i) => {
    const x = 0.6 + i * 2.5;
    s.addShape(pres.shapes.OVAL, { x: x + 0.75, y: 1.7, w: 0.8, h: 0.8, fill: { color: i === 4 ? COR.laranja : COR.navy }, line: { color: i === 4 ? COR.laranja : COR.navy } });
    s.addText(n, { x: x + 0.75, y: 1.7, w: 0.8, h: 0.8, fontSize: 26, bold: true, color: COR.branco, align: "center", valign: "middle", isTextBox: true, margin: 0 });
    if (i < 4) s.addShape(pres.shapes.LINE, { x: x + 1.65, y: 2.1, w: 1.6, h: 0, line: { color: COR.cinza, width: 1.5, endArrowType: "triangle" } });
    s.addText(t, { x: x, y: 2.7, w: 2.3, h: 0.5, fontSize: 19, bold: true, color: COR.navy, align: "center", isTextBox: true, margin: 0 });
    s.addText(d, { x: x, y: 3.2, w: 2.3, h: 1.2, fontSize: 15, color: COR.texto, align: "center", isTextBox: true, margin: 0, valign: "top" });
  });
  cartao(s, 0.6, 4.6, 6.0, 1.9, "Restrição do enunciado",
    "Algoritmos de controle implementados do zero; NumPy só para vetores, complexos e autovalores.", { tc: 16 });
  cartao(s, 6.8, 4.6, 5.9, 1.9, "Nyquist robusto",
    "Contorno adaptativo, desvio de polos no eixo jω e contagem de envoltórios por dois algoritmos independentes.", { tc: 16 });
}

// 7. Sistemas de teste
{
  const s = conteudo("Quatro sistemas de teste",
    "A: estável em malha aberta. B: levitador magnético linearizado, instável (polo em +20 rad/s), estabilizado por avanço de fase. C: zero no semiplano direito. D: PID sobre processo de 2ª ordem com atraso de rede de 0,5 s; é o mesmo laço do HIL.");
  const sis = [
    ["A · Estável", "20 / [(s+1)(s+2)(s+3)]", "3ª ordem, referência"],
    ["B · Instável (P = 1)", "Levitador magnético + avanço", "polos da planta em ±20 rad/s"],
    ["C · Fase não mínima", "7(1 − s) / [(s+1)(s+2)(s+3)]", "zero em s = +1"],
    ["D · Atraso de rede", "PID · 1/[(s+1)(0,5s+1)] · e^(−0,5s)", "mesmo laço do HIL"],
  ];
  sis.forEach(([t, f, c], i) => {
    const x = 0.6 + (i % 2) * 6.15, y = 1.6 + Math.floor(i / 2) * 2.45;
    cartao(s, x, y, 5.95, 2.2, t, "", { tt: 22 });
    s.addText(f, { x: x + 0.2, y: y + 0.75, w: 5.5, h: 0.6, fontSize: 20, color: COR.azul, bold: true, isTextBox: true, margin: 0 });
    s.addText(c, { x: x + 0.2, y: y + 1.4, w: 5.5, h: 0.5, fontSize: 17, color: COR.texto, isTextBox: true, margin: 0 });
  });
}

// 8. Nyquist dos quatro sistemas
{
  const s = conteudo("Diagramas de Nyquist calculados",
    `Todos estáveis em malha fechada (Z = 0). Destaque para o Sistema B: com P = 1, o diagrama precisa envolver −1 no sentido anti-horário (N = −1). As duas contagens de envoltórios (soma de ângulos e cruzamentos) coincidiram em todos os casos.`);
  figura(s, path.join(FIG, "nyquist_sistemas.png"), { x: 0.6, y: 1.35, w: 6.6, h: 5.5 }, "Diagramas de Nyquist dos sistemas A–D");
  const B = e1.sistemas.B;
  destaque(s, 7.6, 1.6, 5, `N = ${String(B.N).replace("-", "−")}`, `Sistema B (P = ${B.P}): um envoltório anti-horário de −1 ⇒ Z = 0, estável`);
  destaque(s, 7.6, 3.6, 5, "2 / 2", "algoritmos de contagem de envoltórios concordaram em todos os testes", COR.navy);
}

// 9. Concordância entre métodos
{
  const s = conteudo("Os métodos concordam na fronteira de estabilidade",
    "Fronteira de estabilidade em K, normalizada pelo ganho nominal. Nos sistemas racionais, Routh, Lugar das Raízes e Nyquist coincidem até a nona casa decimal. No Sistema D, a diferença é o erro da Padé de ordem 3, não do método.");
  const g = (k) => e1.sistemas[k].ganho_critico;
  const lin = ["A", "B", "C", "D"].map((k) => {
    const f = g(k).routh[0];
    const r = (f[1] === null || f[1] === undefined || !isFinite(f[1])) ? f[0] : f[1];
    return [k, br(r, 5), br(g(k).lugar[0], 5), br(g(k).nyquist_mg, 5), (k === "B" ? "mínimo" : "máximo")];
  });
  const cab = ["Sistema", "Routh", "Lugar das Raízes", "Nyquist / Bode", "Tipo de limite"].map((t) => ({ text: t, options: { bold: true, color: COR.branco, fill: { color: COR.navy } } }));
  s.addTable([cab, ...lin], { x: 0.6, y: 1.6, w: 7.4, colW: [1.2, 1.5, 1.8, 1.6, 1.3], fontSize: 16, color: COR.texto, border: { type: "solid", pt: 0.5, color: "C9D3E0" }, fill: { color: COR.branco }, align: "center", valign: "middle", rowH: 0.55 });
  s.addText("Tabela 1 – Fronteira de K (× ganho nominal) por método. Fonte: elaborada pelos autores (2026).", { x: 0.6, y: 4.5, w: 7.4, h: 0.35, fontSize: 10, color: COR.cinza, isTextBox: true, margin: 0 });
  destaque(s, 8.6, 1.6, 4.2, "9 casas", "decimais de concordância entre os métodos nos sistemas A, B e C", COR.navy);
  destaque(s, 8.6, 3.6, 4.2, `${br(e1.sistemas.B.mg_db, 2).replace("-", "−")} dB`, "margem de ganho do Sistema B: a malha fica instável se o ganho for REDUZIDO; o Bode sozinho não mostra isso");
  s.addText("Validação cruzada com python-control: margens idênticas, mesmo N e polos com erro < 10⁻¹³.", { x: 0.6, y: 5.2, w: 7.4, h: 0.9, fontSize: 18, color: COR.texto, isTextBox: true, margin: 0 });
}

// 10. Bode e Lugar das raízes
{
  const s = conteudo("Bode e Lugar das Raízes",
    "Bode exato versus assintótico; no Sistema D a fase cai sem limite por causa do atraso. O Lugar das Raízes do Sistema D só pode ser traçado sobre a aproximação de Padé, que introduz zeros no semiplano direito.");
  figura(s, path.join(FIG, "bode_sistemas.png"), { x: 0.4, y: 1.3, w: 6.4, h: 4.2 }, "Bode exato e assintótico");
  figura(s, path.join(FIG, "lugar_raizes_sistemas.png"), { x: 6.9, y: 1.3, w: 6.0, h: 2.6 }, "Lugar das Raízes (D com Padé 3)");
  bullets(s, [
    "C tem o mesmo |L(jω)| que o gêmeo de fase mínima, mas só é estável até K = " + br(7 * e1.sistemas.C.mg, 2),
    "No Sistema D, o Lugar das Raízes depende da aproximação",
  ], { x: 7.0, y: 4.5, w: 5.8, h: 1.9 }, 17);
}

// 11. Atraso exato vs Padé
{
  const s = conteudo("Atraso exato × aproximação de Padé",
    `Atraso crítico exato pelo Nyquist: ${br(e2.tau_crit_margem, 3)} s. Com Padé de ordem 1, o Routh prevê um atraso tolerável ${ERRO_PADE1} maior: erro do lado perigoso, não conservador. São necessárias ordens ≥ 3 para erro abaixo de 10⁻³.`);
  const p = Object.fromEntries(e2.pade.map((d) => [d.N, d]));
  destaque(s, 0.6, 1.6, 4.0, `${br(e2.tau_crit_margem, 3)} s`, "atraso crítico exato (Nyquist), sem aproximação", COR.navy);
  destaque(s, 0.6, 3.5, 4.0, pct(Math.abs(p[1].erro_rel)), "erro da Padé de 1ª ordem, superestimando o atraso tolerável");
  s.addText(`N = 3: erro de ${br(100 * Math.abs(p[3].erro_rel), 3)}%`, { x: 0.6, y: 5.5, w: 4.0, h: 0.5, fontSize: 18, color: COR.texto, isTextBox: true, margin: 0 });
  figura(s, path.join(FIG, "pade_erro.png"), { x: 4.9, y: 1.5, w: 8.0, h: 4.6 }, "Erro de fase de Padé e erro no atraso crítico");
}

// 12. Estabilidade numérica do Routh (gráfico nativo)
{
  const s = conteudo("Estabilidade numérica: uma falha real do Routh",
    `Com Padé de ordem alta, os coeficientes variam até 10^37. A primeira versão do Routh usava tolerância absoluta para decidir o que é zero e errou até ${ERRO_ROUTH} dos vereditos, sem aviso. A tolerância relativa ao cancelamento e o escalonamento de frequência corrigiram o problema.`);
  const r = e2.robustez_routh;
  s.addChart(pres.charts.LINE, [
    { name: "Tolerância absoluta (versão inicial)", labels: r.map((d) => String(d.N)), values: r.map((d) => +(100 * d.concordancia_absoluta).toFixed(1)) },
    { name: "Cancelamento + escalonamento (final)", labels: r.map((d) => String(d.N)), values: r.map((d) => +(100 * d.concordancia_escalonado).toFixed(1)) },
  ], {
    x: 0.6, y: 1.4, w: 7.6, h: 4.8, chartColors: [COR.laranja, COR.navy], lineSize: 3, lineDataSymbolSize: 7,
    showLegend: true, legendPos: "b", legendFontSize: 13, legendFontFace: FONTE,
    showTitle: true, title: "Concordância Routh × raízes (%)", titleFontSize: 15, titleColor: COR.navy, titleFontFace: FONTE,
    catAxisTitle: "Ordem N da aproximação de Padé", showCatAxisTitle: true, catAxisTitleFontSize: 13, catAxisTitleColor: COR.cinza,
    catAxisLabelColor: COR.cinza, valAxisLabelColor: COR.cinza, catAxisLabelFontSize: 12, valAxisLabelFontSize: 12,
    catAxisLabelFontFace: FONTE, valAxisLabelFontFace: FONTE, catAxisTitleFontFace: FONTE,
    valAxisMinVal: 50, valAxisMaxVal: 100, valGridLine: { color: "D9DFE7", size: 0.5 }, catGridLine: { style: "none" },
  });
  s.addText("Gráfico 1 – Fonte: elaborado pelos autores (2026).", { x: 0.6, y: 6.25, w: 7.6, h: 0.3, fontSize: 10, color: COR.cinza, isTextBox: true, margin: 0 });
  const piorAbs = Math.min(...r.map((d) => d.concordancia_absoluta));
  destaque(s, 8.8, 1.6, 4.0, pct(1 - piorAbs), "dos vereditos errados com tolerância absoluta, sem nenhum aviso");
  destaque(s, 8.8, 3.6, 4.0, "100%", "de acerto após a correção, até Padé de ordem 20 (grau 44)", COR.navy);
}

// 13. Escalabilidade
{
  const s = conteudo("Custo computacional e erro numérico",
    "Routh é o mais leve; o Lugar das Raízes, o mais caro. O custo do Nyquist depende do número de pontos do contorno e quase não muda com n. O erro das raízes cresce com n por mau condicionamento (polinômio de Wilkinson).");
  const R = Object.fromEntries(e3.resultados.map((d) => [`${d.familia}|${d.n}`, d]));
  const a5 = R["aleatória|5"], a20 = R["aleatória|20"], w20 = R["Wilkinson|20"], w5 = R["Wilkinson|5"];
  figura(s, path.join(FIG, "escalabilidade.png"), { x: 0.4, y: 1.35, w: 8.2, h: 4.4 }, "Tempo por método e erro das raízes");
  destaque(s, 8.9, 1.5, 4.0, `< ${Math.ceil(a20.t_nyquist * 1e3)} ms`, "Nyquist completo, de n = 5 a 20", COR.navy);
  destaque(s, 8.9, 3.3, 4.0, `${Math.round(a5.t_routh * 1e6)}–${Math.round(a20.t_routh * 1e6)} µs`, "Routh-Hurwitz, de n = 5 a 20", COR.navy);
  s.addText(`Erro das raízes (Wilkinson): ${cient(w5.erro_companheira)} → ${cient(w20.erro_companheira)}`,
    { x: 8.9, y: 5.2, w: 4.0, h: 0.9, fontSize: 17, color: COR.laranja, bold: true, isTextBox: true, margin: 0 });
}

// 14. HIL: montagem no Tinkercad
{
  const s = conteudo("Aplicação: PID com atraso de rede no Tinkercad",
    "Dois Arduinos Uno: a Planta integra o processo e emula a rede com um buffer de atraso ajustado pelo potenciômetro; a chave ativa atraso variável. O Controlador roda o PID discreto. Serial de hardware a 115200 bit/s; SoftwareSerial perdia quadros no simulador.");
  figura(s, path.join(TK, "T5_circuito_recorte.png"), { x: 0.4, y: 1.3, w: 7.6, h: 5.4 }, "Circuito HIL no Tinkercad durante o ensaio T5", "captura do Tinkercad Circuits pelos autores (2026)");
  bullets(s, [
    "Planta: processo discretizado (ZOH, Ts = 20 ms) + buffer de atraso",
    "Potenciômetro: atraso de 0 a 1,2 s",
    "Chave: atraso variável sorteado",
    "Controlador: PID com antiwindup",
    "LED “L”: alarme de oscilação",
  ], { x: 8.3, y: 1.5, w: 4.5, h: 5.0 }, 18);
}

// 15. HIL: resultado
{
  const t4a = e5.ensaios.T4a, t4b = e5.ensaios.T4b;
  const erroMax = Math.max(...Object.values(e5.ensaios).filter((v) => !v.variavel).map((v) => v.erro_max_gemeo));
  const s = conteudo("Previsão de Nyquist × Tinkercad",
    `O limite medido no Tinkercad ficou entre ${t4a.d_medido} e ${t4b.d_medido} amostras (${br(t4a.d_medido * 0.02, 2)} a ${br(t4b.d_medido * 0.02, 2)} s), contra ${br(e2.tau_crit_margem, 3)} s previstos pelo Nyquist: diferença menor que uma amostra. O traço do Tinkercad coincide amostra a amostra com o gêmeo digital em Python.`);
  figura(s, path.join(FIG, "tinkercad_respostas.png"), { x: 0.4, y: 1.3, w: 7.8, h: 5.4 }, "Respostas medidas no Tinkercad", "simulação no Tinkercad, elaborada pelos autores (2026)");
  destaque(s, 8.6, 1.5, 4.3, `${br(e2.tau_crit_margem, 3)} s`, "atraso crítico previsto pelo Nyquist", COR.navy);
  destaque(s, 8.6, 3.2, 4.3, `${br(t4b.d_medido * 0.02, 2)} s`, `primeiro atraso instável no Tinkercad (d = ${t4b.d_medido})`);
  s.addText(`Erro máximo Tinkercad × gêmeo: ${cient(erroMax, 1)}`,
    { x: 8.6, y: 5.2, w: 4.3, h: 0.9, fontSize: 17, color: COR.texto, bold: true, isTextBox: true, margin: 0 });
}

// 16. Comparação dos métodos (tabela do enunciado validada)
{
  const s = conteudo("A tabela do enunciado, validada com dados",
    "Cada linha da tabela comparativa do enunciado foi confrontada com uma medição. Todas foram confirmadas; a de custo, com a ressalva de que o custo do Nyquist depende da amostragem, não da ordem.");
  const cel = (t, b = false, cor = COR.texto) => ({ text: t, options: { bold: b, color: cor } });
  const cab = ["Característica", "Nyquist", "Routh", "Lugar", "Bode", "Evidência"].map((t) => ({ text: t, options: { bold: true, color: COR.branco, fill: { color: COR.navy } } }));
  const ok = "✔", nao = "✘";
  const linhas = [
    [cel("Estabilidade relativa", true), cel(ok), cel(nao, false, COR.laranja), cel(ok), cel(ok), cel("MG, MF e margem de atraso")],
    [cel("Atraso exato", true), cel(ok), cel("Padé", false, COR.laranja), cel("Padé", false, COR.laranja), cel(ok), cel(`Padé 1 erra ${pct(Math.abs(e2.pade[0].erro_rel))}`)],
    [cel("Instável em malha aberta", true), cel(ok), cel(ok), cel(ok), cel("difícil", false, COR.laranja), cel("Sistema B: MG negativa em dB")],
    [cel("Custo", true), cel("< 1 ms"), cel("µs"), cel("100+ ms"), cel("ms"), cel("Medido para n = 5 a 30")],
  ];
  s.addTable([cab, ...linhas], { x: 0.6, y: 1.6, w: 12.1, colW: [2.9, 1.5, 1.4, 1.4, 1.4, 3.5], fontSize: 17, border: { type: "solid", pt: 0.5, color: "C9D3E0" }, align: "center", valign: "middle", rowH: 0.75 });
  s.addText("Tabela 2 – Síntese da validação empírica. Fonte: elaborada pelos autores (2026).", { x: 0.6, y: 5.6, w: 12, h: 0.35, fontSize: 10, color: COR.cinza, isTextBox: true, margin: 0 });
}

// 17. Conclusões
{
  const s = pres.addSlide({ masterName: "ESCURO" });
  s.addText("Conclusões", { x: 0.8, y: 0.5, w: 11.5, h: 0.9, fontSize: 40, bold: true, color: COR.branco, isTextBox: true, margin: 0 });
  const c = [
    ["Mesma resposta, entradas diferentes", "Os métodos concordam até a 9ª casa; muda o que cada um exige e entrega."],
    ["Nyquist trata o atraso exatamente", `Atraso crítico de ${br(e2.tau_crit_margem, 3)} s; Padé de 1ª ordem errou ${pct(Math.abs(e2.pade[0].erro_rel))}, do lado perigoso.`],
    ["Robustez numérica importa", `Uma tolerância ingênua no Routh errou até ${ERRO_ROUTH} dos vereditos, sem aviso.`],
    ["Previsão confirmada no HIL", "O Tinkercad ficou instável a menos de uma amostra do limite previsto."],
  ];
  c.forEach(([t, d], i) => {
    const x = 0.8 + (i % 2) * 6.0, y = 1.7 + Math.floor(i / 2) * 2.3;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 5.7, h: 2.05, rectRadius: 0.12, fill: { color: "22325A" }, line: { color: "22325A" } });
    s.addText(t, { x: x + 0.25, y: y + 0.2, w: 5.2, h: 0.55, fontSize: 21, bold: true, color: COR.laranja, isTextBox: true, margin: 0 });
    s.addText(d, { x: x + 0.25, y: y + 0.8, w: 5.2, h: 1.1, fontSize: 17, color: COR.branco, isTextBox: true, margin: 0, valign: "top" });
  });
  s.addText("Trabalhos futuros: hardware físico com rede real e perda de pacotes; projeto do controlador pela margem de atraso.",
    { x: 0.8, y: 6.4, w: 11.7, h: 0.5, fontSize: 16, color: "AFC3DD", isTextBox: true, margin: 0 });
  s.addNotes("Fechamento: retomar a pergunta inicial (quanto atraso o laço tolera) e mostrar que o Nyquist a respondeu com exatidão, confirmada no Tinkercad. Código, testes e resultados no repositório GitHub liassuo/controle-processos.");
}

// 18. Referências
{
  const s = conteudo("Referências",
    "Referências completas no artigo, em formato ABNT/SBC.");
  const refs = [
    "ÅSTRÖM, K. J.; MURRAY, R. M. Feedback Systems. Princeton University Press, 2008.",
    "BODE, H. W. Network Analysis and Feedback Amplifier Design. Van Nostrand, 1945.",
    "EVANS, W. R. Graphical analysis of control systems. Trans. AIEE, v. 67, 1948.",
    "FULLER, S. et al. The Python Control Systems Library. IEEE CDC, 2021.",
    "HURWITZ, A. Über die Bedingungen [...]. Math. Annalen, v. 46, 1895.",
    "NISE, N. S. Engenharia de Sistemas de Controle. 7. ed. LTC, 2017.",
    "NYQUIST, H. Regeneration theory. Bell System Tech. Journal, v. 11, 1932.",
    "OGATA, K. Engenharia de Controle Moderno. 5. ed. Pearson, 2010.",
    "PADÉ, H. Sur la représentation approchée [...]. Ann. Sci. ÉNS, 1892.",
    "ROUTH, E. J. A Treatise on the Stability of a Given State of Motion. 1877.",
    "WILKINSON, J. H. The perfidious polynomial. MAA, 1984.",
    "ZHANG, W. et al. Stability of networked control systems. IEEE CSM, 2001.",
  ];
  s.addText(refs.map((t, i) => ({ text: t, options: { breakLine: i < refs.length - 1 } })),
    { x: 0.6, y: 1.4, w: 12.1, h: 5.3, fontSize: 15, color: COR.texto, paraSpaceAfter: 5, isTextBox: true, margin: 0, valign: "top" });
}

const saida = path.join(__dirname, "Apresentacao_Nyquist.pptx");
pres.writeFile({ fileName: saida }).then((f) => console.log("gerado:", f));
