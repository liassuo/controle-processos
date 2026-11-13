# Registro dos ensaios no Tinkercad

- **Data:** 13/11/2026.
- **Ambiente:** Tinkercad Circuits, no projeto da conta `liassuo`, com dois Arduino Uno R3. Os sketches usados estão em `hil/`.
- **Execução:** a simulação foi executada no Tinkercad, com a conta do grupo. Os valores abaixo são **saídas do simulador do Tinkercad**, capturadas do Monitor Serial da placa "Planta". Não são resultados do gêmeo em Python.
- **Velocidade:** o simulador rodou a cerca de 0,4× o tempo real. Os tempos indicados são de tempo **simulado** (`millis()` e o relógio do simulador).

## Método de captura

O Monitor Serial do Tinkercad guarda só os últimos 1000 caracteres. Por isso, cada linha da Planta inclui o índice do período k (`y tau u k`). Um observador no navegador lê o monitor a cada alteração e guarda cada linha pelo seu k. A primeira e a última linha de cada leitura são descartadas, porque podem estar cortadas.

As séries completas estão em `bruto_T*.txt`, uma linha por período de 20 ms. O script `experimentos/exp5_tinkercad.py` confirma que não há lacunas: k é contínuo a partir de 0.

## Ensaios

| Ensaio | τ (s) | Duração simulada | Resultado | Captura |
|---|---|---|---|---|
| T1 | 0,00 | 33 s | estável, sem sobressinal | T1.png |
| T2 | 0,50 (nominal) | 35 s | estável, pico de 1,240 em 1,86 s | — |
| T3 | 1,00 | 44 s | oscilação amortecida (taxa de −0,047 s⁻¹) | T3.png |
| T4a | 1,08 (d = 54) | 124 s | estável, decaimento muito lento (−0,0077 s⁻¹) | — |
| T4b | 1,10 (d = 55) | 93 s | **instável**, crescimento lento (+0,0009 s⁻¹) | — |
| T4c | 1,12 (d = 56) | 63 s | instável (+0,0091 s⁻¹) | — |
| T5 | 1,20 | 41 s | instável (+0,038 s⁻¹); LED "L" aceso | T5.png, T5_circuito_*.png |
| T6 | variável, de 0,80 a 1,12 | 70 s | estável | T6.png |

O limite de estabilidade medido fica entre 54 e 55 amostras (1,08 a 1,10 s). A previsão do critério de Nyquist em tempo contínuo é de 1,122 s, e o gêmeo digital prevê 55 amostras.

Em todos os ensaios, o traço do Tinkercad coincide com o do gêmeo digital, com erro máximo entre 7×10⁻⁵ e 2,3×10⁻⁴. Os valores exatos estão em `results/exp5_tinkercad.json` e `results/tabelas/tinkercad_ensaios.tex`.

## Observações

- Na primeira montagem, as placas se comunicavam por `SoftwareSerial` a 9600 bit/s, e o simulador perdia ou corrompia quadros: o controlador recebeu só 4 quadros em 18 s. A montagem final usa a serial de hardware (D0/D1) a 115200 bit/s, com protocolo de texto, e não houve perdas.
- O código deve ser colado no editor no modo **Texto**.
- O Tinkercad só deixa girar o potenciômetro com a simulação rodando. A posição fica salva e vale para a execução seguinte.
