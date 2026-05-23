#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  MB-Systeme v31 – UHCS MB 4-ECKEN-DESKTOP GUI                                        ║
║  © Meikel Boesing 2026 – Gronau (Westfalen)                                  ║
║  "Ein Mensch. Kein Konzern."                                                 ║
║                                                                              ║
║  UHCS_VERSION = "31.0"                                                       ║
║  BoesingFolge: f(x) = (42x³ + 158x² + 215x + 27) mod 256                   ║
║  Σ = 568 · Meikel-Prim = 331 · Tesla-Anker = {0,3,6,9}                     ║
║                                                                              ║
║  Ruft ausschließlich das uhcs-Binary per subprocess auf (CLI-Brücke).       ║
║  Keine eigene Python-Kompressionslogik.                                      ║
║                                                                              ║
║  LAYOUT:                                                                     ║
║    Oben links  – Einstellungen + Energieprofile + v26-KERN-Module            ║
║    Oben rechts – Live System-Monitor (CPU, RAM, Akku, Disk, CO2)             ║
║    Unten links – MB-Logo + START-Button → Startmenü                          ║
║    Unten rechts– Schnellzugriff-Buttons + Notizen                            ║
║                                                                              ║
║  Starte mit: python3 MBSysteme_v31_E.py                                           ║
║  Voraussetzung: uhcs-Binary im selben Ordner oder im PATH                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import re
import shutil
import threading
import time
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from tkinter.scrolledtext import ScrolledText
    GUI_OK = True
except ImportError:
    print("❌ tkinter nicht verfügbar! sudo apt install python3-tk")
    sys.exit(1)

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# ── §1 Konstanten (UNANTASTBAR) ───────────────────────────────────────────────
UHCS_VERSION   = "31.0"
UHCS_A3        = 42
UHCS_A2        = 158
UHCS_A1        = 215
UHCS_A0        = 27
UHCS_GRONAUER  = 126
UHCS_SIGMA     = UHCS_A3 + UHCS_A2 + UHCS_A1 + UHCS_A0 + UHCS_GRONAUER  # 568
UHCS_PRIM      = 331
UHCS_ALPHA_INV = 137
assert UHCS_SIGMA == 568, "Sigma-Sperre verletzt!"

# ── Farb-Schema (Dunkles Design) ──────────────────────────────────────────────
class C:
    BG   = "#050510"   # Hintergrund
    PNL  = "#0d0d1f"   # Panel
    CRD  = "#111128"   # Karte
    INP  = "#0a0a1e"   # Eingabe
    GRN  = "#00ff88"   # Grün (OK)
    CYN  = "#00d4ff"   # Cyan (Info)
    BLU  = "#4488ff"   # Blau
    PRP  = "#aa44ff"   # Lila
    ORG  = "#ff8800"   # Orange
    RED  = "#ff4444"   # Rot (Fehler)
    GLD  = "#ffd700"   # Gold
    YLW  = "#ffee44"   # Gelb
    TXB  = "#f0f0ff"   # Haupttext
    TXN  = "#b0b0d0"   # Normaler Text
    TXD  = "#606080"   # Gedimmter Text
    BDR  = "#1a1a3a"   # Rand
    # Schriften
    FN   = ("Segoe UI", 10)
    FS   = ("Segoe UI", 8)
    FM   = ("Courier New", 9)
    FT   = ("Segoe UI", 12, "bold")
    FB   = ("Courier New", 22, "bold")
    FBB  = ("Courier New", 16, "bold")

# ── 256 Mathematische Serien (für Serien-Explorer) ───────────────────────────
MATHEMATISCHE_SERIEN: List[Dict[str, str]] = [
    {"id": 0,   "name": "Nullreihe",           "beschr": "Identität (x → x), alle Werte unverändert"},
    {"id": 1,   "name": "Fibonacci mod 256",   "beschr": "1,1,2,3,5,8,13,21,34... mod 256"},
    {"id": 2,   "name": "Lucas mod 256",       "beschr": "2,1,3,4,7,11,18,29... mod 256"},
    {"id": 3,   "name": "Primzahlen mod 256",  "beschr": "2,3,5,7,11,13,17,19,23... mod 256"},
    {"id": 4,   "name": "Quadratzahlen",       "beschr": "0,1,4,9,16,25,36... mod 256"},
    {"id": 5,   "name": "Kubikzahlen",         "beschr": "0,1,8,27,64,125... mod 256"},
    {"id": 6,   "name": "Mersenne mod 256",    "beschr": "1,3,7,15,31,63,127,255... mod 256"},
    {"id": 7,   "name": "Perfekte Zahlen",     "beschr": "6,28,496... mod 256"},
    {"id": 8,   "name": "Catalan mod 256",     "beschr": "1,1,2,5,14,42,132... mod 256"},
    {"id": 9,   "name": "Tesla-Folge",         "beschr": "0,3,6,9,12,15... (× 3 mod 256)"},
    {"id": 10,  "name": "Triangular",          "beschr": "0,1,3,6,10,15,21... mod 256"},
    {"id": 11,  "name": "Pentagonal",          "beschr": "0,1,5,12,22,35... mod 256"},
    {"id": 12,  "name": "Hexagonal",           "beschr": "0,1,6,15,28,45... mod 256"},
    {"id": 13,  "name": "BoesingFolge²",       "beschr": "f(f(x)) mod 256, doppelte Anwendung"},
    {"id": 14,  "name": "ALFONS-Resonanz",     "beschr": "Großvater-Referenzreihe (Slot 201)"},
    {"id": 15,  "name": "RUTH-Resonanz",       "beschr": "Großmutter-Spiegelreihe (Slot 202)"},
    {"id": 16,  "name": "XOR-Kaskade",         "beschr": "x XOR (x >> 1) XOR (x >> 2)"},
    {"id": 17,  "name": "Collatz-Länge",       "beschr": "Collatz-Sequenzlänge mod 256"},
    {"id": 18,  "name": "Hamming-Gewicht",     "beschr": "Anzahl gesetzter Bits in x"},
    {"id": 19,  "name": "Gray-Code",           "beschr": "x XOR (x >> 1)"},
    {"id": 20,  "name": "Eulerphi mod 256",    "beschr": "φ(x) mod 256"},
    {"id": 21,  "name": "Divisor-Summe",       "beschr": "σ(x) mod 256"},
    {"id": 22,  "name": "Möbius-Funktion",     "beschr": "μ(x) + 128 mod 256"},
    {"id": 23,  "name": "LZ77-Muster",         "beschr": "Wiederholungsparameter-Reihe"},
    {"id": 24,  "name": "Range-Coder",         "beschr": "Wahrscheinlichkeitsverteilung"},
    {"id": 25,  "name": "Delta-Reihe",         "beschr": "Differenzen benachbarter Bytes"},
    {"id": 26,  "name": "MTF-Index",           "beschr": "Move-To-Front Positionsreihe"},
    {"id": 27,  "name": "BWT-Transform",       "beschr": "Burrows-Wheeler Reihe"},
    {"id": 28,  "name": "Huffman-Code",        "beschr": "Huffman-Baum-Tiefe mod 256"},
    {"id": 29,  "name": "RLE-Länge",           "beschr": "Run-Length Häufigkeitsreihe"},
    {"id": 30,  "name": "LZ77-Fenster",        "beschr": "Fenstergrößen-Reihe mod 256"},
    {"id": 42,  "name": "Sigma-568-Resonanz",  "beschr": "x * 568 mod 256"},
    {"id": 63,  "name": "Gronauer-Folge",      "beschr": "x * 126 mod 256"},
    {"id": 99,  "name": "Meikel-Prim-Folge",   "beschr": "x * 331 mod 256"},
    {"id": 126, "name": "Gronauer-Anker",       "beschr": "Gronauer Verankerungsreihe (126)"},
    {"id": 137, "name": "Alpha-Inv-Folge",      "beschr": "x * 137 mod 256 (Feinstruktur)"},
    {"id": 158, "name": "A2-Koeffizient",       "beschr": "x * 158 mod 256"},
    {"id": 201, "name": "ALFONS_FOLGE",         "beschr": "Großvater Alfons – Referenzanker (Slot 201)"},
    {"id": 202, "name": "RUTH_FOLGE",           "beschr": "Großmutter Ruth – Spiegel-Inversion (Slot 202)"},
    {"id": 215, "name": "A1-Koeffizient",       "beschr": "x * 215 mod 256"},
    {"id": 255, "name": "Max-Folge",            "beschr": "Alle Werte = 255 (Maximal-Reihe)"},
]
# Auffüllen auf 256 Einträge
_serie_ids = {s["id"] for s in MATHEMATISCHE_SERIEN}
for _i in range(256):
    if _i not in _serie_ids:
        MATHEMATISCHE_SERIEN.append({
            "id": _i,
            "name": f"Serie {_i:03d}",
            "beschr": f"Mathematische Transformationsreihe #{_i} (x * {_i} + {_i % 17}) mod 256"
        })
MATHEMATISCHE_SERIEN.sort(key=lambda s: s["id"])


