#!/bin/bash
# ════════════════════════════════════════════════════════════════════
#  INSTALL_v31.sh – MB-Systeme v31 – UHCS MB Linux Installationsskript
#  © Meikel Bösing 2026 – Gronau (Westfalen)
#  "Ein Mensch. Kein Konzern."
#
#  BoesingFolge: f(x) = (42x³ + 158x² + 215x + 27) mod 256
#  Σ = 568  ·  Meikel-Prim = 331  ·  UHCS_VERSION = "31.0"
#
#  Nutzung:
#    bash INSTALL_v31.sh          — Installation starten
#    bash INSTALL_v31.sh --help   — Hilfe anzeigen
# ════════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Farben ───────────────────────────────────────────────────────────
GRN='\033[0;32m'
RED='\033[0;31m'
YLW='\033[1;33m'
CYN='\033[0;36m'
BLD='\033[1m'
RST='\033[0m'

# ── Konstanten ────────────────────────────────────────────────────────
UHCS_VERSION="31.0"
SIGMA=568
MEIKEL_PRIM=331
INSTALL_BIN="/usr/local/bin/uhcs"
INSTALL_MW="/usr/local/bin/mb_meisterwerk"
MB_DIR="${HOME}/.mb_system"
KERN_SRC="MB_uhcs_v30_KERN.c"
MEISTER_SRC="MB_MEISTERWERK_v31.c"
UHCS_BIN="uhcs"
MEISTER_BIN="mb_meisterwerk"
GUI_PY="MBSysteme_v31_E.py"
MAKEFILE="Makefile_v31"
DESKTOP_FILE="${HOME}/.local/share/applications/mb-system-v31.desktop"

# ── Hilfsfunktionen ──────────────────────────────────────────────────
ok()  { echo -e "${GRN}  ✅ $*${RST}"; }
err() { echo -e "${RED}  ❌ FEHLER: $*${RST}" >&2; }
info(){ echo -e "${CYN}  ℹ  $*${RST}"; }
warn(){ echo -e "${YLW}  ⚠  $*${RST}"; }
hdr() { echo -e "${BLD}${CYN}$*${RST}"; }

# ── Header ausgeben ──────────────────────────────────────────────────
print_header() {
    echo ""
    echo -e "${BLD}${CYN}  ╔════════════════════════════════════════════════════════╗${RST}"
    echo -e "${BLD}${CYN}  ║  MB-Systeme v${UHCS_VERSION} – UHCS MB Installationsskript               ║${RST}"
    echo -e "${BLD}${CYN}  ║  © Meikel Bösing 2026 – Gronau (Westfalen)             ║${RST}"
    echo -e "${BLD}${CYN}  ║  Σ=${SIGMA} · Meikel-Prim=${MEIKEL_PRIM}                              ║${RST}"
    echo -e "${BLD}${CYN}  ║  BoesingFolge: f(x)=(42x³+158x²+215x+27) mod 256      ║${RST}"
    echo -e "${BLD}${CYN}  ╚════════════════════════════════════════════════════════╝${RST}"
    echo ""
}

# ── Hilfe anzeigen ───────────────────────────────────────────────────
print_help() {
    print_header
    echo "  Nutzung: bash INSTALL_v31.sh [OPTION]"
    echo ""
    echo "  Optionen:"
    echo "    --help    Diese Hilfe anzeigen"
    echo "    --check   Nur Voraussetzungen prüfen (nicht installieren)"
    echo "    --uninstall  Deinstallation"
    echo ""
    echo "  Das Skript führt folgende Schritte aus:"
    echo "    1. Voraussetzungen prüfen (gcc, python3, make)"
    echo "    2. C-Kern kompilieren (MB_uhcs_v30_KERN.c → uhcs)"
    echo "    3. Binary nach /usr/local/bin/uhcs installieren"
    echo "    4. ~/.mb_system/ anlegen"
    echo "    5. Desktop-Eintrag erstellen"
    echo "    6. Selbsttest durchführen (Roundtrip-Test)"
    echo ""
    exit 0
}

# ── Deinstallation ───────────────────────────────────────────────────
do_uninstall() {
    hdr "  ── Deinstallation ──────────────────────────────────────────"
    if [ -f "$INSTALL_BIN" ]; then
        rm -f "$INSTALL_BIN"
        ok "Binary entfernt: $INSTALL_BIN"
    else
        info "Binary nicht gefunden: $INSTALL_BIN (nichts zu tun)"
    fi
    if [ -f "$INSTALL_MW" ]; then
        rm -f "$INSTALL_MW"
        ok "Binary entfernt: $INSTALL_MW"
    fi
    if [ -f "$DESKTOP_FILE" ]; then
        rm -f "$DESKTOP_FILE"
        ok "Desktop-Eintrag entfernt: $DESKTOP_FILE"
    fi
    info "Konfigurationsverzeichnis bleibt erhalten: $MB_DIR"
    ok "Deinstallation abgeschlossen."
    exit 0
}

