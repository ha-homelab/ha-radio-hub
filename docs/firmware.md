# Прошивка и программная часть

Основная сборка использует Raspberry Pi 4 с Linux, два независимых USB-радио и Waveshare **ESP32-S3-ETH-M** с 16 MB flash. На S3 работают Ethernet, Bluetooth proxy, LD2450, BME680 и UART-прокси существующего Zooz ZAC93. Отдельная вторая S3-ETH-M с CC1101 обслуживает проводной RF Airbridge; прежний ESP8266 сохраняется для отката. Все платы питаются от общей PoE-системы. Перенос частной конфигурации и HA registry выполняется отдельно по инструкции миграции.

## Что действительно проверено

- Основной `hub-s3-eth.yaml`: schema validation и полная компиляция ESPHome **2026.9.1**, ESP-IDF **5.5.5**, успешны. Статическая RAM 104 319 / 341 760 байт (30,5%); программа 942 199 байт. Это не измерение свободной памяти при работе BLE.
- RF Ethernet: schema validation и полная компиляция **реально импортированного fixture с 15 legacy binary sensors**, отдельными source/topics и RM433 slot прошли на ESPHome **2026.9.1** / ESP-IDF **5.5.5**. Статическая RAM 72 991 / 341 760 байт (21,4%); программа 699 707 байт. Пустой публичный шаблон также собран. Прошли 42 RF/migration regression-теста с ASan/UBSan. Это подтверждает программный порт и merge конфигурации, но реальные домашние файлы и плата не использовались; waveform/RX→TX→RX и физический cutover остаются отдельным этапом. Подробнее — [журнал validation](validation.md).
- `software/render_config.py`: тесты ограничений входных данных и конфигурации прошли; Docker Compose разобрал конфигурацию успешно.
- Ни одна реальная плата не прошивалась. Электрические соединения, совместная работа радиосетей, тепловой режим и долговременная стабильность требуют стенда.
- Docker daemon недоступен на машине разработки: запуск контейнеров, загрузка драйверов Linux и связь с RCP локально не проверялись. ARM-сборка Thread RCP локально не выполнялась; закреплённая прошивка PCA10059 успешно собрана в [Linux GitHub CI](https://github.com/ha-homelab/ha-radio-hub/actions/runs/38992347499). Радиосвязь этим тестом не проверяется.

## 1. Основной ESP32-S3

Используйте именно S3-ETH-M, без камеры и без карты microSD: GPIO4/5 и GPIO1/2/17/18 заняты этими периферийными разъёмами в других вариантах платы. Pin map соответствует [Waveshare](https://www.waveshare.com/wiki/ESP32-S3-ETH) и [Ethernet ESPHome](https://esphome.io/components/ethernet/).

- W5500 уже распаян: SCLK13, MOSI11, MISO12, CS14, IRQ10, RESET9.
- ZAC93: S3 GPIO17 TX → ZAC93 pin 8 RX; S3 GPIO18 RX ← ZAC93 pin 10 TX; 3V3 → pin 1; GND → pin 6. Скорость 115200 8N1. Не подавайте 5 V на ZAC93.
- LD2450: S3 GPIO4 TX → radar RX; S3 GPIO5 RX ← radar TX; питание radar 5 V и общая земля. UART 256000 8N1, логические уровни 3,3 V.
- BME680: SDA GPIO1, SCL GPIO2, 3V3 и GND. По умолчанию адрес Adafruit STEMMA QT **0x77**; для платы с другим адресом измените `bme680_address`.

Python-окружение создаётся из корня репозитория:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r firmware/requirements.txt
python firmware/validate.py --compile
```

Последняя команда использует одноразовые ключи во временном каталоге и удаляет тестовый бинарный файл. Для своей прошивки создайте локальные секреты:

```sh
cp firmware/secrets.example.yaml firmware/secrets.yaml
openssl rand -base64 32
openssl rand -hex 24
```

Поместите первый результат в `api_encryption_key`, второй — в `ota_password` файла `firmware/secrets.yaml`. Не добавляйте его в Git. API-ключ потребуется ESPHome-интеграции и Z-Wave JS. Соберите свою прошивку:

```sh
esphome config firmware/hub-s3-eth.yaml
esphome compile firmware/hub-s3-eth.yaml
```

Перед первой прошивкой отключите питание PoE и периферию. Подключите USB data к компьютеру; при необходимости удерживайте BOOT при нажатии RESET. Выберите фактический serial-порт в команде `esphome upload firmware/hub-s3-eth.yaml --device PORT`. После прошивки отключите USB, подключите периферию по схеме и подайте штатное питание. Не соединяйте независимые источники 5 V без развязки.

Последующие обновления: `esphome upload firmware/hub-s3-eth.yaml --device ha-radio-hub-sensors.local`; при недоступном mDNS используйте зарезервированный DHCP-адрес. Логи: `esphome logs firmware/hub-s3-eth.yaml --device ha-radio-hub-sensors.local`. Конфигурация не включает Wi-Fi fallback: Ethernet требуется для API и OTA.

У LD2450 в [ESPHome](https://esphome.io/components/sensor/ld2450/) доступны координаты трёх целей и датчики присутствия. Начните с проверки одного человека перед открытой платой. Отключите собственный Bluetooth радара через его диагностический switch после настройки, если он не нужен. Это не отключает Bluetooth proxy ESP32. LD2450 не следует считать гарантированным детектором полностью неподвижного человека во всех условиях.

[BME680](https://esphome.io/components/sensor/bme680/) публикует температуру, давление, влажность и **сопротивление газа** раз в 60 секунд. Здесь нет расчётного CO₂, VOC ppm или обещания калиброванного IAQ. Размещайте датчик в вентилируемом боковом отсеке, удалённом от Pi и преобразователей. Пакет `firmware/packages/bme680.yaml` можно отключить до установки датчика. На I²C расширении используйте 3,3 V, короткий кабель до 20 см и проверьте суммарные pull-up: параллельное добавление плат с подтяжками снижает сопротивление. Не подключайте устройства с подтяжками к 5 V.

## 2. Thread RCP: Nordic PCA10059

Это отдельное USB-радио, не BLE proxy и не Zigbee-координатор. OTBR исполняется на Linux Pi; RCP предоставляет ему IEEE 802.15.4. Выбран прозрачный официальный путь [OpenThread nRF52840](https://github.com/openthread/ot-nrf528xx/blob/1ff0a4905e436eb79605582f36b689063b1282ef/src/nrf52840/README.md) с USB bootloader. Этот upstream рекомендует nRF Connect SDK для новых коммерческих продуктов; выбранная legacy-платформа здесь служит воспроизводимым DIY-прототипом.

Установите Arm GNU toolchain с `arm-none-eabi-gcc`, CMake, Ninja, Git и зависимости upstream. Затем:

```sh
bash firmware/build-thread-rcp.sh
```

Скрипт фиксирует Git SHA и submodules, собирает USB RCP с `-DOT_BOOTLOADER=USB`, создаёт `.build/thread-rcp/ot-rcp-pca10059.hex`. Инструменты и системные зависимости не зафиксированы побитово; это source pin, а не заявленная бит-в-бит воспроизводимость.

Прошейте HEX через **nRF Connect for Desktop → Programmer**, выбрав именно PCA10059. Нажмите RESET донгла, чтобы войти в штатный USB bootloader. Используйте запись application, сохраните bootloader; не используйте erase-all. Подробности — [Nordic Programmer](https://docs.nordicsemi.com/r/bundle/nrf-connect-for-desktop/page/app/pc-nrfconnect-programmer/programming_nrf52840_dongle.html/programming-nrf52840-dongle). После перезагрузки на Pi должен появиться USB CDC ACM serial-порт. Найдите его стабильное имя `ls -l /dev/serial/by-id/`; после смены прошивки USB-имя может измениться. Зафиксируйте именно имя рабочей RCP-прошивки.

Если образ не устанавливается или RCP не отвечает, не меняйте случайно Zigbee-радио. Для стенда допустима замена на другой документированный USB Thread RCP, но потребуется проверить скорость, flow control и OpenThread RCP API compatibility. Nordic USB CDC в предоставленном compose использует URL с 1000000 baud и без hardware flow control.

## 3. Zigbee MG24

Используйте SMLIGHT **SLZB-07Mg24** со штатной **Zigbee coordinator / Ember NCP** прошивкой. Сохраните информацию о её версии перед изменениями. Не устанавливайте Thread/multiprotocol прошивку на этот же экземпляр. Перепрошивка нового исправного Zigbee-адаптера не обязательна; обновление выполняется официальным инструментом SMLIGHT для точной модели.

В `ser2net` на стороне Pi включены **115200 8N1 и RTS/CTS**, как для SLZB-07/MGx в [настройках SMLIGHT](https://smlight.tech/support/manuals/books/slzb-07pxmgx/page/zigbee2mqtt-setup). Это управление USB UART между Pi и адаптером; переключатель flow control у удалённого TCP-клиента не заменяет эту настройку. Если производитель изменит UART профиль в новой прошивке, измените renderer и ZHA согласованно. Для другого семейства адаптера настройки требуют отдельной проверки.

## 4. Linux-сервисы на Pi

Установите 64-битный Raspberry Pi OS Lite/Debian, Docker Engine и Compose plugin по [официальному руководству Docker](https://docs.docker.com/engine/install/debian/). Pi — отдельный прибор, Home Assistant продолжает работать на существующем сервере. Подключите оба USB-радио и внутренний Ethernet. Зарезервируйте DHCP-адреса Pi и ESP32. На первом стенде HA, Pi, ESP32 и телефон разместите в одном LAN с рабочим IPv6 и multicast.

Скопируйте репозиторий на Pi. Команда ниже содержит исключительно адреса TEST-NET для примера — замените их, а также USB symlink:

```sh
python3 software/render_config.py \
  --hub-ip 192.0.2.10 --ha-ip 192.0.2.20 --interface eth0 \
  --thread-device /dev/serial/by-id/usb-Thread_REPLACE \
  --zigbee-device /dev/serial/by-id/usb-SMLIGHT_REPLACE
docker compose --env-file software/runtime/hub.env -f software/compose.yaml config --quiet
```

Renderer только создаёт локальные файлы. Он отказывает при одинаковом Thread/Zigbee device, wildcard IP, нестабильном `/dev/ttyUSB0` и недопустимых символах. `--ha-ip` должен быть адресом источника соединений HA **как его видит Pi**, что важно при контейнерах/NAT. Для HA с несколькими адресами добавляйте в allow-list только нужные источники после сетевой проверки.

Теперь примените настройки на **Pi**, не на рабочем компьютере:

```sh
sudo install -m 644 software/runtime/60-ha-radio-hub.conf /etc/sysctl.d/60-ha-radio-hub.conf
sudo sysctl --system
docker compose --env-file software/runtime/hub.env -f software/compose.yaml up -d --build
docker compose --env-file software/runtime/hub.env -f software/compose.yaml logs --tail 100
```

Sysctl включает IP forwarding и приём IPv6 RA/RIO, следуя [OpenThread setup-host](https://github.com/openthread/ot-br-posix/blob/f064121702b7c2a9f7bf853ca39167c26ee11ec9/etc/docker/border-router/setup-host). OTBR использует host networking, NET_ADMIN и TUN для маршрутизации; его штатный entrypoint также меняет правила forwarding/NAT. Поэтому это конфигурация выделенного Pi, а не безусловный install script для существующего маршрутизатора.

`software/versions.json` хранит source/image pins. OTBR REST API слушает только LAN IPv4 Pi:8081, локальный web UI — 127.0.0.1:8080. `ser2net` слушает Pi:6638 и разрешает один клиент с адреса HA. **REST API OTBR не имеет встроенной авторизации**: в firewall/ACL разрешите TCP8081 только HA и выбранному администратору; TCP6638 — HA. ESPHome API6053 и OTA3232 разрешите от HA/администраторского компьютера. Не открывайте эти порты в интернет. Не блокируйте IPv6 ICMP, multicast, mDNS и Thread-routing между разрешёнными устройствами; простой проброс IPv4 портов не заменяет эту связность.

Проверка: OTBR log содержит успешный Spinel handshake и RCP version; `docker compose ... exec otbr ot-ctl state` возвращает Thread state. До создания/подключения сети состояние disabled/detached допустимо. Доступность `http://PI_IP:8081/node` проверяется с HA-хоста. Команда `curl` сама по себе не доказывает, что Matter commissioning работает.

**Только для новой сети**, если в доме ещё нет предпочитаемой Thread-сети:

```sh
docker compose --env-file software/runtime/hub.env -f software/compose.yaml exec otbr ot-ctl dataset init new
docker compose --env-file software/runtime/hub.env -f software/compose.yaml exec otbr ot-ctl dataset networkname HaRadioHub
docker compose --env-file software/runtime/hub.env -f software/compose.yaml exec otbr ot-ctl dataset channel 25
docker compose --env-file software/runtime/hub.env -f software/compose.yaml exec otbr ot-ctl dataset commit active
docker compose --env-file software/runtime/hub.env -f software/compose.yaml exec otbr ot-ctl ifconfig up
docker compose --env-file software/runtime/hub.env -f software/compose.yaml exec otbr ot-ctl thread start
```

Канал 25 — начальная настройка, проверьте его относительно своего Wi-Fi/Zigbee. Не выполняйте `dataset init new` поверх уже выбранной домашней сети: сначала сохраните её credentials и импортируйте существующий dataset. Файлы dataset содержат сетевые ключи. Резервируйте Docker volume `otbr-data` и Z-Wave/Zigbee network backups в приватном хранилище; `docker compose down -v` удаляет состояние OTBR.

## 5. RF Airbridge по Ethernet

`firmware/rf-ethernet.yaml` использует отдельную **вторую S3-ETH-M** с CC1101, MQTT и native API. Сохраняются `rf/received`, `rf/received/raw`, `rf/transmit/result`, RM433 button events, `send_rf_code` и `send_dooya_code`, single worker с `busy` и 750-мс cooldown. Частные source/topics/codes и старые определения датчиков импортируются в локальный wrapper; публичный шаблон их не содержит.

RF SPI3: SCLK7, MOSI8, MISO6, CS15; GPIO4 TX → GDO0 **open-drain с внешней подтяжкой 4.7 кОм к 3,3 В**, GDO2 → GPIO5 RX. W5500 остаётся на GPIO9–14. Это отдельная RF-плата: соединение не применяется к основному S3 с LD2450. Локальный RMT receiver patch соответствует ESPHome 2026.9.1 и обеспечивает управление захватом вокруг TX; работа со штатным ESP8266 patch не предполагается.

```sh
python firmware/validate.py --config rf-ethernet.yaml
python firmware/validate.py --config rf-ethernet.yaml --migration-fixture --compile
```

Первая команда проверяет публичный шаблон, вторая запускает настоящий импортёр на синтетической конфигурации с 15 датчиками и полностью компилирует результат. Используются одноразовые секреты, ничего не прошивается. Для замены установленного узла сначала выполните [офлайн-перенос, стенд, cutover и rollback](../hardware/rf-migration.md). Сохранение `esphome.name` и API key не гарантирует прежний HA device ID/unique ID: у Ethernet-платы другой MAC. Требуются приватное сопоставление сущностей и проверка device triggers. Старый ESP8266 остаётся выключенным резервом после перехода.
