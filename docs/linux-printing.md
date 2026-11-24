# Linux USB printing: installation, operation and monitoring

This guide covers the **original TRONXY XY-3**, an OctoPrint host on Debian
and the FH1 enclosure. Hostnames and SSH logins are placeholders. Use the
values from your private inventory.

## Contents

- [Current installation and acceptance limits](#current-installation-and-acceptance-limits)
- [Install a new Linux host](#install-a-new-linux-host)
- [Connect and identify the printer](#connect-and-identify-the-printer)
- [Prepare enclosure G-code](#prepare-enclosure-g-code)
- [Start an attended print](#start-an-attended-print)
- [Monitor and stop](#monitor-and-stop)
- [Diagnose filament delivery](#diagnose-filament-delivery)
- [Maintenance and recovery](#maintenance-and-recovery)

## Current installation and acceptance limits

The printer is connected by USB to **printer-host.example.invalid**, a Debian 12 Intel Atom x5-Z8350
host with approximately 4 GiB RAM. Ethernet reaches the home network through
an eero mesh node. Give one OctoPrint host exclusive use of the printer’s USB
serial port.

- Browser on the home LAN: **http://printer-host.example.invalid:5000/**.
- SSH: `ssh your-login@printer-host.example.invalid` using the operator's existing credentials.
- OctoPrint **1.11.8**, Python virtual environment `/opt/octoprint/venv`.
- Persistent configuration, accounts, uploads and logs: `/var/lib/octoprint`.
- systemd service: `octoprint`; unprivileged account: `octoprint`.
- Printer: original XY-3, nominal **310 × 310 × 330 mm**, heated bed,
  one **0.4 mm** nozzle, **1.75 mm PLA**, serial **115200 baud**.
- Observed USB bridge: CH340 `1a86:7523`, previously `/dev/ttyUSB0`.
- Observed persistent path:
  `/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0`.
- Actual firmware identification: `CBD make it`, dated Dec 10 2018 15:12:35.
  Official **Fix CBD Firmware 0.4.0** plugin installed; firmware not flashed.

The button finished from the printer's SD card. On 17 November 2026, the
same `Button.gcode` also finished through OctoPrint over USB. The operator observed normal PLA
deposition on the USB run, which finished in about 9½ minutes. This checks the
USB path and the button's footprint. A separate 5 mm extrusion test produced
silver PLA and pulled the marked filament forward by the expected distance.

The ZAC93 cradle covers a larger area. An earlier cradle attempt scored the
build sheet even though both files commanded a 0.35 mm first layer. After the
nozzle lifted, molten PLA emerged. Before another hot start, check the physical
clearance across the cradle's own footprint using the procedure below.
Cradle adhesion, dimensional fit and the large enclosure prints still need a
physical test. The operator supervises the first layer at the printer.

## Install a new Linux host

Skip this section on an already configured host. These commands target a
**fresh Debian 12 host with systemd and Python 3.11**, with administrative SSH
access. Other distributions need their own package names and compatibility
checks. Do not apply a Raspberry Pi OctoPi image to an x86 PC or Orange Pi.

### 1. Prepare the operating system and service account

On the Linux host, while no printer job is running:

```sh
sudo apt-get update
sudo apt-get install --yes python3 python3-venv python3-dev gcc libc6-dev usbutils ca-certificates
sudo useradd --system --user-group --create-home --home-dir /var/lib/octoprint --shell /usr/sbin/nologin octoprint
sudo usermod --append --groups dialout octoprint
sudo install -d -o octoprint -g octoprint -m 0750 /opt/octoprint /var/lib/octoprint
sudo -u octoprint python3 -m venv /opt/octoprint/venv
sudo -u octoprint /opt/octoprint/venv/bin/python -m pip install 'OctoPrint==1.11.8'
sudo -u octoprint /opt/octoprint/venv/bin/python -m pip check
sudo -u octoprint /opt/octoprint/venv/bin/octoprint --version
```

The account-creation command is for first installation only. If the account or
paths already exist, inspect the existing deployment instead of overwriting it.
The version pin reproduces this installation; it is not a claim that 1.11.8
will remain the latest or suitable indefinitely. Review upstream security and
Python compatibility before choosing another version.

### 2. Add a restricted system service

Use this self-contained unit on a new host. It listens on loopback initially,
so the first-run wizard is accessible through an SSH tunnel only.

```sh
sudo tee /etc/systemd/system/octoprint.service > /dev/null <<'UNIT'
[Unit]
Description=OctoPrint USB print host
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=octoprint
Group=octoprint
SupplementaryGroups=dialout
WorkingDirectory=/var/lib/octoprint
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/octoprint/venv/bin/octoprint --basedir /var/lib/octoprint serve --host 127.0.0.1 --port 5000
Restart=on-failure
RestartSec=5
TimeoutStopSec=30
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=true
ProtectSystem=full

[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload
sudo systemctl enable --now octoprint
systemctl status octoprint --no-pager
```

On the workstation, replace `USER` and `LINUX_HOST` with the actual SSH login
and host. This command stays running while the browser is in use:

```sh
ssh -N -L 15000:127.0.0.1:5000 USER@LINUX_HOST
```

Open **http://127.0.0.1:15000/** on the workstation. Complete the first-run wizard,
create a unique administrator login, retain access control and firmware checks,
and leave automatic printer connection disabled. Store passwords and API keys
outside Git. Do not seed an existing server with another host's config.yaml.

In **Settings → Printer Profiles**, create/select the original XY-3 profile:
rectangular bed, lower-left origin, 310 mm width, 310 mm depth, 330 mm height,
heated bed, one extruder and 0.4 mm nozzle. The slicer's separate filament
setting must be 1.75 mm. Confirm real machine travel before homing.

The tunnel is sufficient for normal use. For direct trusted-LAN access after
account setup, use `sudo systemctl edit octoprint`, clear `ExecStart=` and add
the same command with `--host` set to the host's **actual reserved LAN IPv4**.
Then reload systemd and restart only while idle. Restrict port 5000 to the
trusted LAN with the site's existing firewall policy; do not forward it on the
Internet router. Recheck browser login protection. Do not replace unrelated
firewall rules or assume LAN HTTP encrypts credentials.

### 3. Prevent the host from sleeping

On a dedicated print host:

```sh
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target suspend-then-hibernate.target
```

This affects the whole Linux machine. Keep host power, USB and networking
stable; do not reboot, upgrade packages or restart OctoPrint during printing.
A closed workstation browser does not stop the Linux host from streaming a job.

## Connect and identify the printer

1. Finish any SD print first. Leave heaters off. Power the printer normally;
   USB is the data connection, not a replacement for its power supply.
2. Attach a USB data cable matching the actual printer socket. Compare devices
   before and after attachment on Linux:

   ```sh
   lsusb
   ls -l /dev/serial/by-id/ /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
   id octoprint
   ```

3. Choose the actual printer port in OctoPrint and **115200** baud. Prefer the
   observed by-id path when available in the port list. If it is absent, add
   that exact path under additional serial ports in settings, then reconnect
   while idle. `/dev/ttyUSB0` can change or identify another device later.
   Identical CH340 adapters may not have unique serial numbers; inspect them
   rather than assuming the by-id name is globally unique.
4. Use only OctoPrint to own the port. Do not simultaneously open minicom,
   screen, a slicer serial monitor or another print server.
5. In the Terminal tab, inspect `M115` and `M105` responses. Confirm plausible
   ambient temperatures before heating. Opening a serial port may reset a
   controller, so connection experiments belong between jobs.

### Required CBD compatibility step

If `M115` identifies **CBD make it**, install **Fix CBD Firmware** using
**Settings → Plugin Manager → Get More**, then restart the idle OctoPrint
service and reconnect. The qualified local version is 0.4.0. An administrator
can alternatively install the exact reviewed source while the service is
stopped:

```sh
sudo systemctl stop octoprint
sudo -u octoprint /opt/octoprint/venv/bin/python -m pip install 'https://github.com/OctoPrint/OctoPrint-FixCBDFirmware/archive/153f46889c8aea2b33262310a6f79b6a8a3159fa.zip'
sudo -u octoprint /opt/octoprint/venv/bin/python -m pip check
sudo systemctl start octoprint
```

Do not issue **M27 while idle** on this controller: it previously returned
`It's not printing now!` and triggered OctoPrint's emergency-stop/disconnect
handling. Use the web interface and HTTP API for job status instead. Do not
silence firmware errors or disable thermal protections to force a connection.
A firmware replacement requires the actual controller-board revision and a
separate recovery plan; the printer model alone is insufficient.

## Prepare enclosure G-code

### First trial on the original XY-3

Prepare the **ZAC93 cradle by itself** on the workstation. The public
commissioning package includes a PrusaSlicer profile and instructions for
slicing the current `zwave-tray.stl`. Open the
[cradle slicing procedure](../mechanical/full-hub/commissioning/README.md).

1. Use the original XY-3's actual nozzle and spool. The profile is for a
   0.4 mm nozzle and 1.75 mm unfilled PLA. Keep the cradle floor on the bed
   at 100% scale. Follow the spool and sheet specifications for temperature.
2. Preview the first material-depositing move and the full first-layer
   footprint, including the skirt and brim if enabled. Compare their XY
   bounds with the usable sheet, clip positions and any damaged area.
3. With the machine cold, follow its established leveling procedure. Check
   clearance at the start of the first line and across that footprint. Lift
   before moving XY between check points. Use a gauge of known thickness
   under the stationary nozzle. Record the XY, commanded Z and measured
   clearance, then remove the gauge before moving. If a 0.2 mm ruler fits
   and a 1.75 mm filament does not, the gap is still too uncertain to set
   a 0.35 mm first layer. A controller position report (`M114`) cannot
   measure the nozzle-to-sheet gap.
4. If the physical clearance disagrees with the expected layer height, check
   the seated sheet, bed level and Z home reference. Repeat the check after
   adjustment. A single measurement at one point cannot justify a global
   Z compensation. If the next move in a paused file would put the nozzle
   into the sheet, cancel the file and correct the cause before restarting.
5. Export **plain text G-code** under a distinct filename. Check the start
   sequence in the exported file. Heating should begin with the nozzle raised
   clear of the sheet. For the button control, use the same known-good file
   on SD and USB. Its older slicer metadata describes a different nozzle and
   filament diameter, so use the cradle's own profile for the project part.

The full [FH1 print archive](../mechanical/full-hub/README.md#print-package)
contains the STLs for the other jobs. Slice the fastener/SMA coupon separately,
dry-fit the delivered hardware, then progress to the other small trays, radar
holder and pod. Reserve the base and lid for after those checks. Older local
six-plate projects and prior trial G-code are optional operator files.

## Start an attended print

Before each start, the operator at the printer checks:

- Old parts and loose plastic removed; build sheet secured, flat and clean;
  no raised damaged edges or clips in the intended path.
- Correct sheet face up according to its manufacturer. A rough print face
  above a magnetic underside is plausible, but a description alone does not
  identify a replacement sheet. Never use hot nozzle contact to test it.
- Nozzle visibly clear of the surface before stationary heating; current
  bed level/Z offset checked using the machine's known-good procedure.
- PLA reaches continuously from spool through feeder and Bowden tube, without
  breaks or gaps; spool can unwind. Remove all tape markers before printing.
- Correct G-code, material, nozzle and usable filament quantity confirmed.
- Operator can watch the start and reach the printer's physical power switch.

In OctoPrint:

1. Log in, select the correct printer profile and connect to the identified
   port at 115200. Check that no SD or USB job is already active.
2. Use **Upload** to local storage. Avoid **Upload and Print** during initial
   commissioning: inspect the filename and loaded preview before starting.
3. Load/select the intended file. Check the Temperature and GCode Viewer tabs.
   A preview is not physical proof of bed clearance or safe homing.
4. Press **Print once**. If the request times out, inspect job state before
   retrying; never assume that a missing browser response means no start.
5. Watch homing, the raised position during warm-up, the first extruded
   line and the entire first layer. Stop for surface contact, no extrusion, backward-only feed,
   loose loops, dragged parts or repeated feeder clicking.
6. Confirm lines adhere evenly and subsequent layers actually grow. An
   advancing percentage and normal temperature cannot prove deposited plastic.

## Monitor and stop

Use **Temperature** for actual versus target nozzle/bed readings, the job panel
for filename/state/progress and **Terminal** for errors. GCode Viewer reports
commanded paths, not measured nozzle position or actual plastic flow. A target
of 0 °C means heating is off, not that the nozzle is cool.

A camera helps only if a real stream is configured and inspected. For an
optional UVC camera, identify it with `lsusb` and `/dev/video*`, install a camera
server appropriate to that host, then configure and verify stream/snapshot URLs
in OctoPrint's webcam settings. No camera-server package is installed by this
guide. Check image freshness and first-layer visibility under real lighting;
start with modest resolution/frame rate. A stale image can look healthy.

Optional [Home Assistant integration](https://www.home-assistant.io/integrations/octoprint/)
can expose supported state, temperatures and controls after USB operation is
stable. Neither HA, telemetry nor a configured camera creates continuous human
supervision or proven automatic failure detection. Any automatic vision/stop
system requires separate qualification.

### Pause, cancel and an urgent stop

- **Pause** is temporary and may leave heaters on or the nozzle near the part.
  Do not assume a safe park/retraction script is installed. Qualify resume on
  a small attended job. OctoPrint interprets a file's `@pause` when streaming
  it from host storage. Do not rely on that directive to stop a print from
  the printer's SD card.
- **Cancel** ends the streamed job. Wait for an idle state, set tool and bed
  targets to **0**, and verify their readback. Commands already buffered in
  the printer can still execute briefly; cancel is not a physical stop switch.
- For imminent collision, smoke or uncontrolled heating, use the printer's
  physical power switch if safe to do so. Do not wait for a web response.
- A blocking heat command or broken connection can delay queued heater-off
  commands. If the printer does not respond, use local physical control/power;
  a disconnected browser or stopped Linux service does not guarantee heaters
  are off. Reconnect only after the machine is safe and inspect state before
  sending anything else.
- After cancelling or losing power/USB, do not resume an arbitrary file offset.
  Inspect/remove the failed part when cool and plan a new start from zero.

For a normal finish, verify idle status and both heater targets zero. Let the
hotend cooling fan run while the hotend cools, then switch off the printer as
appropriate. Remove the part only after the bed has cooled. Leave the Linux
host running if it serves other purposes.

### Optional read-only API checks

The following targets the installed **OctoPrint 1.11.x API**. Create a scoped
application key in OctoPrint with the permissions needed for status; store the
header locally, outside the repository, with mode 0600. Its file content is
`X-Api-Key: YOUR_APPLICATION_KEY`. Do not paste a real key into documentation,
command history, screenshots or Git.

```sh
# Use your actual trusted-LAN URL, or the local SSH tunnel URL.
OCTOPRINT_URL=http://127.0.0.1:15000
OCTOPRINT_HEADER_FILE="$HOME/.config/octoprint/status.header"
curl --fail --silent --show-error --max-time 10 --header "@$OCTOPRINT_HEADER_FILE" "$OCTOPRINT_URL/api/job"
curl --fail --silent --show-error --max-time 10 --header "@$OCTOPRINT_HEADER_FILE" "$OCTOPRINT_URL/api/printer"
```

Read `state`, current file, progress and `temperature.tool0` / `temperature.bed`
actual/target. A disconnected printer can return an error instead of temperature
state; do not reinterpret that as zero temperature. HTTP acceptance of a motion
command would not prove that motion happened. This guide deliberately uses
attended UI controls for starting and moving the printer.

## Diagnose filament delivery

A thin strand can ooze from residual pressure while the feeder is stopped.
Observe the filament itself, not only sound or nozzle output.

1. Cancel any job. Confirm idle status and physically raised nozzle clearance
   **now**, not from yesterday's position. Never home or lower onto an existing
   part during diagnosis.
2. Check the cold feed path for a brittle break, gap in the Bowden tube,
   spool snag or a released feeder lever. Do not force cold filament through
   the hotend. Do not unplug motor wiring while powered.
3. Place a pen mark on the incoming filament far enough from the feeder to
   remain visible through the test. Keep tape and debris out of the mechanism.
4. Heat to the confirmed PLA setting (205 °C was used here). Wait for the
   actual temperature to reach it, with the nozzle visibly above the bed.
5. Issue **one** small positive feed, approximately 5 mm at 1 mm/s. The local
   observed terminal sequence was `M82`, `G92 E0`, `G1 E5 F60`, `M400`, then
   `M104 S0`, **only while idle and already hot**. It changes the E coordinate
   and is not a macro to inject into a running or paused print. Do not queue
   repeated feeds behind a heating command. Verify the heater-off target.
6. Compare the physical mark with the requested distance. If the gear turns
   but filament barely advances, investigate grip/slipping or resistance. If
   neither moves, investigate command execution and drive operation. If feed
   reverses, stop and compare modes with known-good SD G-code before changing
   motor settings. These are diagnostic leads, not a confirmed cause.
7. Stop for repeated clicking, grinding, a jam, smoke or no forward movement.
   Do not compensate with large feed commands, higher pressure, disabling cold
   extrusion protection or unreviewed temperature increases.

Black output while silver PLA is loaded can have several causes; color alone
cannot prove bed material entered the hotend. Do not perform unlimited purges.
On this machine, a final short test restored silver output and the expected
5 mm advance. That justifies a subsequent attended coupon check, not immediate
acceptance of every long print. Follow a procedure appropriate to the actual
hotend before attempting disassembly or a cold pull.

## Maintenance and recovery

On Linux, read-only service checks:

```sh
systemctl status octoprint --no-pager
sudo journalctl -u octoprint -n 60 --no-pager
sudo -u octoprint /opt/octoprint/venv/bin/python -m pip check
sudo -u octoprint /opt/octoprint/venv/bin/python -m pip show OctoPrint OctoPrint-FixCBDFirmware
ss -ltn | rg ':5000'  # use grep if ripgrep is not installed
```

Never share raw logs/configuration without checking for session data, API keys,
private addresses and account details. For serial permissions, inspect the
actual device group and `id octoprint`; do not use `chmod 777` on USB devices.

Before updating, ensure the printer is idle, heater targets are zero and the
machine is locally safe. Stop the service and make a **private** backup of
`/var/lib/octoprint`, the effective systemd unit/drop-ins/environment files and
`pip freeze` output. Keep secrets out of this repository. Install only reviewed
versions in the virtual environment, run `pip check`, start the service and
verify login, plugins, profile, connection and temperatures. Keep the previous
version set and backup for rollback; test with a coupon after a change.

```sh
# Idle-only service operation, not a printer emergency-stop command.
sudo systemctl restart octoprint
# To retire the service without deleting its state:
# sudo systemctl disable --now octoprint
# To restore sleep availability when retiring a dedicated print host:
# sudo systemctl unmask sleep.target suspend.target hibernate.target hybrid-sleep.target suspend-then-hibernate.target
```

If unreachable, check host/printer power, Ethernet/mesh connectivity, the router's
reservation, SSH and service status in that order. Do not assign a guessed
static address that may conflict. A host/network failure during USB streaming
requires local inspection before restarting a job.

## Primary references

- [OctoPrint installation options](https://octoprint.org/download/).
- [Official Fix CBD Firmware plugin and installation](https://plugins.octoprint.org/plugins/fixcbdfirmware/).
- [Pinned plugin source](https://github.com/OctoPrint/OctoPrint-FixCBDFirmware/tree/153f46889c8aea2b33262310a6f79b6a8a3159fa).
- [OctoPrint 1.11.8 source](https://github.com/OctoPrint/OctoPrint/tree/1.11.8).
- [Printer API](https://docs.octoprint.org/en/main/api/printer.html),
  [job API](https://docs.octoprint.org/en/main/api/job.html) and
  [file API](https://docs.octoprint.org/en/main/api/files.html).
  The rolling documentation may describe newer API versions; examples above
  deliberately use the installed 1.11.x routes.
- [FH1 enclosure and print sequence](../mechanical/full-hub/README.md).