# ── Argument-Verarbeitung ────────────────────────────────────────────
for arg in "$@"; do
    case "$arg" in
        --help|-h)   print_help ;;
        --uninstall) do_uninstall ;;
        --check)     CHECK_ONLY=1 ;;
        *) warn "Unbekannte Option: $arg" ;;
    esac
done

CHECK_ONLY="${CHECK_ONLY:-0}"

print_header

# ════════════════════════════════════════════════════════════════════
#  SCHRITT 1: Voraussetzungen prüfen
# ════════════════════════════════════════════════════════════════════
hdr "  [1/6] Voraussetzungen prüfen ─────────────────────────────────"

DEPS_OK=1

# gcc prüfen
if command -v gcc >/dev/null 2>&1; then
    GCC_VER=$(gcc --version 2>&1 | head -1)
    ok "gcc vorhanden: $GCC_VER"
else
    err "gcc nicht gefunden!"
    info "Installation: sudo apt install gcc"
    DEPS_OK=0
fi

# python3 prüfen
if command -v python3 >/dev/null 2>&1; then
    PY_VER=$(python3 --version 2>&1)
    ok "python3 vorhanden: $PY_VER"
else
    err "python3 nicht gefunden!"
    info "Installation: sudo apt install python3"
    DEPS_OK=0
fi

# make prüfen
if command -v make >/dev/null 2>&1; then
    MAKE_VER=$(make --version 2>&1 | head -1)
    ok "make vorhanden: $MAKE_VER"
else
    err "make nicht gefunden!"
    info "Installation: sudo apt install make"
    DEPS_OK=0
fi

# Quelldateien prüfen
if [ -f "$KERN_SRC" ]; then
    LINES=$(wc -l < "$KERN_SRC" 2>/dev/null || echo "?")
    ok "Quelldatei: $KERN_SRC ($LINES Zeilen)"
else
    err "Quelldatei nicht gefunden: $KERN_SRC"
    info "Das Skript muss im selben Verzeichnis wie $KERN_SRC ausgeführt werden."
    DEPS_OK=0
fi

if [ -f "$MEISTER_SRC" ]; then
    MLINES=$(wc -l < "$MEISTER_SRC" 2>/dev/null || echo "?")
    ok "Quelldatei: $MEISTER_SRC ($MLINES Zeilen)"
else
    warn "Quelldatei nicht gefunden: $MEISTER_SRC (Meisterwerk wird übersprungen)"
fi

# tkinter prüfen (für GUI)
if python3 -c "import tkinter" 2>/dev/null; then
    ok "python3-tkinter vorhanden"
else
    warn "python3-tkinter nicht gefunden – GUI nicht verfügbar"
    info "Installation: sudo apt install python3-tk"
fi

# psutil prüfen (optional)
if python3 -c "import psutil" 2>/dev/null; then
    ok "psutil vorhanden (System-Monitor aktiv)"
else
    info "psutil nicht gefunden (optional) – pip3 install psutil"
fi

if [ "$DEPS_OK" -eq 0 ]; then
    err "Voraussetzungen nicht erfüllt. Installation abgebrochen."
    exit 1
fi

ok "Alle Pflicht-Voraussetzungen erfüllt."

if [ "$CHECK_ONLY" -eq 1 ]; then
    ok "Check abgeschlossen (--check Modus, keine Installation)."
    exit 0
fi

# ════════════════════════════════════════════════════════════════════
#  SCHRITT 2: C-Kern kompilieren
# ════════════════════════════════════════════════════════════════════
hdr "  [2/6] C-Kern kompilieren ──────────────────────────────────────"

if [ -f "$MAKEFILE" ]; then
    info "Nutze $MAKEFILE ..."
    make -f "$MAKEFILE" all
    ok "Kompilierung über $MAKEFILE abgeschlossen."
else
    info "$MAKEFILE nicht gefunden – direkter gcc-Aufruf ..."
    gcc -O3 -std=c11 -Wall -Wextra -pthread -march=native \
        -o "$UHCS_BIN" "$KERN_SRC"
    ok "Kompilierung abgeschlossen: ./$UHCS_BIN"
fi

if [ ! -f "$UHCS_BIN" ]; then
    err "Binary $UHCS_BIN nicht erstellt! Kompilierung fehlgeschlagen."
    exit 1
