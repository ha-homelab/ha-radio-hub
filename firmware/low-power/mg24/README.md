# MGM240P Zigbee NCP — воспроизводимая сборка для LP-P0

**Сборка и офлайн-проверки прошли 2026-10-17 на macOS arm64. На физическом MGM240P прошивка ещё не проверена.** Получены приложение Ember NCP, UART-XMODEM загрузчик с CRC, GBL3 для обновления приложения и объединённый S37 для первоначальной записи через SWD. Это закрывает программную сборку образа; запуск, UART/CTS, pairing, восстановление питания и радиосовместимость остаются аппаратными проверками.

Точный order code — **MGM240PA22VNA3**, SLC target — **MGM240PA22VNA**. Не подменять его произвольным EFR32MG24 target: компонент модуля включает его настройки питания/PA и встроенный HFXO **39 MHz**. В созданной конфигурации `SL_CLOCK_MANAGER_LFXO_EN=0`, источник LF — внутренний LFRCO; внешний 32,768 kHz кварц не требуется.

## Зафиксированные исходники и инструменты

- [Simplicity SDK v2025.6.3](https://github.com/SiliconLabs/simplicity_sdk/releases/tag/v2025.6.3), commit `b41bec3ff2485199c1a5a9995b3e649e118c1b8d`: Zigbee **8.2.3**, EZSP **18 / 0x12**. [Официальный состав версии](https://docs.silabs.com/sisdk-release-notes/2025.6.3/sisdk-release-notes-overview/).
- SLC **6.0.15**, Java **21**, Arm GNU Toolchain **12.2.Rel1** / GCC **12.2.1**, Simplicity Commander **1.25.0 build1995**. IAR, платная лицензия и авторизация в Silicon Labs для выполненной сборки не использовались.
- Приложение: SDK `protocol/zigbee/app/projects/ncp/zigbee_ncp_uart_hw/zigbee_ncp_uart_hw.slcp`; загрузчик: `platform/bootloader/sample-apps/bootloader-uart-xmodem/bootloader-uart-xmodem.slcp`.
- [config.json](config.json) — target, upstream paths и все изменённые макросы; [dependencies-linux.json](dependencies-linux.json) — прямые официальные URL, размеры и SHA256 архивов Linux x86_64. Эти четыре архива фактически скачаны и проверены; суммарно **862 218 788 bytes**. Linux runner отдельно должен подтвердить исполняемость инструментов.

Bootstrap проверяет SHA256 скачанного SDK-архива. При ручном `--sdk` генератор проверяет фактические `sdk_version` и `EZSP_PROTOCOL_VERSION`, но не удостоверяет Git commit всего распакованного дерева: в отчёте `source_commit_verified=false`, ожидаемый commit указан отдельно. SDK и сгенерированные vendor sources не включены в репозиторий; они загружаются отдельно со своими лицензиями. Здесь хранятся настройки, скрипты и [отчёт выполненной сборки](build-evidence.json). Хеши отчёта относятся к указанной macOS сборке, а не являются обещанием идентичных байтов на всех хостах.

## Электрический контракт

Оба образа используют USART0, **115200, 8N1, hardware RTS/CTS**:

- PA05 / module pad12 — NCP RX ← S3 GPIO17 TX.
- PA06 / pad13 — NCP TX → S3 GPIO18 RX.
- PB01 / pad5 — NCP CTS ← S3 GPIO16 RTS.
- PB00 / pad6 — NCP RTS → S3 GPIO21 CTS.
- **PA00 / pad7 — BOOT**, только сервисная перемычка/кнопка к GND, штатно **10 kΩ к 3,3 V**. Удержание LOW во время reset выбирает UART-XMODEM загрузчик. Этот сигнал не занимает S3 GPIO.
- PA01 / pad8 — SWCLK; PA02 / pad9 — SWDIO; RESETn / pad31 — reset; дополнительно GND и VTref. RESETn уже имеет внутреннюю подтяжку к DVDD: внешний сервисный контакт только замыкает его на GND, **не ставить pull-up к 3,3 V**.

[Первичный datasheet MGM240P](https://www.silabs.com/documents/public/data-sheets/mgm240p-datasheet.pdf) определяет питание, остальные GND и RF keepout. Не подключать 5 V UART. USB-UART не заменяет SWD для первого пустого модуля.

## Linux CI / локальная сборка

Нужны Linux x86_64, Python3, Java21, `make`, `unzip`, `tar` с xz/bzip2 и runtime-библиотеки Commander. Bootstrap скачивает только зафиксированные архивы, проверяет размер/SHA256 перед распаковкой и требует новый каталог. Он ничего не прошивает и не устанавливает системно. На headless runner можно задать `QT_QPA_PLATFORM=offscreen`.

Из корня репозитория:

```sh
python3 firmware/low-power/mg24/bootstrap_linux.py --output /tmp/mg24-tools
python3 firmware/low-power/mg24/generate.py \
  --sdk /tmp/mg24-tools/sdk \
  --slc /tmp/mg24-tools/tools/slc_cli/slc \
  --gcc /tmp/mg24-tools/tools/arm-gnu-toolchain-12.2.rel1-x86_64-arm-none-eabi \
  --output /tmp/mg24-build
python3 firmware/low-power/mg24/build.py \
  --project /tmp/mg24-build \
  --gcc /tmp/mg24-tools/tools/arm-gnu-toolchain-12.2.rel1-x86_64-arm-none-eabi \
  --commander /tmp/mg24-tools/tools/commander/commander
python3 -m unittest discover -s firmware/low-power/mg24 -p 'test_*.py'
```

`JAVA_HOME` должен указывать на Java21; при необходимости передать `--java-home` в `generate.py`. Для macOS установить те же версии через [публичный SLT CLI](https://docs.silabs.com/simplicity-installer-slt/latest/slt-getting-started-slt-cli/first-time-installation-setup), либо использовать официальные архивы той же платформы; затем передать абсолютные пути SLC/GCC/Commander. Это тот же генератор, а не другой проект.

SLC `--configuration` меняет активные макросы, но не раскрывает закомментированные pin-tool placeholders. Поэтому `generate.py` после генерации явно задаёт каждый макрос в созданных заголовках и требует ровно одно совпадение. Изменения помечены; SDK не редактируется. `build.py` повторно сверяет активные GPIO/USART/flow-control/clock macros до компиляции. Перегенерацию делать тем же скриптом в новый каталог, иначе pin-tool способен вернуть пустые назначения.

`build.py` запускает штатные `make release` обоих проектов. Commander выполняет официальный bootloader post-build (CRC), создаёт GBL3, объединяет адресованные S37 и распаковывает GBL обратно для проверки. Проверяются S-record checksum, диапазоны flash, отсутствие пересечений, stack/reset vectors, точное сохранение байтов в merged image и GBL roundtrip. Получается `artifacts/build-report.json` с SHA256. Отдельные тесты проверяют повреждённые записи, несовпадения и отсутствующие/дублированные макросы.

## Результат и порядок программирования

[Выполненная сборка](build-evidence.json): NCP **224 852 bytes** адресованных данных; загрузчик с CRC **11 272 bytes**. Приложение начинается с `0x08006000`, загрузчик — с `0x08000000` и целиком помещается в зарезервированные 24 KiB. `size` включает резерв heap/stack в BSS, поэтому его сумму нельзя выдавать за фактическое рабочее потребление RAM.

- `artifacts/ha-radio-hub-mg24-initial.s37` — загрузчик с CRC + приложение, первоначальная запись через совместимый SWD probe.
- `artifacts/ha-radio-hub-mg24-ncp.gbl` — только приложение для последующего UART-XMODEM обновления; не заменяет отсутствующий загрузчик.
- `bootloader/artifact/bootloader-uart-xmodem-crc.s37` — отдельный загрузчик. Использовать CRC-вариант, а не промежуточный `build/release/*.s37`.

На стенде сначала проверить 3,3 V, общий GND, SWD и точную модель. После этого оператор может записать адресованный initial S37 через Commander и проверить запись штатной командой `verify`; не менять debug-lock, OTP/eFuse или security configuration. Скрипты этого каталога **никогда не выполняют flash/erase**. После снятия BOOT-перемычки выполнить reset, затем проверить ASH reset/version response и только после этого подключать ZHA. Для сервисного XMODEM обновления закрыть клиента Zigbee, удерживать PA00 LOW при reset и использовать документированное меню загрузчика; поддержка upload через наш TCP-мост отдельно не реализована/не испытана.

Следующие команды сверены с `Commander1.25.0 --help`, но **на устройстве не выполнялись**. `PROBE_SERIAL` — серийный номер выбранного J-Link/Silicon Labs probe, не USB-UART. Сначала отдельно выполнить только чтение идентификации:

```sh
COMMANDER=/tmp/mg24-tools/tools/commander/commander
PROBE_SERIAL=REPLACE_WITH_ACTUAL_PROBE_SERIAL
"$COMMANDER" device info --serialno "$PROBE_SERIAL" --tif SWD
```

Сгенерированный header задаёт `PART_NUMBER="MGM240PA22VNA"`, flash `0x180000` (1536 KiB), SRAM `0x40000` (256 KiB). Autodetection может назвать underlying silicon вместо order code модуля; сопоставить отчёт с маркировкой/семейством и памятью, не форсировать неизвестный `--device`. Только после этой проверки для нового тестового модуля:

```sh
"$COMMANDER" flash /tmp/mg24-build/artifacts/ha-radio-hub-mg24-initial.s37 --serialno "$PROBE_SERIAL" --tif SWD
"$COMMANDER" verify /tmp/mg24-build/artifacts/ha-radio-hub-mg24-initial.s37 --serialno "$PROBE_SERIAL" --tif SWD
```

S37 уже содержит адреса. `--address`, `--masserase`, `--force` и отключение проверки здесь не нужны.

Не стирать NVM действующего координатора без резервной копии: этот путь пока предназначен для нового тестового модуля. GBL/bootloader здесь не подписаны ключом secure boot; настройка ключей и необратимых lock-битов не входит в прототип.

## Совместимость хостов — проверка кода, не pairing

- **ZHA**: EZSP18 добавлен в [bellows0.49.0](https://github.com/zigpy/bellows/releases/tag/0.49.0). Проверенный срез [Home Assistant2026.10.2](https://github.com/home-assistant/core/blob/2026.10.2/homeassistant/components/zha/manifest.json) использует ZHA2.3.1, который [фиксирует bellows1.1.0](https://github.com/zigpy/zha/blob/2.3.1/pyproject.toml). Он содержит обработчик EZSP18.
- **Zigbee2MQTT**: [2.14.2](https://github.com/Koenkk/zigbee2mqtt/blob/2.14.2/package.json) использует zigbee-herdsman10.10.0; [официальная документация `ember`](https://www.zigbee2mqtt.io/guide/adapters/emberznet.html) включает EmberZNet8.2.x. Выбирать **`adapter: ember`**, не устаревший `ezsp`.
- Один активный клиент TCP-моста на порт6638. ZHA и Z2M одновременно не подключать. Скорость/CTS/RTS реализует S3 UART; TCP не передаёт управляющие линии USB-UART.

Источники сборки: [SLC usage](https://docs.silabs.com/simplicity-studio-5-users-guide/latest/ss-5-users-guide-tools-slc-cli/03-usage), [Commander offline convert](https://docs.silabs.com/simplicity-commander/latest/simplicity-commander-commands/convert-and-modify-file-commands), upstream `readme.md` обоих примеров в зафиксированном SDK.
