#include <DHT.h>
#include <math.h>

#define DHTPIN 2
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);

float dewPoint(float t, float rh) {
  float a = 17.625, b = 243.04;
  float g = (a * t / (b + t)) + log(rh / 100.0);
  return (b * g) / (a - g);
}

float heatIndex(float t, float rh) {
  return -8.784695
    + 1.61139411 * t
    + 2.338549   * rh
    - 0.14611605 * t  * rh
    - 0.01230809 * t  * t
    - 0.01642483 * rh * rh
    + 0.00221173 * t  * t  * rh
    + 0.00072546 * t  * rh * rh
    - 0.00000358 * t  * t  * rh * rh;
}

void setup() {
  Serial.begin(9600);
  dht.begin();
}

void loop() {
  delay(2000);

  float h = dht.readHumidity();
  float t = dht.readTemperature();

  if (isnan(h) || isnan(t)) {
    Serial.println("{\"error\":true}");
    return;
  }

  float dp = dewPoint(t, h);
  float hi = heatIndex(t, h);

  Serial.print("{\"t\":");  Serial.print(t,  1);
  Serial.print(",\"h\":");  Serial.print(h,  1);
  Serial.print(",\"dp\":"); Serial.print(dp, 1);
  Serial.print(",\"hi\":"); Serial.print(hi, 1);
  Serial.println("}");
}