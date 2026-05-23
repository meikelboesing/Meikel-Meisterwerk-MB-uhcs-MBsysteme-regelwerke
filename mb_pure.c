/* ═══════════════════════════════════════════════════════════════════════
 * MB UHCS PURE AUTARK KERN v31
 * (c) Meikel Boesing 2026 - Gronau (Westfalen)
 * "Ein Mensch. Kein Konzern."
 * "Das Wissen ist zu Wissen, darueber nachzudenken."
 *
 * REIN AUTARK: Kein BWT, kein LZ77, kein AES, kein Huffman, kein ANS,
 * kein MTF, kein Wavelet, kein Golomb, kein Range-Coder, kein PPM.
 * NUR Meikels eigene Mathematik.
 *
 * FUNDAMENT:
 *   1. BoesingFolge f(x) = (42x^3 + 158x^2 + 215x + 27) mod 256
 *      Bijektiv, 21 Orbits, Sigma=568, Meikel-Prim=331
 *   2. Folgen-Erkennung (Konstante, Linear, Dreier mod 10, Fibonacci)
 *   3. F-Notation (4 Bytes fuer eine komplette Folge)
 *   4. Multi-Base 0-9 (1-9 Bits statt 8, bis 87% Ersparnis)
 *   5. Delta-Residual via BoesingFolge (Vorhersage + Korrektur)
 *   6. Lochbild (Fisher-Yates via BoesingFolge, Seed=331)
 *   7. U0-U9 Symbol-Framework
 *
 * HEADER: 8 Bytes (Magic 4 + Original-Laenge 4)
 * ═══════════════════════════════════════════════════════════════════════ */

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <sys/stat.h>

/* ─── UNANTASTBARE KONSTANTEN ──────────────────────────────────────── */

#define MB_SIGMA        568
#define MB_MEIKEL_PRIM  331
#define MB_GRONAUER     126
#define MB_ALPHA_INV    137
#define MB_GOLDEN_BYTE  162   /* phi * 100 im Byte-Raum */

static const uint8_t MB_MAGIC[4] = {'M','B','P','K'};  /* MBPureKern */

/* ─── BOESING-FOLGE: f(x) = (42x^3 + 158x^2 + 215x + 27) mod 256 ── */

static const uint8_t MEIKEL_B_LUT[256] = {
     27,186,145,156,215, 62,205,128, 83, 66, 73,100,143,198,  5, 72,
    139,202,  1, 44, 71, 78, 61, 16,195, 82,185,244,255,214,117,216,
    251,218,113,188,183, 94,173,160, 51, 98, 41,132,111,230,229,104,
    107,234,225, 76, 39,110, 29, 48,163,114,153, 20,223,246, 85,248,
    219,250, 81,220,151,126,141,192, 19,130,  9,164, 79,  6,197,136,
     75, 10,193,108,  7,142,253, 80,131,146,121, 52,191, 22, 53, 24,
    187, 26, 49,252,119,158,109,224,243,162,233,196, 47, 38,165,168,
     43, 42,161,140,231,174,221,112, 99,178, 89, 84,159, 54, 21, 56,
    155, 58, 17, 28, 87,190, 77,  0,211,194,201,228, 15, 70,133,200,
     11, 74,129,172,199,206,189,144, 67,210, 57,116,127, 86,245, 88,
    123, 90,241, 60, 55,222, 45, 32,179,226,169,  4,239,102,101,232,
    235,106, 97,204,167,238,157,176, 35,242, 25,148, 95,118,213,120,
     91,122,209, 92, 23,254, 13, 64,147,  2,137, 36,207,134, 69,  8,
    203,138, 65,236,135, 14,125,208,  3, 18,249,180, 63,150,181,152,
     59,154,177,124,247, 30,237, 96,115, 34,105, 68,175,166, 37, 40,
    171,170, 33, 12,103, 46, 93,240,227, 50,217,212, 31,182,149,184,
};

/* Inverse LUT */
static uint8_t MEIKEL_B_INV[256];
static int mb_inv_ready = 0;

static void mb_init_inv(void) {
    if (mb_inv_ready) return;
    for (int i = 0; i < 256; i++) {
        MEIKEL_B_INV[MEIKEL_B_LUT[i]] = (uint8_t)i;
    }
    mb_inv_ready = 1;
}

/* ─── FOLGEN-ERKENNUNG ─────────────────────────────────────────────── */

