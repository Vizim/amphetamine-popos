# Amphetamine for Pop!_OS

A Wayland-native keep-awake tray utility for Pop!_OS, inspired by [Amphetamine for macOS](https://apps.apple.com/us/app/amphetamine/id937984704).

![Active](pill_awake_preview.png) ![Inactive](pill_sleep_preview.png)

## Features

- **Icon in top bar** — active (green) / inactive (grey)
- **Indefinite sessions** — keep awake until you stop it
- **Timed sessions** — 5m / 15m / 30m / 1h / 2h / 4h / 8h with live countdown in the menu
- **Wayland native** — uses `systemd-inhibit` (no X11 hacks)
- **Auto-starts on login** via `.desktop` entry
- Zero dependencies beyond Python 3 + GTK3 (pre-installed on Pop!_OS)

## Requirements

Both packages below are pre-installed on Pop!_OS 22.04+. If missing:

```bash
sudo apt install gir1.2-ayatanaappindicator3-0.1 libayatana-appindicator3-1
```

## Install

```bash
git clone https://github.com/Vizim/amphetamine-popos.git
cd amphetamine-popos
bash install.sh
python3 ~/.local/bin/amphetamine &
```

## How it works

Amphetamine calls `systemd-inhibit --what=sleep:idle:handle-lid-switch`, which acquires a system-level inhibitor lock via D-Bus.

## Uninstall

```bash
rm ~/.local/bin/amphetamine
rm ~/.config/autostart/amphetamine.desktop
```

## License

MIT
