/* ╔══════════════════════════════════════════════════════════════════════════════╗
 * ║  uhcs_mb_typen.h — MB-Systeme v31 / UHCS MB Typ-Definitionen              ║
 * ║  (c) Meikel Boesing 2026 — Gronau (Westfalen)                              ║
 * ║                                                                            ║
 * ║  Zweiter Header: Exportierte Typen für externe Integration.                ║
 * ║  Der erste Header (MB_REGELWERK_v31.h) enthält die Konstanten & Regeln.    ║
 * ║  Dieser Header stellt die Datentypen bereit, die GUI/Plugins brauchen.     ║
 * ╚══════════════════════════════════════════════════════════════════════════════╝ */

#ifndef UHCS_MB_TYPEN_H
#define UHCS_MB_TYPEN_H

#include <stdint.h>
#include <stddef.h>

/* ═══════════════════════════════════════════════════════════════════════════════
 *  §1  MATHEMATISCHE KONSTANTEN (UNANTASTBAR — Regelwerk §1)
 * ═══════════════════════════════════════════════════════════════════════════════ */

#define UHCS_MB_VERSION      "31.0"
#define UHCS_MB_SIGMA        568
#define UHCS_MB_A3           42
#define UHCS_MB_A2           158
#define UHCS_MB_A1           215
#define UHCS_MB_A0           27
#define UHCS_MB_GRONAUER     126
#define UHCS_MB_MEIKEL_PRIM  331
#define UHCS_MB_ALPHA_INV    137
#define UHCS_MB_TESLA_0      0
#define UHCS_MB_TESLA_3      3
#define UHCS_MB_TESLA_6      6
#define UHCS_MB_TESLA_9      9

/* Sigma-Sperre: Koeffizientensumme MUSS 568 ergeben */
_Static_assert(UHCS_MB_A3 + UHCS_MB_A2 + UHCS_MB_A1 + UHCS_MB_A0 + UHCS_MB_GRONAUER == UHCS_MB_SIGMA,
               "Sigma-Sperre verletzt: 42+158+215+27+126 != 568");

/* ═══════════════════════════════════════════════════════════════════════════════
 *  §2  WERKSTEIN-TYPEN (Regelwerk §15-§16)
 * ═══════════════════════════════════════════════════════════════════════════════ */

/* Welt-Zuordnung (§18) */
typedef enum {
    UHCS_WORLD_A      = 0,   /* Gerade, +, Floor, Fixiert, Konvergent */
    UHCS_WORLD_B      = 1,   /* Ungerade, −, Ceil, Offen, Divergent  */
    UHCS_WORLD_HYBRID = 2    /* Brücke A↔B (§29)                     */
} UhcsMBWelt;

/* Polarität */
typedef enum {
    UHCS_POL_POS    = 0,
    UHCS_POL_NEG    = 1,
    UHCS_POL_HYBRID = 2
} UhcsMBPolaritaet;

/* Rundungsrichtung (§24-§25) */
typedef enum {
    UHCS_ROUND_FLOOR = 0,    /* Fixierung / Boden / Welt A */
    UHCS_ROUND_CEIL  = 1     /* Öffnung / Spannung / Welt B */
} UhcsMBRundung;

/* Werkstein-Kategorie (§15) */
typedef enum {
    UHCS_WS_LUT        = 0,
    UHCS_WS_INVERS     = 1,
    UHCS_WS_TRANSFORM  = 2,
    UHCS_WS_KERN       = 3,
    UHCS_WS_REFERENZ   = 4,
    UHCS_WS_BEOBACHTER = 5,
    UHCS_WS_SIGNATUR   = 6
} UhcsMBWerksteinKat;

/* Funktionswürde (§26) */
typedef enum {
    UHCS_FW_FIXIEREND     = 0,  /* Fixierung */
    UHCS_FW_RUECKFUEHREND = 1,  /* Rückführung */
    UHCS_FW_OEFFNEND      = 2,  /* Öffnung */
    UHCS_FW_FORTSETZEND   = 3,  /* Fortsetzung */
    UHCS_FW_VERMITTELND   = 4,  /* Vermittlung */
    UHCS_FW_BEOBACHTEND   = 5,  /* Beobachtung */
    UHCS_FW_SPIEGELND     = 6,  /* Spiegelung */
    UHCS_FW_INVERTIEREND  = 7   /* Inversion */
} UhcsMBFunktionswuerde;

/* ═══════════════════════════════════════════════════════════════════════════════
 *  §3  WERKSTEIN-DNA (Regelwerk §15: Jede Funktion = Stein mit DNA)
 * ═══════════════════════════════════════════════════════════════════════════════ */