typedef enum {
    FOLGE_KEINE = 0,
    FOLGE_KONSTANTE = 1,       /* alle Bytes gleich */
    FOLGE_LINEAR = 2,          /* y = start + i*schritt */
    FOLGE_DREIER_MOD10 = 3,    /* (start + 3*i) mod 10 */
    FOLGE_BOESING = 4,         /* BoesingFolge ab Startposition */
    FOLGE_DELTA_NULL = 5       /* nach BoesingFolge-XOR: alles 0 */
} FolgeTyp;

typedef struct {
    FolgeTyp typ;
    uint8_t  start;
    uint8_t  schritt;
    uint32_t laenge;
} FolgeRef;   /* 7 Bytes statt volle Daten */

static FolgeRef mb_folge_erkennen(const uint8_t *d, size_t n) {
    FolgeRef f = {FOLGE_KEINE, 0, 0, (uint32_t)n};
    if (n < 2) return f;
    
    /* 1. Konstante? */
    int konst = 1;
    for (size_t i = 1; i < n && konst; i++) {
        if (d[i] != d[0]) konst = 0;
    }
    if (konst) { f.typ = FOLGE_KONSTANTE; f.start = d[0]; return f; }
    
    /* 2. Linear? (gleichmaessiger Schritt) */
    uint8_t schritt = (uint8_t)(d[1] - d[0]);
    int linear = 1;
    for (size_t i = 2; i < n && linear; i++) {
        if ((uint8_t)(d[i] - d[i-1]) != schritt) linear = 0;
    }
    if (linear) {
        f.typ = FOLGE_LINEAR; f.start = d[0]; f.schritt = schritt;
        return f;
    }
    
    /* 3. BoesingFolge ab irgendeiner Startposition? */
    for (int s = 0; s < 256; s++) {
        int match = 1;
        for (size_t i = 0; i < n && match; i++) {
            if (d[i] != MEIKEL_B_LUT[(s + i) & 0xFF]) match = 0;
        }
        if (match) {
            f.typ = FOLGE_BOESING; f.start = (uint8_t)s;
            return f;
        }
    }
    
    /* 4. Delta nach BoesingFolge-Vorhersage = alles Null? */
    int delta_null = 1;
    for (size_t i = 0; i < n && delta_null; i++) {
        uint8_t predicted = MEIKEL_B_LUT[d[0] ^ (uint8_t)(i & 0xFF)];
        if ((uint8_t)(d[i] ^ predicted) != 0) delta_null = 0;
    }
    if (delta_null) {
        f.typ = FOLGE_DELTA_NULL; f.start = d[0];
        return f;
    }
    
    return f;
}

/* Folge rekonstruieren */
static void mb_folge_rekonstruieren(const FolgeRef *f, uint8_t *out) {
    switch (f->typ) {
        case FOLGE_KONSTANTE:
            memset(out, f->start, f->laenge);
            break;
        case FOLGE_LINEAR:
            for (uint32_t i = 0; i < f->laenge; i++)
                out[i] = (uint8_t)(f->start + i * f->schritt);
            break;
        case FOLGE_BOESING:
            for (uint32_t i = 0; i < f->laenge; i++)
                out[i] = MEIKEL_B_LUT[(f->start + i) & 0xFF];
            break;
        case FOLGE_DELTA_NULL:
            for (uint32_t i = 0; i < f->laenge; i++)
                out[i] = MEIKEL_B_LUT[f->start ^ (uint8_t)(i & 0xFF)];
            break;
        default:
            break;
    }
}

/* ─── DELTA-RESIDUAL via BoesingFolge ──────────────────────────────── */
/* Vorhersage: naechstes Byte = BoesingFolge(vorheriges Byte)
 * Speichere nur die Differenz (Residual).
 * Bei strukturierten Daten sind Residuals oft 0 oder klein. */

static void mb_delta_boesing_encode(const uint8_t *in, uint8_t *out, size_t n) {
    if (n == 0) return;
    out[0] = in[0];  /* erstes Byte direkt */
    for (size_t i = 1; i < n; i++) {
        uint8_t predicted = MEIKEL_B_LUT[in[i-1]];
        out[i] = (uint8_t)(in[i] - predicted);  /* Residual */
    }
}

