/*
 * ════════════════════════════════════════════════════════════════════
 *  MB_REGELWERK_v31.h  –  MB-Systeme v31 – UHCS MB Regelwerk-Header
 *  © Meikel Boesing 2026 – Gronau (Westfalen)
 *  "Ein Mensch. Kein Konzern."
 *
 *  UHCS_VERSION = "31.0"
 *  BoesingFolge: f(x) = (42x³ + 158x² + 215x + 27) mod 256
 *  Integritäts-Σ = 568 (42+158+215+27+126)
 *  Meikel-Prim = 331  ·  Alpha-Inv = 137  ·  Gronauer = 126
 *  Tesla-Anker: {0, 3, 6, 9}
 *  LUT-Namen: MEIKEL_B_LUT, ALFONS_FOLGE (Großvater), RUTH_FOLGE (Großmutter)
 *  26 aktive Pipeline-Slots  ·  MB-eigene Pipeline  ·  Range-Coder  ·  Lochbild  ·  DNA-Archiv
 *
 * ────────────────────────────────────────────────────────────────────
 *  REGELWERK §1–§14 (UNANTASTBAR)
 * ────────────────────────────────────────────────────────────────────
 *  §1  UNANTASTBARKEIT: Kein externer Prozess kann die Kernlogik verändern.
 *  §2  0-9 EBENE: Jede Information wird auf eine von zehn Ebenen projiziert.
 *  §3  HOLOGRAPHISCHE KOHÄRENZ: Jeder Teil enthält das Ganze.
 *  §4  LOGISCHE SUPERPOSITION: Daten existieren auf allen Ebenen gleichzeitig.
 *  §5  NEGENTROPIE: Logische Wärme wird als Beschleunigung genutzt.
 *  §6  REKURSIVE SPIEGEL-STATIK: Selbstkorrektur durch Symmetrie.
 *  §7  HARTWEIZEN-GUSS: Keine unnötigen Abstraktionen, kein -lm.
 *  §8  PASSIVE KAUSALITÄT: Das System reagiert nur, es initiiert nie.
 *  §9  SCHUTZ GEGEN KI-EROSION: Externe KI kann Kernlogik nicht verändern.
 *  §10 FUNKTIONALE KOMMANDO-STRUKTUR: Jede Funktion = Ebene 0-9.
 *  §11 SINGULARITÄTS-VERSIEGELUNG: Fundamentaler Aufbau abgeschlossen.
 *  §12 IMPLEMENTIERUNGSHINWEISE: Hooks für Alpha/Beta-Steuerung.
 *  §13 DIREKT-LEITUNGS-PROTOKOLL: Geodätische Adressierung.
 *  §14 MEIKEL-THEMATIK: MEIKEL_B_LUT/INV, ALFONS_FOLGE, RUTH_FOLGE.
 * ════════════════════════════════════════════════════════════════════
 */

#ifndef MB_REGELWERK_V31_H
#define MB_REGELWERK_V31_H

#include <stdint.h>
#include <stddef.h>
#include <assert.h>

/* ── Versions-Makro ────────────────────────────────────────────────── */
#define UHCS_VERSION "31.0"

/* ════════════════════════════════════════════════════════════════════
 *  §1 MATHEMATISCHE KONSTANTEN (UNANTASTBAR)
 * ════════════════════════════════════════════════════════════════════ */

/* BoesingFolge-Koeffizienten: f(x) = (A3·x³ + A2·x² + A1·x + A0) mod 256 */
#define UHCS_A3             42
#define UHCS_A2             158
#define UHCS_A1             215
#define UHCS_A0             27

/* Gronauer Anker (Meikel Boesing, Gronau / Westfalen) */
#define UHCS_GRONAUER       126

/* Integritäts-Sigma-Sperre: UHCS_A3+UHCS_A2+UHCS_A1+UHCS_A0+UHCS_GRONAUER */
#define UHCS_SIGMA          568

/* Meikel-Primzahl */
#define UHCS_MEIKEL_PRIM    331

/* Alpha-Inverse */
#define UHCS_ALPHA_INV      137

