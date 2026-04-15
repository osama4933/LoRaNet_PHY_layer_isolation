#include <SPI.h>
#include <RH_RF95.h>

RH_RF95 rf95(8, 3); // Adafruit Feather M0 with RFM95
//RH_RF95 rf95;
uint16_t lambda = 1;    // transmissions a sec
uint16_t tx_time = 10;  // time in seconds

uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
uint8_t len = sizeof(buf);

void setup()
{
  Serial.begin(9600);

  if (!rf95.init())
    Serial.println("init failed");

  pinMode(LED_BUILTIN, OUTPUT);

  rf95.setTxPower(23, false);
  rf95.setSpreadingFactor(8);
  rf95.setFrequency(915);
  rf95.setSignalBandwidth(125000);
  rf95.setSyncWord(0x12);             // Set SYNC WORD Here

  Serial.println("Sending to rf95_server");
  delay(2000);
}

void loop() {
  for (int i = 1; i < 11; i++) {
    delay(300);
    digitalWrite(LED_BUILTIN, HIGH);
    uint8_t data3[5];                    // <= Beacon
    data3[0] = i & 0xFF;
    data3[1] = lambda >> 0x8;
    data3[2] = lambda & 0xFF;
    data3[3] = tx_time >> 0x8;
    data3[4] = tx_time & 0xFF;

    rf95.send(data3, sizeof(data3));
    rf95.waitPacketSent();
    digitalWrite(LED_BUILTIN, LOW);

    if (rf95.available()) {
      if (rf95.recv(buf, &len)) {
        String rx_m = (char*)buf;
        Serial.println(buf[0]);
      } else {
        Serial.println("node missed");
      }
    }
  }
  //  delay(1500);
  //  uint8_t data4[] = "Rst";                      // <= Reset Beacon
  //  rf95.send(data4, sizeof(data4));
  //  rf95.waitPacketSent();
  //  delay(100);
  //  rf95.send(data4, sizeof(data4));              // <= Make sure all nodes reset
  //  rf95.waitPacketSent();
  //  delay(100);
  //  rf95.send(data4, sizeof(data4));              // <= Really make sure all nodes reset
  //  rf95.waitPacketSent();
  while (true)
    delay(1000);
}