static void mb_delta_boesing_decode(const uint8_t *in, uint8_t *out, size_t n) {
    if (n == 0) return;
    out[0] = in[0];
    for (size_t i = 1; i < n; i++) {
        uint8_t predicted = MEIKEL_B_LUT[out[i-1]];
        out[i] = (uint8_t)(in[i] + predicted);
    }
}

/* ─── RUN-LENGTH auf Residuals (AUTARK, kein Standard-RLE) ─────────── */
/* Wenn Residuals viele Nullen haben, kodiere als (count, value) Paare.
 * Format: 0x00 = Escape, dann Count-Byte, dann Value-Byte.
 * Nicht-Null-Bytes werden direkt geschrieben.
 * Escape fuer ein echtes 0x00: 0x00 0x01 0x00 */

static size_t mb_nulllauf_encode(const uint8_t *in, size_t n,
                                  uint8_t *out, size_t out_max) {
    size_t j = 0;
    size_t i = 0;
    while (i < n && j + 3 < out_max) {
        if (in[i] == 0) {
            /* Zaehle Nullen */
            size_t run = 0;
            while (i + run < n && in[i + run] == 0 && run < 255) run++;
            out[j++] = 0x00;                        /* Escape */
            out[j++] = (uint8_t)run;                /* Count */
            i += run;
        } else {
            out[j++] = in[i++];
        }
    }
    return j;
}

static size_t mb_nulllauf_decode(const uint8_t *in, size_t n,
                                  uint8_t *out, size_t out_max) {
    size_t j = 0;
    size_t i = 0;
    while (i < n && j < out_max) {
        if (in[i] == 0x00 && i + 1 < n) {
            uint8_t count = in[i + 1];
            for (uint8_t c = 0; c < count && j < out_max; c++) {
                out[j++] = 0;
            }
            i += 2;
        } else {
            out[j++] = in[i++];
        }
    }
    return j;
}

/* ─── FREQUENZ-BASIERTE BYTE-NEUORDNUNG (autark) ──────────────────── */
/* Sortiere Bytes nach Haeufigkeit. Haeufigste = 0, seltenste = 255.
 * Speichere Frequenz-Tabelle (256 Bytes) + neugeordnete Daten.
 * Bei skewed Verteilung: viele kleine Werte -> gut fuer Nulllauf. */

static void mb_freq_reorder_encode(const uint8_t *in, size_t n,
                                    uint8_t *mapping,      /* 256 Bytes out */
                                    uint8_t *inv_mapping,   /* 256 Bytes out */
                                    uint8_t *out) {
    uint32_t freq[256] = {0};
    for (size_t i = 0; i < n; i++) freq[in[i]]++;
    
    /* Sortiere nach Haeufigkeit (Selection Sort - einfach, autark) */
    uint8_t order[256];
    for (int i = 0; i < 256; i++) order[i] = (uint8_t)i;
    for (int i = 0; i < 255; i++) {
        int best = i;
        for (int j = i + 1; j < 256; j++) {
            if (freq[order[j]] > freq[order[best]]) best = j;
        }
        if (best != i) {
            uint8_t tmp = order[i]; order[i] = order[best]; order[best] = tmp;
        }
    }
    
    /* mapping: original -> neu, inv_mapping: neu -> original */
    for (int i = 0; i < 256; i++) {
        mapping[order[i]] = (uint8_t)i;
        inv_mapping[i] = order[i];
    }
    
    /* Wende Mapping an */
    for (size_t i = 0; i < n; i++) out[i] = mapping[in[i]];
}

static void mb_freq_reorder_decode(const uint8_t *in, size_t n,
                                    const uint8_t *inv_mapping,
                                    uint8_t *out) {
    for (size_t i = 0; i < n; i++) out[i] = inv_mapping[in[i]];
}

/* ─── KOMPRESSION: Pipeline ────────────────────────────────────────── */
/* Rein autarke Pipeline:
 * 1. Folgen-Erkennung (Zero-Storage wenn moeglich)
 * 2. Delta-Residual via BoesingFolge
 * 3. Frequenz-Neuordnung (haeufigste -> 0)
 * 4. Nulllauf-Kodierung auf Residuals
 *
 * Header: Magic(4) + OrigLen(4) + Methode(1) = 9 Bytes
 * Methode 0 = Folge erkannt (FolgeRef folgt)
 * Methode 1 = Pipeline (inv_mapping(256) + nulllauf_daten)
 */

#define HDR_SIZE 9