class MBApp:
    """MB-Systeme v31 – UHCS MB 4-Ecken-Desktop Hauptklasse"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"MB-Systeme v{UHCS_VERSION} – UHCS MB – © Meikel Boesing 2026 – Gronau (Westfalen)")
        self.root.geometry("1440x900")
        self.root.minsize(1100, 700)
        self.root.configure(bg=C.BG)

        # Pfade
        self.uhcs_bin    = self._find_binary()
        self.config_dir  = Path.home() / ".mb_system"
        self.config_dir.mkdir(exist_ok=True)
        self.settings_f  = self.config_dir / "settings.json"
        self.logbuch_f   = self.config_dir / "logbuch.json"
        self.notes_f     = self.config_dir / "notes.txt"

        # Zustand
        self.settings        = self._load_json(self.settings_f, self._default_settings())
        self.logbuch: List[Dict] = self._load_json(self.logbuch_f, [])
        self.tasks: List[Dict]   = []
        self._scheduler_modus_val = "normal"
        self.co2_gramm           = 0.0

        # Tk-Variablen
        self.status_var   = tk.StringVar(value=f"MB-Systeme v{UHCS_VERSION} bereit  |  Σ={UHCS_SIGMA}  |  Prim={UHCS_PRIM}")
        self.progress_var = tk.DoubleVar(value=0.0)

        # Grid-Layout (2×2)
        for r in range(2):
            self.root.grid_rowconfigure(r, weight=1)
        self.root.grid_rowconfigure(2, weight=0)
        self.root.grid_rowconfigure(3, weight=0)
        for c in range(2):
            self.root.grid_columnconfigure(c, weight=1)

        # 4 Ecken aufbauen
        self.f_tl = self._make_corner(0, 0, "⚙  EINSTELLUNGEN & PROFILE")
        self.f_tr = self._make_corner(0, 1, "📊 LIVE SYSTEM-MONITOR")
        self.f_bl = self._make_corner(1, 0, "▶  MB-Systeme – UHCS MB  |  START")
        self.f_br = self._make_corner(1, 1, "⚡ SCHNELLZUGRIFF & NOTIZEN")

        self._build_tl()
        self._build_tr()
        self._build_bl()
        self._build_br()

        # Statusleiste
        sf = tk.Frame(self.root, bg=C.PNL, height=26)
        sf.grid(row=2, column=0, columnspan=2, sticky="ew")
        sf.grid_propagate(False)
        tk.Label(sf, textvariable=self.status_var, bg=C.PNL, fg=C.TXN,
                 font=C.FS).pack(side=tk.LEFT, padx=10, pady=3)
        tk.Label(sf, text=f"Σ={UHCS_SIGMA} · Meikel-Prim={UHCS_PRIM} · BoesingFolge",
                 bg=C.PNL, fg=C.TXD, font=C.FS).pack(side=tk.RIGHT, padx=10, pady=3)

        # Fortschrittsbalken
        pf = tk.Frame(self.root, bg=C.BG)
        pf.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        style = ttk.Style()
        style.configure("MB.Horizontal.TProgressbar",
                         troughcolor=C.INP, background=C.GRN, thickness=6)
        self.pbar = ttk.Progressbar(pf, variable=self.progress_var, maximum=100,
                                     length=600, style="MB.Horizontal.TProgressbar")
        self.pbar.pack(pady=2)

        # Binary-Warnung
        if not self.uhcs_bin:
            messagebox.showwarning(
                "uhcs fehlt",
                "uhcs-Binary nicht gefunden.\n"
                "Bitte kompilieren:\n"
                "  make -f Makefile_v31\n"
                "oder:\n"
                "  gcc -O3 -std=c11 -Wall -Wextra -pthread -march=native "
                "-o uhcs MB_uhcs_v30_KERN.c"
            )

        self._start_monitor()
        self.root.protocol("WM_DELETE_WINDOW", self._quit)

    # ══ Hilfsfunktionen ══════════════════════════════════════════════════════

    def _find_binary(self) -> Optional[Path]:
        """uhcs oder mb_meisterwerk Binary suchen (Meisterwerk bevorzugt)"""
        d = Path(__file__).parent
        # Bevorzugt: mb_meisterwerk (Monolith mit 376+ Tests)
        for name in ("mb_meisterwerk", "uhcs"):
            p = d / name
            if p.exists() and os.access(str(p), os.X_OK):
                return p
        # Im PATH suchen
        for name in ("mb_meisterwerk", "uhcs"):
            w = shutil.which(name)
            if w:
                return Path(w)
        return None

    def _default_settings(self) -> dict:
        return {
            "mode": "auto",
            "security": 0,
            "threads": os.cpu_count() or 4,
            "self_healing": True,
            "auto_days": 7,
            "sigma": UHCS_SIGMA,
            "meikel_prim": UHCS_PRIM,
        }

    def _load_json(self, path: Path, default):
        try:
            if path.exists():
                return json.loads(path.read_text("utf-8"))
        except Exception:
            pass
        return default

    def _save_json(self, path: Path, data):
        try:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
        except Exception:
            pass

    def _make_corner(self, row: int, col: int, title: str) -> tk.Frame:
        """Ecken-Panel erzeugen"""
        outer = tk.Frame(self.root, bg=C.BDR, padx=1, pady=1)
        outer.grid(row=row, column=col, sticky="nsew", padx=3, pady=3)
        inner = tk.Frame(outer, bg=C.PNL)
        inner.pack(fill=tk.BOTH, expand=True)
        hdr = tk.Frame(inner, bg=C.BDR, height=28)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text=title, bg=C.BDR, fg=C.CYN,
                 font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=8, pady=4)
        body = tk.Frame(inner, bg=C.PNL)
        body.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        return body

    def _btn(self, parent, text: str, cmd, fg=C.TXN, bg=C.CRD, font=C.FS, **kw) -> tk.Button:
        return tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                         font=font, relief="flat", activebackground=C.BDR,
                         activeforeground=C.GRN, cursor="hand2", padx=4, pady=2, **kw)

    def _lbl(self, parent, text: str, fg=C.TXN, font=C.FS, **kw) -> tk.Label:
        return tk.Label(parent, text=text, bg=C.PNL, fg=fg, font=font, **kw)

    # ══ OBEN LINKS: Einstellungen & Profile ══════════════════════════════════

    def _build_tl(self):
        f = self.f_tl

        # Einstellungen-Block
        ef = tk.LabelFrame(f, text=" Einstellungen ", bg=C.PNL, fg=C.CYN,
                           font=C.FS, bd=1, relief="solid")
        ef.pack(fill=tk.X, padx=4, pady=4)

        row0 = tk.Frame(ef, bg=C.PNL); row0.pack(fill=tk.X, padx=6, pady=2)
        tk.Label(row0, text="Modus:", bg=C.PNL, fg=C.TXN, font=C.FS).pack(side=tk.LEFT)
        self.mode_var = tk.StringVar(value=self.settings.get("mode", "auto"))
        ttk.Combobox(row0, textvariable=self.mode_var, width=14,
                     values=["auto", "schnell", "mathematisch", "delta",
                              "ultra", "text", "musik", "sicher"]).pack(side=tk.LEFT, padx=4)

        row1 = tk.Frame(ef, bg=C.PNL); row1.pack(fill=tk.X, padx=6, pady=2)
        tk.Label(row1, text="Security:", bg=C.PNL, fg=C.TXN, font=C.FS).pack(side=tk.LEFT)
        self.sec_var = tk.IntVar(value=self.settings.get("security", 0))
        tk.Spinbox(row1, from_=0, to=3, textvariable=self.sec_var, width=4,
                   bg=C.INP, fg=C.TXB, insertbackground=C.GRN).pack(side=tk.LEFT, padx=4)
        tk.Label(row1, text="Threads:", bg=C.PNL, fg=C.TXN, font=C.FS).pack(side=tk.LEFT, padx=(8, 0))
        self.thr_var = tk.IntVar(value=self.settings.get("threads", os.cpu_count() or 4))
        tk.Spinbox(row1, from_=1, to=64, textvariable=self.thr_var, width=4,
                   bg=C.INP, fg=C.TXB).pack(side=tk.LEFT, padx=4)

        row2 = tk.Frame(ef, bg=C.PNL); row2.pack(fill=tk.X, padx=6, pady=2)
        self.heal_var = tk.BooleanVar(value=self.settings.get("self_healing", True))
        tk.Checkbutton(row2, text="Selbstheilung", variable=self.heal_var,
                       bg=C.PNL, fg=C.TXN, selectcolor=C.CRD,
                       activebackground=C.PNL, font=C.FS).pack(side=tk.LEFT)
        tk.Label(row2, text="Auto-Tage:", bg=C.PNL, fg=C.TXN, font=C.FS).pack(side=tk.LEFT, padx=(10, 0))
        self.days_var = tk.IntVar(value=self.settings.get("auto_days", 7))
        tk.Spinbox(row2, from_=1, to=365, textvariable=self.days_var, width=4,
                   bg=C.INP, fg=C.TXB).pack(side=tk.LEFT, padx=4)

        bf = tk.Frame(ef, bg=C.PNL); bf.pack(fill=tk.X, padx=6, pady=(2, 6))
        self._btn(bf, "Einstellungen speichern", self._save_settings_action,
                  fg=C.GRN, bg="#002211").pack(side=tk.LEFT, padx=2)

        # Energieprofile
        epf = tk.LabelFrame(f, text=" Energieprofil ", bg=C.PNL, fg=C.ORG,
                            font=C.FS, bd=1, relief="solid")
        epf.pack(fill=tk.X, padx=4, pady=4)
        self.profil_var = tk.StringVar(value="Normal")
        for p, fg in [("Eco", C.GRN), ("Normal", C.CYN), ("Performance", C.ORG), ("Turbo", C.RED)]:
            tk.Radiobutton(epf, text=p, variable=self.profil_var, value=p,
                           bg=C.PNL, fg=fg, selectcolor=C.CRD,
                           activebackground=C.PNL, font=C.FS,
                           command=self._apply_profil).pack(side=tk.LEFT, padx=6, pady=3)

        # Make-Button
        mkf = tk.Frame(f, bg=C.PNL); mkf.pack(fill=tk.X, padx=4, pady=4)
        self._btn(mkf, "⚙ make -f Makefile_v31", self._run_make,
                  fg=C.YLW, bg="#1a1500", font=C.FN).pack(fill=tk.X)

        # v26-KERN-Module Status
        kf = tk.LabelFrame(f, text=" v26-KERN-Module ", bg=C.PNL, fg=C.PRP,
                           font=C.FS, bd=1, relief="solid")
        kf.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        kern_module = [
            ("DRK", "Differenz-Rausch-Kern"),
            ("GK",  "Gronauer-Kern"),
            ("BYZ", "Byzanz-Transform"),
            ("MESSER", "Mess-Resonanz"),
            ("PHYSIK",  "Physik-Folge"),
            ("NATUR",   "Natur-Resonanz"),
            ("GERECHT", "Gerechtigkeits-Filter"),
            ("HK",  "Haupt-Kern"),
        ]
        for i, (k, desc) in enumerate(kern_module):
            row = tk.Frame(kf, bg=C.PNL); row.pack(fill=tk.X, padx=4, pady=1)
            tk.Label(row, text=f"◆ {k}", bg=C.PNL, fg=C.PRP,
                     font=("Courier New", 8, "bold"), width=8, anchor="w").pack(side=tk.LEFT)
            tk.Label(row, text=desc, bg=C.PNL, fg=C.TXD, font=C.FS).pack(side=tk.LEFT)
            tk.Label(row, text="v31", bg=C.PNL, fg=C.GRN, font=C.FS).pack(side=tk.RIGHT, padx=4)

    # ══ OBEN RECHTS: Live System-Monitor ══════════════════════════════════════

    def _build_tr(self):
        f = self.f_tr

        # CPU
        cf = tk.Frame(f, bg=C.PNL); cf.pack(fill=tk.X, padx=4, pady=3)
        tk.Label(cf, text="CPU:", bg=C.PNL, fg=C.TXN, font=C.FS, width=8, anchor="w").pack(side=tk.LEFT)
        self.cpu_var = tk.DoubleVar(value=0.0)
        self.cpu_bar = ttk.Progressbar(cf, variable=self.cpu_var, maximum=100, length=180)
        self.cpu_bar.pack(side=tk.LEFT, padx=4)
        self.cpu_lbl = tk.Label(cf, text="0.0%", bg=C.PNL, fg=C.CYN, font=C.FS, width=6)
        self.cpu_lbl.pack(side=tk.LEFT)

        # RAM
        rf = tk.Frame(f, bg=C.PNL); rf.pack(fill=tk.X, padx=4, pady=3)
        tk.Label(rf, text="RAM:", bg=C.PNL, fg=C.TXN, font=C.FS, width=8, anchor="w").pack(side=tk.LEFT)
        self.ram_var = tk.DoubleVar(value=0.0)
        self.ram_bar = ttk.Progressbar(rf, variable=self.ram_var, maximum=100, length=180)
        self.ram_bar.pack(side=tk.LEFT, padx=4)
        self.ram_lbl = tk.Label(rf, text="0.0%", bg=C.PNL, fg=C.BLU, font=C.FS, width=6)
        self.ram_lbl.pack(side=tk.LEFT)

        # Akku
        self.bat_lbl = tk.Label(f, text="Akku: n/a", bg=C.PNL, fg=C.GLD, font=C.FS)
        self.bat_lbl.pack(anchor="w", padx=12, pady=2)

        # Disk
        self.dsk_lbl = tk.Label(f, text="Disk: n/a", bg=C.PNL, fg=C.TXN, font=C.FS)
        self.dsk_lbl.pack(anchor="w", padx=12, pady=2)

        # Trennlinie
        tk.Frame(f, bg=C.BDR, height=1).pack(fill=tk.X, padx=4, pady=4)

        # CO2 und Operationen
        self.co2_lbl = tk.Label(f, text="CO₂ gespart: 0.000 g", bg=C.PNL, fg=C.GRN, font=C.FN)
        self.co2_lbl.pack(anchor="w", padx=12, pady=2)
        self.ops_lbl = tk.Label(f, text="Operationen: 0", bg=C.PNL, fg=C.TXN, font=C.FS)
        self.ops_lbl.pack(anchor="w", padx=12, pady=2)

        # Kompressionsratio-Graph (Textbasiert)
        tk.Label(f, text="Kompressionshistorie:", bg=C.PNL, fg=C.TXD, font=C.FS).pack(
            anchor="w", padx=12, pady=(6, 0))
        self.ratio_text = ScrolledText(f, bg=C.INP, fg=C.GRN, font=("Courier New", 8),
                                        height=6, width=30, state=tk.DISABLED,
                                        wrap=tk.NONE)
        self.ratio_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Konstanten-Block
        kf = tk.Frame(f, bg=C.CRD)
        kf.pack(fill=tk.X, padx=4, pady=4)
        tk.Label(kf, text=f"Σ={UHCS_SIGMA}  Prim={UHCS_PRIM}  α⁻¹={UHCS_ALPHA_INV}",
                 bg=C.CRD, fg=C.TXD, font=("Courier New", 8)).pack(pady=3)
        tk.Label(kf, text=f"Tesla: {{0,3,6,9}}  Gronauer={UHCS_GRONAUER}",
                 bg=C.CRD, fg=C.TXD, font=("Courier New", 8)).pack(pady=1)

    # ══ UNTEN LINKS: MB-Logo + START-Button ══════════════════════════════════

    def _build_bl(self):
        f = self.f_bl

        # MB-Logo (Text)
        logo_f = tk.Frame(f, bg=C.PNL); logo_f.pack(pady=(8, 4))
        tk.Label(logo_f, text="MB", bg=C.PNL, fg=C.GRN,
                 font=("Courier New", 52, "bold")).pack()
        tk.Label(logo_f, text="SYSTEM", bg=C.PNL, fg=C.CYN,
                 font=("Courier New", 18, "bold")).pack()
        tk.Label(logo_f, text=f"v{UHCS_VERSION}", bg=C.PNL, fg=C.TXD,
                 font=("Courier New", 11)).pack()
        tk.Label(logo_f, text=f"BoesingFolge · Σ={UHCS_SIGMA}",
                 bg=C.PNL, fg=C.TXD, font=("Courier New", 8)).pack()
        tk.Label(logo_f, text="© Meikel Boesing 2026 – Gronau",
                 bg=C.PNL, fg=C.TXD, font=("Segoe UI", 8, "italic")).pack()

        # START-Button (öffnet Startmenü)
        start_f = tk.Frame(f, bg=C.PNL); start_f.pack(pady=8)
        self._btn(start_f, "▶  START  ◀", self._open_startmenu,
                  fg=C.BG, bg=C.GRN, font=("Courier New", 14, "bold")).pack(
                  ipadx=20, ipady=8)

        # Schnell-Status
        self.stat_lbl = tk.Label(f, text="Bereit", bg=C.PNL, fg=C.TXD, font=C.FS)
        self.stat_lbl.pack(pady=2)

        # Fortschritt lokal
        pf = tk.Frame(f, bg=C.PNL); pf.pack(fill=tk.X, padx=8, pady=4)
        self.pbar2 = ttk.Progressbar(pf, variable=self.progress_var, maximum=100, length=300)
        self.pbar2.pack(fill=tk.X)

    # ══ UNTEN RECHTS: Schnellzugriff + Notizen ════════════════════════════════

    def _build_br(self):
        f = self.f_br

        # Schnellzugriff-Buttons
        qf = tk.LabelFrame(f, text=" Schnellzugriff ", bg=C.PNL, fg=C.CYN,
                           font=C.FS, bd=1, relief="solid")
        qf.pack(fill=tk.X, padx=4, pady=4)

        quick_buttons = [
            ("Komprimieren",    C.GRN, self._action_compress),
            ("Dekomprimieren",  C.CYN, self._action_decompress),
            ("Lochbild C",      C.BLU, self._action_loch_c),
            ("Lochbild D",      C.BLU, self._action_loch_d),
            ("Benchmark",       C.ORG, self._action_benchmark),
            ("Logbuch",         C.PRP, self._open_logbuch),
        ]
        for i, (txt, clr, cmd) in enumerate(quick_buttons):
            row_i = i // 3
            col_i = i % 3
            if col_i == 0:
                row_fr = tk.Frame(qf, bg=C.PNL)
                row_fr.pack(fill=tk.X, pady=2, padx=4)
            self._btn(row_fr, txt, cmd, fg=clr, bg=C.CRD, font=C.FS).pack(
                side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        # Notizen
        nf = tk.LabelFrame(f, text=" Notizen ", bg=C.PNL, fg=C.TXD,
                           font=C.FS, bd=1, relief="solid")
        nf.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.notes_txt = ScrolledText(nf, bg=C.INP, fg=C.TXB, font=C.FM,
                                       wrap=tk.WORD, height=7,
                                       insertbackground=C.GRN)
        self.notes_txt.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        # Gespeicherte Notizen laden
        if self.notes_f.exists():
            try:
                self.notes_txt.insert(tk.END, self.notes_f.read_text("utf-8"))
            except Exception:
                pass
        # Notizen-Buttons
        nbf = tk.Frame(nf, bg=C.PNL); nbf.pack(fill=tk.X, padx=4, pady=(0, 4))
        self._btn(nbf, "💾 Speichern", self._save_notes,
                  fg=C.GRN, bg="#002211").pack(side=tk.LEFT, padx=2)
        self._btn(nbf, "✖ Löschen", self._clear_notes,
                  fg=C.RED, bg="#220000").pack(side=tk.LEFT, padx=2)
        self._btn(nbf, "Ext. Editor", lambda: self._open_ext("gedit"),
                  fg=C.TXN, bg=C.CRD).pack(side=tk.RIGHT, padx=2)

    # ══ STARTMENÜ ═════════════════════════════════════════════════════════════

    def _open_startmenu(self):
        """Startmenü-Popup öffnen"""
        menu = tk.Toplevel(self.root)
        menu.title("MB-Systeme v31 – UHCS MB Startmenü")
        menu.geometry("360x540")
        menu.configure(bg=C.PNL)
        menu.transient(self.root)
        menu.resizable(False, False)

        # Header
        tk.Label(menu, text="MB-Systeme", bg=C.PNL, fg=C.GRN,
                 font=("Courier New", 20, "bold")).pack(pady=(16, 0))
        tk.Label(menu, text=f"v{UHCS_VERSION}", bg=C.PNL, fg=C.TXD,
                 font=C.FN).pack()
        tk.Frame(menu, bg=C.BDR, height=1).pack(fill=tk.X, padx=20, pady=8)

        entries = [
            ("📦  Komprimieren",           C.GRN,  lambda: (menu.destroy(), self._action_compress())),
            ("📂  Dekomprimieren",          C.CYN,  lambda: (menu.destroy(), self._action_decompress())),
            ("🗂  Ordner komprimieren",     C.BLU,  lambda: (menu.destroy(), self._action_ordner())),
            ("🔐  Lochbild-Kompression",    C.BLU,  lambda: (menu.destroy(), self._action_loch_c())),
            ("🔓  Lochbild-Dekompression",  C.BLU,  lambda: (menu.destroy(), self._action_loch_d())),
            ("⚡  Benchmark",              C.ORG,  lambda: (menu.destroy(), self._action_benchmark())),
            ("📊  Serien-Explorer",         C.PRP,  lambda: (menu.destroy(), self._open_serien())),
            ("📋  TaskManager",             C.GLD,  lambda: (menu.destroy(), self._open_taskmanager())),
            ("📜  Logbuch",                 C.TXN,  lambda: (menu.destroy(), self._open_logbuch())),
            ("📖  Regelwerk",               C.CYN,  lambda: (menu.destroy(), self._open_regelwerk())),
            ("🔩  Kern-Module",             C.PRP,  lambda: (menu.destroy(), self._open_kernmodule())),
            ("🔬  Vakuum-Analyse",          C.BLU,  lambda: (menu.destroy(), self._action_vakuum())),
            ("📐  Shannon-Gap",             C.PRP,  lambda: (menu.destroy(), self._action_shannon())),
            ("🌊  Haar-Wavelet",            C.CYN,  lambda: (menu.destroy(), self._action_haar())),
            ("📑  Fusions-Manifest",        C.GLD,  lambda: (menu.destroy(), self._action_manifest())),
            ("🧪  Self-Test (737 Tests)",   C.ORG,  lambda: (menu.destroy(), self._action_self_test())),
            ("📈  Entropie-Profil",         C.PRP,  lambda: (menu.destroy(), self._action_entropie_profil())),
            ("🔗  Selbst-Verifikation",     C.CYN,  lambda: (menu.destroy(), self._action_selbst_verifikation())),
            ("🔎  System-Analyse",          C.GRN,  lambda: (menu.destroy(), self._action_system_analyse())),
            ("🎮  Scheduler-Modus",          C.CYN,  lambda: (menu.destroy(), self._action_scheduler_modus())),
            ("📊  Sprach-Frequenz",           C.BLU,  lambda: (menu.destroy(), self._action_sprach_frequenz())),
            ("🔬  Dual-Layer",                C.MAG,  lambda: (menu.destroy(), self._action_dual_layer())),
            ("🛡️  Garantie-Fallback",         C.GRN,  lambda: (menu.destroy(), self._action_garantie_fallback())),
            ("💾  Pattern-Cache",             C.CYN,  lambda: (menu.destroy(), self._action_pattern_cache())),
            ("🔢  Primzahl-Resonanz",         C.MAG,  lambda: (menu.destroy(), self._action_prim_resonanz())),
            ("📉  ARIMA-Zeitvektor",          C.BLU,  lambda: (menu.destroy(), self._action_arima_zeitvektor())),
            ("🌸  Bloom-Dedup",               C.GRN,  lambda: (menu.destroy(), self._action_bloom_dedup())),
            ("⚡  ANS-Kodierer",              C.YEL,  lambda: (menu.destroy(), self._action_ans_kodierer())),
            ("🧠  Kontext-Intelligenz",       C.PRP,  lambda: (menu.destroy(), self._action_kontext_intel())),
            ("📐  Dyn-Block-Sizer",           C.CYN,  lambda: (menu.destroy(), self._action_dyn_block())),
            ("🔗  Synergie-Matrix",           C.MAG,  lambda: (menu.destroy(), self._action_synergie_matrix())),
            ("🎯  Adaptive-Serien",           C.BLU,  lambda: (menu.destroy(), self._action_adaptive_serien())),
            ("🔧  Bit-Optimierer",            C.GRN,  lambda: (menu.destroy(), self._action_bit_optimierer())),
            ("💿  mmap-Analyse",              C.BLU,  lambda: (menu.destroy(), self._action_mmap_analyse())),
            ("🧊  Sparse-Block",              C.CYN,  lambda: (menu.destroy(), self._action_sparse_block())),
            ("🔍  Fingerprint-Delta",         C.MAG,  lambda: (menu.destroy(), self._action_fingerprint_delta())),
            ("📝  Suffix-Array BWT",          C.PRP,  lambda: (menu.destroy(), self._action_suffix_bwt())),
            ("🔒  SHA-256 Integritaet",       C.GRN,  lambda: (menu.destroy(), self._action_sha256_integ())),
            ("📇  Index-Block",               C.BLU,  lambda: (menu.destroy(), self._action_index_block())),
            ("❄️   Cold-Storage",              C.CYN,  lambda: (menu.destroy(), self._action_cold_storage())),
            ("⚙️   UHCS-Config",               C.GLD,  lambda: (menu.destroy(), self._action_uhcs_config())),
            ("🤖  RL-Pipeline",               C.MAG,  lambda: (menu.destroy(), self._action_rl_pipeline())),
            ("🔢  DezimalSprache-Erw",        C.PRP,  lambda: (menu.destroy(), self._action_dezimal_erw())),
            ("🔌  Plugin-System",             C.BLU,  lambda: (menu.destroy(), self._action_plugin_info())),
            ("📊  Fortschritt-System",        C.CYN,  lambda: (menu.destroy(), self._action_fortschritt_info())),
            ("🏆  Omega-Vollendung",          C.GLD,  lambda: (menu.destroy(), self._action_omega_vollendung())),
            # === UHCS 7.0 Erweiterte Features (TEILe CLI-CLXIV) ===
            ("📦  Format-v3 64-Bit",          C.CYN,  lambda: (menu.destroy(), self._action_format_v3())),
            ("🌊  Streaming-Kompression",     C.BLU,  lambda: (menu.destroy(), self._action_streaming())),
            ("🧠  Context-Manager",           C.VIO,  lambda: (menu.destroy(), self._action_context_mgr())),
            ("⚡  Parallel-Block",            C.GRN,  lambda: (menu.destroy(), self._action_parallel_block())),
            ("🔐  AES-256-GCM",               C.RED,  lambda: (menu.destroy(), self._action_aes_gcm())),
            ("🔄  Externe Backends",          C.CYN,  lambda: (menu.destroy(), self._action_extern_backends())),
            ("🐧  Kernel-Interface",          C.GRN,  lambda: (menu.destroy(), self._action_kernel_iface())),
            ("✅  Block-CRC32",               C.BLU,  lambda: (menu.destroy(), self._action_block_crc())),
            ("📈  Lernende Blockgröße",       C.VIO,  lambda: (menu.destroy(), self._action_lernende_block())),
            ("🚀  Deployment-Check",          C.GLD,  lambda: (menu.destroy(), self._action_deployment_check())),
            ("⚡  Vektor-Guss",               C.GRN,  lambda: (menu.destroy(), self._action_vektor_guss())),
            ("✖  Beenden",                 C.RED,  lambda: (menu.destroy(), self._quit())),
        ]
        for txt, clr, cmd in entries:
            btn = tk.Button(menu, text=txt, command=cmd,
                           bg=C.CRD, fg=clr, font=("Segoe UI", 11),
                           relief="flat", activebackground=C.BDR,
                           activeforeground=C.GRN, cursor="hand2",
                           anchor="w", padx=20)
            btn.pack(fill=tk.X, padx=20, pady=2, ipady=5)

        tk.Label(menu, text="© Meikel Boesing 2026 – Gronau (Westfalen)",
                 bg=C.PNL, fg=C.TXD, font=("Segoe UI", 7, "italic")).pack(
                 side=tk.BOTTOM, pady=8)

    # ══ UHCS CLI-Brücke ════════════════════════════════════════════════════════

    def _run_uhcs(self, mode: str, inp: str = "", out: str = "", seed: int = 0,
                  callback=None, extra: str = ""):
        """uhcs-Binary per subprocess aufrufen (CLI-Brücke, §7 Hartweizen-Guss)"""
        if not self.uhcs_bin or not self.uhcs_bin.exists():
            messagebox.showerror("Fehler", "uhcs-Binary nicht gefunden!\nBitte: make -f Makefile_v31")
            return

        def worker():
            try:
                self.progress_var.set(5)
                self.status_var.set(f"{mode} läuft...")
                self.stat_lbl.configure(text=f"{mode}...")

                cmd = [str(self.uhcs_bin)]
                if mode == "compress":
                    cmd += ["--compress", inp, "--output", out]
                elif mode == "decompress":
                    cmd += ["--decompress", inp, "--output", out]
                elif mode == "loch_c":
                    cmd += ["--lochbild-compress", inp, "--output", out, "--seed", str(seed)]
                elif mode == "loch_d":
                    cmd += ["--lochbild-decompress", inp, "--output", out, "--seed", str(seed)]
                elif mode == "benchmark":
                    cmd += ["--benchmark"]
                elif mode == "self-test":
                    cmd += ["--self-test"]
                elif mode == "ordner":
                    cmd += ["--compress", inp, "--output", out, "--recursive"]
                elif mode == "vakuum":
                    cmd += ["--vakuum-analyse", inp]
                elif mode == "shannon":
                    cmd += ["--shannon-gap", inp]
                elif mode == "haar":
                    cmd += ["--haar-gorilla", inp]
                elif mode == "manifest":
                    cmd += ["--fusions-manifest"]
                elif mode == "system-analyse":
                    cmd += ["--finale-perfektion"]
                elif mode == "entropie-profil":
                    cmd += ["--entropie-profil"]
                elif mode == "selbst-verifikation":
                    cmd += ["--selbst-verifikation"]
                elif mode == "scheduler-modus":
                    cmd += ["--scheduler-modus", self._scheduler_modus_val or "normal"]
                elif mode == "sprach-frequenz" and extra:
                    cmd += ["--sprach-frequenz", extra]
                elif mode == "dual-layer" and extra:
                    cmd += ["--dual-layer", extra]
                elif mode == "garantie-fallback" and extra:
                    cmd += ["--garantie-fallback", extra]
                elif mode == "pattern-cache":
                    cmd += ["--pattern-cache"]
                elif mode == "prim-resonanz" and extra:
                    cmd += ["--prim-resonanz", extra]
                elif mode == "arima-zeitvektor" and extra:
                    cmd += ["--arima-zeitvektor", extra]
                elif mode == "bloom-dedup":
                    cmd += ["--bloom-dedup"]
                elif mode == "ans-kodierer" and extra:
                    cmd += ["--ans-kodierer", extra]
                elif mode == "kontext-intel" and extra:
                    cmd += ["--kontext-intel", extra]
                elif mode == "dyn-block" and extra:
                    cmd += ["--dyn-block", extra]
                elif mode == "synergie-matrix" and extra:
                    cmd += ["--synergie-matrix", extra]
                elif mode == "adaptive-serien" and extra:
                    cmd += ["--adaptive-serien", extra]
                elif mode == "bit-optimierer" and extra:
                    cmd += ["--bit-optimierer", extra]
                elif mode == "mmap-analyse" and extra:
                    cmd += ["--mmap-analyse", extra]
                elif mode == "sparse-block" and extra:
                    cmd += ["--sparse-block", extra]
                elif mode == "fingerprint-delta" and extra:
                    cmd += ["--fingerprint-delta", extra]
                elif mode == "suffix-bwt" and extra:
                    cmd += ["--suffix-bwt", extra]
                elif mode == "sha256-integ" and extra:
                    cmd += ["--sha256-integ", extra]
                elif mode == "index-block" and extra:
                    cmd += ["--index-block", extra]
                elif mode == "cold-storage" and extra:
                    cmd += ["--cold-storage", extra]
                elif mode == "uhcs-config":
                    cmd += ["--uhcs-config"]
                elif mode == "rl-pipeline" and extra:
                    cmd += ["--rl-pipeline", extra]
                elif mode == "dezimal-erw" and extra:
                    cmd += ["--dezimal-erw", extra]
                elif mode == "omega-vollendung":
                    cmd += ["--omega-vollendung"]
                elif mode == "format-v3":
                    cmd += ["--format-v3", filepath] if filepath else ["--format-v3", "test"]
                elif mode == "streaming":
                    cmd += ["--streaming", filepath] if filepath else ["--streaming", "test"]
                elif mode == "context-manager":
                    cmd += ["--context-manager", filepath] if filepath else ["--context-manager", "test"]
                elif mode == "parallel-block":
                    cmd += ["--parallel-block", filepath] if filepath else ["--parallel-block", "test"]
                elif mode == "aes-gcm":
                    cmd += ["--aes-gcm", filepath] if filepath else ["--aes-gcm", "test"]
                elif mode == "extern-backends":
                    cmd += ["--extern-backends", filepath] if filepath else ["--extern-backends", "test"]
                elif mode == "kernel-interface":
                    cmd += ["--kernel-interface"]
                elif mode == "block-crc":
                    cmd += ["--block-crc", filepath] if filepath else ["--block-crc", "test"]
                elif mode == "lernende-block":
                    cmd += ["--lernende-block", filepath] if filepath else ["--lernende-block", "test"]
                elif mode == "deployment-check":
                    cmd += ["--deployment-check"]
                elif mode == "vektor-guss":
                    cmd += ["--self-test"]

                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, bufsize=1
                )

                stdout_lines = []
                stderr_lines = []

                # stderr lesen für PROGRESS:XX
                def read_stderr():
                    for line in proc.stderr:
                        stderr_lines.append(line)
                        m = re.search(r"PROGRESS:(\d+)", line)
                        if m:
                            pct = min(95, int(m.group(1)))
                            self.root.after(0, lambda p=pct: self.progress_var.set(p))

                t_err = threading.Thread(target=read_stderr, daemon=True)
                t_err.start()

                stdout_out, _ = proc.communicate(timeout=600)
                stdout_lines = stdout_out.splitlines()
                t_err.join(timeout=5)

                self.progress_var.set(98)
                rc = proc.returncode

                # CO2 berechnen (ca. 0.002 g pro MB komprimiert)
                if rc == 0 and inp and os.path.exists(inp):
                    sz = os.path.getsize(inp)
                    self.co2_gramm += (sz / (1024 * 1024)) * 0.002

                # Kompressionsratio berechnen
                ratio_str = ""
                if rc == 0 and inp and out and os.path.exists(inp) and os.path.exists(out):
                    in_sz  = os.path.getsize(inp)
                    out_sz = os.path.getsize(out)
                    if out_sz > 0:
                        ratio = in_sz / out_sz
                        ratio_str = f"{ratio:.2f}x"

                # Logbuch-Eintrag
                log_entry = {
                    "ts": datetime.now().isoformat(timespec="seconds"),
                    "mode": mode,
                    "inp": inp,
                    "out": out,
                    "rc": rc,
                    "ratio": ratio_str,
                }
                self.logbuch.append(log_entry)
                self._save_json(self.logbuch_f, self.logbuch[-500:])

                # Task-Eintrag
                self.tasks.append(log_entry)

                if rc == 0:
                    self.progress_var.set(100)
                    status = f"{mode} OK" + (f"  Ratio: {ratio_str}" if ratio_str else "")
                    self.status_var.set(status)
                    self.stat_lbl.configure(text=status)
                    # Ratio-History aktualisieren
                    self.root.after(0, lambda: self._add_ratio_entry(log_entry))
                    if callback:
                        result = "\n".join(stdout_lines[:40]) if stdout_lines else "OK"
                        self.root.after(0, lambda r=result: callback(True, r))
                    elif stdout_lines:
                        result = "\n".join(stdout_lines[:40])
                        self.root.after(0, lambda r=result: messagebox.showinfo("Ergebnis", r))
                else:
                    self.progress_var.set(0)
                    err_msg = "\n".join(stderr_lines[:20]) or "\n".join(stdout_lines[:20]) or "?"
                    self.status_var.set(f"{mode} FEHLER (rc={rc})")
                    self.stat_lbl.configure(text="FEHLER")
                    if callback:
                        self.root.after(0, lambda e=err_msg: callback(False, e))
                    else:
                        self.root.after(0, lambda e=err_msg: messagebox.showerror("Fehler", e[:800]))

            except subprocess.TimeoutExpired:
                self.progress_var.set(0)
                self.status_var.set("Timeout nach 600s")
                self.stat_lbl.configure(text="Timeout")
            except Exception as ex:
                self.progress_var.set(0)
                self.status_var.set(str(ex)[:60])
            finally:
                time.sleep(1.5)
                self.root.after(0, lambda: self.progress_var.set(0))
                self.root.after(0, lambda: self.ops_lbl.configure(
                    text=f"Operationen: {len(self.logbuch)}"))
                self.root.after(0, lambda: self.co2_lbl.configure(
                    text=f"CO₂ gespart: {self.co2_gramm:.3f} g"))

        threading.Thread(target=worker, daemon=True).start()

    def _add_ratio_entry(self, entry: dict):
        """Kompressionsratio zur History hinzufügen"""
        self.ratio_text.configure(state=tk.NORMAL)
        ts   = entry.get("ts", "")[-8:]  # nur HH:MM:SS
        mode = entry.get("mode", "?")[:8]
        ratio = entry.get("ratio", "?")
        self.ratio_text.insert(tk.END, f"{ts} {mode:8s} {ratio}\n")
        self.ratio_text.see(tk.END)
        self.ratio_text.configure(state=tk.DISABLED)

    # ══ Aktionen ══════════════════════════════════════════════════════════════

    def _action_compress(self):
        f = filedialog.askopenfilename(title="Datei komprimieren", parent=self.root)
        if not f: return
        o = filedialog.asksaveasfilename(title="Speichern als", defaultextension=".uhcs",
                                          filetypes=[("UHCS", "*.uhcs"), ("Alle", "*")],
                                          parent=self.root)
        if not o: o = f + ".uhcs"
        self._run_uhcs("compress", f, o)

    def _action_decompress(self):
        f = filedialog.askopenfilename(title="Dekomprimieren",
                                        filetypes=[("UHCS", "*.uhcs"), ("Alle", "*")],
                                        parent=self.root)
        if not f: return
        o = filedialog.asksaveasfilename(title="Wiederherstellen als", parent=self.root)
        if not o: o = f + ".restored"
        self._run_uhcs("decompress", f, o)

    def _action_ordner(self):
        d = filedialog.askdirectory(title="Ordner komprimieren", parent=self.root)
        if not d: return
        o = filedialog.asksaveasfilename(title="Ausgabe-Archiv", defaultextension=".uhcs",
                                          parent=self.root)
        if not o: o = d + ".uhcs"
        self._run_uhcs("ordner", d, o)

    def _action_loch_c(self):
        f = filedialog.askopenfilename(title="Lochbild-Kompression", parent=self.root)
        if not f: return
        o = filedialog.asksaveasfilename(title="Lochbild speichern als",
                                          defaultextension=".loch", parent=self.root)
        if not o: o = f + ".loch"
        seed = int(hashlib.sha256(f.encode()).hexdigest()[:8], 16)
        self._run_uhcs("loch_c", f, o, seed=seed)

    def _action_loch_d(self):
        f = filedialog.askopenfilename(title="Lochbild-Dekompression",
                                        filetypes=[("Lochbild", "*.loch"), ("Alle", "*")],
                                        parent=self.root)
        if not f: return
        o = filedialog.asksaveasfilename(title="Wiederherstellen", parent=self.root)
        if not o: o = f.replace(".loch", "_restored")
        seed = int(hashlib.sha256(f.replace(".loch", "").encode()).hexdigest()[:8], 16)
        self._run_uhcs("loch_d", f, o, seed=seed)

    def _action_benchmark(self):
        w = tk.Toplevel(self.root)
        w.title("Benchmark")
        w.geometry("700x400")
        w.configure(bg=C.PNL)
        tk.Label(w, text="UHCS v31 Benchmark läuft...",
                 bg=C.PNL, fg=C.ORG, font=C.FT).pack(pady=10)
        out = ScrolledText(w, bg=C.INP, fg=C.GRN, font=C.FM, height=18)
        out.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        out.insert(tk.END, f"Starte Benchmark... ({datetime.now().strftime('%H:%M:%S')})\n\n")

        def cb(ok: bool, msg: str):
            out.configure(state=tk.NORMAL)
            out.insert(tk.END, msg + "\n")
            if ok:
                out.insert(tk.END, f"\n✅ Benchmark abgeschlossen\n")
            else:
                out.insert(tk.END, f"\n❌ Fehler: {msg}\n")
            out.see(tk.END)

        self._run_uhcs("benchmark", callback=cb)

    # ══ TEIL LXXXVI-XCI Analyse-Aktionen (Fusion v31) ═════════════════════════

    def _action_vakuum(self):
        """VakuumPrediktor & PatternOfPatterns (TEIL LXXXVI)"""
        f = filedialog.askopenfilename(title="Datei für Vakuum-Analyse")
        if not f:
            return
        w = tk.Toplevel(self.root)
        w.title("Vakuum-Analyse – TEIL LXXXVI")
        w.geometry("700x350")
        w.configure(bg=C.PNL)
        out = ScrolledText(w, bg=C.INP, fg=C.GRN, font=C.FM, height=16)
        out.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        out.insert(tk.END, f"Analysiere: {f}\n\n")
        def cb(ok, msg):
            out.configure(state=tk.NORMAL)
            out.insert(tk.END, msg + "\n")
            out.see(tk.END)
        self._run_uhcs("vakuum", inp=f, callback=cb)

    def _action_shannon(self):
        """ShannonGapAnalyzer (TEIL LXXXIX)"""
        f = filedialog.askopenfilename(title="Datei für Shannon-Gap-Analyse")
        if not f:
            return
        w = tk.Toplevel(self.root)
        w.title("Shannon-Gap – TEIL LXXXIX")
        w.geometry("700x350")
        w.configure(bg=C.PNL)
        out = ScrolledText(w, bg=C.INP, fg=C.GRN, font=C.FM, height=16)
        out.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        out.insert(tk.END, f"Analysiere: {f}\n\n")
        def cb(ok, msg):
            out.configure(state=tk.NORMAL)
            out.insert(tk.END, msg + "\n")
            out.see(tk.END)
        self._run_uhcs("shannon", inp=f, callback=cb)

    def _action_haar(self):
        """HaarWavelet & GorillaEncoder (TEIL XC)"""
        f = filedialog.askopenfilename(title="Datei für Haar-Wavelet-Analyse")
        if not f:
            return
        w = tk.Toplevel(self.root)
        w.title("Haar-Wavelet – TEIL XC")
        w.geometry("700x350")
        w.configure(bg=C.PNL)
        out = ScrolledText(w, bg=C.INP, fg=C.GRN, font=C.FM, height=16)
        out.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        out.insert(tk.END, f"Analysiere: {f}\n\n")
        def cb(ok, msg):
            out.configure(state=tk.NORMAL)
            out.insert(tk.END, msg + "\n")
            out.see(tk.END)
        self._run_uhcs("haar", inp=f, callback=cb)

    def _action_manifest(self):
        """Fusions-Manifest & Gesamt-Validator (TEIL XCI)"""
        w = tk.Toplevel(self.root)
        w.title("Fusions-Manifest – TEIL XCI")
        w.geometry("700x350")
        w.configure(bg=C.PNL)
        out = ScrolledText(w, bg=C.INP, fg=C.GRN, font=C.FM, height=16)
        out.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        out.insert(tk.END, "Generiere Fusions-Manifest...\n\n")
        def cb(ok, msg):
            out.configure(state=tk.NORMAL)
            out.insert(tk.END, msg + "\n")
            out.see(tk.END)
        self._run_uhcs("manifest", callback=cb)

    def _action_system_analyse(self):
        """System-Analyse: Finale-Perfektion-Zertifikat (TEIL CXXII) — Min/Max-Werte"""
        w = tk.Toplevel(self.root)
        w.title("System-Analyse – Finale Perfektion (TEIL CXXII)")
        w.geometry("780x500")
        w.configure(bg=C.PNL)
        tk.Label(w, text="🔎  MB-Systeme v31 – System-Analyse",
                 bg=C.PNL, fg=C.GLD, font=C.FT).pack(pady=(10, 0))
        tk.Label(w, text="20-Punkt-Audit · Entropie · Integrität · Freigabe-Zertifikat",
                 bg=C.PNL, fg=C.TXD, font=C.FS).pack()
        out = ScrolledText(w, bg=C.INP, fg=C.GRN, font=C.FM, height=22)
        out.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        out.insert(tk.END, f"System-Analyse gestartet ({datetime.now().strftime('%H:%M:%S')})\n")
        out.insert(tk.END, "Prüfe: LUT/INV · Boesing · Entropie · Roundtrip · Freigabe\n\n")
        def cb(ok, msg):
            out.configure(state=tk.NORMAL)
            out.insert(tk.END, msg + "\n")
            if ok:
                out.insert(tk.END, "\n✅ System-Analyse abgeschlossen\n")
            else:
                out.insert(tk.END, "\n❌ Fehler bei System-Analyse\n")
            out.see(tk.END)
        self._run_uhcs("system-analyse", callback=cb)

    def _action_self_test(self):
        """Self-Test: 571 Tests, HARDWARE-REIF Prüfung"""
        w = tk.Toplevel(self.root)
        w.title("Self-Test – MB-Systeme v31 (571 Tests)")
        w.geometry("780x500")
        w.configure(bg=C.PNL)
        tk.Label(w, text="🧪  MB-Systeme v31 – Self-Test",
                 bg=C.PNL, fg=C.ORG, font=C.FT).pack(pady=(10, 0))
        tk.Label(w, text="122 TEILe · 280 Paragraphen · Hardware-Reif-Prüfung",
                 bg=C.PNL, fg=C.TXD, font=C.FS).pack()
        out = ScrolledText(w, bg=C.INP, fg=C.GRN, font=C.FM, height=22)
        out.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        out.insert(tk.END, f"Self-Test gestartet ({datetime.now().strftime('%H:%M:%S')})\n\n")
        def cb(ok, msg):
            out.configure(state=tk.NORMAL)
            out.insert(tk.END, msg + "\n")
            if ok:
                out.insert(tk.END, "\n✅ Self-Test abgeschlossen\n")
            else:
                out.insert(tk.END, "\n❌ Self-Test fehlgeschlagen\n")
            out.see(tk.END)
        self._run_uhcs("self-test", callback=cb)

    def _action_entropie_profil(self):
        """Entropie-Profil-Analysator (TEIL CXX): Shannon/Chi²/Kompressibilität"""
        w = tk.Toplevel(self.root)
        w.title("Entropie-Profil – TEIL CXX")
        w.geometry("700x400")
        w.configure(bg=C.PNL)
        tk.Label(w, text="📈  Entropie-Profil-Analysator",
                 bg=C.PNL, fg=C.PRP, font=C.FT).pack(pady=(10, 0))
        tk.Label(w, text="Shannon-Entropie · Chi²-Verteilung · Kompressibilität",
                 bg=C.PNL, fg=C.TXD, font=C.FS).pack()
        out = ScrolledText(w, bg=C.INP, fg=C.GRN, font=C.FM, height=18)
        out.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        out.insert(tk.END, f"Entropie-Profil-Analyse ({datetime.now().strftime('%H:%M:%S')})\n\n")
        def cb(ok, msg):
            out.configure(state=tk.NORMAL)
            out.insert(tk.END, msg + "\n")
            if ok:
                out.insert(tk.END, "\n✅ Entropie-Profil abgeschlossen\n")
            else:
                out.insert(tk.END, "\n❌ Fehler bei Entropie-Profil\n")
            out.see(tk.END)
        self._run_uhcs("entropie-profil", callback=cb)

    def _action_selbst_verifikation(self):
        """Selbst-Verifikations-Kette (TEIL CXXI): Siegel/Tamper/Beweis"""
        w = tk.Toplevel(self.root)
        w.title("Selbst-Verifikation – TEIL CXXI")
        w.geometry("700x400")
        w.configure(bg=C.PNL)
        tk.Label(w, text="🔗  Selbst-Verifikations-Kette",
                 bg=C.PNL, fg=C.CYN, font=C.FT).pack(pady=(10, 0))
        tk.Label(w, text="Siegel-Kette · Tamper-Detection · Integritäts-Beweis",
                 bg=C.PNL, fg=C.TXD, font=C.FS).pack()
        out = ScrolledText(w, bg=C.INP, fg=C.GRN, font=C.FM, height=18)
        out.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        out.insert(tk.END, f"Selbst-Verifikation ({datetime.now().strftime('%H:%M:%S')})\n\n")
        def cb(ok, msg):
            out.configure(state=tk.NORMAL)
            out.insert(tk.END, msg + "\n")
            if ok:
                out.insert(tk.END, "\n✅ Selbst-Verifikation abgeschlossen\n")
            else:
                out.insert(tk.END, "\n❌ Fehler bei Selbst-Verifikation\n")
            out.see(tk.END)
        self._run_uhcs("selbst-verifikation", callback=cb)

    def _action_scheduler_modus(self):
        """Scheduler-Modus: Gaming/Arbeits-Modus (TEIL CXXIII)"""
        import tkinter.simpledialog as sd
        modus = sd.askstring("Scheduler-Modus", "Modus eingeben (normal/arbeit/gaming/ultra):",
                             initialvalue="normal")
        if not modus:
            return
        self._scheduler_modus_val = modus
        w = tk.Toplevel(self.root)
        w.title(f"Scheduler-Modus – {modus.upper()} (TEIL CXXIII)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#00ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  Scheduler-Modus '{modus}' wird aktiviert...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            if ok:
                out.insert(tk.END, f"🎮  SCHEDULER-MODUS: {modus.upper()}\n{'='*60}\n{txt}\n")
            else:
                out.insert(tk.END, f"\n❌ Fehler: {txt}\n")
            out.see(tk.END)
        self._run_uhcs("scheduler-modus", callback=cb)

    def _action_sprach_frequenz(self):
        """Sprach-Frequenz-Analyse (TEIL CXXIV)"""
        path = filedialog.askopenfilename(title="Datei fuer Sprach-Frequenz-Analyse")
        if not path:
            return
        w = tk.Toplevel(self.root)
        w.title("Sprach-Frequenz-Analyse (TEIL CXXIV)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#00ccff", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  Analysiere {os.path.basename(path)}...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            if ok:
                out.insert(tk.END, f"📊  SPRACH-FREQUENZ-ANALYSE\n{'='*60}\n{txt}\n")
            else:
                out.insert(tk.END, f"\n❌ Fehler: {txt}\n")
            out.see(tk.END)
        self._run_uhcs("sprach-frequenz", callback=cb, extra=path)

    def _action_dual_layer(self):
        """Dual-Layer Meta-Kompression (TEIL CXXV)"""
        path = filedialog.askopenfilename(title="Datei fuer Dual-Layer Kompression")
        if not path:
            return
        w = tk.Toplevel(self.root)
        w.title("Dual-Layer Meta-Kompression (TEIL CXXV)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#ff99cc", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  Dual-Layer Analyse {os.path.basename(path)}...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            if ok:
                out.insert(tk.END, f"🔬  DUAL-LAYER META-KOMPRESSION\n{'='*60}\n{txt}\n")
            else:
                out.insert(tk.END, f"\n❌ Fehler: {txt}\n")
            out.see(tk.END)
        self._run_uhcs("dual-layer", callback=cb, extra=path)

    def _action_garantie_fallback(self):
        """Garantie-Fallback Kompression (TEIL CXXVI)"""
        path = filedialog.askopenfilename(title="Datei fuer Garantie-Fallback Test")
        if not path:
            return
        w = tk.Toplevel(self.root)
        w.title("Garantierte Dreifach-Fallback (TEIL CXXVI)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  Teste Garantie-Fallback {os.path.basename(path)}...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            if ok:
                out.insert(tk.END, f"🛡️  GARANTIERTE DREIFACH-FALLBACK\n{'='*60}\n{txt}\n")
            else:
                out.insert(tk.END, f"\n❌ Fehler: {txt}\n")
            out.see(tk.END)
        self._run_uhcs("garantie-fallback", callback=cb, extra=path)

    # --- Methoden fuer v31 erweiterte TEILe CXXVII-CXXXVI ---

    def _action_pattern_cache(self):
        """Pattern-Cache Analyse"""
        w = tk.Toplevel(self.root)
        w.title("Pattern-Cache (TEIL CXXVIII)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, "⏳  Pattern-Cache Analyse...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"💾  PATTERN-CACHE\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("pattern-cache", callback=cb)

    def _action_prim_resonanz(self):
        """Primzahl-Resonanz Analyse"""
        path = filedialog.askopenfilename(title="Datei fuer Primzahl-Resonanz")
        if not path: return
        w = tk.Toplevel(self.root)
        w.title("Primzahl-Resonanz (TEIL CXXIX)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  Primzahl-Resonanz {os.path.basename(path)}...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"🔢  PRIMZAHL-RESONANZ\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("prim-resonanz", callback=cb, extra=path)

    def _action_arima_zeitvektor(self):
        """ARIMA-Zeitvektor Analyse"""
        path = filedialog.askopenfilename(title="Datei fuer ARIMA-Zeitvektor")
        if not path: return
        w = tk.Toplevel(self.root)
        w.title("ARIMA-Zeitvektor (TEIL CXXX)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  ARIMA {os.path.basename(path)}...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"📉  ARIMA-ZEITVEKTOR\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("arima-zeitvektor", callback=cb, extra=path)

    def _action_bloom_dedup(self):
        """Bloom-Dedup Check"""
        w = tk.Toplevel(self.root)
        w.title("Bloom-Dedup (TEIL CXXXI)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, "⏳  Bloom-Dedup...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"🌸  BLOOM-DEDUP\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("bloom-dedup", callback=cb)

    def _action_ans_kodierer(self):
        """ANS-Kodierer Analyse"""
        path = filedialog.askopenfilename(title="Datei fuer ANS-Kodierer")
        if not path: return
        w = tk.Toplevel(self.root)
        w.title("ANS-Kodierer (TEIL CXXXII)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  ANS {os.path.basename(path)}...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"⚡  ANS-KODIERER\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("ans-kodierer", callback=cb, extra=path)

    def _action_kontext_intel(self):
        """Kontext-Intelligenz Analyse"""
        path = filedialog.askopenfilename(title="Datei fuer Kontext-Intelligenz")
        if not path: return
        w = tk.Toplevel(self.root)
        w.title("Kontext-Intelligenz (TEIL CXXXIII)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  Kontext-Analyse {os.path.basename(path)}...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"🧠  KONTEXT-INTELLIGENZ\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("kontext-intel", callback=cb, extra=path)

    def _action_dyn_block(self):
        """Dynamischer Block-Sizer"""
        path = filedialog.askopenfilename(title="Datei fuer Dyn-Block-Sizer")
        if not path: return
        w = tk.Toplevel(self.root)
        w.title("Dyn-Block-Sizer (TEIL CXXXIV)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  Block-Analyse {os.path.basename(path)}...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"📐  DYN-BLOCK-SIZER\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("dyn-block", callback=cb, extra=path)

    def _action_synergie_matrix(self):
        """Synergie-Matrix Analyse"""
        path = filedialog.askopenfilename(title="Datei fuer Synergie-Matrix")
        if not path: return
        w = tk.Toplevel(self.root)
        w.title("Synergie-Matrix (TEIL CXXXV)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  Synergie-Analyse {os.path.basename(path)}...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"🔗  SYNERGIE-MATRIX\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("synergie-matrix", callback=cb, extra=path)

    def _action_adaptive_serien(self):
        """Adaptive-Serien Analyse"""
        path = filedialog.askopenfilename(title="Datei fuer Adaptive-Serien")
        if not path: return
        w = tk.Toplevel(self.root)
        w.title("Adaptive-Serien (TEIL CXXXVI)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  Adaptive-Serien {os.path.basename(path)}...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"🎯  ADAPTIVE-SERIEN\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("adaptive-serien", callback=cb, extra=path)

    def _action_bit_optimierer(self):
        """Bit-Optimierer Analyse"""
        path = filedialog.askopenfilename(title="Datei fuer Bit-Optimierer")
        if not path: return
        w = tk.Toplevel(self.root)
        w.title("Bit-Optimierer (TEIL CXXXVI)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  Bit-Optimierung {os.path.basename(path)}...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"🔧  BIT-OPTIMIERER\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("bit-optimierer", callback=cb, extra=path)

    # --- Methoden fuer UHCS 7.0 TEILe CXXXVII-CL ---

    def _action_mmap_analyse(self):
        """mmap-Datei-I/O Analyse (TEIL CXXXVII)"""
        path = filedialog.askopenfilename(title="Datei fuer mmap-Analyse")
        if not path: return
        w = tk.Toplevel(self.root)
        w.title("mmap-Datei-I/O (TEIL CXXXVII)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  mmap-Analyse {os.path.basename(path)}...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"💿  MMAP-DATEI-I/O\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("mmap-analyse", callback=cb, extra=path)

    def _action_sparse_block(self):
        """Sparse-Block-Optimierung (TEIL CXXXVIII)"""
        path = filedialog.askopenfilename(title="Datei fuer Sparse-Block")
        if not path: return
        w = tk.Toplevel(self.root)
        w.title("Sparse-Block (TEIL CXXXVIII)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  Sparse-Block {os.path.basename(path)}...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"🧊  SPARSE-BLOCK-OPTIMIERUNG\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("sparse-block", callback=cb, extra=path)

    def _action_fingerprint_delta(self):
        """Fingerprint-Delta-Kompression (TEIL CXXXIX)"""
        path = filedialog.askopenfilename(title="Datei fuer Fingerprint-Delta")
        if not path: return
        w = tk.Toplevel(self.root)
        w.title("Fingerprint-Delta (TEIL CXXXIX)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  Fingerprint-Delta {os.path.basename(path)}...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"🔍  FINGERPRINT-DELTA\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("fingerprint-delta", callback=cb, extra=path)

    def _action_suffix_bwt(self):
        """Suffix-Array BWT-Beschleunigung (TEIL CXL)"""
        path = filedialog.askopenfilename(title="Datei fuer Suffix-Array BWT")
        if not path: return
        w = tk.Toplevel(self.root)
        w.title("Suffix-Array BWT (TEIL CXL)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  Suffix-Array BWT {os.path.basename(path)}...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"📝  SUFFIX-ARRAY BWT\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("suffix-bwt", callback=cb, extra=path)

    def _action_sha256_integ(self):
        """SHA-256 Integritaets-Pruefung (TEIL CXLII)"""
        path = filedialog.askopenfilename(title="Datei fuer SHA-256 Integritaet")
        if not path: return
        w = tk.Toplevel(self.root)
        w.title("SHA-256 Integritaet (TEIL CXLII)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  SHA-256 {os.path.basename(path)}...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"🔒  SHA-256 INTEGRITAET\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("sha256-integ", callback=cb, extra=path)

    def _action_index_block(self):
        """Index-Block am Dateiende (TEIL CXLIII)"""
        path = filedialog.askopenfilename(title="Datei fuer Index-Block")
        if not path: return
        w = tk.Toplevel(self.root)
        w.title("Index-Block (TEIL CXLIII)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  Index-Block {os.path.basename(path)}...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"📇  INDEX-BLOCK\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("index-block", callback=cb, extra=path)

    def _action_cold_storage(self):
        """Cold-Storage Tiefschlaf-Manager (TEIL CXLV)"""
        path = filedialog.askopenfilename(title="Datei fuer Cold-Storage")
        if not path: return
        w = tk.Toplevel(self.root)
        w.title("Cold-Storage (TEIL CXLV)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  Cold-Storage {os.path.basename(path)}...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"❄️  COLD-STORAGE\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("cold-storage", callback=cb, extra=path)

    def _action_uhcs_config(self):
        """UHCS-Config Konfigurations-Manager (TEIL CXLVI)"""
        w = tk.Toplevel(self.root)
        w.title("UHCS-Config (TEIL CXLVI)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, "⏳  UHCS-Config laden...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"⚙️  UHCS KONFIGURATIONS-MANAGER\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("uhcs-config", callback=cb)

    def _action_rl_pipeline(self):
        """RL-Pipeline-Optimierer (TEIL CXLVIII)"""
        path = filedialog.askopenfilename(title="Datei fuer RL-Pipeline")
        if not path: return
        w = tk.Toplevel(self.root)
        w.title("RL-Pipeline (TEIL CXLVIII)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  RL-Pipeline {os.path.basename(path)}...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"🤖  RL-PIPELINE-OPTIMIERER\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("rl-pipeline", callback=cb, extra=path)

    def _action_dezimal_erw(self):
        """DezimalSprache Erweiterung (TEIL CXLIX)"""
        path = filedialog.askopenfilename(title="Datei fuer DezimalSprache")
        if not path: return
        w = tk.Toplevel(self.root)
        w.title("DezimalSprache-Erweiterung (TEIL CXLIX)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  DezimalSprache {os.path.basename(path)}...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"🔢  DEZIMALSPRACHE-ERWEITERUNG\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("dezimal-erw", callback=cb, extra=path)

    def _action_plugin_info(self):
        """Plugin-System Info (TEIL CXLIV)"""
        w = tk.Toplevel(self.root)
        w.title("Plugin-System (TEIL CXLIV)")
        w.geometry("700x300")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, "🔌  PLUGIN-SCHNITTSTELLE\n" + "="*60 + "\n")
        out.insert(tk.END, "ABI-Version: 1\n")
        out.insert(tk.END, "Kann komprimieren: ✓\nKann dekomprimieren: ✓\nKann analysieren: ✓\n")
        out.insert(tk.END, "\nPlugins werden ueber --plugin-register geladen.\n")
        out.insert(tk.END, "Stabile C-ABI fuer externe Kompressoren.\n")

    def _action_fortschritt_info(self):
        """Fortschritts-Callback-System Info (TEIL CXLI)"""
        w = tk.Toplevel(self.root)
        w.title("Fortschritts-System (TEIL CXLI)")
        w.geometry("700x300")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, "📊  FORTSCHRITTS-CALLBACK-SYSTEM\n" + "="*60 + "\n")
        out.insert(tk.END, "Ermoeglicht GUI-Integration und Fortschrittsanzeige.\n")
        out.insert(tk.END, "Callback wird alle N Bytes aufgerufen.\n")
        out.insert(tk.END, "Integriert in CLI via PROGRESS:XX stderr-Meldungen.\n")
        out.insert(tk.END, "\nDiese GUI nutzt das System bereits fuer die Fortschrittsleiste.\n")

    def _action_omega_vollendung(self):
        """Omega-Vollendung Universal-Zertifikat (TEIL CL)"""
        w = tk.Toplevel(self.root)
        w.title("Omega-Vollendung (TEIL CL)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, "⏳  Omega-Vollendung...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"🏆  OMEGA-VOLLENDUNG & UNIVERSAL-ZERTIFIKAT\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("omega-vollendung", callback=cb)

    # === UHCS 7.0 Erweiterte Features – Aktionsmethoden ===

    def _action_format_v3(self):
        """Format v3 64-Bit Analyse (TEIL CLI)"""
        path = filedialog.askopenfilename(title="Datei für Format-v3 Analyse")
        if not path:
            return
        w = tk.Toplevel(self.root)
        w.title("Format v3 — 64-Bit (TEIL CLI)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  Format-v3 Analyse: {path}\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"📦  FORMAT V3 — 64-BIT\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("format-v3", filepath=path, callback=cb)

    def _action_streaming(self):
        """Streaming-Kompression (TEIL CLII)"""
        path = filedialog.askopenfilename(title="Datei für Streaming-Kompression")
        if not path:
            return
        w = tk.Toplevel(self.root)
        w.title("Streaming-Kompression (TEIL CLII)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  Streaming: {path}\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"🌊  STREAMING-KOMPRESSION\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("streaming", filepath=path, callback=cb)

    def _action_context_mgr(self):
        """Context-Manager Hybrid (TEIL CLIII)"""
        path = filedialog.askopenfilename(title="Datei für Context-Manager Analyse")
        if not path:
            return
        w = tk.Toplevel(self.root)
        w.title("Context-Manager (TEIL CLIII)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  Context-Manager: {path}\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"🧠  CONTEXT-MANAGER HYBRID\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("context-manager", filepath=path, callback=cb)

    def _action_parallel_block(self):
        """Parallele Block-Kompression (TEIL CLIV)"""
        path = filedialog.askopenfilename(title="Datei für Parallel-Block")
        if not path:
            return
        w = tk.Toplevel(self.root)
        w.title("Parallele Block-Kompression (TEIL CLIV)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  Parallel-Block: {path}\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"⚡  PARALLELE BLOCK-KOMPRESSION\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("parallel-block", filepath=path, callback=cb)

    def _action_aes_gcm(self):
        """AES-256-GCM Verschlüsselung (TEIL CLV)"""
        path = filedialog.askopenfilename(title="Datei für AES-256-GCM")
        if not path:
            return
        w = tk.Toplevel(self.root)
        w.title("AES-256-GCM (TEIL CLV)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  AES-256-GCM: {path}\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"🔐  AES-256-GCM VERSCHLÜSSELUNG\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("aes-gcm", filepath=path, callback=cb)

    def _action_extern_backends(self):
        """Externe Backend-Vergleich (TEIL CLVI)"""
        path = filedialog.askopenfilename(title="Datei für Backend-Vergleich")
        if not path:
            return
        w = tk.Toplevel(self.root)
        w.title("Externe Backends (TEIL CLVI)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  Backend-Vergleich: {path}\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"🔄  EXTERNE BACKEND-VERGLEICH\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("extern-backends", filepath=path, callback=cb)

    def _action_kernel_iface(self):
        """Linux-Kernel-Interface (TEIL CLVII)"""
        w = tk.Toplevel(self.root)
        w.title("Kernel-Interface (TEIL CLVII)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, "⏳  Kernel-Interface...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"🐧  LINUX-KERNEL-INTERFACE\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("kernel-interface", callback=cb)

    def _action_block_crc(self):
        """Per-Block-CRC32 (TEIL CLVIII)"""
        path = filedialog.askopenfilename(title="Datei für Block-CRC32")
        if not path:
            return
        w = tk.Toplevel(self.root)
        w.title("Block-CRC32 (TEIL CLVIII)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  Block-CRC32: {path}\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"✅  PER-BLOCK-CRC32\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("block-crc", filepath=path, callback=cb)

    def _action_lernende_block(self):
        """Lernende Blockgröße (TEIL CLIX)"""
        path = filedialog.askopenfilename(title="Datei für Lernende Blockgröße")
        if not path:
            return
        w = tk.Toplevel(self.root)
        w.title("Lernende Blockgröße (TEIL CLIX)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, f"⏳  Lernende Blockgröße: {path}\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"📈  LERNENDE BLOCKGRÖẞE\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("lernende-block", filepath=path, callback=cb)

    def _action_deployment_check(self):
        """Deployment-Check & STRICT_MODE (TEIL CLXIV)"""
        w = tk.Toplevel(self.root)
        w.title("Deployment-Check (TEIL CLXIV)")
        w.geometry("700x400")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, "⏳  Deployment-Check...\n")
        def cb(ok, txt):
            out.delete("1.0", tk.END)
            out.insert(tk.END, f"🚀  DEPLOYMENT-CHECK\n{'='*60}\n{txt}\n")
            out.see(tk.END)
        self._run_uhcs("deployment-check", callback=cb)

    def _action_vektor_guss(self):
        """Gronauer-Vektor-Guss: Hardware-Statik Validierung (TEIL CLXXI)"""
        w = tk.Toplevel(self.root)
        w.title("Gronauer-Vektor-Guss (TEIL CLXXI)")
        w.geometry("700x500")
        out = tk.Text(w, bg="#1a1a2e", fg="#99ff99", font=("Consolas", 10), wrap=tk.WORD)
        out.pack(fill=tk.BOTH, expand=True)
        out.insert(tk.END, "⚡  Gronauer-Vektor-Guss — Hardware-Statik...\n")
        out.insert(tk.END, "="*60 + "\n")
        out.insert(tk.END, "  BoesingFolge: f(x) = (42x³+158x²+215x+27) mod 256\n")
        out.insert(tk.END, "  Sigma-Sperre: 568 (42+158+215+27+126)\n")
        out.insert(tk.END, "  Branchless Perfekt-Step · AVX-512 Vektor-Pfad\n")
        out.insert(tk.END, "  9-Bit-Differenz-Siegel · Cache-Line Alignment 64B\n")
        out.insert(tk.END, "  LZ77/Huffman: DEAKTIVIERT — MB-eigene Pipeline\n")
        out.insert(tk.END, "="*60 + "\n\n")
        out.insert(tk.END, "⏳  Starte 742 Selbsttests...\n\n")
        def cb(ok, txt):
            out.insert(tk.END, txt + "\n")
            if ok:
                out.insert(tk.END, "\n✅  GRONAUER-VEKTOR-GUSS: VERSIEGELT\n")
            else:
                out.insert(tk.END, "\n❌  FEHLER IM GUSS — Sigma-Sperre aktiv\n")
            out.see(tk.END)
        self._run_uhcs("vektor-guss", callback=cb)

    def _save_settings_action(self):
        self.settings.update({
            "mode": self.mode_var.get(),
            "security": self.sec_var.get(),
            "threads": self.thr_var.get(),
            "self_healing": self.heal_var.get(),
            "auto_days": self.days_var.get(),
        })
        self._save_json(self.settings_f, self.settings)
        self.status_var.set("Einstellungen gespeichert")

    def _apply_profil(self):
        p = self.profil_var.get()
        if p == "Eco":
            self.mode_var.set("schnell"); self.thr_var.set(1)
        elif p == "Normal":
            self.mode_var.set("auto"); self.thr_var.set(os.cpu_count() or 4)
        elif p == "Performance":
            self.mode_var.set("mathematisch"); self.thr_var.set(os.cpu_count() or 4)
        elif p == "Turbo":
            self.mode_var.set("ultra"); self.thr_var.set(min(64, (os.cpu_count() or 4) * 2))
        self.status_var.set(f"Energieprofil: {p}")

    def _run_make(self):
        """make -f Makefile_v31 aufrufen"""
        def worker():
            try:
                result = subprocess.run(
                    ["make", "-f", "Makefile_v31"],
                    capture_output=True, text=True, timeout=120,
                    cwd=str(Path(__file__).parent)
                )
                if result.returncode == 0:
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Make", f"✅ Build erfolgreich!\n\n{result.stdout[:600]}"))
                    self.uhcs_bin = self._find_binary()
                else:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Make Fehler", result.stderr[:800] or result.stdout[:800]))
            except subprocess.TimeoutExpired:
                self.root.after(0, lambda: messagebox.showerror("Make", "Timeout!"))
            except FileNotFoundError:
                self.root.after(0, lambda: messagebox.showerror("Make", "make nicht gefunden!"))

        threading.Thread(target=worker, daemon=True).start()

    # ══ Popup-Fenster ═════════════════════════════════════════════════════════

    def _open_serien(self):
        """256 Mathematische Serien-Explorer"""
        w = tk.Toplevel(self.root)
        w.title("Serien-Explorer – 256 Mathematische Reihen")
        w.geometry("760x520")
        w.configure(bg=C.PNL)

        tk.Label(w, text="256 Mathematische Serien – UHCS v31",
                 bg=C.PNL, fg=C.PRP, font=C.FT).pack(pady=(10, 4))
        tk.Label(w, text=f"BoesingFolge · Σ={UHCS_SIGMA} · Meikel-Prim={UHCS_PRIM}",
                 bg=C.PNL, fg=C.TXD, font=C.FS).pack()

        # Suchleiste
        sf = tk.Frame(w, bg=C.PNL); sf.pack(fill=tk.X, padx=8, pady=4)
        tk.Label(sf, text="Suche:", bg=C.PNL, fg=C.TXN, font=C.FS).pack(side=tk.LEFT)
        search_var = tk.StringVar()
        tk.Entry(sf, textvariable=search_var, bg=C.INP, fg=C.TXB, font=C.FS,
                  insertbackground=C.GRN, width=30).pack(side=tk.LEFT, padx=4)

        # Tabelle
        cols = ("ID", "Name", "Beschreibung")
        tree = ttk.Treeview(w, columns=cols, show="headings", height=22)
        tree.heading("ID",         text="ID")
        tree.heading("Name",       text="Name")
        tree.heading("Beschreibung", text="Beschreibung")
        tree.column("ID",          width=45,  anchor="center")
        tree.column("Name",        width=200, anchor="w")
        tree.column("Beschreibung", width=460, anchor="w")

        sb = ttk.Scrollbar(w, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=8)
        sb.pack(side=tk.LEFT, fill=tk.Y, pady=8, padx=(0, 8))

        def populate(filter_str=""):
            tree.delete(*tree.get_children())
            for s in MATHEMATISCHE_SERIEN:
                if filter_str.lower() in s["name"].lower() or \
                   filter_str.lower() in s["beschr"].lower() or \
                   filter_str == str(s["id"]):
                    tree.insert("", tk.END, values=(s["id"], s["name"], s["beschr"]))

        populate()
        search_var.trace("w", lambda *_: populate(search_var.get()))
        tk.Label(w, text=f"Gesamt: {len(MATHEMATISCHE_SERIEN)} Serien",
                 bg=C.PNL, fg=C.TXD, font=C.FS).pack(pady=4)

    def _open_taskmanager(self):
        """TaskManager – vergangene Kompressionsaufgaben"""
        w = tk.Toplevel(self.root)
        w.title("TaskManager – Kompressionsaufgaben")
        w.geometry("820x460")
        w.configure(bg=C.PNL)

        tk.Label(w, text="TaskManager – Vergangene Kompressionsaufgaben",
                 bg=C.PNL, fg=C.GLD, font=C.FT).pack(pady=(10, 4))

        cols = ("Nr", "Zeitstempel", "Modus", "Eingabe", "Ausgabe", "Ratio", "Status")
        tree = ttk.Treeview(w, columns=cols, show="headings", height=18)
        for col, width in [("Nr", 40), ("Zeitstempel", 150), ("Modus", 80),
                           ("Eingabe", 200), ("Ausgabe", 150), ("Ratio", 60), ("Status", 60)]:
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor="w")

        sb = ttk.Scrollbar(w, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=8)
        sb.pack(side=tk.LEFT, fill=tk.Y, pady=8, padx=(0, 8))

        all_tasks = self.logbuch + self.tasks
        for i, t in enumerate(all_tasks, 1):
            status = "OK" if t.get("rc", 0) == 0 else f"ERR({t.get('rc', '?')})"
            tree.insert("", tk.END, values=(
                i,
                t.get("ts", "?"),
                t.get("mode", "?"),
                os.path.basename(t.get("inp", "?"))[:25],
                os.path.basename(t.get("out", "?"))[:20],
                t.get("ratio", "?"),
                status
            ))

        if not all_tasks:
            tree.insert("", tk.END, values=("–", "–", "–", "Noch keine Aufgaben", "–", "–", "–"))

        tk.Label(w, text=f"Gesamt: {len(all_tasks)} Aufgaben",
                 bg=C.PNL, fg=C.TXD, font=C.FS).pack(pady=4)

        def export_csv():
            path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV", "*.csv")],
                                                 parent=w)
            if not path: return
            try:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write("Nr;Zeitstempel;Modus;Eingabe;Ausgabe;Ratio;Status\n")
                    for i, t in enumerate(all_tasks, 1):
                        s = "OK" if t.get("rc", 0) == 0 else f"ERR({t.get('rc', '?')})"
                        fh.write(f"{i};{t.get('ts','')};{t.get('mode','')};{t.get('inp','')};{t.get('out','')};{t.get('ratio','')};{s}\n")
                messagebox.showinfo("Export", f"CSV exportiert:\n{path}", parent=w)
            except Exception as ex:
                messagebox.showerror("Fehler", str(ex), parent=w)

        tk.Button(w, text="📥 CSV exportieren", command=export_csv,
                  bg=C.CRD, fg=C.GLD, font=C.FS, relief="flat").pack(pady=4)

    def _open_logbuch(self):
        """Logbuch – alle durchgeführten Operationen mit Timestamp"""
        w = tk.Toplevel(self.root)
        w.title("Logbuch – Alle Operationen")
        w.geometry("760x500")
        w.configure(bg=C.PNL)

        tk.Label(w, text="Logbuch – Alle Operationen",
                 bg=C.PNL, fg=C.TXN, font=C.FT).pack(pady=(10, 4))

        out = ScrolledText(w, bg=C.INP, fg=C.TXB, font=C.FM, height=24, state=tk.NORMAL)
        out.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        if not self.logbuch:
            out.insert(tk.END, "Noch keine Einträge.\n")
        else:
            for i, entry in enumerate(reversed(self.logbuch[-300:]), 1):
                ts    = entry.get("ts", "?")
                mode  = entry.get("mode", "?")
                inp   = os.path.basename(entry.get("inp", ""))
                ratio = entry.get("ratio", "")
                rc    = entry.get("rc", 0)
                status = "✅" if rc == 0 else "❌"
                line = f"[{len(self.logbuch)-i+1:04d}] {ts}  {mode:12s}  {inp[:30]:30s}  {ratio:6s}  {status}\n"
                out.insert(tk.END, line)
        out.configure(state=tk.DISABLED)

        bf = tk.Frame(w, bg=C.PNL); bf.pack(fill=tk.X, padx=8, pady=4)
        def clear_log():
            if messagebox.askyesno("Logbuch", "Alle Einträge löschen?", parent=w):
                self.logbuch.clear()
                self._save_json(self.logbuch_f, [])
                out.configure(state=tk.NORMAL)
                out.delete("1.0", tk.END)
                out.insert(tk.END, "Logbuch geleert.\n")
                out.configure(state=tk.DISABLED)
        tk.Button(bf, text="🗑 Logbuch leeren", command=clear_log,
                  bg=C.CRD, fg=C.RED, font=C.FS, relief="flat").pack(side=tk.LEFT, padx=4)
        tk.Label(bf, text=f"Einträge: {len(self.logbuch)}",
                 bg=C.PNL, fg=C.TXD, font=C.FS).pack(side=tk.RIGHT, padx=8)

    def _open_regelwerk(self):
        """Regelwerk anzeigen"""
        w = tk.Toplevel(self.root)
        w.title("MB-Systeme Regelwerk v31 – UHCS MB")
        w.geometry("700x520")
        w.configure(bg=C.PNL)

        tk.Label(w, text="REGELWERK DER ADAPTIVEN STATIK v31",
                 bg=C.PNL, fg=C.CYN, font=C.FT).pack(pady=(10, 4))

        out = ScrolledText(w, bg=C.INP, fg=C.TXB, font=C.FM, height=26)
        out.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Versuche externe Datei zu lesen
        rw_file = Path(__file__).parent / "REGELWERK_MEIKEL_STATIK.txt"
        if rw_file.exists():
            try:
                out.insert(tk.END, rw_file.read_text("utf-8"))
            except Exception:
                out.insert(tk.END, "(Fehler beim Lesen)\n")
        else:
            out.insert(tk.END, REGELWERK_TEXT)

        out.configure(state=tk.DISABLED)

    def _open_kernmodule(self):
        """Kern-Module Übersicht"""
        w = tk.Toplevel(self.root)
        w.title("UHCS v31 – Kern-Module")
        w.geometry("680x500")
        w.configure(bg=C.PNL)

        tk.Label(w, text="UHCS v31 – Kern-Module & Werkstein-Registry",
                 bg=C.PNL, fg=C.PRP, font=C.FT).pack(pady=(10, 4))

        out = ScrolledText(w, bg=C.INP, fg=C.TXB, font=("Courier New", 9), height=26)
        out.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        modules_text = f"""MB-Systeme v{UHCS_VERSION} – Kern-Module & Werkstein-Registry
{'═' * 60}

