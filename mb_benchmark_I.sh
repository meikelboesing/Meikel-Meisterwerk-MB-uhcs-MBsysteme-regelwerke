#!/bin/bash
# ══════════════════════════════════════════════════════════════════════
#  mb_benchmark_I.sh — ISOLIERTER BENCHMARK-TEST
#  MB-Systeme v31 – UHCS MB
#  Dateikennung: _I (Neunte Datei im Guss-Reihenfolge A-I)
#
#  (c) Meikel Boesing 2026 – Gronau (Westfalen)
#  "Ein Mensch. Kein Konzern."
#
#  BoesingFolge: f(x) = (42x³ + 158x² + 215x + 27) mod 256
#  Σ = 568 · Meikel-Prim = 331 · Tesla-Anker = {0,3,6,9}
#
#  ZWECK: Isolierter, unabhängiger Benchmark-Test
#         Kein GUI nötig. Kein Python nötig.
#         Nur das kompilierte mb_meisterwerk Binary.
#
#  NUTZUNG:
#    chmod +x mb_benchmark_I.sh
#    ./mb_benchmark_I.sh              — Vollständiger Benchmark
#    ./mb_benchmark_I.sh --quick      — Nur Kurztest (1KB + 16KB)
#    ./mb_benchmark_I.sh --roundtrip  — Nur Roundtrip-Tests
#    ./mb_benchmark_I.sh --selftest   — Nur Self-Test
#
#  AUSGABE: Benchmark-Ergebnisse werden in mb_benchmark_results.txt
#           gespeichert (optional).
# ══════════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Konfiguration ────────────────────────────────────────────────────
VERSION="31.0"
SIGMA=568
MEIKEL_PRIM=331
BINARY="./mb_meisterwerk"
RESULT_FILE="mb_benchmark_results.txt"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# ── Farben (Terminal) ────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

# ── Funktionen ───────────────────────────────────────────────────────