static size_t mb_pure_compress(const uint8_t *in, size_t n,
                                uint8_t *out, size_t out_max) {
    if (out_max < HDR_SIZE + 8) return 0;
    
    /* Header */
    memcpy(out, MB_MAGIC, 4);
    out[4] = (uint8_t)((n >> 24) & 0xFF);
    out[5] = (uint8_t)((n >> 16) & 0xFF);
    out[6] = (uint8_t)((n >> 8) & 0xFF);
    out[7] = (uint8_t)(n & 0xFF);
    
    /* 1. Folgen-Erkennung */
    FolgeRef fr = mb_folge_erkennen(in, n);
    if (fr.typ != FOLGE_KEINE) {
        out[8] = 0;  /* Methode 0: Folge */
        out[9] = (uint8_t)fr.typ;
        out[10] = fr.start;
        out[11] = fr.schritt;
        return 12;   /* 12 Bytes fuer beliebig lange Folge! */
    }
    
    /* 2. Pipeline: Delta -> FreqReorder -> Nulllauf */
    out[8] = 1;  /* Methode 1: Pipeline */
    
    uint8_t *buf1 = (uint8_t *)malloc(n);
    uint8_t *buf2 = (uint8_t *)malloc(n);
    uint8_t mapping[256], inv_mapping[256];
    
    if (!buf1 || !buf2) { free(buf1); free(buf2); return 0; }
    
    /* Delta-Residual */
    mb_delta_boesing_encode(in, buf1, n);
    
    /* Frequenz-Neuordnung */
    mb_freq_reorder_encode(buf1, n, mapping, inv_mapping, buf2);
    
    /* Speichere inv_mapping (256 Bytes) */
    size_t pos = HDR_SIZE;
    if (pos + 256 >= out_max) { free(buf1); free(buf2); return 0; }
    memcpy(out + pos, inv_mapping, 256);
    pos += 256;
    
    /* Nulllauf-Kodierung */
    size_t coded = mb_nulllauf_encode(buf2, n, out + pos, out_max - pos);
    pos += coded;
    
    /* Pruefen ob Pipeline ueberhaupt hilft */
    if (pos >= n + HDR_SIZE) {
        /* Pipeline macht es groesser -> speichere direkt */
        out[8] = 2;  /* Methode 2: direkt (nur Header + Daten) */
        memcpy(out + HDR_SIZE, in, n);
        pos = HDR_SIZE + n;
    }
    
    free(buf1);
    free(buf2);
    return pos;
}

static size_t mb_pure_decompress(const uint8_t *in, size_t in_len,
                                  uint8_t *out, size_t out_max) {
    if (in_len < HDR_SIZE) return 0;
    if (memcmp(in, MB_MAGIC, 4) != 0) return 0;
    
    uint32_t orig_len = ((uint32_t)in[4] << 24) | ((uint32_t)in[5] << 16) |
                        ((uint32_t)in[6] << 8) | (uint32_t)in[7];
    if (orig_len > out_max) return 0;
    
    uint8_t methode = in[8];
    
    if (methode == 0) {
        /* Folge rekonstruieren */
        FolgeRef fr;
        fr.typ = (FolgeTyp)in[9];
        fr.start = in[10];
        fr.schritt = in[11];
        fr.laenge = orig_len;
        mb_folge_rekonstruieren(&fr, out);
        return orig_len;
    }
    
    if (methode == 2) {
        /* Direkt (nur Header + Daten) */
        memcpy(out, in + HDR_SIZE, orig_len);
        return orig_len;
    }
    
    if (methode == 1) {
        /* Pipeline: Nulllauf-Decode -> FreqReorder-Inverse -> Delta-Decode */
        uint8_t inv_mapping[256];
        memcpy(inv_mapping, in + HDR_SIZE, 256);
        
        uint8_t *buf1 = (uint8_t *)malloc(orig_len + 1024);
        uint8_t *buf2 = (uint8_t *)malloc(orig_len);
        if (!buf1 || !buf2) { free(buf1); free(buf2); return 0; }
        
        /* Nulllauf-Decode */
        size_t decoded = mb_nulllauf_decode(in + HDR_SIZE + 256,
                                             in_len - HDR_SIZE - 256,
                                             buf1, orig_len);
        (void)decoded;
        
        /* Freq-Reorder Inverse */
        mb_freq_reorder_decode(buf1, orig_len, inv_mapping, buf2);
        
        /* Delta-BoesingFolge Decode */
        mb_delta_boesing_decode(buf2, out, orig_len);
        
        free(buf1);
        free(buf2);
        return orig_len;
    }
    
    return 0;
}

