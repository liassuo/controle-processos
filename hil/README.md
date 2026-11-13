# Simulação HIL no Tinkercad (trilha EC)

Laço de controle PID com atraso de comunicação variável, simulado com **dois Arduinos Uno** no [Tinkercad Circuits](https://www.tinkercad.com/circuits). O objetivo é comparar, no circuito simulado, o atraso crítico previsto pelo critério de Nyquist.

```
 ┌──────────────────────────┐   y[k] (serial 9600)   ┌───────────────────────┐
 │ Arduino 1: PLANTA + REDE │ ─────────────────────▶ │ Arduino 2: PID        │
 │  G_p(s)=1/((s+1)(0,5s+1))│ ◀───────────────────── │  Kp=2 Ki=1 Kd=0,5     │
 │  buffer de atraso d·Ts   │   u[k]                 │  Tf=0,1 s  Ts=20 ms   │
 │  pot. A0 → d             │                        └───────────────────────┘
 │  chave D12 → atraso var. │
 │  LCD 16x2 · LED D13      │
 └──────────────────────────┘
```

## Previsões para conferir no Tinkercad

As previsões vêm de `experimentos/exp4_hil.py` e de `results/exp4_hil.json`.

| Grandeza | Valor previsto |
|---|---|
| Atraso crítico, Nyquist em tempo contínuo | **1,122 s** (MF = 89,8° em ω_cg = 1,397 rad/s, sem atraso) |
| Atraso crítico do gêmeo digital (Ts = 20 ms) | **d = 55 amostras = 1,10 s** |
| Atraso nominal (Sistema D) | 0,50 s (25 amostras): resposta estável com sobressinal |

## Montagem

1. Crie um circuito novo e adicione **dois Arduino Uno R3**. Chame-os de "Planta" e "Controlador".
2. Faça as ligações seriais em cruz e una os GNDs:
   - D11 da Planta → D10 do Controlador;
   - D11 do Controlador → D10 da Planta;
   - GND da Planta ↔ GND do Controlador.
3. Monte os periféricos na **Planta**:
   - **Potenciômetro**: extremos em 5V e GND, cursor em **A0**. Ele ajusta o atraso de 0 a 60 amostras (0 a 1,2 s).
   - **Chave deslizante**: comum em **D12**, um lado em 5V e o outro em GND. Em 5V, soma ao atraso um valor aleatório de 0 a 20 amostras.
   - **Botão**: entre **D8** e GND. Ele reinicia o ensaio de degrau.
   - **LED** com resistor de 220 Ω em **D13**. Ele acende quando |erro| > 0,5 depois de 10 s.
   - **LCD 16x2** (paralelo): RS=D7, E=D6, D4=D5, D5=D4, D6=D3, D7=D2, RW=GND. Ligue um potenciômetro de contraste em V0.
4. Copie o código para cada placa, no modo **Código → Texto**:
   - Planta: `hil/planta_rede/planta_rede.ino`;
   - Controlador: `hil/controlador_pid/controlador_pid.ino`.
5. Clique em **Iniciar simulação**, abra o **Monitor serial** da Planta e use o modo gráfico. As colunas são `r y u tau`.

## Roteiro de ensaios (para o artigo)

Para cada ensaio, registre em `results/tinkercad/registro.md` e salve a captura de tela em `results/tinkercad/`:

| # | Configuração | O que capturar |
|---|---|---|
| T1 | Potenciômetro em 0 (τ = 0), chave em FIX | Circuito completo e gráfico do degrau |
| T2 | τ = 0,50 s, nominal (LCD mostra `tau=0.50s`) | Gráfico com o sobressinal |
| T3 | τ = 1,00 s | Gráfico com oscilação amortecida |
| T4 | Aumente τ até a oscilação deixar de decair; anote o τ do LCD | Gráfico no limite e o τ medido |
| T5 | τ = 1,20 s, acima do crítico | Gráfico com oscilação crescente e o LED aceso |
| T6 | Chave em VAR, base em 0,80 s | Gráfico com atraso variável |

Para cada ensaio de T2 a T6, aperte o botão (D8) depois de ajustar τ, para reiniciar o degrau. Com saturação em ±10, a instabilidade aparece como oscilação crescente que vira um ciclo-limite de amplitude limitada.

## Observações

- O Tinkercad pode rodar mais devagar que o tempo real. `millis()` acompanha o tempo **simulado**, então os resultados não dependem da velocidade do PC. Ainda assim, anote o tempo indicado pelo Tinkercad.
- O mapeamento do potenciômetro é discreto, com passo de 1 amostra (20 ms). Use o valor mostrado no LCD.
- O teste `tests/test_hil.py` garante que as constantes dos sketches (ZOH, PID e Ts) são as mesmas do gêmeo digital em Python.