typedef struct {
    uint16_t           slot;          /* Slot-Nummer 1-800 */
    char               name[64];      /* Funktionsname */
    uint8_t            ebene;         /* 0-9 Ebenen-Zuordnung (§2) */
    UhcsMBWelt         welt;          /* A / B / Hybrid */
    UhcsMBPolaritaet   polaritaet;    /* + / − / Hybrid */
    UhcsMBRundung      rundung;       /* Floor / Ceil */
    UhcsMBWerksteinKat kategorie;     /* LUT/Invers/Transform/... */
    UhcsMBFunktionswuerde wuerde;     /* Fixierend/Öffnend/... */
    uint8_t            paritaet;      /* 0=gerade, 1=ungerade */
    uint8_t            aktiv;         /* 1=belegt, 0=frei */
} UhcsMBWerksteinDNA;

/* ═══════════════════════════════════════════════════════════════════════════════
 *  §4  KOMPRIMIERUNGS-ERGEBNIS
 * ═══════════════════════════════════════════════════════════════════════════════ */

typedef struct {
    size_t    original_groesse;
    size_t    komprimiert_groesse;
    double    ratio;                 /* komprimiert / original */
    double    durchsatz_mbs;         /* MB/s */
    uint32_t  crc32;                 /* CRC32 des Originals */
    uint32_t  siegel;                /* UHCS-Siegel */
    uint8_t   hardware_reif;         /* 1 = bereit */
} UhcsMBKompressionsInfo;

/* ═══════════════════════════════════════════════════════════════════════════════
 *  §5  TEIL-SPEZIFISCHE TYPEN (TEIL LXXXVI-XCI)
 * ═══════════════════════════════════════════════════════════════════════════════ */

/* TEIL LXXXVI: VakuumPrediktor */
typedef struct {
    double   vorhersagbarkeit;       /* 0.0-100.0 */
    uint32_t null_count;
    uint32_t gleich_count;
    uint8_t  ist_vakuum;             /* 1 = Block überspringbar */
    uint16_t pattern_periode;        /* 0 = kein Pattern */
    uint8_t  skip_empfehlung;        /* 1 = überspringen */
    uint32_t siegel;
} UhcsMBVakuumAnalyse;

/* TEIL LXXXVII: DreiStufenStatik */
typedef struct {
    uint8_t  stufe;                  /* 1=Basis(33.3%), 2=Mittel(66.6%), 3=Hoch(99.9%) */
    double   qualitaet;              /* 0.0-100.0 */
    uint8_t  kaskade_bestanden;      /* 1 = alle 9 Primzahlen ok */
    uint32_t kaskaden_siegel;
    double   fusions_score;
    uint32_t siegel;
} UhcsMBDreiStufen;

/* TEIL LXXXVIII: UniversalApproximator */
typedef struct {
    int32_t  koeffizienten[8];       /* Polynom Grad 0-7 */
    uint8_t  grad;                   /* Bester Polynomgrad */
    double   fehler;                 /* Mittlerer Fehler */
    uint64_t champernowne_offset;    /* Adresse im Champernowne-Strom */
    uint32_t siegel;
} UhcsMBApproxErgebnis;

/* TEIL LXXXIX: ShannonGapAnalyzer */
typedef struct {
    double   shannon_entropie;       /* Bits/Byte (0-8) */
    double   kompressionsrate;       /* Erreichte Rate */
    double   gap_prozent;            /* Lücke zum Optimum */
    uint16_t woerterbuch_groesse;    /* Aktive Einträge */
    double   fusions_effizienz;
    uint32_t siegel;
} UhcsMBShannonGap;

/* TEIL XC: HaarWavelet & GorillaEncoder */
typedef struct {
    uint32_t low_summe;              /* Tiefpass-Komponente */
    uint32_t high_summe;             /* Hochpass-Komponente */
    double   haar_ratio;             /* low/(low+high) */
    double   gorilla_effizienz;      /* % Null-Deltas */
    uint32_t siegel;
} UhcsMBHaarGorilla;

/* TEIL XCI: Fusions-Manifest */
typedef struct {
    uint16_t teile_anzahl;           /* Anzahl TEILe (174) */
    uint16_t paragraphen_anzahl;     /* Anzahl §§ (436) */
    uint16_t testgruppen;            /* Anzahl Testgruppen */
    uint16_t werksteine;             /* Belegte Werksteine */
    uint16_t tests_gesamt;           /* Selbsttest-Anzahl */
    double   gesamt_score;           /* Gesamtqualität */
    uint32_t manifest_siegel;        /* Deterministisches Siegel */
    uint8_t  validierung_bestanden;  /* 1 = alles ok */
} UhcsMBFusionsManifest;

/* ═══════════════════════════════════════════════════════════════════════════════
 *  §6  SYSTEM-SIGNATUR
 * ═══════════════════════════════════════════════════════════════════════════════ */

#define UHCS_MB_SIGNATUR  "MB-Systeme v31.0 | UHCS MB | Meikel Boesing 2026 | Gronau"
#define UHCS_MB_MAGIC     0x4D42    /* 'MB' in Big-Endian */
#define UHCS_MB_TEILE     174
#define UHCS_MB_PARAGRAPHEN 438
#define UHCS_MB_TESTS     742

#endif /* UHCS_MB_TYPEN_H */