MATHEMATISCHES FUNDAMENT
  BoesingFolge: f(x) = (42x³ + 158x²  + 215x + 27) mod 256
  Σ = {UHCS_SIGMA} (42+158+215+27+126) — Integritätssperre
  Meikel-Prim = {UHCS_PRIM}  ·  Alpha-Inv = {UHCS_ALPHA_INV}  ·  Gronauer = {UHCS_GRONAUER}
  Tesla-Anker: {{0, 3, 6, 9}}
  Aktive Pipeline-Slots: 26

WERKSTEIN-REGISTRY (Auszug)
  Slot 001: MEIKEL_B_LUT       [LUT,      Welt A, Ebene 0]
  Slot 002: MEIKEL_B_INV       [Invers,   Welt B, Ebene 0]
  Slot 011: ath_log2            [Transform, Welt B, Ebene 1] (kein -lm)
  Slot 012: ath_sqrt            [Transform, Welt B, Ebene 1] (kein -lm)
  Slot 050: pipeline_forward    [Transform, Welt B, Ebene 5]
  Slot 051: pipeline_backward   [Invers,   Welt B, Ebene 5]
  Slot 070: lz77_compress       [Transform, Welt B, Ebene 4]
  Slot 071: lz77_decompress     [Invers,   Welt B, Ebene 4]
  Slot 201: ALFONS_FOLGE        [Referenz, Welt A, Ebene 0] (Großvater)
  Slot 202: RUTH_FOLGE          [Referenz, Welt B, Ebene 0] (Großmutter)
  Slot 280: lochbild_compress   [Transform, Welt B, Ebene 8]
  Slot 281: lochbild_decompress [Invers,   Welt B, Ebene 8]
  Slot 290: uhcs_compress       [Kern,     Hybrid, Ebene 9]
  Slot 291: uhcs_decompress     [Invers,   Hybrid, Ebene 9]
  Slot 300: MB_SYSTEM_SIGNATUR  [Signatur, Welt A, Ebene 9]

