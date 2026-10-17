# Подключение к Home Assistant

Прибор появляется в HA через стандартные интеграции. Логические сети остаются независимыми: Zigbee в ZHA, Thread через OTBR, Matter через Matter Server, Bluetooth и датчики через ESPHome, Z-Wave через существующий Z-Wave JS driver. Не нужен второй экземпляр Home Assistant на Pi.

## Zigbee

1. Сначала проверьте готовность `ser2net` и доступность Pi:6638 с HA-хоста. Один радиоадаптер обслуживает только один Zigbee stack: одновременно ZHA и Zigbee2MQTT не запускаются.
2. Settings → Devices & services → Add integration → **Zigbee Home Automation**. Выберите ручную настройку radio **EZSP/Ember (Silicon Labs)**, serial device path `socket://PI_IP:6638`, baud 115200. RTS/CTS для физического USB UART уже включён в `ser2net` на Pi. Формат `socket://` — не `tcp://` и не `http://`.
3. Для новой сети разрешите pairing и проверьте событие от одного тестового датчика. При переносе существующей ZHA-сети используйте её backup/migration, а не factory reset координатора.
4. Если нужен Zigbee2MQTT вместо ZHA: adapter `ember`, port `tcp://PI_IP:6638`; не используйте его параллельно с ZHA. Этот вариант в составе нового хаба ещё не проверен на железе.

[ZHA](https://www.home-assistant.io/integrations/zha/) поддерживает сетевые serial adapters, но стабильность зависит от LAN. Радио находится рядом с Pi, не рядом с HA-сервером. При firmware update координатора сначала остановите единственного клиента и `ser2net`; восстановите тот же Ember UART-профиль после обновления.

## Thread и Matter

В HA добавьте **OpenThread Border Router** с URL `http://PI_IP:8081`. Это [REST endpoint OTBR](https://www.home-assistant.io/integrations/otbr/), не web UI 8080. В интеграции **Thread** проверьте network name и preferred network; синхронизируйте Thread credentials с телефоном по [инструкции HA Thread](https://www.home-assistant.io/integrations/thread/). Для уже существующей сети используйте её credentials вместо создания второй сети с тем же именем.

На HA-сервере требуется **Matter Server**: OTBR его не заменяет. HA OS может установить официальный Matter Server app; для HA Container применяются отдельные [инструкции Matter Server](https://github.com/home-assistant-libs/python-matter-server). Подключите интеграцию Matter к тому же серверу, который уже обслуживает существующие Matter-устройства. Не создавайте новую fabric без причины.

Добавляйте Matter-over-Thread устройство из Companion app на телефоне, находясь рядом с новым устройством. Нужны QR/setup code, Bluetooth телефона, рабочая IPv6/multicast связность и правильный Thread dataset. **Bluetooth proxy ESPHome не заменяет Bluetooth телефона при Matter commissioning**. [HA Matter](https://www.home-assistant.io/integrations/matter/) описывает этот процесс и различие Matter/Thread: один логотип Thread не гарантирует поддержку Matter.

После включения одного устройства проверьте три вещи: состояние в HA меняется физически; отключение WAN не мешает локальному управлению; после перезапуска OTBR с сохранённым volume устройство возвращается без нового pairing. Для проверки независимости выключайте только один радиоузел за раз.

## Bluetooth, LD2450 и BME680

Добавьте **ESPHome**, узел `ha-radio-hub-sensors.local` или его DHCP reservation, и локальный API encryption key. HA получит координаты/количество целей LD2450, presence, uptime, температуру/влажность/давление/газовое сопротивление BME680. Назначьте датчикам комнату; entity IDs создаёт HA, не подставляйте заранее выдуманные IDs в автоматизации.

Добавьте **Bluetooth**, если его ещё нет. [ESPHome Bluetooth proxy](https://esphome.io/components/bluetooth_proxy/) передаёт BLE advertisements и предоставляет три одновременных активных GATT-соединения. BLE-устройства добавляются через свои интеграции (например, BTHome); proxy не делает совместимым произвольный Bluetooth Classic прибор. Число broadcast-датчиков не равно числу активных слотов.

Проверка LD2450: переместитесь слева направо и подтвердите изменение координат; отойдите и проверьте timeout. Presence не используйте как единственное условие отключения критичной нагрузки. Проверка BME680: сравните температуру/влажность с отдельным датчиком после прогрева и с закрытым корпусом; нагрев Pi не исправляется универсальным вычитанием нескольких градусов. Gas Resistance публикуется в омах, не в ppm.

## Z-Wave: перенос существующего ZAC93

Плата ZAC93 сохраняет существующую сеть при замене UART-host, если её память не стирается. Сначала сделайте backup NVM и ключей существующего Z-Wave JS, остановите его driver, обесточьте обе ESP32, перенесите четыре провода ZAC93 по схеме и запустите новый S3-ETH. У старого ESP32 больше не должно быть физического подключения к этому модулю.

В **существующем Z-Wave JS UI** замените Serial Port на `esphome://ha-radio-hub-sensors.local:6053?key=URL_ENCODED_API_KEY`, сохранив network keys. Получить корректно encoded URL можно локальной командой Python:

```sh
python3 -c 'from getpass import getpass; from urllib.parse import quote; print("esphome://ha-radio-hub-sensors.local:6053?key=" + quote(getpass("API key: "), safe=""))'
```

Результат содержит секрет; не публикуйте его в issue/log. Формат transport определён [Z-Wave JS](https://github.com/zwave-js/zwave-js/blob/master/docs/usage/esphome-connection.md). В поле WebSocket server интеграции HA остаётся адрес **Z-Wave JS server**, обычно `ws://ZWAVE_JS_HOST:3000`, а не ESP32:6053. Один driver подписывается на proxy. Отдельное подключение ESPHome-интеграции для BLE/датчиков нормально.

Подтвердите прежний Home ID, регион радио и список устройств; вызовите физическое событие известного Z-Wave-датчика. Не выполняйте exclusion/re-inclusion всех устройств для смены UART-host. Если новая комбинация нестабильна, остановите driver, верните модуль на старую ESP32 и верните её transport URL, сохранив те же сетевые ключи. Для нового пустого ZAC93 следуйте [проекту zac93-esp32](https://github.com/ha-homelab/zac93-esp32).

## RF

В базовой сборке существующая ESPHome-интеграция RF, MQTT topics и HA automations сохраняются. Проверьте настоящую кнопку RF-пульта, событие в HA и исполнительное устройство после переноса платы в новый корпус. USB data для NodeMCU не требуется при нормальной работе: это питание, а транспорт пока Wi-Fi.

Экспериментальный Ethernet RF-узел добавляется **отдельным** ESPHome device. Для `homeassistant.event` включите разрешение устройству выполнять действия HA в параметрах интеграции. В Developer Tools → Events слушайте `esphome.radio_hub_rf_received`. Его новые события не имеют старого RM433/MQTT-контракта; миграция описана в [руководстве firmware](firmware.md#5-сохранение-rf-и-переход-на-ethernet). Не оставляйте две автоматизации, одновременно передающие одну команду через старый и новый передатчики.