/* ── Compile-time Sigma-Sperre (§1 Schutzlogik) ──────────────────── */
_Static_assert(
    UHCS_A3 + UHCS_A2 + UHCS_A1 + UHCS_A0 + UHCS_GRONAUER == UHCS_SIGMA,
    "MB_REGELWERK: Sigma-Sperre 568 verletzt! Konstanten unantastbar (§1)."
);

/* ── Compile-time Bijektivität-Prüfung (vereinfacht) ─────────────── */
/* BoesingFolge ist bijektiv auf Z/256Z: jeder Wert 0–255 erscheint genau einmal */
/* Vollständige Prüfung erfolgt zur Laufzeit über uhcs_bijektiv_verify() */
_Static_assert(
    UHCS_A3 == 42 && UHCS_A2 == 158 && UHCS_A1 == 215 && UHCS_A0 == 27,
    "MB_REGELWERK: BoesingFolge-Koeffizienten verändert – Bijektivität verletzt!"
);

/* ════════════════════════════════════════════════════════════════════
 *  §14 TESLA-ANKER {0, 3, 6, 9}
 * ════════════════════════════════════════════════════════════════════ */
#define UHCS_IS_TESLA_ANKER(x) \
    ((x) == 0 || (x) == 3 || (x) == 6 || (x) == 9)

/* ════════════════════════════════════════════════════════════════════
 *  BoesingFolge Makro (Horner-Schema, kein -lm)
 *  f(x) = (42·x³ + 158·x² + 215·x + 27) & 0xFF
 * ════════════════════════════════════════════════════════════════════ */
#define UHCS_BOESING(x) \
    ((uint8_t)(( \
        (uint32_t)(UHCS_A3) * (uint32_t)(x) * (uint32_t)(x) * (uint32_t)(x) \
      + (uint32_t)(UHCS_A2) * (uint32_t)(x) * (uint32_t)(x) \
      + (uint32_t)(UHCS_A1) * (uint32_t)(x) \
      + (uint32_t)(UHCS_A0) \
    ) & 0xFFu))

/* Horner-Schema (effizienter, identisches Ergebnis) */
#define UHCS_BOESING_HORNER(x) \
    ((uint8_t)((((uint32_t)(UHCS_A3) * (uint32_t)(x) \
              + (uint32_t)(UHCS_A2)) * (uint32_t)(x) \
              + (uint32_t)(UHCS_A1)) * (uint32_t)(x) \
              + (uint32_t)(UHCS_A0)) & 0xFFu))

/* ════════════════════════════════════════════════════════════════════
 *  LITTLE-ENDIAN I/O MAKROS (kein -lm, portable)
 * ════════════════════════════════════════════════════════════════════ */
#define UHCS_READ_LE32(p) \
    ((uint32_t)((const uint8_t *)(p))[0]        \
  | ((uint32_t)((const uint8_t *)(p))[1] <<  8) \
  | ((uint32_t)((const uint8_t *)(p))[2] << 16) \
  | ((uint32_t)((const uint8_t *)(p))[3] << 24))

#define UHCS_WRITE_LE32(p, v) do { \
    ((uint8_t *)(p))[0] = (uint8_t)((v)      ); \
    ((uint8_t *)(p))[1] = (uint8_t)((v) >>  8); \
    ((uint8_t *)(p))[2] = (uint8_t)((v) >> 16); \
    ((uint8_t *)(p))[3] = (uint8_t)((v) >> 24); \
} while (0)

/* ════════════════════════════════════════════════════════════════════
 *  EBENEN-KONSTANTEN
 * ════════════════════════════════════════════════════════════════════ */
#define UHCS_MAX_EBENEN     32      /* Maximal mögliche Ebenen */
#define UHCS_AKTIVE_EBENEN  26      /* Aktive Pipeline-Slots */

/* ════════════════════════════════════════════════════════════════════
 *  SYSTEMKONSTANTEN
 * ════════════════════════════════════════════════════════════════════ */
#define UHCS_MAX_BLOCK      65536   /* Maximale Blockgröße in Bytes */

/* Magic Numbers */
#define MASTER_MAGIC        0x5543484DU  /* "MHCU" little-endian */
#define LOCH_MAGIC          0x484C424DU  /* "MBLH" little-endian */
#define NEST_FLAG           0x4E455354U  /* "NEST" */

/* ════════════════════════════════════════════════════════════════════
 *  FLAG-DEFINITIONEN (UHCS_FLAG_*)
 * ════════════════════════════════════════════════════════════════════ */