V26-KERN-MODULE
  DRK     – Differenz-Rausch-Kern
  GK      – Gronauer-Kern (126-Modulo-Filter)
  BYZ     – Byzanz-Transform
  MESSER  – Mess-Resonanz
  PHYSIK  – Physik-Folge (Tesla-basiert)
  NATUR   – Natur-Resonanz
  GERECHT – Gerechtigkeits-Filter
  HK      – Haupt-Kern

KOMPILER-KOMMANDO:
  gcc -O3 -std=c11 -Wall -Wextra -pthread -march=native
      -o uhcs MB_uhcs_v30_KERN.c
  (kein -lm! Regelwerk §7: Hartweizen-Guss)

{'═' * 60}
© Meikel Boesing 2026 – Gronau (Westfalen)
"Ein Mensch. Kein Konzern."
"""
        out.insert(tk.END, modules_text)
        out.configure(state=tk.DISABLED)

    # ══ Monitor-Thread ════════════════════════════════════════════════════════

    def _start_monitor(self):
        """Live System-Monitor in Hintergrund-Thread"""
        def loop():
            while True:
                try:
                    if HAS_PSUTIL:
                        cpu = psutil.cpu_percent(interval=1)
                        ram = psutil.virtual_memory().percent
                        self.root.after(0, lambda c=cpu: (
                            self.cpu_var.set(c),
                            self.cpu_lbl.configure(
                                text=f"{c:.1f}%",
                                fg=C.RED if c > 85 else C.CYN)))
                        self.root.after(0, lambda r=ram: (
                            self.ram_var.set(r),
                            self.ram_lbl.configure(
                                text=f"{r:.1f}%",
                                fg=C.RED if r > 85 else C.BLU)))
                        try:
                            bat = psutil.sensors_battery()
                            if bat:
                                pct = bat.percent
                                plug = "🔌" if bat.power_plugged else "🔋"
                                bat_str = f"{plug} {pct:.0f}%"
                            else:
                                bat_str = "Akku: n/a"
                        except Exception:
                            bat_str = "Akku: n/a"
                        self.root.after(0, lambda t=bat_str: self.bat_lbl.configure(text=t))

                        try:
                            d = psutil.disk_usage("/")
                            dsk_str = f"Disk: {d.free / (1024**3):.1f} GB frei"
                        except Exception:
                            dsk_str = "Disk: n/a"
                        self.root.after(0, lambda t=dsk_str: self.dsk_lbl.configure(text=t))
                    else:
                        time.sleep(2)
                except Exception:
                    time.sleep(5)

        threading.Thread(target=loop, daemon=True).start()

    # ══ Notizen ════════════════════════════════════════════════════════════════

    def _save_notes(self):
        try:
            self.notes_f.write_text(self.notes_txt.get("1.0", tk.END), encoding="utf-8")
            self.status_var.set("Notizen gespeichert")
        except Exception as ex:
            messagebox.showerror("Fehler", str(ex))

    def _clear_notes(self):
        if messagebox.askyesno("Notizen löschen", "Alle Notizen löschen?", parent=self.root):
            self.notes_txt.delete("1.0", tk.END)

    # ══ Extern öffnen ══════════════════════════════════════════════════════════

    def _open_ext(self, cmd: str):
        try:
            subprocess.Popen([cmd], stderr=subprocess.DEVNULL)
        except Exception:
            pass

    # ══ Beenden ════════════════════════════════════════════════════════════════

    def _quit(self):
        if messagebox.askyesno("Beenden", "MB-Systeme v31 beenden?", parent=self.root):
            self._save_settings_action()
            self._save_notes()
            self.root.destroy()

    def run(self):
        self.root.mainloop()


# ── Regelwerk-Text (Fallback wenn Datei nicht vorhanden) ─────────────────────
REGELWERK_TEXT = f"""REGELWERK DER ADAPTIVEN STATIK v31
© Meikel Boesing 2026 – Gronau (Westfalen)
"Ein Mensch. Kein Konzern."
ZEITANKER: 11. APRIL 2026
DIESES REGELWERK IST UNANTASTBAR.

