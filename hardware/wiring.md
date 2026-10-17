# Соединения ревизии A

[Машиночитаемый список сигналов](wiring.csv). Список задаёт **имена сигналов**, а не вид разъёма спереди: обратная сторона платы зеркальна. Перед монтажом сверить маркировку и [схему Waveshare](https://files.waveshare.com/wiki/ESP32-S3-ETH/ESP32-S3-ETH-Schematic.pdf). GPIO — номер ESP32, не номер контакта Pico header.

## Ethernet и USB

- Внешний PoE кабель → вход splitter. Ethernet out splitter → port 1 TL-SF1005D v13.
- Port 2 switch → RJ45 Pi 4; port 3 → RJ45 ESP32-S3-ETH. Ports 4–5 оставлены для расширения, в том числе отдельной проводной RF платы.
- Pi USB 2.0 → короткий экранированный USB удлинитель → SLZB-07Mg24 (Zigbee).
- Второй Pi USB 2.0 → короткий удлинитель → Nordic PCA10059 (Thread).
- 5 V распределение → Pi USB-C, switch DC input, S3 USB-C, NodeMCU micro-USB и LD2450 5V. Выход splitter только 5 V; проверить точный размер/полярность DC штекера switch по своему экземпляру. Не полагаться на совпадение наружного диаметра.

У S3 плата **ESP32-S3-ETH-M**, 16 MB flash + 8 MB PSRAM, без камеры, карты microSD и дополнительного PoE модуля. Задействованы аппаратные UART; это исключает общую загрузку bit-bang UART с BLE.

## Встроенный W5500

Эти цепи уже на плате, их не нужно соединять проводами: SCLK GPIO13, MOSI GPIO11, MISO GPIO12, CS GPIO14, INT GPIO10, RESET GPIO9. GPIO19/20 заняты native USB; GPIO21 — RGB LED. Эти контакты не используются как expansion.

## ZAC93

Проверить ревизию и маркировку модуля. [Zooz manual](https://www.getzooz.com/downloads/zooz-z-wave-800-series-long-range-gpio-module-zac93-LR-manual.pdf) задаёт **3.3 V DC**. На совместимом 2×5 header:

- ZAC93 pin 1 `3V3` ← S3 `3V3`.
- ZAC93 pin 6 `GND` ↔ S3 GND; pin 9 тоже земля.
- ZAC93 pin 8 `RX` ← S3 GPIO17 TX.
- ZAC93 pin 10 `TX` → S3 GPIO18 RX.
- Остальные пины не подключаются. У hardware v2 pin 7 является reset, у старой ревизии обозначался PC01. Не повторять чужой reset circuit без проверки ревизии.

UART 115200, 8N1. Логика 3.3 V; MAX232/RS232 уровни сюда не подходят. Это перенос самой ZAC93 с прежней ESP32 платы; прежняя ESP32 прошивка остаётся вариантом отката. До переноса сохранить Z-Wave NVM/ключи приватно и остановить прежнего владельца serial/controller. Один контроллер не должен одновременно обслуживаться двумя Z-Wave серверами.

## LD2450

Использовать коннектор, поставляемый с **HLK-LD2450**, а не кабель от LD2410. Распиновку читать с самого модуля:

- `5V` ← отдельная защищённая 5 V ветвь.
- `GND` ↔ общая земля S3.
- `TX` → S3 GPIO5 RX.
- `RX` ← S3 GPIO4 TX.

UART 256000, 8N1, уровни 3.3 V. GPIO4/5 соединены также со слотом microSD, поэтому **карта microSD должна отсутствовать**. Камера также отсутствует. Минимальная версия radar firmware для ESPHome — V2.02.23090617 согласно [ESPHome](https://esphome.io/components/sensor/ld2450/).

## BME680 и I²C expansion

Выбрана Adafruit BME680 STEMMA QT, product 3660. Разъём JST-SH 4-pin/1.0 mm подключается коротким breakout кабелем; порядок смотреть по маркировке производителя, не «на глаз»:

- VIN/V+ → S3 **3V3**.
- GND → S3 GND.
- SDA/SDI → S3 GPIO1.
- SCL/SCK → S3 GPIO2.

I²C 100 kHz. Адрес Adafruit по умолчанию **0x77**; `SDO→GND` переключает в 0x76. На breakout уже есть подтяжки; при нескольких модулях проверить их параллельное сопротивление. GPIO1/2 разделены с камерой, поэтому подключение камеры исключено. Длина I²C жгута — первоначально 10–20 cm; большее расстояние требует проверки фронтов/ёмкости или дифференциального I²C extender, не просто длинного кабеля.

Второй STEMMA QT разъём можно использовать для ещё одного **3.3 V-compatible** I²C датчика с другим адресом. Свободный адрес не означает гарантированный запас питания. В готовой прошивке подключён BME680; дополнительные сенсоры требуют явного компонента ESPHome. Не подключать hot-plug, 5 V pull-ups, длинные уличные провода или сильные нагрузки на этот разъём.

## RF Airbridge — исходная плата

Существующий NodeMCU v2/ESP8266 сохранён с CC1101 433.92 MHz. По публичному проекту [RF Airbridge](https://github.com/ha-homelab/rf-airbridge): SCLK GPIO14/D5, MOSI GPIO13/D7, MISO GPIO12/D6, CS GPIO15/D8, GDO0 GPIO4/D2, VCC 3V3, GND общий. GDO0 общий для RX/TX, радио полудуплексное. GDO2 не используется. Питание NodeMCU 5 V через micro-USB; CC1101 получает 3.3 V от своей NodeMCU, не соединять его 3V3 с выходом S3 регулятора.

Сеть этой исходной платы — Wi-Fi. Наличие внутреннего Ethernet switch само по себе не меняет транспорт ESP8266. Реальные RF коды, MAC/IP, ключи и Wi-Fi учётные данные в публичный проект не переносятся.

## RF Ethernet — экспериментальная замена NodeMCU

Вторая ESP32-S3-ETH-M получает отдельные 5 V и Ethernet port 4. Основная плата с BME680/ZAC93/LD2450 не используется для этих соединений. Карта новой прошивки: CLK GPIO7, MOSI GPIO8, MISO GPIO6, CS GPIO15; **GPIO4 TX → GDO0**, **GDO2 → GPIO5 RX**; CC1101 VCC3V3/GND. MicroSD и камера отсутствуют. GDO0/GDO2 разделены намеренно, это не существующая однопроводная распиновка NodeMCU. Если у модуля GDO2 не выведен, сначала выбрать подходящий модуль/пайку по его схеме; не подставлять другую площадку.

Проверить нагрузку общего питания с этой веткой по [power.md](power.md). Перенос private RF codes и identities не выполняется автоматически. Прототип не выдаётся за проверенный на устройстве полный перенос прежнего RF Airbridge.

## Локальные настройки Zigbee USB

Для SLZB-07Mg24 исходный профиль — 115200 baud, 8N1 и hardware RTS/CTS. [SMLIGHT setup](https://smlight.tech/support/manuals/books/slzb-07pxmgx/page/zigbee2mqtt-setup) указывает RTS/CTS для SLZB-07/MGx; [benchmark](https://smlight.tech/blog/zigbee-over-ethernet-vs-usb-latency-test) использует 115200. Проверить по установленной версии NCP; значение на стороне ZHA TCP не меняет настройки физического UART в ser2net на Pi. Для изменённой прошивки UART параметры должны быть обновлены именно на Pi.