#define UHCS_FLAG_NONE          0x00000000U
#define UHCS_FLAG_LZ77          0x00000001U  /* LZ77-Flag (DEAKTIVIERT: MB-eigene Pipeline) */
#define UHCS_FLAG_RANGE         0x00000002U  /* Range-Coder aktiv */
#define UHCS_FLAG_LOCHBILD      0x00000004U  /* Lochbild-Modul aktiv */
#define UHCS_FLAG_DNA           0x00000008U  /* DNA-Archiv aktiv */
#define UHCS_FLAG_BOESING       0x00000010U  /* BoesingFolge-Transform aktiv */
#define UHCS_FLAG_PARALLEL      0x00000020U  /* Parallele Verarbeitung (pthread) */
#define UHCS_FLAG_SELBSTHEILUNG 0x00000040U  /* Selbstheilungs-Modus */
#define UHCS_FLAG_SICHER        0x00000080U  /* Sicherheits-Modus */
#define UHCS_FLAG_ULTRA         0x00000100U  /* Ultra-Kompressionsmodus */
#define UHCS_FLAG_DELTA         0x00000200U  /* Delta-Kodierung aktiv */
#define UHCS_FLAG_BWT           0x00000400U  /* Burrows-Wheeler-Transform */
#define UHCS_FLAG_MTF           0x00000800U  /* Move-To-Front aktiv */
#define UHCS_FLAG_HUFFMAN       0x00001000U  /* Huffman-Flag (nur RAW-Fallback-Marker) */
#define UHCS_FLAG_RLE           0x00002000U  /* Run-Length-Encoding aktiv */
#define UHCS_FLAG_TESLA         0x00004000U  /* Tesla-Anker-Filter aktiv */
#define UHCS_FLAG_GRONAUER      0x00008000U  /* Gronauer-Anker aktiv */
#define UHCS_FLAG_COMPRESSED    0x80000000U  /* Daten sind komprimiert */

/* ════════════════════════════════════════════════════════════════════
 *  EFFIZIENZ-KONSTANTEN (333/666/999 Muster)
 * ════════════════════════════════════════════════════════════════════ */
#define EFFIZIENZ_333       333     /* Basis-Effizienz-Schwelle (33.3%) */
#define EFFIZIENZ_666       666     /* Mittlere Effizienz-Schwelle (66.6%) */
#define EFFIZIENZ_999       999     /* Höchste Effizienz-Schwelle (99.9%) */

/* Effizienz-Makros (Eingabe: Verhältnis * 1000) */
#define UHCS_EFFIZIENZ_BASIS(r)  ((r) >= EFFIZIENZ_333)
#define UHCS_EFFIZIENZ_MITTEL(r) ((r) >= EFFIZIENZ_666)
#define UHCS_EFFIZIENZ_HOCH(r)   ((r) >= EFFIZIENZ_999)

/* ════════════════════════════════════════════════════════════════════
 *  WERKSTEIN-SLOT-KONSTANTEN (Regelwerk §15–§21)
 * ════════════════════════════════════════════════════════════════════ */
#define UHCS_SLOT_LUT           1   /* MEIKEL_B_LUT */
#define UHCS_SLOT_INV           2   /* MEIKEL_B_INV */
#define UHCS_SLOT_ALFONS       201  /* ALFONS_FOLGE (Großvater) */
#define UHCS_SLOT_RUTH         202  /* RUTH_FOLGE (Großmutter) */
#define UHCS_SLOT_LOCHBILD_C   280  /* lochbild_compress */
#define UHCS_SLOT_LOCHBILD_D   281  /* lochbild_decompress */
#define UHCS_SLOT_COMPRESS     290  /* uhcs_compress */
#define UHCS_SLOT_DECOMPRESS   291  /* uhcs_decompress */
#define UHCS_SLOT_SIGNATUR     300  /* MB_SYSTEM_SIGNATUR */

/* ════════════════════════════════════════════════════════════════════
 *  HILFSMAKROS
 * ════════════════════════════════════════════════════════════════════ */

/* Minimum/Maximum ohne -lm */
#define UHCS_MIN(a, b)  ((a) < (b) ? (a) : (b))
#define UHCS_MAX(a, b)  ((a) > (b) ? (a) : (b))