print_banner() {
    echo ""
    echo -e "${CYAN}  ╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}  ║  ${BOLD}MB-Systeme v${VERSION} — ISOLIERTER BENCHMARK${NC}${CYAN}                        ║${NC}"
    echo -e "${CYAN}  ║  Σ=${SIGMA} · Meikel-Prim=${MEIKEL_PRIM} · Tesla-Anker={0,3,6,9}              ║${NC}"
    echo -e "${CYAN}  ║  BoesingFolge: f(x) = (42x³ + 158x² + 215x + 27) mod 256       ║${NC}"
    echo -e "${CYAN}  ║  (c) Meikel Boesing 2026 — Gronau (Westfalen)                   ║${NC}"
    echo -e "${CYAN}  ╚════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

check_binary() {
    if [ ! -f "$BINARY" ]; then
        # Versuche zu kompilieren
        if [ -f "MB_MEISTERWERK_v31_A.c" ]; then
            echo -e "${YELLOW}  ℹ  Binary nicht gefunden. Kompiliere MB_MEISTERWERK_v31_A.c ...${NC}"
            gcc -O3 -std=c11 -Wall -Wextra -pthread -o "$BINARY" MB_MEISTERWERK_v31_A.c
            echo -e "${GREEN}  ✅ Kompilierung erfolgreich (0 Warnungen)${NC}"
        elif [ -f "MB_MEISTERWERK_v31.c" ]; then
            echo -e "${YELLOW}  ℹ  Binary nicht gefunden. Kompiliere MB_MEISTERWERK_v31.c ...${NC}"
            gcc -O3 -std=c11 -Wall -Wextra -pthread -o "$BINARY" MB_MEISTERWERK_v31.c
            echo -e "${GREEN}  ✅ Kompilierung erfolgreich (0 Warnungen)${NC}"
        else
            echo -e "${RED}  ❌ FEHLER: Weder $BINARY noch MB_MEISTERWERK_v31_A.c gefunden!${NC}"
            echo "     Bitte zuerst kompilieren: make -f Makefile_v31_D"
            exit 1
        fi
    fi
    echo -e "${GREEN}  ✅ Binary gefunden: $BINARY${NC}"
    echo ""
}

# ── Test 1: Self-Test (Korrektheit) ──────────────────────────────────
run_selftest() {
    echo -e "${BOLD}  ═══ TEST 1: SELF-TEST (Korrektheit) ═══════════════════════════════${NC}"
    echo ""
    RESULT=$("$BINARY" --self-test 2>&1)
    PASSED=$(echo "$RESULT" | grep -oP '\d+/\d+ bestanden' || echo "?")
    HW_REIF=$(echo "$RESULT" | grep "HARDWARE-REIF" || echo "?")
    echo "  $PASSED"
    echo "  $HW_REIF"
    echo ""
    echo "$TIMESTAMP — Self-Test: $PASSED" >> "$RESULT_FILE"
}

# ── Test 2: Roundtrip-Benchmark (5 Dateigrößen) ─────────────────────
run_roundtrip() {
    local SIZES=("$@")
    echo -e "${BOLD}  ═══ TEST 2: ROUNDTRIP-BENCHMARK ═════════════════════════════════${NC}"
    echo ""
    echo -e "  ${CYAN}  Größe    │ Status    │ Ratio     │ Zeit      │ Throughput${NC}"
    echo "  ─────────┼───────────┼───────────┼───────────┼───────────"

    TOTAL_PASS=0
    TOTAL_FAIL=0
    TOTAL_TIME_MS=0
    TOTAL_BYTES=0

    for SZ in "${SIZES[@]}"; do
        ORIG=$(mktemp /tmp/mb_bench_orig_XXXXXX)
        COMP=$(mktemp /tmp/mb_bench_comp_XXXXXX.uhcs)
        DECO=$(mktemp /tmp/mb_bench_deco_XXXXXX)

        dd if=/dev/urandom of="$ORIG" bs=1k count="$SZ" 2>/dev/null

        START_NS=$(date +%s%N)
        "$BINARY" --compress "$ORIG" --output "$COMP" 2>/dev/null || true
        "$BINARY" --decompress "$COMP" --output "$DECO" 2>/dev/null || true
        END_NS=$(date +%s%N)

        ELAPSED_MS=$(( (END_NS - START_NS) / 1000000 ))
        TOTAL_TIME_MS=$(( TOTAL_TIME_MS + ELAPSED_MS ))
        TOTAL_BYTES=$(( TOTAL_BYTES + SZ * 1024 ))

        ORIG_SZ=$(stat -c%s "$ORIG" 2>/dev/null || stat -f%z "$ORIG" 2>/dev/null)
        COMP_SZ=$(stat -c%s "$COMP" 2>/dev/null || stat -f%z "$COMP" 2>/dev/null || echo "0")

        if [ "$ORIG_SZ" -gt 0 ] && [ "$COMP_SZ" -gt 0 ]; then
            RATIO=$(echo "scale=1; $COMP_SZ * 100 / $ORIG_SZ" | bc 2>/dev/null || echo "?")
        else
            RATIO="?"
        fi

        if [ "$ELAPSED_MS" -gt 0 ]; then
            THROUGHPUT=$(echo "scale=1; $SZ * 1000 / $ELAPSED_MS" | bc 2>/dev/null || echo "?")
        else
            THROUGHPUT="∞"
        fi

        if diff -q "$ORIG" "$DECO" >/dev/null 2>&1; then
            echo -e "  ${GREEN}  ${SZ}KB     │ ✅ OK     │ ${RATIO}%     │ ${ELAPSED_MS}ms     │ ${THROUGHPUT} KB/s${NC}"
            TOTAL_PASS=$((TOTAL_PASS + 1))
        else
            echo -e "  ${RED}  ${SZ}KB     │ ❌ FAIL   │ ${RATIO}%     │ ${ELAPSED_MS}ms     │ -${NC}"
            TOTAL_FAIL=$((TOTAL_FAIL + 1))
        fi

        rm -f "$ORIG" "$COMP" "$DECO"
    done

    echo "  ─────────┴───────────┴───────────┴───────────┴───────────"

    if [ "$TOTAL_TIME_MS" -gt 0 ]; then
        AVG_THROUGHPUT=$(echo "scale=1; $TOTAL_BYTES / $TOTAL_TIME_MS" | bc 2>/dev/null || echo "?")
    else
        AVG_THROUGHPUT="∞"
    fi

    echo ""
    echo -e "  Ergebnis: ${TOTAL_PASS}/${#SIZES[@]} Roundtrips bestanden"
    echo -e "  Gesamt-Durchsatz: ~${AVG_THROUGHPUT} KB/s (Kompression + Dekompression)"
    echo ""
    echo "$TIMESTAMP — Roundtrip: $TOTAL_PASS/${#SIZES[@]} bestanden, Avg ${AVG_THROUGHPUT} KB/s" >> "$RESULT_FILE"
}

# ── Test 3: Entropie-Profil ──────────────────────────────────────────
run_entropie() {
    echo -e "${BOLD}  ═══ TEST 3: ENTROPIE-PROFIL ═════════════════════════════════════${NC}"
    echo ""
    "$BINARY" --entropie-profil 2>/dev/null || echo "  ℹ  --entropie-profil nicht verfügbar"
    echo ""
}

# ── Test 4: Selbst-Verifikation ──────────────────────────────────────
run_verifikation() {
    echo -e "${BOLD}  ═══ TEST 4: SELBST-VERIFIKATION ═════════════════════════════════${NC}"
    echo ""
    "$BINARY" --selbst-verifikation 2>/dev/null || echo "  ℹ  --selbst-verifikation nicht verfügbar"
    echo ""
}

# ── Test 5: Finale Perfektion (20-Punkt-Audit) ──────────────────────
run_perfektion() {
    echo -e "${BOLD}  ═══ TEST 5: FINALE PERFEKTION (20-PUNKT-AUDIT) ═════════════════${NC}"
    echo ""
    "$BINARY" --finale-perfektion 2>/dev/null || echo "  ℹ  --finale-perfektion nicht verfügbar"
    echo ""
}

print_footer() {
    echo -e "${CYAN}  ╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}  ║  ${GREEN}✅ BENCHMARK ABGESCHLOSSEN${NC}${CYAN}                                        ║${NC}"
    echo -e "${CYAN}  ║  Ergebnisse gespeichert in: ${RESULT_FILE}                     ║${NC}"
    echo -e "${CYAN}  ║  (c) Meikel Boesing 2026 — Gronau (Westfalen)                   ║${NC}"
    echo -e "${CYAN}  ╚════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# ── Hauptprogramm ────────────────────────────────────────────────────
MODE="${1:-full}"

print_banner
check_binary

# Header in Ergebnis-Datei
echo "═══ MB-Systeme v${VERSION} Benchmark — $TIMESTAMP ═══" >> "$RESULT_FILE"

case "$MODE" in
    --quick)
        run_selftest
        run_roundtrip 1 16
        ;;
    --roundtrip)
        run_roundtrip 1 4 16 64 256
        ;;
    --selftest)
        run_selftest
        ;;
    --full|full|*)
        run_selftest
        run_roundtrip 1 4 16 64 256
        run_entropie
        run_verifikation
        run_perfektion
        ;;
esac

echo "" >> "$RESULT_FILE"
print_footer
