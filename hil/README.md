# Simulação HIL no Tinkercad (trilha EC)

Laço PID com atraso de comunicação variável, simulado com **dois Arduinos Uno** no [Tinkercad Circuits](https://www.tinkercad.com/circuits). O objetivo é comparar o atraso crítico observado no simulador com a previsão do critério de Nyquist.

```
 ┌──────────────────────────┐  "y tau u k\n" (serial 115200)  ┌───────────────────────┐
 │ Arduino 1: PLANTA + REDE │ D1(TX) ───────────────▶ D0(RX)  │ Arduino 2: PID        │
 │  G_p(s)=1/((s+1)(0,5s+1))│ D0(RX) ◀─────────────── D1(TX)  │  Kp=2 Ki=1 Kd=0,5     │
 │  buffer de atraso d·Ts   │            "u\n"                │  Tf=0,1 s  Ts=20 ms   │
 │  pot. A0 → d (0–60)      │                                 └───────────────────────┘
 │  chave D12 → +[0,20]     │
 │  LED "L" (D13): alerta   │
 └──────────────────────────┘
```

## Montagem

1. Coloque dois **Arduino Uno R3**. O primeiro é a Planta e o segundo é o Controlador.
2. Ligue a serial em cruz:
   - D1 (TX) da Planta → D0 (RX) do Controlador;
   - D1 (TX) do Controlador → D0 (RX) da Planta;
   - GND da Planta ↔ GND do Controlador.
3. Monte os periféricos na Planta:
   - **Potenciômetro**: um extremo em 5V, o outro em GND e o cursor em **A0**.
   - **Chave deslizante**: comum em **D12**, um extremo em 5V e o outro em GND.
   - O alerta usa o LED "L" da própria placa (D13), sem componente extra.
4. Em **Código**, mude o modo para **Texto** e cole o código de cada placa:
   - Planta: `planta_rede/planta_rede.ino`;
   - Controlador: `controlador_pid/controlador_pid.ino`.
5. Inicie a simulação e abra o **Monitor serial** da Planta. Cada linha traz `y tau u k`, com t = k·0,02 s.

O potenciômetro e a chave só respondem com a simulação rodando. As posições ficam salvas para a execução seguinte.

## Previsões

As previsões vêm de `experimentos/exp4_hil.py`.

| Grandeza | Valor |
|---|---|
| Atraso crítico, Nyquist em tempo contínuo | 1,122 s |
| Atraso crítico do gêmeo digital (Ts = 20 ms) | 55 amostras (1,10 s) |

Os ensaios executados no Tinkercad e os resultados estão em [`results/tinkercad/registro.md`](../results/tinkercad/registro.md). As séries completas estão em `results/tinkercad/bruto_T*.txt`, e a análise em `experimentos/exp5_tinkercad.py`.

## Observações

- A serial de hardware também alimenta o Monitor Serial. Por isso, a Planta envia `y tau u k`: o controlador usa só o primeiro número e ignora linhas iniciadas por `#`. A linha `R` reinicia o PID.
- `SoftwareSerial` foi testada e descartada, porque perdia quadros no simulador.
- O LCD 16x2 era opcional e foi removido para simplificar a fiação.
- `tests/test_hil.py` garante que as constantes dos sketches (ZOH, PID, Ts) são as mesmas do gêmeo digital.
