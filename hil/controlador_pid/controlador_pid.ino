/*
 * HIL – Arduino 2: CONTROLADOR PID  (Tinkercad Circuits, Arduino Uno)
 *
 * Recebe y[k] da planta virtual, calcula u[k] e devolve imediatamente.
 * O período é imposto pela planta (relógio mestre, TS = 20 ms).
 *
 * PID discreto, idêntico ao gêmeo digital (src/estabilidade/hil.py):
 *   e = r - y
 *   D[k] = a_d D[k-1] + b_d (e[k] - e[k-1]),  a_d = Tf/(Tf+TS), b_d = Kd/(Tf+TS)
 *   I[k] = I[k-1] + Ki TS e[k]   (atualizado só fora da saturação: antiwindup)
 *   u = sat(Kp e + I + D, +-UMAX)
 * Parâmetros contínuos: Kp = 2, Ki = 1, Kd = 0,5, Tf = 0,1 s (Sistema D).
 *
 * Ligações: D10 (RX) <- D11 da planta; D11 (TX) -> D10 da planta; GND comum.
 * Saída serial (115200): "e u" por linha.
 */
#include <SoftwareSerial.h>

const float TS = 0.02f;
const float KP = 2.0f, KI = 1.0f, KD = 0.5f, TF = 0.1f;
const float UMAX = 10.0f;
const float REF = 1.0f;
const float A_D = TF / (TF + TS);
const float B_D = KD / (TF + TS);

SoftwareSerial enlace(10, 11);   // RX, TX

float integ = 0.0f, deriv = 0.0f, e_ant = 0.0f;

void envia_float(float v) {
  byte *b = (byte *)&v;
  byte ck = b[0] ^ b[1] ^ b[2] ^ b[3];
  enlace.write(0xA5);
  enlace.write(b, 4);
  enlace.write(ck);
}

// leitura não bloqueante de um quadro [0xA5][4 bytes][xor]
byte buf[5];
int n = -1;
bool quadro_pronto(float &v) {
  while (enlace.available()) {
    byte c = enlace.read();
    if (n < 0) { if (c == 0xA5) n = 0; continue; }
    buf[n++] = c;
    if (n == 5) {
      n = -1;
      if ((buf[0] ^ buf[1] ^ buf[2] ^ buf[3]) == buf[4]) { memcpy(&v, buf, 4); return true; }
    }
  }
  return false;
}

void setup() {
  Serial.begin(115200);
  enlace.begin(9600);
  Serial.println("e u");
}

void loop() {
  float y;
  if (!quadro_pronto(y)) return;
  if (isnan(y)) {                 // pedido de reinício vindo da planta
    integ = deriv = e_ant = 0.0f;
    return;
  }
  float e = REF - y;
  deriv = A_D * deriv + B_D * (e - e_ant);
  float integ_nova = integ + KI * TS * e;
  float u = KP * e + integ_nova + deriv;
  if (u > -UMAX && u < UMAX) {
    integ = integ_nova;           // antiwindup condicional
  } else {
    u = KP * e + integ + deriv;
  }
  if (u > UMAX) u = UMAX;
  if (u < -UMAX) u = -UMAX;
  e_ant = e;
  envia_float(u);
  Serial.print(e, 4); Serial.print(' ');
  Serial.println(u, 4);
}