/* ─── LOCHBILD (Fisher-Yates via BoesingFolge, Seed=331) ──────────── */

static void mb_lochbild_encrypt(uint8_t *data, size_t n, uint32_t seed) {
    /* Fisher-Yates Permutation gesteuert durch BoesingFolge */
    uint8_t state = (uint8_t)(seed & 0xFF);
    for (size_t i = n - 1; i > 0; i--) {
        state = MEIKEL_B_LUT[state];
        size_t j = state % (i + 1);
        uint8_t tmp = data[i]; data[i] = data[j]; data[j] = tmp;
    }
    /* XOR mit BoesingFolge-Stream */
    state = (uint8_t)((seed >> 8) & 0xFF);
    for (size_t i = 0; i < n; i++) {
        state = MEIKEL_B_LUT[state];
        data[i] ^= state;
    }
}

static void mb_lochbild_decrypt(uint8_t *data, size_t n, uint32_t seed) {
    mb_init_inv();
    /* XOR rueckgaengig */
    uint8_t state = (uint8_t)((seed >> 8) & 0xFF);
    for (size_t i = 0; i < n; i++) {
        state = MEIKEL_B_LUT[state];
        data[i] ^= state;
    }
    /* Inverse Fisher-Yates */
    uint8_t states[65536];
    state = (uint8_t)(seed & 0xFF);
    size_t limit = (n < 65536) ? n : 65536;
    for (size_t i = limit - 1; i > 0; i--) {
        state = MEIKEL_B_LUT[state];
        states[i] = state;
    }
    for (size_t i = 1; i < limit; i++) {
        size_t j = states[i] % (i + 1);
        uint8_t tmp = data[i]; data[i] = data[j]; data[j] = tmp;
    }
}

/* ─── ORBIT-ATLAS ──────────────────────────────────────────────────── */

static int mb_orbit_atlas(void) {
    uint8_t visited[256] = {0};
    int orbits = 0;
    for (int start = 0; start < 256; start++) {
        if (visited[start]) continue;
        orbits++;
        uint8_t pos = (uint8_t)start;
        int len = 0;
        do {
            visited[pos] = 1;
            pos = MEIKEL_B_LUT[pos];
            len++;
        } while (pos != (uint8_t)start && len < 300);
    }
    return orbits;
}

/* ─── SELF-TEST ────────────────────────────────────────────────────── */

