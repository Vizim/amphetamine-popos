# Amphetamine for Pop!_OS 🫖

A Wayland-native keep-awake tray utility for Pop!_OS, inspired by [Amphetamine for macOS](https://apps.apple.com/us/app/amphetamine/id937984704).

## Features

- ☕ **Icon in top bar** — green (active) / grey (inactive)
- **Indefinite sessions** — keep awake forever until you stop it
- **Timed sessions** — 5m / 15m / 30m / 1h / 2h / 4h / 8h with live countdown in the menu
- **Wayland native** — uses `systemd-inhibit` (no X11 hacks)
- **Auto-starts on login** via `.desktop` entry
- Zero dependencies beyond Python 3 + GTK3 (pre-installed on Pop!_OS)

## Requirements

```bash
sudo apt install gir1.2-ayatanaappindicator3-0.1 libayatana-appindicator3-1
```

Both are pre-installed on Pop!_OS 22.04+.

## Install

```bash
git clone https://github.com/YOUR_USERNAME/amphetamine-popos.git
cd amphetamine-popos
bash install.sh
python3 ~/.local/bin/amphetamine &
```

## How it works

Amphetamine calls `systemd-inhibit --what=sleep:idle:handle-lid-switch` which acquires
a system-level inhibitor lock via D-Bus. This is the correct, Wayland-compatible way to
prevent sleep — no display server hacks, no simulated keypresses.

The lock is released the moment you end the session or quit the app.

## Uninstall

```bash
rm ~/.local/bin/amphetamine
rm ~/.config/autostart/amphetamine.desktop
rm -rf ~/.local/share/amphetamine
```

## License

MIT
