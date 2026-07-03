#!/usr/bin/env python3
# chatgptemuchip8 FULL · files = off · CHIP-8 · HUD auto-detect USB/OS ROMs
import math
import os
import sys
import random
import platform
import subprocess
import pygame

FILES_OFF = True
WIDTH, HEIGHT = 64, 32
SCALE = 10
MENUBAR_H = 28
WINDOW_WIDTH = WIDTH * SCALE
WINDOW_HEIGHT = MENUBAR_H + HEIGHT * SCALE
ROM_START = 0x200
MAX_ROM = 4096 - ROM_START
FONT_ADDR = 0x50
FPS = 60
CPU_HZ = 500
CYCLES_PER_FRAME = max(1, CPU_HZ // FPS)

BLACK = (0, 0, 0)
WHITE = (240, 240, 245)
GRAY = (48, 48, 56)
GRAY_HI = (72, 72, 84)
BLUE = (40, 140, 255)
ACCENT = (50, 160, 255)
BG = (8, 8, 12)
BLANK_BG = (252, 252, 254)  # blank main window until ROM loaded

# macOS Tahoe · Liquid Glass palette
TAHOE_GLASS = (248, 248, 252)
TAHOE_GLASS_EDGE = (255, 255, 255)
TAHOE_GLASS_SHADOW = (0, 0, 0)
TAHOE_SCRIM = (12, 14, 22)
TAHOE_TITLE = (22, 22, 28)
TAHOE_BODY = (48, 48, 54)
TAHOE_DIM = (110, 110, 118)
TAHOE_ACCENT = (0, 122, 255)
TAHOE_FIELD = (255, 255, 255)
TAHOE_FIELD_BORDER = (180, 182, 192)
TAHOE_BTN = (240, 240, 246)
TAHOE_BTN_BORDER = (190, 192, 200)
TAHOE_TRAFFIC = ((255, 95, 86), (255, 189, 46), (39, 201, 63))

MENU_BG = (248, 248, 252, 210)
MENU_HOVER = (255, 255, 255, 120)
MENU_ACTIVE = (0, 122, 255)
MENU_DROP = (252, 252, 255)
MENU_DROP_BORDER = (210, 212, 220)
MENU_TEXT = (22, 22, 28)
MENU_TEXT_DIM = (110, 110, 118)
MENU_ACCEL = (140, 140, 150)

KEYMAP = {
    pygame.K_x: 0x0, pygame.K_1: 0x1, pygame.K_2: 0x2, pygame.K_3: 0x3,
    pygame.K_q: 0x4, pygame.K_w: 0x5, pygame.K_e: 0x6,
    pygame.K_a: 0x7, pygame.K_s: 0x8, pygame.K_d: 0x9,
    pygame.K_z: 0xA, pygame.K_c: 0xB, pygame.K_4: 0xC,
    pygame.K_r: 0xD, pygame.K_f: 0xE, pygame.K_v: 0xF,
}

FONTSET = [
    0xF0, 0x90, 0x90, 0x90, 0xF0, 0x20, 0x60, 0x20, 0x20, 0x70,
    0xF0, 0x10, 0xF0, 0x80, 0xF0, 0xF0, 0x10, 0xF0, 0x10, 0xF0,
    0x90, 0x90, 0xF0, 0x10, 0x10, 0xF0, 0x80, 0xF0, 0x10, 0xF0,
    0xF0, 0x80, 0xF0, 0x90, 0xF0, 0xF0, 0x10, 0x20, 0x40, 0x40,
    0xF0, 0x90, 0xF0, 0x90, 0xF0, 0xF0, 0x90, 0xF0, 0x10, 0xF0,
    0xF0, 0x90, 0xF0, 0x90, 0x90, 0xE0, 0x90, 0xE0, 0x90, 0xE0,
    0xF0, 0x80, 0x80, 0x80, 0xF0, 0xE0, 0x90, 0x90, 0x90, 0xE0,
    0xF0, 0x80, 0xF0, 0x80, 0xF0, 0xF0, 0x80, 0xF0, 0x80, 0x80,
]

# IBM logo · embedded demo (files = off)
EMBED_ROM = bytes([
    0x00, 0xE0, 0xA2, 0x2A, 0x60, 0x08, 0xD1, 0x23, 0x22, 0x0A, 0x8F, 0xB6, 0x8F, 0x33, 0x6D, 0x25,
    0x60, 0x78, 0x68, 0x60, 0x68, 0x23, 0x18, 0x14, 0x8F, 0x35, 0x87, 0x94, 0x3D, 0x50, 0x68, 0x63,
    0x0A, 0xC8, 0x88, 0xF0, 0xE6, 0x0E, 0x81, 0xF0, 0xA2, 0xCE, 0xA2, 0xCD, 0xFF, 0xE5, 0x18, 0x08,
    0x60, 0x18, 0x47, 0x01, 0x0A, 0xC8, 0xFC, 0xCC, 0xE0, 0xD0, 0x80, 0x7E, 0x20, 0xD0, 0x60, 0x18,
    0x22, 0x0A, 0xAE, 0xD8, 0x67, 0x58, 0x4D, 0x00, 0x80, 0xA2, 0xAA,
])

ABOUT_TEXT = [
    "chatgptemuchip8 FULL",
    "CHIP-8 emulator · files = off",
    "Python + pygame · all opcodes",
    "",
    "Keys: 1 2 3 4",
    "      Q W E R",
    "      A S D F",
    "      Z X C V",
    "",
    "Esc = pause · F5 = reset",
]


class Chip8:
    def __init__(self):
        self.reset()

    def reset(self):
        self.memory = [0] * 4096
        self.V = [0] * 16
        self.I = 0
        self.pc = ROM_START
        self.stack = [0] * 16
        self.sp = 0
        self.delay_timer = 0
        self.sound_timer = 0
        self.display = [[0] * WIDTH for _ in range(HEIGHT)]
        self.keys = [0] * 16
        self.waiting_key = False
        self.wait_reg = 0
        self.halted = False
        for i, b in enumerate(FONTSET):
            self.memory[FONT_ADDR + i] = b

    def load_bytes(self, data: bytes) -> bool:
        if not data or len(data) > MAX_ROM:
            return False
        self.reset()
        for i, b in enumerate(data):
            self.memory[ROM_START + i] = b
        return True

    def load_rom(self, path: str) -> bool:
        try:
            with open(path, "rb") as f:
                return self.load_bytes(f.read())
        except OSError:
            return False

    def fetch(self) -> int:
        self.pc &= 0xFFF
        if self.pc > 4094:
            return 0xFFFF
        return (self.memory[self.pc] << 8) | self.memory[self.pc + 1]

    def clear(self):
        self.display = [[0] * WIDTH for _ in range(HEIGHT)]

    def scroll(self, dy: int):
        if dy > 0:
            self.display = self.display[dy:] + [[0] * WIDTH for _ in range(dy)]
        elif dy < 0:
            self.display = [[0] * WIDTH for _ in range(-dy)] + self.display[:dy]

    def draw_sprite(self, x, y, height):
        self.V[0xF] = 0
        x %= WIDTH
        y %= HEIGHT
        for row in range(height):
            sprite = self.memory[(self.I + row) & 0xFFF]
            for col in range(8):
                if sprite & (0x80 >> col):
                    px = (x + col) % WIDTH
                    py = (y + row) % HEIGHT
                    if self.display[py][px]:
                        self.V[0xF] = 1
                    self.display[py][px] ^= 1

    def _set_key_from_wait(self):
        for i, pressed in enumerate(self.keys):
            if pressed:
                self.V[self.wait_reg] = i
                self.waiting_key = False
                self.pc = (self.pc + 2) & 0xFFF
                return True
        return False

    def step(self):
        if self.halted:
            return
        if self.waiting_key:
            self._set_key_from_wait()
            return

        op = self.fetch()
        if op == 0xFFFF:
            self.halted = True
            return
        x = (op & 0x0F00) >> 8
        y = (op & 0x00F0) >> 4
        n = op & 0x000F
        nn = op & 0x00FF
        nnn = op & 0x0FFF
        hi = op & 0xF000

        if hi == 0x0000:
            if op == 0x00E0:
                self.clear()
                self.pc = (self.pc + 2) & 0xFFF
            elif op == 0x00EE:
                self.sp = (self.sp - 1) & 0xF
                self.pc = self.stack[self.sp] & 0xFFF
            elif op == 0x00FB:
                self.scroll(1)
                self.pc = (self.pc + 2) & 0xFFF
            elif op == 0x00FC:
                self.scroll(-1)
                self.pc = (self.pc + 2) & 0xFFF
            else:
                self.pc = (self.pc + 2) & 0xFFF

        elif hi == 0x1000:
            self.pc = nnn

        elif hi == 0x2000:
            self.stack[self.sp] = self.pc
            self.sp = (self.sp + 1) & 0xF
            self.pc = nnn

        elif hi == 0x3000:
            self.pc = (self.pc + (4 if self.V[x] == nn else 2)) & 0xFFF

        elif hi == 0x4000:
            self.pc = (self.pc + (4 if self.V[x] != nn else 2)) & 0xFFF

        elif hi == 0x5000:
            self.pc = (self.pc + (4 if self.V[x] == self.V[y] else 2)) & 0xFFF

        elif hi == 0x6000:
            self.V[x] = nn
            self.pc = (self.pc + 2) & 0xFFF

        elif hi == 0x7000:
            self.V[x] = (self.V[x] + nn) & 0xFF
            self.pc = (self.pc + 2) & 0xFFF

        elif hi == 0x8000:
            if n == 0x0:
                self.V[x] = self.V[y]
            elif n == 0x1:
                self.V[x] |= self.V[y]
            elif n == 0x2:
                self.V[x] &= self.V[y]
            elif n == 0x3:
                self.V[x] ^= self.V[y]
            elif n == 0x4:
                total = self.V[x] + self.V[y]
                self.V[0xF] = 1 if total > 0xFF else 0
                self.V[x] = total & 0xFF
            elif n == 0x5:
                self.V[0xF] = 1 if self.V[x] > self.V[y] else 0
                self.V[x] = (self.V[x] - self.V[y]) & 0xFF
            elif n == 0x6:
                self.V[0xF] = self.V[x] & 1
                self.V[x] >>= 1
            elif n == 0x7:
                self.V[0xF] = 1 if self.V[y] > self.V[x] else 0
                self.V[x] = (self.V[y] - self.V[x]) & 0xFF
            elif n == 0xE:
                self.V[0xF] = (self.V[x] >> 7) & 1
                self.V[x] = (self.V[x] << 1) & 0xFF
            self.pc = (self.pc + 2) & 0xFFF

        elif hi == 0x9000:
            self.pc = (self.pc + (4 if self.V[x] != self.V[y] else 2)) & 0xFFF

        elif hi == 0xA000:
            self.I = nnn
            self.pc = (self.pc + 2) & 0xFFF

        elif hi == 0xB000:
            self.pc = (nnn + self.V[0]) & 0xFFF

        elif hi == 0xC000:
            self.V[x] = random.randint(0, 255) & nn
            self.pc = (self.pc + 2) & 0xFFF

        elif hi == 0xD000:
            self.draw_sprite(self.V[x], self.V[y], n)
            self.pc = (self.pc + 2) & 0xFFF

        elif hi == 0xE000:
            k = self.V[x] & 0xF
            if nn == 0x9E:
                self.pc = (self.pc + (4 if self.keys[k] else 2)) & 0xFFF
            elif nn == 0xA1:
                self.pc = (self.pc + (4 if not self.keys[k] else 2)) & 0xFFF
            else:
                self.pc = (self.pc + 2) & 0xFFF

        elif hi == 0xF000:
            if nn == 0x07:
                self.V[x] = self.delay_timer
                self.pc = (self.pc + 2) & 0xFFF
            elif nn == 0x0A:
                self.waiting_key = True
                self.wait_reg = x
            elif nn == 0x15:
                self.delay_timer = self.V[x]
                self.pc = (self.pc + 2) & 0xFFF
            elif nn == 0x18:
                self.sound_timer = self.V[x]
                self.pc = (self.pc + 2) & 0xFFF
            elif nn == 0x1E:
                self.I = (self.I + self.V[x]) & 0xFFF
                self.pc = (self.pc + 2) & 0xFFF
            elif nn == 0x29:
                self.I = FONT_ADDR + self.V[x] * 5
                self.pc = (self.pc + 2) & 0xFFF
            elif nn == 0x33:
                v = self.V[x]
                self.memory[self.I] = v // 100
                self.memory[self.I + 1] = (v // 10) % 10
                self.memory[self.I + 2] = v % 10
                self.pc = (self.pc + 2) & 0xFFF
            elif nn == 0x55:
                for i in range(x + 1):
                    self.memory[(self.I + i) & 0xFFF] = self.V[i]
                self.pc = (self.pc + 2) & 0xFFF
            elif nn == 0x65:
                for i in range(x + 1):
                    self.V[i] = self.memory[(self.I + i) & 0xFFF]
                self.pc = (self.pc + 2) & 0xFFF
            else:
                self.pc = (self.pc + 2) & 0xFFF

        else:
            self.pc = (self.pc + 2) & 0xFFF

    def tick_timers(self):
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1
            return True
        return False


# ---- ROM detect · USB / OS / embedded (files = off · no bundled ROMs) ----
ROM_EXTS = (".ch8", ".bin", ".rom", ".chip8", ".gx")
SCAN_DEPTH = 4
RESCAN_SEC = 6
MACOS_VOL_SKIP = {"Preboot", "Recovery", "Update", "VM", "Hardware", "iSCPreboot", "xART"}


def _home() -> str:
    return os.path.expanduser("~")


def _safe_listdir(path: str) -> list[str]:
    try:
        return os.listdir(path)
    except OSError:
        return []


def _is_rom(name: str) -> bool:
    return name.lower().endswith(ROM_EXTS)


def _classify_darwin_volume(path: str) -> str | None:
    """Return usb · sd · disk · None(skip)."""
    try:
        r = subprocess.run(
            ["diskutil", "info", path],
            capture_output=True, text=True, timeout=4,
        )
        if r.returncode != 0:
            return "disk"
        t = r.stdout.lower()
        if "disk image" in t or "virtual" in t:
            return None
        if "sd card" in t or "secure digital" in t or ("internal, physical" in t and "sd" in t):
            return "sd"
        if "removable media:       removable" in t:
            return "usb"
        if "protocol:              usb" in t:
            return "usb"
        if "device location:       external" in t:
            return "usb"
    except (OSError, subprocess.TimeoutExpired):
        pass
    name = os.path.basename(path.rstrip("/")).lower()
    if any(k in name for k in ("sd", "sdcard", "no name", "untitled", "usb")):
        return "usb"
    if path.startswith("/Volumes/") and "Macintosh HD" not in path:
        return "usb"
    return "disk"


def _darwin_volumes() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    if not os.path.isdir("/Volumes"):
        return out
    for name in _safe_listdir("/Volumes"):
        if name.startswith(".") or name in MACOS_VOL_SKIP:
            continue
        p = os.path.join("/Volumes", name)
        if not os.path.isdir(p):
            continue
        kind = _classify_darwin_volume(p)
        if kind is None or kind == "disk":
            continue
        tag = {"usb": "USB", "sd": "SD Card"}.get(kind, "USB")
        out.append((f"{tag} · {name}", p, kind))
    return out


def _linux_external() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    seen: set[str] = set()

    def add(label: str, path: str, kind: str):
        if path in seen or not os.path.isdir(path):
            return
        seen.add(path)
        out.append((label, path, kind))

    try:
        r = subprocess.run(
            ["lsblk", "-rno", "NAME,RM,HOTPLUG,TRAN,MOUNTPOINT,LABEL"],
            capture_output=True, text=True, timeout=5,
        )
        for line in r.stdout.splitlines():
            parts = line.split(maxsplit=5)
            if len(parts) < 5:
                continue
            rm, hot, tran = parts[1], parts[2], parts[3].lower()
            mount = parts[4] if parts[4].startswith("/") else ""
            label = parts[5] if len(parts) > 5 else parts[0]
            if rm != "1" and hot != "1":
                continue
            if not mount:
                continue
            kind = "sd" if "mmc" in tran else "usb"
            tag = "SD Card" if kind == "sd" else "USB"
            add(f"{tag} · {label or parts[0]}", mount, kind)
    except (OSError, subprocess.TimeoutExpired, FileNotFoundError):
        pass

    for base in ("/media", "/mnt", "/run/media"):
        if not os.path.isdir(base):
            continue
        for user in _safe_listdir(base):
            up = os.path.join(base, user)
            if os.path.isdir(up):
                for vol in _safe_listdir(up):
                    vp = os.path.join(up, vol)
                    if os.path.isdir(vp):
                        kind = "sd" if "mmc" in vol.lower() else "usb"
                        tag = "SD Card" if kind == "sd" else "USB"
                        add(f"{tag} · {vol}", vp, kind)
            elif os.path.ismount(up):
                add(f"USB · {user}", up, "usb")
    return out


def _windows_external() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        DRIVE_REMOVABLE = 2
        DRIVE_FIXED = 3
        for i in range(26):
            letter = chr(ord("A") + i)
            root = f"{letter}:\\"
            dtype = kernel32.GetDriveTypeW(root)
            if dtype == DRIVE_REMOVABLE:
                out.append((f"USB/SD · {letter}:", root, "usb"))
            elif dtype == DRIVE_FIXED and letter not in ("C",):
                out.append((f"Disk · {letter}:", root, "disk"))
    except (OSError, AttributeError):
        pass
    return out


def _external_mounts() -> list[tuple[str, str, str]]:
    sysname = platform.system()
    if sysname == "Darwin":
        return _darwin_volumes()
    if sysname == "Linux":
        return _linux_external()
    if sysname == "Windows":
        return _windows_external()
    return []


class RomScanner:
    """Detect CHIP-8 ROMs from USB · SD · external · OS · embedded · files = off."""

    def __init__(self):
        self.sources: list[dict] = []
        self.rom_index: list[dict] = []
        self.total_roms = 0
        self.usb_count = 0
        self.sd_count = 0
        self.ext_count = 0
        self.scanning = False
        self.scan_line = "Idle"
        self.last_scan = 0
        self._cache: dict[str, list[dict]] = {}

    def build_sources(self):
        self.sources = []
        self.usb_count = 0
        self.sd_count = 0
        self.ext_count = 0
        for label, path, kind in _external_mounts():
            self.sources.append({
                "id": f"ext:{path}", "label": label, "path": path, "kind": kind,
            })
            self.ext_count += 1
            if kind == "sd":
                self.sd_count += 1
            elif kind == "usb":
                self.usb_count += 1
        self.sources.append({"id": "embed", "label": "Embedded", "path": None, "kind": "embed"})
        for sid, label, path in (
            ("desktop", "Desktop", os.path.join(_home(), "Desktop")),
            ("documents", "Documents", os.path.join(_home(), "Documents")),
            ("downloads", "Downloads", os.path.join(_home(), "Downloads")),
            ("home", "Home", _home()),
            ("cwd", "Current Folder", os.getcwd()),
        ):
            self.sources.append({"id": sid, "label": label, "path": path, "kind": "os"})

    def default_source_id(self) -> str:
        for src in self.sources:
            if src["kind"] in ("usb", "sd"):
                return src["id"]
        for src in self.sources:
            if src["kind"] == "usb":
                return src["id"]
        return "embed"

    def scan_tree(self, root: str, depth: int = SCAN_DEPTH) -> list[dict]:
        found: list[dict] = []
        if not root or not os.path.isdir(root):
            return found

        def walk(d: str, lvl: int):
            if lvl > depth:
                return
            for name in _safe_listdir(d):
                if name.startswith("."):
                    continue
                fp = os.path.join(d, name)
                try:
                    if os.path.isfile(fp) and _is_rom(name):
                        found.append({
                            "kind": "rom", "name": name, "path": fp,
                            "size": os.path.getsize(fp), "ftype": "CHIP-8 ROM",
                        })
                    elif os.path.isdir(fp):
                        walk(fp, lvl + 1)
                except OSError:
                    pass

        walk(root, 0)
        return sorted(found, key=lambda e: e["name"].lower())

    def scan_all(self):
        self.scanning = True
        self.rom_index = []
        self._cache.clear()
        self.build_sources()
        self.scan_line = f"Detect · USB {self.usb_count} · SD {self.sd_count} · {platform.system()}"
        for src in self.sources:
            if src["kind"] == "embed":
                for name, data in EMBED_ROMS.items():
                    self.rom_index.append({
                        "kind": "embed", "name": f"{name}.ch8", "rom_key": name,
                        "path": None, "size": len(data), "source": "Embedded",
                    })
                continue
            root = src["path"]
            if not root or not os.path.isdir(root):
                continue
            depth = SCAN_DEPTH + (2 if src["kind"] in ("usb", "sd") else 0)
            self.scan_line = f"Scanning {src['label']}…"
            hits = self.scan_tree(root, depth=depth)
            self._cache[src["id"]] = hits
            for h in hits:
                self.rom_index.append({**h, "source": src["label"]})
        self.total_roms = len(self.rom_index)
        self.last_scan = pygame.time.get_ticks() if pygame.get_init() else 0
        self.scan_line = (
            f"Found {self.total_roms} ROM(s) · USB {self.usb_count} · SD {self.sd_count} · files=off"
        )
        self.scanning = False

    def list_fs(self, path: str) -> list[dict]:
        entries: list[dict] = []
        if not path or not os.path.isdir(path):
            return entries
        parent = os.path.dirname(path.rstrip(os.sep))
        if parent and os.path.isdir(parent) and parent != path:
            entries.append({
                "kind": "up", "name": "..", "path": parent,
                "size": 0, "ftype": "Parent folder",
            })
        try:
            names = sorted(_safe_listdir(path), key=str.lower)
        except OSError:
            return entries
        for name in names:
            if name.startswith("."):
                continue
            fp = os.path.join(path, name)
            try:
                if os.path.isdir(fp):
                    entries.append({
                        "kind": "folder", "name": name, "path": fp,
                        "size": 0, "ftype": "File folder",
                    })
                elif os.path.isfile(fp) and _is_rom(name):
                    entries.append({
                        "kind": "rom", "name": name, "path": fp,
                        "size": os.path.getsize(fp), "ftype": "CHIP-8 ROM",
                    })
            except OSError:
                pass
        return entries

    def hud_summary(self) -> str:
        return (
            f"ROM {self.total_roms} · USB {self.usb_count} · SD {self.sd_count} · "
            f"Ext {self.ext_count} · files=off"
        )


class RomDetectHUD:
    """Tahoe glass HUD · live detect status."""

    def __init__(self, scanner: RomScanner):
        self.scanner = scanner
        self.visible = True
        self._expanded = False
        self._panel = pygame.Rect(0, 0, 0, 0)
        self._refresh_btn = pygame.Rect(0, 0, 0, 0)
        self.hover_refresh = False

    def toggle(self):
        self._expanded = not self._expanded

    def tick(self):
        sc = self.scanner
        if sc.scanning:
            return
        now = pygame.time.get_ticks()
        if sc.last_scan and now - sc.last_scan > RESCAN_SEC * 1000:
            sc.scan_all()

    def motion(self, pos):
        self.hover_refresh = self._refresh_btn.collidepoint(pos) if self._expanded else False

    def click(self, pos) -> bool:
        if self._expanded and self._refresh_btn.collidepoint(pos):
            self.scanner.scan_all()
            return True
        if self._panel.collidepoint(pos):
            self._expanded = not self._expanded
            return True
        return False

    def draw(self, surf, caption_font, small_font):
        if not self.visible:
            return
        sc = self.scanner
        line = sc.hud_summary() if not sc.scanning else sc.scan_line
        pw = min(WINDOW_WIDTH - 16, 300 if self._expanded else 220)
        ph = 88 if self._expanded else 24
        px = WINDOW_WIDTH - pw - 8
        py = MENUBAR_H + 6
        self._panel = pygame.Rect(px, py, pw, ph)
        draw_glass_panel(surf, self._panel, radius=10, alpha=215)
        t = caption_font.render(line, True, TAHOE_TITLE)
        surf.blit(t, (px + 10, py + 5))
        if sc.scanning:
            draw_tahoe_spinner(surf, px + pw - 16, py + 12, pygame.time.get_ticks() * 0.01, r=8)
        if not self._expanded:
            return
        y = py + 28
        for src in sc.sources[:8]:
            n = len(sc._cache.get(src["id"], [])) if src["kind"] != "embed" else len(EMBED_ROMS)
            if src["kind"] == "embed":
                n = len(EMBED_ROMS)
            row = small_font.render(f"{src['label']}: {n}", True, TAHOE_DIM)
            surf.blit(row, (px + 10, y))
            y += 14
        self._refresh_btn = pygame.Rect(px + pw - 72, py + ph - 24, 62, 18)
        draw_glass_panel(surf, self._refresh_btn, radius=5, alpha=250 if self.hover_refresh else 230)
        rb = small_font.render("Rescan", True, TAHOE_ACCENT if self.hover_refresh else TAHOE_BODY)
        surf.blit(rb, (self._refresh_btn.x + 8, self._refresh_btn.y + 2))


# ---- mGBA-style menu strip (files = off · embedded demos) ------------
EMBED_ROMS = {
    "IBM Logo": EMBED_ROM,
}

MENU_ITEMS = [
    ("File", "f", [
        ("Load ROM...", "open_rom", "Ctrl+O"),
        ("Load Demo ROM", "load_demo", ""),
        ("---", None, ""),
        ("Reset", "reset", "F5"),
        ("---", None, ""),
        ("Quit", "quit", "Ctrl+Q"),
    ]),
    ("Emulation", "e", [
        ("Pause", "toggle_run", "Space"),
        ("Run", "toggle_run", ""),
        ("Step Frame", "step", "F12"),
        ("---", None, ""),
        ("Hard Reset", "reset", "F5"),
    ]),
    ("Help", "h", [
        ("About chatgptemuchip8", "about", ""),
        ("Keyboard Layout", "controls", ""),
    ]),
]


class MenuBar:
    DROPDOWN_W = 248

    def __init__(self, font, small_font):
        self.font = font
        self.small = small_font
        self.open_menu = None
        self.hover_top = -1
        self.hover_row = -1
        self.sel_row = 0
        self.dropdown_entries = []
        self.top_rects = []
        self._layout()

    def _layout(self):
        self.top_rects = []
        x = 4
        for label, _, _ in MENU_ITEMS:
            w = self.font.size(label)[0] + 20
            self.top_rects.append(pygame.Rect(x, 0, w, MENUBAR_H))
            x += w

    def is_open(self) -> bool:
        return self.open_menu is not None

    def close(self):
        self.open_menu = None
        self.hover_row = -1

    def _build_dropdown(self, idx: int):
        self.dropdown_entries = []
        _, _, items = MENU_ITEMS[idx]
        for label, action, accel in items:
            if label == "---":
                self.dropdown_entries.append({"kind": "sep", "h": 9})
            else:
                self.dropdown_entries.append({
                    "kind": "item", "label": label, "action": action,
                    "accel": accel, "h": 26,
                })

    def _dropdown_rect(self):
        if self.open_menu is None:
            return None
        x = self.top_rects[self.open_menu].x
        y = MENUBAR_H
        h = sum(e["h"] for e in self.dropdown_entries)
        return pygame.Rect(x, y, self.DROPDOWN_W, h)

    def draw_bar(self, surf, status: str, rom_label: str = ""):
        bar = pygame.Surface((WINDOW_WIDTH, MENUBAR_H), pygame.SRCALPHA)
        bar.fill(MENU_BG)
        surf.blit(bar, (0, 0))
        pygame.draw.line(surf, MENU_DROP_BORDER, (0, MENUBAR_H - 1), (WINDOW_WIDTH, MENUBAR_H - 1))
        for i, (label, _, _) in enumerate(MENU_ITEMS):
            r = self.top_rects[i]
            active = i == self.open_menu
            hover = i == self.hover_top
            if active:
                pill = r.inflate(-4, -6)
                draw_glass_panel(surf, pill, radius=6, alpha=255)
                pygame.draw.rect(surf, MENU_ACTIVE, pill, 0, border_radius=6)
            elif hover:
                pill = r.inflate(-4, -6)
                hover_s = pygame.Surface((pill.width, pill.height), pygame.SRCALPHA)
                hover_s.fill(MENU_HOVER)
                mask = _rounded_mask(pill.width, pill.height, 6)
                hover_s.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                surf.blit(hover_s, pill.topleft)
            t = self.font.render(label, True, WHITE if active else MENU_TEXT)
            surf.blit(t, (r.x + 10, r.centery - t.get_height() // 2))
        center = rom_label or status
        st = self.small.render(center, True, MENU_TEXT_DIM)
        sx = max(8, (WINDOW_WIDTH - st.get_width()) // 2)
        surf.blit(st, (sx, MENUBAR_H // 2 - st.get_height() // 2))
        hint = self.small.render(status, True, MENU_TEXT_DIM)
        surf.blit(hint, (WINDOW_WIDTH - hint.get_width() - 8, MENUBAR_H // 2 - hint.get_height() // 2))

    def draw_dropdown(self, surf):
        if self.open_menu is None:
            return
        box = self._dropdown_rect()
        if not box:
            return
        draw_glass_panel(surf, box, radius=10, alpha=245)
        pygame.draw.rect(surf, MENU_DROP_BORDER, box, 1, border_radius=10)
        cy = box.y
        row_i = 0
        for entry in self.dropdown_entries:
            h = entry["h"]
            if entry["kind"] == "sep":
                pygame.draw.line(surf, MENU_DROP_BORDER,
                                 (box.x + 8, cy + 4), (box.right - 8, cy + 4))
                cy += h
                continue
            rr = pygame.Rect(box.x, cy, box.width, h)
            if row_i == self.hover_row or row_i == self.sel_row:
                hi = pygame.Rect(box.x + 4, cy + 2, box.width - 8, h - 4)
                pygame.draw.rect(surf, MENU_ACTIVE, hi, border_radius=6)
            label = self.font.render(entry["label"], True, MENU_TEXT)
            surf.blit(label, (box.x + 12, cy + 5))
            if entry["accel"]:
                acc = self.small.render(entry["accel"], True, MENU_ACCEL)
                surf.blit(acc, (box.right - acc.get_width() - 12, cy + 6))
            entry["_rect"] = rr
            entry["_row"] = row_i
            cy += h
            row_i += 1

    def _row_at(self, pos):
        if self.open_menu is None:
            return -1
        for entry in self.dropdown_entries:
            if entry.get("kind") != "item":
                continue
            if entry.get("_rect") and entry["_rect"].collidepoint(pos):
                return entry["_row"]
        return -1

    def _action_at(self, pos):
        row = self._row_at(pos)
        if row < 0:
            return None
        for entry in self.dropdown_entries:
            if entry.get("_row") == row:
                return entry.get("action")
        return None

    def _item_rows(self):
        return [e for e in self.dropdown_entries if e["kind"] == "item"]

    def click(self, pos) -> str | None:
        if pos[1] < MENUBAR_H:
            for i, r in enumerate(self.top_rects):
                if r.collidepoint(pos):
                    if self.open_menu == i:
                        self.close()
                    else:
                        self.open_menu = i
                        self._build_dropdown(i)
                        self.sel_row = 0
                        self.hover_row = 0
                    return None
            self.close()
            return None
        act = self._action_at(pos)
        self.close()
        return act

    def motion(self, pos):
        self.hover_top = -1
        if pos[1] < MENUBAR_H:
            for i, r in enumerate(self.top_rects):
                if r.collidepoint(pos):
                    self.hover_top = i
                    if self.open_menu is not None and self.open_menu != i:
                        self.open_menu = i
                        self._build_dropdown(i)
                        self.sel_row = 0
                        self.hover_row = 0
                    break
        elif self.open_menu is not None:
            self.hover_row = self._row_at(pos)

    def key_nav(self, key) -> str | None:
        if self.open_menu is None:
            return None
        items = self._item_rows()
        n = len(items)
        if n == 0:
            return None
        if key == pygame.K_UP:
            self.sel_row = (self.sel_row - 1) % n
            self.hover_row = self.sel_row
        elif key == pygame.K_DOWN:
            self.sel_row = (self.sel_row + 1) % n
            self.hover_row = self.sel_row
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            act = items[self.sel_row]["action"]
            self.close()
            return act
        elif key == pygame.K_ESCAPE:
            self.close()
        return None

    def alt_open(self, letter: str) -> bool:
        for i, (_, mnem, _) in enumerate(MENU_ITEMS):
            if mnem == letter.lower():
                self.open_menu = i
                self._build_dropdown(i)
                self.sel_row = 0
                self.hover_row = 0
                return True
        return False


# ---- macOS Tahoe · Liquid Glass UI -----------------------------------
def _rounded_mask(w: int, h: int, r: int) -> pygame.Surface:
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=r)
    return mask


def draw_glass_panel(surf, rect: pygame.Rect, radius: int = 14, alpha: int = 228):
    """Frosted Liquid Glass sheet (blur simulated via layered fills)."""
    w, h = rect.width, rect.height
    if w <= 0 or h <= 0:
        return
    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    mask = _rounded_mask(w, h, radius)
    for rgba in ((248, 248, 252, alpha), (255, 255, 255, max(40, alpha // 3))):
        layer_s = pygame.Surface((w, h), pygame.SRCALPHA)
        layer_s.fill(rgba)
        panel.blit(layer_s, (0, 0))
    panel.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    hi = pygame.Surface((w, max(2, h // 3)), pygame.SRCALPHA)
    hi.fill((255, 255, 255, 48))
    hi_mask = _rounded_mask(w, max(2, h // 3), radius)
    hi.blit(hi_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    panel.blit(hi, (0, 0))
    shadow = pygame.Surface((w + 10, h + 10), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 70), (5, 5, w, h), border_radius=radius + 2)
    surf.blit(shadow, (rect.x - 3, rect.y - 1))
    surf.blit(panel, rect.topleft)
    pygame.draw.rect(surf, TAHOE_GLASS_EDGE, rect, 1, border_radius=radius)


def draw_traffic_lights(surf, x: int, y: int):
    for i, col in enumerate(TAHOE_TRAFFIC):
        cx = x + i * 18 + 7
        pygame.draw.circle(surf, col, (cx, y), 6)
        pygame.draw.circle(surf, (0, 0, 0, 30), (cx, y), 6, 1)


def draw_tahoe_spinner(surf, cx: int, cy: int, angle: float, r: int = 14):
    """macOS-style indeterminate spinner."""
    for i in range(12):
        t = i / 12.0
        a = angle + t * math.tau
        fade = 0.15 + 0.85 * (1.0 - t)
        c = int(40 + 180 * fade)
        x1 = cx + math.cos(a) * (r - 4)
        y1 = cy + math.sin(a) * (r - 4)
        x2 = cx + math.cos(a) * r
        y2 = cy + math.sin(a) * r
        pygame.draw.line(surf, (c, c, c + 10), (x1, y1), (x2, y2), 2)


def draw_tahoe_badge(surf, rect: pygame.Rect, text: str, font, accent=False):
    if accent:
        pygame.draw.rect(surf, TAHOE_ACCENT, rect, border_radius=rect.height // 2)
        t = font.render(text, True, WHITE)
    else:
        draw_glass_panel(surf, rect, radius=rect.height // 2, alpha=240)
        t = font.render(text, True, TAHOE_DIM)
    surf.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))


class TahoeLoader:
    """macOS Tahoe full-screen boot · Liquid Glass · files = off · USB/SD detect."""

    STEPS = [
        ("Starting chatgptemuchip8", "Initializing CHIP-8 core…"),
        ("Detecting devices", "USB · SD card · external volumes…"),
        ("Scanning for ROMs", "Removable media · OS folders…"),
        ("Ready", "Opening ROM picker…"),
    ]

    def __init__(self):
        self.active = False
        self.phase = 0
        self.frame = 0
        self.spin = 0.0
        self.done_cb = None
        self.scanner: RomScanner | None = None
        self._phase_done: set[int] = set()

    def start(self, done_cb=None, scanner: RomScanner | None = None):
        self.active = True
        self.phase = 0
        self.frame = 0
        self.spin = 0.0
        self.done_cb = done_cb
        self.scanner = scanner
        self._phase_done = set()

    def dismiss(self):
        self.active = False
        if self.done_cb:
            self.done_cb()
            self.done_cb = None

    def _run_phase_work(self, phase: int):
        if phase in self._phase_done or not self.scanner:
            return
        self._phase_done.add(phase)
        if phase == 1:
            self.scanner.build_sources()
            sc = self.scanner
            sc.scan_line = f"Detect · USB {sc.usb_count} · SD {sc.sd_count} · {platform.system()}"
        elif phase == 2:
            self.scanner.scan_all()

    def tick(self):
        if not self.active:
            return
        self.frame += 1
        self.spin += 0.16
        prev = self.phase
        if self.frame > 0 and self.frame % 30 == 0 and self.phase < len(self.STEPS) - 1:
            self.phase += 1
        if self.phase != prev:
            self._run_phase_work(self.phase)
        if self.phase == 0 and self.frame == 1:
            self._run_phase_work(0)
        if self.phase >= len(self.STEPS) - 1 and self.frame > 30 * len(self.STEPS) + 18:
            self.dismiss()

    def _step_status(self, idx: int) -> str:
        if idx < self.phase:
            return "done"
        if idx == self.phase:
            return "active"
        return "pending"

    def draw(self, surf, title_font, body_font, caption_font):
        if not self.active:
            return

        surf.fill(BLANK_BG)
        wash = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        wash.fill((240, 242, 250, 120))
        surf.blit(wash, (0, 0))

        pw = min(WINDOW_WIDTH - 32, 440)
        ph = min(WINDOW_HEIGHT - 40, 300)
        px = (WINDOW_WIDTH - pw) // 2
        py = (WINDOW_HEIGHT - ph) // 2
        panel = pygame.Rect(px, py, pw, ph)
        draw_glass_panel(surf, panel, radius=20)

        draw_traffic_lights(surf, panel.x + 16, panel.y + 16)
        win_title = caption_font.render("chatgptemuchip8", True, TAHOE_DIM)
        surf.blit(win_title, (panel.x + 76, panel.y + 14))

        badge = pygame.Rect(panel.right - 118, panel.y + 12, 102, 22)
        draw_tahoe_badge(surf, badge, "files = off", caption_font, accent=True)

        icon = pygame.Rect(panel.x + 28, panel.y + 52, 72, 72)
        draw_glass_panel(surf, icon, radius=16, alpha=245)
        pygame.draw.rect(surf, TAHOE_ACCENT, icon.inflate(-8, -8), border_radius=12)
        ic = title_font.render("C8", True, WHITE)
        surf.blit(ic, (icon.centerx - ic.get_width() // 2, icon.centery - ic.get_height() // 2))

        app_t = title_font.render("chatgptemuchip8 FULL", True, TAHOE_TITLE)
        surf.blit(app_t, (panel.x + 116, panel.y + 58))
        sub = body_font.render("CHIP-8 Emulator · macOS Tahoe", True, TAHOE_BODY)
        surf.blit(sub, (panel.x + 116, panel.y + 80))
        plat = caption_font.render(
            f"{platform.system()} {platform.release()} · detect USB/SD",
            True, TAHOE_DIM,
        )
        surf.blit(plat, (panel.x + 116, panel.y + 98))

        steps_top = panel.y + 138
        for i, (stitle, ssub) in enumerate(self.STEPS):
            sy = steps_top + i * 32
            st = self._step_status(i)
            dot_x = panel.x + 32
            dot_y = sy + 8
            if st == "done":
                pygame.draw.circle(surf, TAHOE_ACCENT, (dot_x, dot_y), 7)
                chk = caption_font.render("✓", True, WHITE)
                surf.blit(chk, (dot_x - chk.get_width() // 2, dot_y - chk.get_height() // 2))
            elif st == "active":
                draw_tahoe_spinner(surf, dot_x, dot_y, self.spin, r=9)
            else:
                pygame.draw.circle(surf, TAHOE_FIELD_BORDER, (dot_x, dot_y), 6, 2)

            tc = TAHOE_TITLE if st == "active" else TAHOE_BODY if st == "done" else TAHOE_DIM
            t1 = body_font.render(stitle, True, tc)
            surf.blit(t1, (panel.x + 52, sy))
            t2 = caption_font.render(ssub, True, TAHOE_DIM if st != "active" else TAHOE_BODY)
            surf.blit(t2, (panel.x + 52, sy + 16))

        progress = min(1.0, (self.frame % 30) / 30.0)
        bar_w = pw - 56
        bar_x = panel.x + 28
        bar_y = panel.bottom - 52
        pygame.draw.rect(surf, (225, 228, 236), pygame.Rect(bar_x, bar_y, bar_w, 8), border_radius=4)
        fill_w = max(10, int(bar_w * ((self.phase + progress) / len(self.STEPS))))
        pygame.draw.rect(surf, TAHOE_ACCENT, pygame.Rect(bar_x, bar_y, fill_w, 8), border_radius=4)

        live = self.scanner.scan_line if self.scanner else "Loading…"
        if self.scanner and self.scanner.scanning:
            draw_tahoe_spinner(surf, panel.right - 28, bar_y - 10, self.spin, r=7)
        hint = caption_font.render(live[:64], True, TAHOE_DIM)
        surf.blit(hint, (bar_x, panel.bottom - 28))

        ver = caption_font.render("Liquid Glass · files = off · no bundled ROMs", True, TAHOE_DIM)
        surf.blit(ver, (panel.x + 28, panel.bottom - 14))


def draw_tahoe_sheet(surf, title_font, body_font, caption_font,
                     title: str, lines: list[str], sheet_h: int = 0):
    """Tahoe info sheet (About, Controls, no-ROM)."""
    scrim = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT - MENUBAR_H), pygame.SRCALPHA)
    scrim.fill((*TAHOE_SCRIM, 140))
    surf.blit(scrim, (0, MENUBAR_H))

    line_h = 20
    content_h = 56 + len(lines) * line_h + 24
    ph = sheet_h or min(WINDOW_HEIGHT - MENUBAR_H - 40, max(180, content_h))
    pw = min(420, WINDOW_WIDTH - 48)
    px = (WINDOW_WIDTH - pw) // 2
    py = MENUBAR_H + (WINDOW_HEIGHT - MENUBAR_H - ph) // 2
    panel = pygame.Rect(px, py, pw, ph)
    draw_glass_panel(surf, panel, radius=14)

    draw_traffic_lights(surf, panel.x + 12, panel.y + 12)
    t = title_font.render(title, True, TAHOE_TITLE)
    surf.blit(t, (panel.x + 68, panel.y + 10))

    y = panel.y + 48
    for line in lines:
        if line:
            s = body_font.render(line, True, TAHOE_BODY if line[0].isupper() else TAHOE_DIM)
            surf.blit(s, (panel.x + 24, y))
        y += line_h


# ---- macOS Tahoe · XP-style file picker (files = off) ----------------
TAHOE_XP_HEADER = (232, 244, 255)
TAHOE_XP_HEADER_LINE = (180, 200, 228)
TAHOE_XP_SIDEBAR = (245, 247, 252)
TAHOE_XP_ROW_HI = (0, 122, 255, 80)
TAHOE_XP_FOLDER = (255, 204, 64)


def _fmt_size(n: int) -> str:
    if n <= 0:
        return ""
    if n < 1024:
        return f"{n} bytes"
    return f"{n // 1024} KB"


class TahoeFilePicker:
    """XP layout · Tahoe glass · USB/OS/embed browse · file select only."""

    COLS = ("Name", "Size", "Type")
    ROW_H = 22

    def __init__(self, scanner: RomScanner):
        self.scanner = scanner
        self.open = False
        self.source_id = "embed"
        self.fs_path: str | None = None
        self.sel = 0
        self.scroll = 0
        self.hover_row = -1
        self.hover_place = -1
        self.hover_open = False
        self.hover_cancel = False
        self.hover_refresh = False
        self._last_click = 0
        self._last_click_row = -1
        self.panel = pygame.Rect(0, 0, 0, 0)
        self._open_btn = pygame.Rect(0, 0, 0, 0)
        self._cancel_btn = pygame.Rect(0, 0, 0, 0)
        self._refresh_btn = pygame.Rect(0, 0, 0, 0)
        self._row_rects: list[pygame.Rect] = []
        self._place_rects: list[pygame.Rect] = []

    def is_open(self) -> bool:
        return self.open

    def show(self, source_id: str = "embed"):
        if not self.scanner.sources:
            self.scanner.scan_all()
        self.open = True
        self.source_id = source_id
        src = self._source_by_id(source_id)
        self.fs_path = src["path"] if src and src["kind"] != "embed" else None
        self.sel = 0
        self.scroll = 0
        self.hover_row = -1
        self.hover_place = -1

    def close(self):
        self.open = False

    def _source_by_id(self, sid: str) -> dict | None:
        for s in self.scanner.sources:
            if s["id"] == sid:
                return s
        return None

    def _places(self) -> list[dict]:
        return self.scanner.sources

    def entries(self) -> list[dict]:
        src = self._source_by_id(self.source_id)
        if not src:
            return []
        if src["kind"] == "embed":
            return [{
                "kind": "embed", "name": f"{n}.ch8", "rom_key": n,
                "size": len(d), "ftype": "CHIP-8 ROM",
            } for n, d in EMBED_ROMS.items()]
        if self.fs_path:
            return self.scanner.list_fs(self.fs_path)
        return self.scanner._cache.get(self.source_id, [])

    def selected_entry(self) -> dict | None:
        items = self.entries()
        idx = self.sel - self.scroll
        if not items or self.sel < 0 or self.sel >= len(items):
            return None
        return items[self.sel]

    def _pick_result(self, entry: dict) -> dict | str:
        if entry["kind"] == "embed":
            self.close()
            return {"kind": "embed", "key": entry["rom_key"]}
        if entry["kind"] == "rom":
            self.close()
            return {"kind": "path", "path": entry["path"]}
        return "noop"

    def _confirm(self) -> dict | str | None:
        entry = self.selected_entry()
        if not entry:
            return None
        if entry["kind"] in ("folder", "up"):
            self.fs_path = entry["path"]
            self.sel = 0
            self.scroll = 0
            return None
        return self._pick_result(entry)

    def _enter_source(self, src: dict):
        self.source_id = src["id"]
        self.fs_path = src["path"] if src["kind"] != "embed" else None
        self.sel = 0
        self.scroll = 0

    def _look_in_path(self) -> str:
        src = self._source_by_id(self.source_id)
        if not src:
            return ""
        if src["kind"] == "embed":
            return "Embedded › CHIP-8 ROMs"
        if self.fs_path:
            return self.fs_path
        return src["label"]

    def draw(self, surf, title_font, body_font, caption_font):
        if not self.open:
            return

        scrim = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        scrim.fill((*TAHOE_SCRIM, 165))
        surf.blit(scrim, (0, 0))

        pw = WINDOW_WIDTH - 24
        ph = WINDOW_HEIGHT - MENUBAR_H - 20
        px, py = 12, MENUBAR_H + 10
        self.panel = pygame.Rect(px, py, pw, ph)
        draw_glass_panel(surf, self.panel, radius=14)

        draw_traffic_lights(surf, self.panel.x + 12, self.panel.y + 12)
        title = title_font.render("Open — Detect & Select ROM", True, TAHOE_TITLE)
        surf.blit(title, (self.panel.x + 68, self.panel.y + 10))

        look_y = self.panel.y + 38
        look = caption_font.render("Look in:", True, TAHOE_BODY)
        surf.blit(look, (self.panel.x + 16, look_y + 4))
        combo = pygame.Rect(self.panel.x + 72, look_y, pw - 160, 24)
        draw_glass_panel(surf, combo, radius=6, alpha=250)
        pygame.draw.rect(surf, TAHOE_FIELD_BORDER, combo, 1, border_radius=6)
        path_t = body_font.render(self._look_in_path()[:58], True, TAHOE_TITLE)
        surf.blit(path_t, (combo.x + 8, combo.y + 4))

        self._refresh_btn = pygame.Rect(combo.right + 8, look_y, 72, 24)
        draw_glass_panel(surf, self._refresh_btn, radius=6, alpha=255 if self.hover_refresh else 240)
        rt = caption_font.render("Rescan", True, TAHOE_ACCENT if self.hover_refresh else TAHOE_BODY)
        surf.blit(rt, (self._refresh_btn.x + 12, self._refresh_btn.y + 5))

        content_y = look_y + 32
        content_h = ph - 132
        sidebar_w = 128
        sidebar = pygame.Rect(self.panel.x + 12, content_y, sidebar_w, content_h)
        list_box = pygame.Rect(sidebar.right + 8, content_y, pw - sidebar_w - 28, content_h)

        draw_glass_panel(surf, sidebar, radius=8, alpha=235)
        pygame.draw.rect(surf, TAHOE_XP_HEADER_LINE, sidebar, 1, border_radius=8)
        pl = caption_font.render("Detect", True, TAHOE_DIM)
        surf.blit(pl, (sidebar.x + 10, sidebar.y + 6))

        places = self._places()
        self._place_rects = []
        py_place = sidebar.y + 26
        for i, src in enumerate(places):
            pr = pygame.Rect(sidebar.x + 4, py_place, sidebar.width - 8, self.ROW_H)
            self._place_rects.append(pr)
            active = src["id"] == self.source_id
            if i == self.hover_place or active:
                hi = pr.inflate(-2, -2)
                s = pygame.Surface((hi.width, hi.height), pygame.SRCALPHA)
                s.fill(TAHOE_XP_ROW_HI if i == self.hover_place else (0, 122, 255, 45))
                surf.blit(s, hi.topleft)
            kind = {"usb": "⬤", "sd": "▣", "os": "◆", "embed": "★", "disk": "◎"}.get(src["kind"], "·")
            label = body_font.render(f"{kind} {src['label'][:14]}", True, TAHOE_TITLE)
            surf.blit(label, (pr.x + 4, pr.y + 3))
            py_place += self.ROW_H
            if py_place > sidebar.bottom - self.ROW_H:
                break

        draw_glass_panel(surf, list_box, radius=8, alpha=245)
        pygame.draw.rect(surf, TAHOE_FIELD_BORDER, list_box, 1, border_radius=8)

        hdr = pygame.Rect(list_box.x + 1, list_box.y + 1, list_box.width - 2, 22)
        hdr_s = pygame.Surface((hdr.width, hdr.height), pygame.SRCALPHA)
        hdr_s.fill((*TAHOE_XP_HEADER, 230))
        mask = _rounded_mask(hdr.width, hdr.height, 7)
        hdr_s.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surf.blit(hdr_s, hdr.topleft)
        pygame.draw.line(surf, TAHOE_XP_HEADER_LINE, (list_box.x, list_box.y + 23), (list_box.right, list_box.y + 23))
        col_x = [list_box.x + 8, list_box.x + 210, list_box.x + 280]
        for label, cx in zip(self.COLS, col_x):
            ht = caption_font.render(label, True, TAHOE_BODY)
            surf.blit(ht, (cx, list_box.y + 4))

        items = self.entries()
        self._row_rects = []
        row_top = list_box.y + 24
        visible = max(1, (list_box.height - 26) // self.ROW_H)
        if items:
            self.sel = max(0, min(self.sel, len(items) - 1))
        if self.sel >= self.scroll + visible:
            self.scroll = self.sel - visible + 1
        if self.sel < self.scroll:
            self.scroll = self.sel

        for vi in range(visible):
            i = vi + self.scroll
            if i >= len(items):
                break
            item = items[i]
            rr = pygame.Rect(list_box.x + 2, row_top + vi * self.ROW_H, list_box.width - 4, self.ROW_H)
            self._row_rects.append((i, rr))
            if i == self.sel or i == self.hover_row:
                hi = rr.inflate(-2, 0)
                pygame.draw.rect(surf, MENU_ACTIVE if i == self.sel else (200, 220, 255), hi, border_radius=4)
            if item["kind"] in ("folder", "up"):
                fr = pygame.Rect(rr.x + 6, rr.y + 5, 14, 11)
                pygame.draw.rect(surf, TAHOE_XP_FOLDER, fr, border_radius=2)
            else:
                pygame.draw.rect(surf, TAHOE_ACCENT, (rr.x + 8, rr.y + 6, 10, 12), border_radius=1)
            name_c = WHITE if (i == self.sel or i == self.hover_row) else TAHOE_TITLE
            nm = body_font.render(item["name"][:28], True, name_c)
            surf.blit(nm, (col_x[0] + 16, rr.y + 3))
            sz = caption_font.render(_fmt_size(item.get("size", 0)), True, name_c)
            surf.blit(sz, (col_x[1], rr.y + 4))
            ft = caption_font.render(item.get("ftype", "")[:14], True, name_c)
            surf.blit(ft, (col_x[2], rr.y + 4))

        foot_y = self.panel.bottom - 72
        fn_l = caption_font.render("File name:", True, TAHOE_BODY)
        surf.blit(fn_l, (self.panel.x + 16, foot_y + 6))
        fn_box = pygame.Rect(self.panel.x + 88, foot_y, pw - 200, 26)
        draw_glass_panel(surf, fn_box, radius=6, alpha=252)
        pygame.draw.rect(surf, TAHOE_FIELD_BORDER, fn_box, 1, border_radius=6)
        sel = self.selected_entry()
        fn_text = sel["name"] if sel else ""
        fn_t = body_font.render(fn_text, True, TAHOE_TITLE)
        surf.blit(fn_t, (fn_box.x + 8, fn_box.y + 4))

        det = caption_font.render(self.scanner.hud_summary(), True, TAHOE_DIM)
        surf.blit(det, (self.panel.x + 16, foot_y + 36))

        self._open_btn = pygame.Rect(self.panel.right - 188, self.panel.bottom - 40, 84, 28)
        self._cancel_btn = pygame.Rect(self.panel.right - 96, self.panel.bottom - 40, 84, 28)
        for rect, label, hover in (
            (self._open_btn, "Open", self.hover_open),
            (self._cancel_btn, "Cancel", self.hover_cancel),
        ):
            draw_glass_panel(surf, rect, radius=8, alpha=255 if hover else 240)
            pygame.draw.rect(surf, TAHOE_BTN_BORDER, rect, 1, border_radius=8)
            bt = body_font.render(label, True, TAHOE_TITLE)
            surf.blit(bt, (rect.centerx - bt.get_width() // 2, rect.centery - bt.get_height() // 2))

        hint = caption_font.render("USB · OS · embedded · double-click folder/ROM", True, TAHOE_DIM)
        surf.blit(hint, (self.panel.x + 16, self.panel.bottom - 18))

    def motion(self, pos):
        if not self.open:
            return
        self.hover_row = -1
        self.hover_place = -1
        self.hover_open = self._open_btn.collidepoint(pos)
        self.hover_cancel = self._cancel_btn.collidepoint(pos)
        self.hover_refresh = self._refresh_btn.collidepoint(pos)
        for i, pr in enumerate(self._place_rects):
            if pr.collidepoint(pos):
                self.hover_place = i
                break
        for i, rr in self._row_rects:
            if rr.collidepoint(pos):
                self.hover_row = i
                break

    def click(self, pos) -> dict | str | None:
        if not self.open:
            return None
        if self._cancel_btn.collidepoint(pos):
            self.close()
            return "cancel"
        if self._refresh_btn.collidepoint(pos):
            self.scanner.scan_all()
            return None
        if self._open_btn.collidepoint(pos):
            return self._confirm()

        places = self._places()
        for i, pr in enumerate(self._place_rects):
            if pr.collidepoint(pos) and i < len(places):
                self._enter_source(places[i])
                return None

        for i, rr in self._row_rects:
            if rr.collidepoint(pos):
                now = pygame.time.get_ticks()
                items = self.entries()
                if i < len(items):
                    if i == self._last_click_row and now - self._last_click < 400:
                        self.sel = i
                        entry = items[i]
                        if entry["kind"] in ("folder", "up"):
                            self.fs_path = entry["path"]
                            self.sel = 0
                            self.scroll = 0
                        else:
                            return self._pick_result(entry)
                    self.sel = i
                    self._last_click = now
                    self._last_click_row = i
                return None

        if not self.panel.collidepoint(pos):
            self.close()
            return "cancel"
        return None

    def key_nav(self, key) -> dict | str | None:
        if not self.open:
            return None
        items = self.entries()
        n = len(items)
        if key == pygame.K_ESCAPE:
            self.close()
            return "cancel"
        if key == pygame.K_UP and n:
            self.sel = (self.sel - 1) % n
        elif key == pygame.K_DOWN and n:
            self.sel = (self.sel + 1) % n
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return self._confirm()
        return None


def pick_rom_file() -> str | None:
    """Native file picker — no tkinter (crashes with pygame on macOS)."""
    if platform.system() == "Darwin":
        script = (
            'try\n'
            'POSIX path of (choose file with prompt "Open CHIP-8 ROM")\n'
            "on error number -128\n"
            'return ""\n'
            "end try"
        )
        try:
            r = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=120,
            )
            path = r.stdout.strip()
            return path if path else None
        except (OSError, subprocess.TimeoutExpired):
            return None
    try:
        r = subprocess.run(
            ["zenity", "--file-selection", "--title=Open CHIP-8 ROM",
             "--file-filter=CHIP-8 ROM | *.ch8", "--file-filter=All | *"],
            capture_output=True, text=True, timeout=120,
        )
        if r.returncode == 0:
            return r.stdout.strip() or None
    except (OSError, subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def draw_main_area(surf, chip: Chip8, rom_loaded: bool):
    """Blank canvas until ROM loaded · then CHIP-8 display."""
    area = pygame.Rect(0, MENUBAR_H, WINDOW_WIDTH, WINDOW_HEIGHT - MENUBAR_H)
    if not rom_loaded:
        surf.fill(BLANK_BG, area)
        return
    draw_display(surf, chip, MENUBAR_H)


def draw_display(surf, chip: Chip8, y0: int):
    surf.fill(BG, (0, y0, WINDOW_WIDTH, HEIGHT * SCALE))
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if chip.display[y][x]:
                pygame.draw.rect(surf, BLUE, (x * SCALE, y0 + y * SCALE, SCALE, SCALE))
    if not chip.display or not any(chip.display[y][x] for y in range(HEIGHT) for x in range(WIDTH)):
        pass


def handle_menu_action(act, ctx) -> bool:
    """Run menu action · returns False to quit."""
    if not act:
        return True
    if act == "quit":
        return False
    if act == "open_rom":
        ctx["do_open_rom"]()
    elif act == "load_demo":
        ctx["begin_load_demo"]()
    elif act == "reset":
        ctx["do_reset"]()
    elif act == "toggle_run":
        if ctx["rom_loaded"]:
            ctx["running_emu"] = not ctx["running_emu"]
            ctx["status"] = f"{'Running' if ctx['running_emu'] else 'Paused'}: {ctx['rom_name']}"
    elif act == "step":
        if ctx["rom_loaded"]:
            ctx["chip"].step()
            ctx["status"] = "Step"
    elif act == "about":
        ctx["show_about"] = not ctx["show_about"]
        ctx["show_controls"] = False
    elif act == "controls":
        ctx["show_controls"] = not ctx["show_controls"]
        ctx["show_about"] = False
    return True


def main():
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=256)
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("chatgptemuchip8 FULL")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Helvetica Neue", 13)
    small = pygame.font.SysFont("Helvetica Neue", 11)
    title_font = pygame.font.SysFont("Helvetica Neue", 14, bold=True)
    body_font = font
    caption_font = small
    beep_snd = None
    try:
        import array
        buf = array.array("h", [int(8000 * (1 if i % 40 < 20 else -1)) for i in range(800)])
        beep_snd = pygame.mixer.Sound(buffer=buf)
    except Exception:
        pass

    chip = Chip8()
    rom_name = "none"
    rom_bytes: bytes | None = None
    rom_loaded = False
    running_emu = False
    show_about = False
    show_controls = False
    status = "Blank · scan USB/SD · File → Load ROM"

    menu = MenuBar(font, small)
    loader = TahoeLoader()
    rom_scanner = RomScanner()
    file_picker = TahoeFilePicker(rom_scanner)
    rom_hud = RomDetectHUD(rom_scanner)
    alt_down = False

    def apply_pick(result):
        nonlocal status
        if result == "cancel" or not result:
            status = "Open ROM canceled"
        elif isinstance(result, dict):
            if result.get("kind") == "embed":
                load_demo(result["key"])
            elif result.get("kind") == "path":
                load_rom_path(result["path"])

    def load_demo(name: str = "IBM Logo"):
        nonlocal rom_name, rom_loaded, running_emu, status, rom_bytes
        data = EMBED_ROMS.get(name, EMBED_ROM)
        if chip.load_bytes(data):
            rom_bytes = data
            rom_name = f"{name} (embedded)"
            rom_loaded = True
            running_emu = True
            status = f"Running: {rom_name}"
            menu.close()
            return True
        return False

    def begin_load_demo(name: str = "IBM Logo"):
        loader.start(done_cb=lambda n=name: load_demo(n), scanner=rom_scanner)

    def load_rom_path(path: str) -> bool:
        nonlocal rom_name, rom_loaded, running_emu, status, rom_bytes
        path = path.strip()
        if not path:
            return False
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError:
            status = f"Load failed: {path}"
            return False
        if chip.load_bytes(data):
            import os
            rom_bytes = data
            rom_name = os.path.basename(path)
            rom_loaded = True
            running_emu = True
            status = f"Running: {rom_name}"
            return True
        status = "Load failed: invalid ROM size"
        return False

    def do_open_rom():
        nonlocal status
        if FILES_OFF:
            if not rom_scanner.sources:
                rom_scanner.scan_all()
            file_picker.show(rom_scanner.default_source_id())
            status = rom_scanner.hud_summary()
            menu.close()
            return
        path = pick_rom_file()
        if path:
            load_rom_path(path)
        else:
            status = "Open ROM canceled"

    def boot_finish():
        nonlocal status
        status = rom_scanner.hud_summary()
        if not rom_loaded:
            file_picker.show(rom_scanner.default_source_id())

    def do_reset():
        nonlocal status
        if rom_loaded and rom_bytes:
            chip.load_bytes(rom_bytes)
            running_emu = True
            status = f"Reset: {rom_name}"

    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1], "rb") as f:
                data = f.read()
            if chip.load_bytes(data):
                import os
                rom_bytes = data
                rom_name = os.path.basename(sys.argv[1])
                rom_loaded = True
                running_emu = True
                status = f"Running: {rom_name}"
        except OSError:
            pass
    if not rom_loaded and FILES_OFF:
        loader.start(done_cb=boot_finish, scanner=rom_scanner)

    ctx = {
        "chip": chip, "rom_loaded": rom_loaded, "rom_name": rom_name,
        "running_emu": running_emu, "status": status,
        "show_about": show_about, "show_controls": show_controls,
        "load_demo": load_demo, "begin_load_demo": begin_load_demo,
        "do_open_rom": do_open_rom, "do_reset": do_reset,
    }

    def sync_ctx():
        ctx["rom_loaded"] = rom_loaded
        ctx["rom_name"] = rom_name
        ctx["running_emu"] = running_emu
        ctx["status"] = status
        ctx["show_about"] = show_about
        ctx["show_controls"] = show_controls

    def apply_ctx():
        nonlocal rom_loaded, rom_name, running_emu, status, show_about, show_controls
        rom_loaded = ctx["rom_loaded"]
        rom_name = ctx["rom_name"]
        running_emu = ctx["running_emu"]
        status = ctx["status"]
        show_about = ctx["show_about"]
        show_controls = ctx["show_controls"]

    main_running = True
    while main_running:
        clock.tick(FPS)
        beeping = False
        menu_open = menu.is_open() or file_picker.is_open() or loader.active

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                main_running = False

            elif event.type == pygame.MOUSEMOTION:
                menu.motion(event.pos)
                file_picker.motion(event.pos)
                if not file_picker.is_open() and not loader.active:
                    rom_hud.motion(event.pos)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if loader.active:
                    continue
                if file_picker.is_open():
                    apply_pick(file_picker.click(event.pos))
                    continue
                if rom_hud.click(event.pos):
                    continue
                act = menu.click(event.pos)
                sync_ctx()
                if not handle_menu_action(act, ctx):
                    main_running = False
                if act in ("toggle_run", "about", "controls"):
                    apply_ctx()
                elif act:
                    sync_ctx()

            elif event.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()
                if file_picker.is_open():
                    apply_pick(file_picker.key_nav(event.key))
                    continue

                if event.key in (pygame.K_LALT, pygame.K_RALT):
                    alt_down = True
                    continue

                if menu.is_open():
                    act = menu.key_nav(event.key)
                    sync_ctx()
                    if act and not handle_menu_action(act, ctx):
                        main_running = False
                    if act in ("toggle_run", "about", "controls"):
                        apply_ctx()
                    elif act:
                        sync_ctx()
                    continue

                if alt_down or (mods & pygame.KMOD_ALT):
                    for _, mnem, _ in MENU_ITEMS:
                        if event.unicode and event.unicode.lower() == mnem:
                            menu.alt_open(mnem)
                            break

                if event.key == pygame.K_o and (mods & pygame.KMOD_CTRL or mods & pygame.KMOD_META):
                    do_open_rom()
                elif event.key == pygame.K_q and (mods & pygame.KMOD_CTRL or mods & pygame.KMOD_META):
                    main_running = False
                elif event.key == pygame.K_F5:
                    do_reset()
                elif event.key == pygame.K_SPACE and not menu_open:
                    if rom_loaded:
                        running_emu = not running_emu
                        status = f"{'Running' if running_emu else 'Paused'}: {rom_name}"
                elif event.key == pygame.K_F12 and rom_loaded and not menu_open:
                    chip.step()
                elif event.key == pygame.K_ESCAPE:
                    if menu.is_open():
                        menu.close()
                    elif rom_loaded:
                        running_emu = not running_emu
                        status = f"{'Running' if running_emu else 'Paused'}: {rom_name}"
                elif event.key in KEYMAP and not menu_open:
                    chip.keys[KEYMAP[event.key]] = 1

            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_LALT, pygame.K_RALT):
                    alt_down = False
                if event.key in KEYMAP and not menu_open:
                    chip.keys[KEYMAP[event.key]] = 0

        loader.tick()
        if not loader.active and not file_picker.is_open():
            rom_hud.tick()

        if rom_loaded and running_emu and not menu_open and not show_about and not show_controls:
            for _ in range(CYCLES_PER_FRAME):
                chip.step()
            if chip.tick_timers():
                beeping = True

        screen.fill(BLANK_BG if not rom_loaded else BG)
        if not loader.active:
            draw_main_area(screen, chip, rom_loaded)

        if loader.active:
            loader.draw(screen, title_font, body_font, caption_font)
        elif show_about:
            draw_tahoe_sheet(screen, title_font, body_font, caption_font, "About", [
                *ABOUT_TEXT, "", "Help → About to close",
            ], sheet_h=300)
        elif show_controls:
            draw_tahoe_sheet(screen, title_font, body_font, caption_font, "Controls", [
                *ABOUT_TEXT[4:],
            ], sheet_h=260)

        if not loader.active:
            menu.draw_bar(screen, status, rom_name if rom_loaded else "")
            menu.draw_dropdown(screen)

        if file_picker.is_open():
            file_picker.draw(screen, title_font, body_font, caption_font)
        elif not loader.active:
            rom_hud.draw(screen, caption_font, small)

        if beeping and beep_snd:
            beep_snd.play()

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
