#!/usr/bin/env python3
"""
Amphetamine for Pop!_OS
Wayland-compatible keep-awake tray app — mirrors macOS Amphetamine behaviour.
Uses systemd-inhibit to block sleep/idle properly on Wayland.
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AyatanaAppIndicator3', '0.1')

from gi.repository import Gtk, GLib, AyatanaAppIndicator3 as AppIndicator3

import subprocess
import signal
import os
import math
import struct
import zlib

APP_ID     = "amphetamine-popos"
ICON_DIR   = os.path.expanduser("~/.local/share/amphetamine")
ICON_AWAKE = os.path.join(ICON_DIR, "awake.png")
ICON_SLEEP = os.path.join(ICON_DIR, "sleep.png")


# ── Pure-Python RGBA PNG writer ───────────────────────────────────────────────

def _write_png(path, width, height, get_pixel):
    """
    Write a PNG file with RGBA colour (colour type 6).
    get_pixel(x, y) must return a 4-tuple (r, g, b, a) with values 0-255.
    """
    def chunk(tag, data):
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', crc)

    # Build raw image data: one filter byte (0) per row, then RGBA pixels
    rows = b''
    for y in range(height):
        rows += b'\x00'                          # filter type = None
        for x in range(width):
            rows += bytes(get_pixel(x, y))       # 4 bytes: R G B A

    png  = b'\x89PNG\r\n\x1a\n'
    # IHDR: width, height, bit depth=8, colour type=6 (RGBA)
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(rows, 9))
    png += chunk(b'IEND', b'')

    with open(path, 'wb') as f:
        f.write(png)


# ── Pill icon drawing ─────────────────────────────────────────────────────────

def _circle_pill_pixel(x, y, size, active):
    """
    Circular scored tablet — like the Mac Amphetamine icon.
    Round disc with a horizontal score line through the centre.
    Top half slightly lighter, bottom slightly darker for depth.
    """
    cx, cy = size / 2.0, size / 2.0
    r_out  = size * 0.44          # outer radius
    r_in   = r_out - 2.2          # inner edge of outline ring

    dx = x - cx
    dy = y - cy
    d  = math.sqrt(dx * dx + dy * dy)

    if d > r_out + 0.5:
        return (0, 0, 0, 0)       # transparent outside

    # Anti-aliased alpha on outer edge
    a = min(255, max(0, int(255 * (r_out + 0.5 - d))))

    # Dark border ring
    if d > r_in:
        return (28, 28, 28, a)

    # Horizontal score line ±1.2 px from centre
    if abs(dy) <= 1.2:
        if active:
            return (15, 100, 44, a)   # dark green groove
        else:
            return (80, 80, 80, a)    # dark grey groove

    # Two-tone depth: lighter top, darker bottom
    if dy < 0:                        # top half
        if active:
            return (80, 220, 130, a)  # lighter green
        else:
            return (200, 200, 200, a) # lighter grey
    else:                             # bottom half
        if active:
            return (22, 155, 65, a)   # darker green
        else:
            return (115, 115, 115, a) # darker grey


def generate_icons(size=64):
    os.makedirs(ICON_DIR, exist_ok=True)
    _write_png(ICON_AWAKE, size, size,
               lambda x, y: _circle_pill_pixel(x, y, size, True))
    _write_png(ICON_SLEEP, size, size,
               lambda x, y: _circle_pill_pixel(x, y, size, False))


# ── Main app ──────────────────────────────────────────────────────────────────

class Amphetamine:
    def __init__(self):
        self.inhibit_proc  = None   # systemd-inhibit process
        self.timer_id      = None   # GLib countdown timer
        self.remaining_sec = 0
        self.session_type  = None   # None | 'indefinite' | 'timed'

        generate_icons()

        self.indicator = AppIndicator3.Indicator.new(
            APP_ID,
            ICON_SLEEP,
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_icon_full(ICON_SLEEP, "Amphetamine — Inactive")

        self.menu = Gtk.Menu()
        self.indicator.set_menu(self.menu)
        self._rebuild_menu()

    # ── Menu ──────────────────────────────────────────────────────────────────

    def _rebuild_menu(self):
        for child in self.menu.get_children():
            self.menu.remove(child)

        # Status header (non-clickable)
        if self.session_type == 'indefinite':
            hdr_text = "💊  Active — indefinite session"
        elif self.session_type == 'timed':
            m = self.remaining_sec // 60
            s = self.remaining_sec % 60
            hdr_text = f"💊  Active — {m}m {s:02d}s remaining"
        else:
            hdr_text = "💤  Inactive — system may sleep"

        header = Gtk.MenuItem(label=hdr_text)
        header.set_sensitive(False)
        self.menu.append(header)
        self.menu.append(Gtk.SeparatorMenuItem())

        # Main toggle
        if self.session_type:
            toggle = Gtk.MenuItem(label="⏹  End Session")
            toggle.connect("activate", self._end_session)
        else:
            toggle = Gtk.MenuItem(label="▶  Start Indefinite Session")
            toggle.connect("activate", self._start_indefinite)
        self.menu.append(toggle)

        # Timed sessions submenu
        timed_item = Gtk.MenuItem(label="⏱  Start Session For…")
        timed_menu = Gtk.Menu()
        for label, secs in [
            ("5 minutes",   5   * 60),
            ("15 minutes",  15  * 60),
            ("30 minutes",  30  * 60),
            ("1 hour",      60  * 60),
            ("2 hours",     120 * 60),
            ("4 hours",     240 * 60),
            ("8 hours",     480 * 60),
        ]:
            item = Gtk.MenuItem(label=label)
            item.connect("activate", self._start_timed, secs)
            timed_menu.append(item)
        timed_item.set_submenu(timed_menu)
        self.menu.append(timed_item)

        self.menu.append(Gtk.SeparatorMenuItem())

        quit_item = Gtk.MenuItem(label="Quit Amphetamine")
        quit_item.connect("activate", self._quit)
        self.menu.append(quit_item)

        self.menu.show_all()

    # ── Session control ───────────────────────────────────────────────────────

    def _start_inhibit(self):
        if self.inhibit_proc:
            return
        try:
            self.inhibit_proc = subprocess.Popen([
                "systemd-inhibit",
                "--what=sleep:idle:handle-lid-switch",
                "--who=Amphetamine",
                "--why=User-requested keep-awake session",
                "--mode=block",
                "sleep", "infinity"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.indicator.set_icon_full(ICON_AWAKE, "Amphetamine — Active")
        except FileNotFoundError:
            self._show_error("systemd-inhibit not found. Is systemd installed?")

    def _stop_inhibit(self):
        if self.inhibit_proc:
            self.inhibit_proc.terminate()
            try:
                self.inhibit_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.inhibit_proc.kill()
            self.inhibit_proc = None
        if self.timer_id:
            GLib.source_remove(self.timer_id)
            self.timer_id = None
        self.remaining_sec = 0
        self.session_type  = None
        self.indicator.set_icon_full(ICON_SLEEP, "Amphetamine — Inactive")

    def _start_indefinite(self, _=None):
        self._stop_inhibit()
        self._start_inhibit()
        self.session_type = 'indefinite'
        self._rebuild_menu()

    def _start_timed(self, _, seconds):
        self._stop_inhibit()
        self._start_inhibit()
        self.session_type  = 'timed'
        self.remaining_sec = seconds
        self.timer_id = GLib.timeout_add_seconds(1, self._tick)
        self._rebuild_menu()

    def _tick(self):
        self.remaining_sec -= 1
        if self.remaining_sec <= 0:
            self._end_session()
            return False
        self._rebuild_menu()
        return True

    def _end_session(self, _=None):
        self._stop_inhibit()
        self._rebuild_menu()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _show_error(self, msg):
        dlg = Gtk.MessageDialog(
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=msg
        )
        dlg.run()
        dlg.destroy()

    def _quit(self, _=None):
        self._stop_inhibit()
        Gtk.main_quit()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    Amphetamine()
    Gtk.main()


if __name__ == "__main__":
    main()
