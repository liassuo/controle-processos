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
 * Ligações:
 *   D10 (RX) <- D11 do controlador     D11 (TX) -> D10 do controlador     GND comum
 *   A0  <- cursor do potenciômetro (extremos em 5V e GND)
 *   D12 <- chave deslizante (5V = atraso variável, GND = fixo)
 *   D8  <- botão para GND (reinicia o ensaio de degrau), INPUT_PULLUP
 *   D13 -> LED (aceso quando |erro| > 0,5 após 10 s: oscilação/instabilidade)
 *   LCD 16x2: RS=D7, E=D6, D4=D5, D5=D4, D6=D3, D7=D2
 *
 * Saída serial (115200): "r y u tau" por linha, para o Serial Plotter do Tinkercad.
 */
#include <SoftwareSerial.h>
#include <LiquidCrystal.h>

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

SoftwareSerial enlace(10, 11);       // RX, TX
LiquidCrystal lcd(7, 6, 5, 4, 3, 2);

float x0 = 0.0f, x1 = 0.0f;
float historico[DMAX + 1];           // buffer circular dos comandos recebidos
long k = 0;                          // índice do período
long j_ant = -1;                     // índice do último comando aplicado
float u_ultimo = 0.0f;
unsigned long proximo = 0;
unsigned int perdas = 0;

// ---------- protocolo: [0xA5][float LE 4 bytes][xor dos 4 bytes] ----------
void envia_float(float v) {
  byte *b = (byte *)&v;
  byte ck = b[0] ^ b[1] ^ b[2] ^ b[3];
  enlace.write(0xA5);
  enlace.write(b, 4);
  enlace.write(ck);
}

bool recebe_float(float &v, unsigned long timeout_ms) {
  unsigned long t0 = millis();
  byte buf[5];
  int n = -1;                         // -1: aguardando cabeçalho
  while (millis() - t0 < timeout_ms) {
    if (!enlace.available()) continue;
    byte c = enlace.read();
    if (n < 0) { if (c == 0xA5) n = 0; continue; }
    buf[n++] = c;
    if (n == 5) {
      if ((buf[0] ^ buf[1] ^ buf[2] ^ buf[3]) == buf[4]) { memcpy(&v, buf, 4); return true; }
      n = -1;                         // checksum inválido: descarta
    }
  }
  return false;
}

void reinicia() {
  x0 = x1 = 0.0f;
  k = 0;
  j_ant = -1;
  u_ultimo = 0.0f;
  perdas = 0;
  for (int i = 0; i <= DMAX; i++) historico[i] = 0.0f;
  envia_float(NAN);                   // NaN avisa o controlador para zerar o PID
}

void setup() {
  Serial.begin(115200);
  enlace.begin(9600);
  pinMode(8, INPUT_PULLUP);
  pinMode(12, INPUT);
  pinMode(13, OUTPUT);
  lcd.begin(16, 2);
  randomSeed(7);
  delay(200);                          // aguarda o controlador iniciar
  reinicia();
  proximo = millis();
  Serial.println("r y u tau");
}

void loop() {
  if (digitalRead(8) == LOW) { reinicia(); delay(300); proximo = millis(); }
  if ((long)(millis() - proximo) < 0) return;
  proximo += TS_MS;

  int d = map(analogRead(A0), 0, 1023, 0, DMAX - JITTER);
  if (digitalRead(12) == HIGH) d += random(0, JITTER + 1);

  float y = C0 * x0 + C1 * x1;        // 1) saída da planta
  envia_float(y);
  float u;
  if (recebe_float(u, TIMEOUT_MS)) {  // 2) comando do controlador
    u_ultimo = u;
  } else {
    u = u_ultimo;                     // pacote perdido: mantém o último
    perdas++;
  }
  historico[k % (DMAX + 1)] = u;

  long j = k - d;                     // 3) rede: entrega com atraso, sem reordenar
  if (j < j_ant) j = j_ant;
  float u_ap = (j >= 0) ? historico[j % (DMAX + 1)] : 0.0f;
  j_ant = j;

  float n0 = AD00 * x0 + AD01 * x1 + BD0 * u_ap;   // 4) planta
  float n1 = AD10 * x0 + AD11 * x1 + BD1 * u_ap;
  x0 = n0;
  x1 = n1;

  float tau = (k - j) * TS;
  Serial.print(REF); Serial.print(' ');
  Serial.print(y, 4); Serial.print(' ');
  Serial.print(u_ap, 4); Serial.print(' ');
  Serial.println(tau, 2);

  digitalWrite(13, (k * TS > 10.0f && fabs(REF - y) > 0.5f) ? HIGH : LOW);
  if (k % 25 == 0) {                  // LCD a cada 0,5 s
    lcd.setCursor(0, 0);
    lcd.print("tau="); lcd.print(tau, 2); lcd.print("s ");
    lcd.print(digitalRead(12) ? "VAR" : "FIX"); lcd.print("   ");
    lcd.setCursor(0, 1);
    lcd.print("y="); lcd.print(y, 3); lcd.print(" t="); lcd.print((int)(k * TS)); lcd.print("s   ");
  }
  k++;
}