fi

ok "Binary: ./$UHCS_BIN ($(du -h "$UHCS_BIN" | cut -f1))"

if [ -f "$MEISTER_BIN" ]; then
    ok "Binary: ./$MEISTER_BIN ($(du -h "$MEISTER_BIN" | cut -f1))"
elif [ -f "$MEISTER_SRC" ]; then
    info "Fallback: Kompiliere $MEISTER_SRC direkt ..."
    gcc -O3 -std=c11 -Wall -Wextra -pthread -march=native \
        -o "$MEISTER_BIN" "$MEISTER_SRC"
    ok "Kompilierung abgeschlossen: ./$MEISTER_BIN"
fi

# ════════════════════════════════════════════════════════════════════
#  SCHRITT 3: Binary installieren
# ════════════════════════════════════════════════════════════════════
hdr "  [3/6] Binaries installieren ────────────────────────────────────"

# Hilfsfunktion: Binary installieren
_install_bin() {
    local SRC="$1" DST="$2"
    if [ ! -f "$SRC" ]; then return; fi
    if [ "$(id -u)" -eq 0 ]; then
        cp -f "$SRC" "$DST"
        chmod 755 "$DST"
        ok "Binary installiert: $DST"
    else
        if sudo cp -f "$SRC" "$DST" && sudo chmod 755 "$DST"; then
            ok "Binary installiert: $DST (mit sudo)"
        else
            err "Installation nach $DST fehlgeschlagen."
            info "Manuelle Installation: sudo cp $SRC $DST"
            info "Binary bleibt lokal verfügbar: ./$SRC"
        fi
    fi
}

# Prüfe ob Root-Rechte vorhanden
if [ "$(id -u)" -ne 0 ]; then
    warn "Keine Root-Rechte – versuche sudo ..."
fi

_install_bin "$UHCS_BIN" "$INSTALL_BIN"
if [ -f "$MEISTER_BIN" ]; then
    _install_bin "$MEISTER_BIN" "$INSTALL_MW"
fi

# ════════════════════════════════════════════════════════════════════
#  SCHRITT 4: ~/.mb_system/ anlegen
# ════════════════════════════════════════════════════════════════════
hdr "  [4/6] Konfigurationsverzeichnis anlegen ───────────────────────"

mkdir -p "$MB_DIR"
ok "Verzeichnis angelegt: $MB_DIR"

# DNA-Archiv initialisieren (leer)
if [ ! -f "${MB_DIR}/dna.bin" ]; then
    touch "${MB_DIR}/dna.bin"
    ok "DNA-Archiv initialisiert: ${MB_DIR}/dna.bin"
else
    ok "DNA-Archiv existiert bereits: ${MB_DIR}/dna.bin"
fi

# Settings-Datei erstellen falls nicht vorhanden
if [ ! -f "${MB_DIR}/settings.json" ]; then
    cat > "${MB_DIR}/settings.json" << 'EOF'
{
    "version": "31.0",
    "mode": "auto",
    "security": 0,
    "threads": 4,
    "self_healing": true,
    "auto_days": 7,
    "sigma": 568,
    "meikel_prim": 331
}
EOF
    ok "Einstellungen erstellt: ${MB_DIR}/settings.json"
fi

# ════════════════════════════════════════════════════════════════════
#  SCHRITT 5: Desktop-Eintrag erstellen
# ════════════════════════════════════════════════════════════════════
hdr "  [5/6] Desktop-Eintrag erstellen ──────────────────────────────"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPS_DIR="${HOME}/.local/share/applications"
mkdir -p "$APPS_DIR"

if [ -f "${SCRIPT_DIR}/${GUI_PY}" ]; then
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=MB-Systeme v31
GenericName=UHCS Kompressor
Comment=MB-Systeme v31 – UHCS MB Kompression – © Meikel Bösing 2026
Exec=python3 ${SCRIPT_DIR}/${GUI_PY}
Terminal=false
Categories=Utility;Compression;
Keywords=kompression;uhcs;meikel;boesing;gronau;
StartupNotify=true
EOF
    ok "Desktop-Eintrag erstellt: $DESKTOP_FILE"
    # Desktop-Datenbank aktualisieren
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$APPS_DIR" 2>/dev/null || true
    fi
else
    warn "$GUI_PY nicht gefunden – Desktop-Eintrag übersprungen"
    info "GUI-Datei: ${SCRIPT_DIR}/${GUI_PY}"
fi

# ════════════════════════════════════════════════════════════════════
#  SCHRITT 6: Selbsttest (Roundtrip-Test)
# ════════════════════════════════════════════════════════════════════
hdr "  [6/6] Selbsttest ──────────────────────────────────────────────"

