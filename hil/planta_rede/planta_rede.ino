/*
 * HIL – Arduino 1: PLANTA VIRTUAL + EMULADOR DE REDE  (Tinkercad Circuits, Arduino Uno)
 *
 * Projeto: Análise Computacional e Comparativa de Critérios de Estabilidade
 * Trilha EC – controle PID com atraso de comunicação variável.
 *
 * Função:
 *  - Relógio mestre do laço (período TS = 20 ms).
 *  - Integra a planta G_p(s) = 1/((s+1)(0,5s+1)) discretizada por ZOH
 *    (matrizes calculadas em src/estabilidade/hil.py -> discretiza_zoh).
 *  - Emula a rede: guarda os comandos u recebidos e aplica o comando de
 *    d amostras atrás (atraso tau = d*TS), sem reordenar pacotes.
 *  - d é ajustado pelo potenciômetro (A0). Com a chave em D12 em nível alto, o
 *    atraso varia aleatoriamente em [d, d + JITTER] a cada período.
 *
 * Sequência em cada período k (idêntica ao gêmeo digital em Python):
 *   1) envia y[k] ao controlador     2) recebe u[k]
 *   3) j = max(j_ant, k - d[k]); aplica u[j]
 *   4) x[k+1] = Ad x[k] + Bd u[j]
 *
 * Enlace: serial de hardware a 115200 bit/s, protocolo de texto (uma linha por
 * mensagem). A linha enviada "y tau u_aplicado k" também é exibida no Monitor
 * Serial/plotter da Planta. Linhas iniciadas por '#' são ignoradas pelo controlador;
 * a linha "R" pede que ele reinicie o PID.
 *
 * Ligações:
 *   D1 (TX) -> D0 (RX) do controlador   D0 (RX) <- D1 (TX) do controlador   GND comum
 *   A0  <- cursor do potenciômetro (extremos em 5V e GND)
 *   D12 <- comum da chave deslizante (extremos em 5V = atraso variável, GND = fixo)
 *   D13 -> LED "L" da própria placa (aceso quando |erro| > 0,5 após 10 s)
 */

// ---------- parâmetros (devem coincidir com o gêmeo digital) ----------
const unsigned long TS_MS = 20;      // período de amostragem
const float TS = 0.02f;
const int DMAX = 80;                 // atraso máximo: 80 amostras = 1,6 s
const int JITTER = 20;               // amplitude do atraso variável (amostras)
const float REF = 1.0f;              // referência (degrau unitário)
const unsigned long TIMEOUT_MS = 15; // espera máxima pela resposta do controlador

// Planta discretizada (ZOH, TS = 20 ms): x[k+1] = Ad x[k] + Bd u, y = C x
const float AD00 = 0.94138020f, AD01 = -0.038818467f;
const float AD10 = 0.019409234f, AD11 = 0.99960792f;
const float BD0 = 0.019409234f, BD1 = 0.00019604627f;
const float C0 = 0.0f, C1 = 2.0f;

float x0 = 0.0f, x1 = 0.0f;
float historico[DMAX + 1];           // buffer circular dos comandos recebidos
long k = 0;                          // índice do período
long j_ant = -1;                     // índice do último comando aplicado
float u_ultimo = 0.0f;
unsigned long proximo = 0;
unsigned int perdas = 0;

char linha[24];

// lê uma linha terminada em '\n' com prazo máximo; devolve true se completa
bool le_linha(unsigned long timeout_ms) {
  unsigned long t0 = millis();
  int n = 0;
  while (millis() - t0 < timeout_ms) {
    if (!Serial.available()) continue;
    char c = Serial.read();
    if (c == '\n') { linha[n] = 0; return n > 0; }
    if (c != '\r' && n < (int)sizeof(linha) - 1) linha[n++] = c;
  }
  return false;
}

void setup() {
  Serial.begin(115200);
  pinMode(12, INPUT);
  pinMode(13, OUTPUT);
  randomSeed(7);
  for (int i = 0; i <= DMAX; i++) historico[i] = 0.0f;
  delay(200);                        // aguarda o controlador iniciar
  Serial.println("R");               // controlador zera o PID
  Serial.println("# y tau u k");
  proximo = millis();
}

void loop() {
  if ((long)(millis() - proximo) < 0) return;
  proximo += TS_MS;

  int d = map(analogRead(A0), 0, 1023, 0, DMAX - JITTER);
  if (digitalRead(12) == HIGH) d += random(0, JITTER + 1);

  float y = C0 * x0 + C1 * x1;        // 1) saída da planta
  long j = k - d;                     // 3) rede: entrega com atraso, sem reordenar
  if (j < j_ant) j = j_ant;
  float tau = (k - j) * TS;
  // a linha leva y (lido pelo controlador), tau, o comando aplicado no período
  // anterior e o índice k (permite reconstruir a série temporal: t = k*TS)
  Serial.print(y, 4); Serial.print(' ');
  Serial.print(tau, 2); Serial.print(' ');
  Serial.print(u_ultimo, 4); Serial.print(' ');
  Serial.println(k);

  float u;
  if (le_linha(TIMEOUT_MS)) {         // 2) comando do controlador
    u = atof(linha);
  } else {
    u = (k > 0) ? historico[(k - 1) % (DMAX + 1)] : 0.0f;   // perda: repete o último
    perdas++;
  }
  historico[k % (DMAX + 1)] = u;

  float u_ap = (j >= 0) ? historico[j % (DMAX + 1)] : 0.0f;
  j_ant = j;
  u_ultimo = u_ap;

  float n0 = AD00 * x0 + AD01 * x1 + BD0 * u_ap;   // 4) planta
  float n1 = AD10 * x0 + AD11 * x1 + BD1 * u_ap;
  x0 = n0;
  x1 = n1;

  digitalWrite(13, (k * TS > 10.0f && fabs(REF - y) > 0.5f) ? HIGH : LOW);
  k++;
}