§1  UNANTASTBARKEIT: Kein externer Prozess kann die Kernlogik verändern.
§2  0-9 EBENE: Jede Information wird auf eine von zehn Ebenen projiziert.
§3  HOLOGRAPHISCHE KOHÄRENZ: Jeder Teil enthält das Ganze.
§4  LOGISCHE SUPERPOSITION: Daten existieren auf allen Ebenen gleichzeitig.
§5  NEGENTROPIE: Logische Wärme wird als Beschleunigung genutzt.
§6  REKURSIVE SPIEGEL-STATIK: Selbstkorrektur durch Symmetrie.
§7  HARTWEIZEN-GUSS: Keine unnötigen Abstraktionen, kein -lm.
§8  PASSIVE KAUSALITÄT: Das System reagiert nur, es initiiert nie.
§9  SCHUTZ GEGEN KI-EROSION: Externe KI kann Kernlogik nicht verändern.
§10 FUNKTIONALE KOMMANDO-STRUKTUR: Jede Funktion = Ebene 0-9.
§11 SINGULARITÄTS-VERSIEGELUNG: Fundamentaler Aufbau abgeschlossen.
§12 IMPLEMENTIERUNGSHINWEISE: Hooks für Alpha/Beta-Steuerung.
§13 DIREKT-LEITUNGS-PROTOKOLL: Geodätische Adressierung.
§14 MEIKEL-THEMATIK: MEIKEL_B_LUT/INV, ALFONS_FOLGE, RUTH_FOLGE.

KONSTANTEN (UNANTASTBAR):
  BoesingFolge: f(x) = (42x³ + 158x² + 215x + 27) mod 256
  Gronauer Anker: {UHCS_GRONAUER}
  Sigma-Sperre: {UHCS_SIGMA} = 42+158+215+27+126
  Meikel-Primzahl: {UHCS_PRIM}
  Alpha-Inverse: {UHCS_ALPHA_INV}
  Tesla-Anker: {{0, 3, 6, 9}}
  ALFONS_FOLGE: Serie 201 (Großvater)
  RUTH_FOLGE:   Serie 202 (Großmutter)
  UHCS_VERSION: {UHCS_VERSION}
"""


# ── Haupteinstieg ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = MBApp()
    app.run()