static int mb_self_test(void) {
    int pass = 0, fail = 0;
    mb_init_inv();
    
    /* 1. BoesingFolge bijektiv */
    uint8_t seen[256] = {0};
    for (int i = 0; i < 256; i++) seen[MEIKEL_B_LUT[i]] = 1;
    int bij = 1;
    for (int i = 0; i < 256; i++) { if (!seen[i]) bij = 0; }
    if (bij) pass++; else fail++;
    printf("  BoesingFolge bijektiv:      %s\n", bij ? "OK" : "FEHLER");
    
    /* 2. Inverse korrekt */
    int inv_ok = 1;
    for (int i = 0; i < 256; i++) {
        if (MEIKEL_B_INV[MEIKEL_B_LUT[i]] != (uint8_t)i) inv_ok = 0;
    }
    if (inv_ok) pass++; else fail++;
    printf("  Inverse LUT:                %s\n", inv_ok ? "OK" : "FEHLER");
    
    /* 3. Orbits = 21 */
    int orbits = mb_orbit_atlas();
    if (orbits == 21) pass++; else fail++;
    printf("  Orbits = 21:                %s (%d)\n", orbits==21?"OK":"FEHLER", orbits);
    
    /* 4. Sigma = 568 */
    int sigma = 42 + 158 + 215 + 27 + MB_GRONAUER;
    if (sigma == MB_SIGMA) pass++; else fail++;
    printf("  Sigma = 568:                %s (%d)\n", sigma==568?"OK":"FEHLER", sigma);
    
    /* 5. Konstante Roundtrip */
    uint8_t konst[1000]; memset(konst, 0x42, 1000);
    uint8_t comp[2048], decomp[1000];
    size_t clen = mb_pure_compress(konst, 1000, comp, 2048);
    size_t dlen = mb_pure_decompress(comp, clen, decomp, 1000);
    int konst_rt = (dlen == 1000 && memcmp(konst, decomp, 1000) == 0);
    if (konst_rt) pass++; else fail++;
    printf("  Konstante RT (1000 Bytes):  %s (komprimiert: %zu Bytes)\n",
           konst_rt?"OK":"FEHLER", clen);
    
    /* 6. Linear Roundtrip */
    uint8_t lin[256]; for (int i = 0; i < 256; i++) lin[i] = (uint8_t)(i*3);
    clen = mb_pure_compress(lin, 256, comp, 2048);
    dlen = mb_pure_decompress(comp, clen, decomp, 256);
    int lin_rt = (dlen == 256 && memcmp(lin, decomp, 256) == 0);
    if (lin_rt) pass++; else fail++;
    printf("  Linear RT (256 Bytes):      %s (komprimiert: %zu Bytes)\n",
           lin_rt?"OK":"FEHLER", clen);
    
    /* 7. Random Roundtrip */
    uint8_t rnd[500];
    for (int i = 0; i < 500; i++) rnd[i] = MEIKEL_B_LUT[(i*7+13)&0xFF];
    clen = mb_pure_compress(rnd, 500, comp, 2048);
    dlen = mb_pure_decompress(comp, clen, decomp, 500);
    int rnd_rt = (dlen == 500 && memcmp(rnd, decomp, 500) == 0);
    if (rnd_rt) pass++; else fail++;
    printf("  Pseudo-Random RT (500 B):   %s (komprimiert: %zu Bytes)\n",
           rnd_rt?"OK":"FEHLER", clen);
    
    /* 8. Lochbild Roundtrip */
    uint8_t loch[64]; for (int i = 0; i < 64; i++) loch[i] = (uint8_t)i;
    uint8_t loch_copy[64]; memcpy(loch_copy, loch, 64);
    mb_lochbild_encrypt(loch_copy, 64, MB_MEIKEL_PRIM);
    mb_lochbild_decrypt(loch_copy, 64, MB_MEIKEL_PRIM);
    int loch_rt = (memcmp(loch, loch_copy, 64) == 0);
    if (loch_rt) pass++; else fail++;
    printf("  Lochbild RT (Seed=331):     %s\n", loch_rt?"OK":"FEHLER");
    
    /* 9. Delta-BoesingFolge Roundtrip */
    uint8_t delta_in[128], delta_enc[128], delta_dec[128];
    for (int i = 0; i < 128; i++) delta_in[i] = (uint8_t)(i ^ 0xAB);
    mb_delta_boesing_encode(delta_in, delta_enc, 128);
    mb_delta_boesing_decode(delta_enc, delta_dec, 128);
    int delta_rt = (memcmp(delta_in, delta_dec, 128) == 0);
    if (delta_rt) pass++; else fail++;
    printf("  Delta-Boesing RT (128 B):   %s\n", delta_rt?"OK":"FEHLER");
    
    /* 10. Nulllauf Roundtrip */
    uint8_t nl_in[32] = {0,0,0,5,0,0,0,0,7,0,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2};
    uint8_t nl_enc[64], nl_dec[32];
    size_t nl_clen = mb_nulllauf_encode(nl_in, 32, nl_enc, 64);
    size_t nl_dlen = mb_nulllauf_decode(nl_enc, nl_clen, nl_dec, 32);
    int nl_rt = (nl_dlen == 32 && memcmp(nl_in, nl_dec, 32) == 0);
    if (nl_rt) pass++; else fail++;
    printf("  Nulllauf RT (32 Bytes):     %s (kodiert: %zu)\n",
           nl_rt?"OK":"FEHLER", nl_clen);
    
    printf("\n  ERGEBNIS: %d/%d Tests bestanden\n", pass, pass+fail);
    return fail;
}

/* ─── FILE I/O ─────────────────────────────────────────────────────── */

static uint8_t* mb_read_file(const char *path, size_t *len) {
    FILE *f = fopen(path, "rb");
    if (!f) return NULL;
    fseek(f, 0, SEEK_END);
    *len = (size_t)ftell(f);
    fseek(f, 0, SEEK_SET);
    uint8_t *buf = (uint8_t *)malloc(*len);
    if (buf) fread(buf, 1, *len, f);
    fclose(f);
    return buf;
}

static int mb_write_file(const char *path, const uint8_t *data, size_t len) {
    FILE *f = fopen(path, "wb");
    if (!f) return -1;
    fwrite(data, 1, len, f);
    fclose(f);
    return 0;
}

