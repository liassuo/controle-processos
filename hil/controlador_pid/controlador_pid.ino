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
 * Enlace: serial de hardware a 115200 bit/s, uma linha de texto por mensagem.
 * Entrada: "y tau u" (só o primeiro número é usado); "R" reinicia; '#' é comentário.
 * Saída: "u" (exibida também no Monitor Serial do controlador).
 *
 * Ligações: D0 (RX) <- D1 (TX) da planta; D1 (TX) -> D0 (RX) da planta; GND comum.
 */

const float TS = 0.02f;
const float KP = 2.0f, KI = 1.0f, KD = 0.5f, TF = 0.1f;
const float UMAX = 10.0f;
const float REF = 1.0f;
const float A_D = TF / (TF + TS);
const float B_D = KD / (TF + TS);

float integ = 0.0f, deriv = 0.0f, e_ant = 0.0f;
char linha[40];
int n = 0;

void setup() {
  Serial.begin(115200);
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\r') continue;
    if (c != '\n') {
      if (n < (int)sizeof(linha) - 1) linha[n++] = c;
      continue;
    }
    linha[n] = 0;
    n = 0;
    if (linha[0] == 0 || linha[0] == '#') continue;
    if (linha[0] == 'R') { integ = deriv = e_ant = 0.0f; continue; }

    float y = atof(linha);
    float e = REF - y;
    deriv = A_D * deriv + B_D * (e - e_ant);
    float integ_nova = integ + KI * TS * e;
    float u = KP * e + integ_nova + deriv;
    if (u > -UMAX && u < UMAX) {
      integ = integ_nova;         // antiwindup condicional
    } else {
      u = KP * e + integ + deriv;
    }
    if (u > UMAX) u = UMAX;
    if (u < -UMAX) u = -UMAX;
    e_ant = e;
    Serial.println(u, 5);
  }
}