/* Ausrichtung auf nächste Zweierpotenz */
#define UHCS_ALIGN_UP(x, a)  (((x) + (a) - 1) & ~((a) - 1))

/* Byte-Zugriff */
#define UHCS_BYTE(x, n)  (((x) >> (8 * (n))) & 0xFF)

/* Clamp */
#define UHCS_CLAMP(v, lo, hi)  UHCS_MAX((lo), UHCS_MIN((hi), (v)))

/* Prüft ob x eine der Tesla-Anker-Zahlen ist */
#define UHCS_SIGMA_CHECK()  \
    (UHCS_A3 + UHCS_A2 + UHCS_A1 + UHCS_A0 + UHCS_GRONAUER == UHCS_SIGMA)

/* RUTH_FOLGE Ableitung aus ALFONS: RUTH[i] = 255 - ALFONS[255-i] */
#define UHCS_RUTH_FROM_ALFONS(alfons_val_at_255_minus_i) \
    ((uint8_t)(255u - (uint8_t)(alfons_val_at_255_minus_i)))

/* ════════════════════════════════════════════════════════════════════
 *  DNA-ARCHIV PFAD
 * ════════════════════════════════════════════════════════════════════ */
#define UHCS_DNA_DIR    "/.mb_system"
#define UHCS_DNA_FILE   "/.mb_system/dna.bin"

/* ════════════════════════════════════════════════════════════════════
 *  PIPELINE-MASKEN
 * ════════════════════════════════════════════════════════════════════ */
/* Alle 26 aktiven Ebenen */
#define UHCS_PIPELINE_ALL       0x03FFFFFFU
/* Standard-Pipeline (Ebenen 0-15) */
#define UHCS_PIPELINE_STANDARD  0x0000FFFFU
/* Schnell-Pipeline (Ebenen 0-7) */
#define UHCS_PIPELINE_SCHNELL   0x000000FFU

/* ════════════════════════════════════════════════════════════════════
 *  COMPILER-ATTRIBUTE (portable)
 * ════════════════════════════════════════════════════════════════════ */
#if defined(__GNUC__) || defined(__clang__)
#  define UHCS_LIKELY(x)    __builtin_expect(!!(x), 1)
#  define UHCS_UNLIKELY(x)  __builtin_expect(!!(x), 0)
#  define UHCS_INLINE       __attribute__((always_inline)) static inline
#  define UHCS_NOINLINE     __attribute__((noinline))
#  define UHCS_PURE         __attribute__((pure))
#  define UHCS_CONST_FN     __attribute__((const))
#else
#  define UHCS_LIKELY(x)    (x)
#  define UHCS_UNLIKELY(x)  (x)
#  define UHCS_INLINE       static inline
#  define UHCS_NOINLINE
#  define UHCS_PURE
#  define UHCS_CONST_FN
#endif

/* ════════════════════════════════════════════════════════════════════
 *  INLINE-HILFSFUNKTIONEN (kein -lm)
 * ════════════════════════════════════════════════════════════════════ */

/* BoesingFolge als inline-Funktion (Horner, schnellste Variante) */
UHCS_INLINE uint8_t uhcs_boesing_inline(uint8_t x) {
    uint32_t t = (uint32_t)x;
    t = ((UHCS_A3 * t + UHCS_A2) * t + UHCS_A1) * t + UHCS_A0;
    return (uint8_t)(t & 0xFFu);
}

/* Sigma-Prüfung zur Laufzeit */
UHCS_INLINE int uhcs_sigma_check(void) {
    return (UHCS_A3 + UHCS_A2 + UHCS_A1 + UHCS_A0 + UHCS_GRONAUER) == UHCS_SIGMA;
}

/* Tesla-Anker-Prüfung */
UHCS_INLINE int uhcs_is_tesla(uint8_t x) {
    return x == 0 || x == 3 || x == 6 || x == 9;
}

/* Gronauer-Resonanz: x % 3 == 0 (da 126 = 2·63 = 2·7·9 = 2·7·3²) */
UHCS_INLINE int uhcs_gronauer_resonanz(uint8_t x) {
    return (x % 3 == 0);
}

#endif /* MB_REGELWERK_V31_H */