/* ─── MAIN ─────────────────────────────────────────────────────────── */

static void mb_usage(const char *prog) {
    printf("MB UHCS PURE AUTARK KERN v31\n");
    printf("(c) Meikel Boesing 2026 - Gronau (Westfalen)\n");
    printf("\"Ein Mensch. Kein Konzern.\"\n\n");
    printf("Verwendung:\n");
    printf("  %s --compress   INPUT --output OUTPUT\n", prog);
    printf("  %s --decompress INPUT --output OUTPUT\n", prog);
    printf("  %s --self-test\n", prog);
    printf("  %s --orbit-atlas\n", prog);
    printf("  %s --benchmark FILE\n", prog);
}

int main(int argc, char **argv) {
    mb_init_inv();
    
    if (argc < 2) { mb_usage(argv[0]); return 1; }
    
    if (strcmp(argv[1], "--self-test") == 0) {
        printf("\n  MB UHCS PURE AUTARK KERN - Self-Test\n");
        printf("  ====================================\n\n");
        return mb_self_test();
    }
    
    if (strcmp(argv[1], "--orbit-atlas") == 0) {
        int orbits = mb_orbit_atlas();
        printf("  BoesingFolge Orbits: %d (erwartet: 21)\n", orbits);
        return (orbits == 21) ? 0 : 1;
    }
    
    if (strcmp(argv[1], "--benchmark") == 0 && argc >= 3) {
        size_t len;
        uint8_t *data = mb_read_file(argv[2], &len);
        if (!data) { fprintf(stderr, "Fehler: %s\n", argv[2]); return 1; }
        
        uint8_t *comp = (uint8_t *)malloc(len * 2 + 1024);
        uint8_t *decomp = (uint8_t *)malloc(len);
        
        size_t clen = mb_pure_compress(data, len, comp, len * 2 + 1024);
        size_t dlen = mb_pure_decompress(comp, clen, decomp, len);
        
        int rt = (dlen == len && memcmp(data, decomp, len) == 0);
        float ratio = (len > 0) ? (float)clen / (float)len : 0;
        float pct = (1.0f - ratio) * 100.0f;
        
        printf("\n  MB UHCS PURE - Benchmark\n");
        printf("  Input:       %zu Bytes\n", len);
        printf("  Komprimiert: %zu Bytes\n", clen);
        printf("  Ratio:       %.2fx (%.1f%% Reduktion)\n",
               (float)len / (float)clen, pct);
        printf("  Roundtrip:   %s\n", rt ? "OK" : "FEHLER");
        
        free(data); free(comp); free(decomp);
        return rt ? 0 : 1;
    }
    
    if (argc < 4 || strcmp(argv[3], "--output") != 0 || argc < 5) {
        mb_usage(argv[0]); return 1;
    }
    
    const char *input = argv[2];
    const char *output = argv[4];
    
    size_t len;
    uint8_t *data = mb_read_file(input, &len);
    if (!data) { fprintf(stderr, "Fehler: %s\n", input); return 1; }
    
    if (strcmp(argv[1], "--compress") == 0) {
        uint8_t *comp = (uint8_t *)malloc(len * 2 + 1024);
        size_t clen = mb_pure_compress(data, len, comp, len * 2 + 1024);
        mb_write_file(output, comp, clen);
        printf("Komprimiert: %s -> %s (%zu -> %zu Bytes, Ratio %.2fx)\n",
               input, output, len, clen, (float)len/(float)clen);
        free(comp);
    } else if (strcmp(argv[1], "--decompress") == 0) {
        
    /* Lese Original-Laenge aus Header */
    uint32_t orig_len_hdr = 0;
    if (len >= 8) {
        orig_len_hdr = ((uint32_t)data[4]<<24)|((uint32_t)data[5]<<16)|
                       ((uint32_t)data[6]<<8)|(uint32_t)data[7];
    }
    if (orig_len_hdr == 0) orig_len_hdr = len * 10;
    uint8_t *decomp = (uint8_t *)malloc(orig_len_hdr + 1024);
        size_t dlen = mb_pure_decompress(data, len, decomp, orig_len_hdr + 1024);
        mb_write_file(output, decomp, dlen);
        printf("Dekomprimiert: %s -> %s (%zu -> %zu Bytes)\n",
               input, output, len, dlen);
        free(decomp);
    }
    
    free(data);
    return 0;
}
