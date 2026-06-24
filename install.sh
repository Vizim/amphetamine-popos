#!/bin/bash
# Amphetamine for Pop!_OS — Installer
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/bin"
AUTOSTART_DIR="$HOME/.config/autostart"
INSTALL_PATH="$INSTALL_DIR/amphetamine"

echo "🔧 Installing Amphetamine for Pop!_OS..."

mkdir -p "$INSTALL_DIR" "$AUTOSTART_DIR"

cp "$SCRIPT_DIR/amphetamine.py" "$INSTALL_PATH"
chmod +x "$INSTALL_PATH"

cat > "$AUTOSTART_DIR/amphetamine.desktop" << DESKTOP
[Desktop Entry]
Type=Application
Name=Amphetamine
Comment=Keep-awake utility for Pop!_OS (Wayland)
Exec=python3 $INSTALL_PATH
Icon=caffeine
StartupNotify=false
X-GNOME-Autostart-enabled=true
DESKTOP

echo ""
echo "✅ Installed to $INSTALL_PATH"
echo "✅ Will auto-start on login"
echo ""
echo "Launch now:"
echo "  python3 $INSTALL_PATH &"