# Binary-Pfad bestimmen
BIN_PATH="./$UHCS_BIN"
if [ -x "$INSTALL_BIN" ]; then
    BIN_PATH="$INSTALL_BIN"
fi

# Interner Selbsttest
info "Starte Selbsttest: $BIN_PATH --self-test ..."
if "$BIN_PATH" --self-test 2>&1; then
    ok "Selbsttest bestanden."
else
    err "Selbsttest fehlgeschlagen!"
    exit 1
fi

# Roundtrip-Test
info "Starte Roundtrip-Test ..."
ORIG=$(mktemp /tmp/uhcs_install_test_orig_XXXXXX)
COMP=$(mktemp /tmp/uhcs_install_test_comp_XXXXXX)
DECO=$(mktemp /tmp/uhcs_install_test_deco_XXXXXX)

# Testdaten generieren
dd if=/dev/urandom of="$ORIG" bs=1k count=8 2>/dev/null
ORIG_SIZE=$(wc -c < "$ORIG")

# Komprimieren
if "$BIN_PATH" --compress "$ORIG" --output "$COMP" 2>/dev/null; then
    COMP_SIZE=$(wc -c < "$COMP")
    # Dekomprimieren
    if "$BIN_PATH" --decompress "$COMP" --output "$DECO" 2>/dev/null; then
        # Vergleichen
        if diff -q "$ORIG" "$DECO" >/dev/null 2>&1; then
            RATIO=$(echo "scale=1; $ORIG_SIZE * 100 / $COMP_SIZE" | bc 2>/dev/null || echo "?")
            ok "Roundtrip-Test: OK (${ORIG_SIZE} → ${COMP_SIZE} Bytes, Ratio: ${RATIO}%)"
        else
            err "Roundtrip-Test: Daten unterschiedlich nach Dekompression!"
            rm -f "$ORIG" "$COMP" "$DECO"
            exit 1
        fi
    else
        err "Roundtrip-Test: Dekompression fehlgeschlagen!"
        rm -f "$ORIG" "$COMP" "$DECO"
        exit 1
    fi
else
    err "Roundtrip-Test: Kompression fehlgeschlagen!"
    rm -f "$ORIG" "$COMP" "$DECO"
    exit 1
fi

rm -f "$ORIG" "$COMP" "$DECO"

# ════════════════════════════════════════════════════════════════════
#  ABSCHLUSS
# ════════════════════════════════════════════════════════════════════
echo ""
echo -e "${BLD}${GRN}  ╔════════════════════════════════════════════════════════╗${RST}"
echo -e "${BLD}${GRN}  ║  ✅ MB-Systeme v${UHCS_VERSION} – UHCS MB erfolgreich installiert!          ║${RST}"
echo -e "${BLD}${GRN}  ╠════════════════════════════════════════════════════════╣${RST}"
echo -e "${GRN}  ║  UHCS-Kern:    ${INSTALL_BIN}                     ║${RST}"
if [ -f "$INSTALL_MW" ] || [ -f "$MEISTER_BIN" ]; then
echo -e "${GRN}  ║  Meisterwerk:  ${INSTALL_MW}        ║${RST}"
fi
echo -e "${GRN}  ║  Config:       ${MB_DIR}/                  ║${RST}"
echo -e "${GRN}  ║  DNA-Archiv:   ${MB_DIR}/dna.bin          ║${RST}"
echo -e "${GRN}  ╠════════════════════════════════════════════════════════╣${RST}"
echo -e "${GRN}  ║  Nutzung:                                              ║${RST}"
echo -e "${GRN}  ║    uhcs --compress eingabe --output ausgabe.uhcs       ║${RST}"
echo -e "${GRN}  ║    uhcs --decompress ausgabe.uhcs --output rekons.dat ║${RST}"
echo -e "${GRN}  ║    uhcs --benchmark                                    ║${RST}"
echo -e "${GRN}  ║    mb_meisterwerk --self-test  (376+ Tests)            ║${RST}"
echo -e "${GRN}  ║    python3 MBSysteme_v31_E.py   (GUI starten)              ║${RST}"
echo -e "${BLD}${GRN}  ╚════════════════════════════════════════════════════════╝${RST}"
echo ""
echo -e "${CYN}  Σ=${SIGMA} · Meikel-Prim=${MEIKEL_PRIM} · UHCS_VERSION=\"${UHCS_VERSION}\"${RST}"
echo -e "${CYN}  © Meikel Bösing 2026 – Gronau (Westfalen)${RST}"
echo -e "${CYN}  \"Ein Mensch. Kein Konzern.\"${RST}"
echo ""
