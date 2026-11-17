# Step 7 source pack — MANIFEST

Built: 2026-11-17 10:13 AM AZ (America/Phoenix)
For: Codex resume of Chassis Step 7, against private repo `jderomanis1/chassis` main `42f0fa0`.
Purpose: the files Codex reported missing from the repository, attachments, and source search.

## Scan

Every text file in this zip was scanned before packaging for secrets (tokens, passphrases, keys, test-server URLs, credentials) and for real Andy venture or deal names. Screenshots were checked: the home screen and prototype HTML use only fictional sample data (Ridgeview HOA, Acme D2C, and labeled Sample placeholders).

- No secrets found. No owner passphrase is included. No test-server URLs or credentials are included.
- No real Andy venture or deal names found in ANDY-CHECK-02.md or in the rest of the pack.
- No redactions were required. ANDY-CHECK-02.md is included unredacted. It is Andy's 11/16 product-direction note (canvas-first, Miro optional, gateway skipped for the MVP) plus a public claude.ai artifact URL; it does not name real ventures or deals.

## Layout (names Codex expects)

```
SECOPS-STEP6.md
ANDY-CHECK-02.md
CODEX_STEP6_REPORT.md
PORTAL-ADR.md
QE-STEP6.md
MANIFEST.md
portal-prototype/
  index.html
  README.md
  tokens.json
  screens/          (16 PNGs + wow-demo.gif + wow-demo.mp4)
  tools/contrast.py
  tools/capture/    (screenshot / perf / demo helper scripts)
```

`docs/STEP7-CANVAS-SCOPE.md` at `42f0fa0` SOURCE NOTES list: ANDY-CHECK-02.md, PORTAL-ADR.md, portal-prototype/README.md, tokens.json, screens/, CODEX_STEP6_REPORT.md. The same scope also requires SECOPS-STEP6.md section 4 for C1, and names QE-STEP6.md for Playwright acceptance criteria. PORTAL-ADR.md here is the repo file at `42f0fa0` (`docs/PORTAL-ADR.md`, "local command canvas"), not the older pre-pivot local copy.

## Files

| Path | Bytes | sha256 (12) |
|---|---:|---|
| `ANDY-CHECK-02.md` | 3202 | `1158c0815608` |
| `CODEX_STEP6_REPORT.md` | 5667 | `6519291f56ed` |
| `PORTAL-ADR.md` | 7059 | `13ba8ee0b8cc` |
| `QE-STEP6.md` | 12806 | `0d88e35bfae1` |
| `SECOPS-STEP6.md` | 13474 | `b9664e4d3c58` |
| `portal-prototype/README.md` | 5277 | `8dc56b3783f1` |
| `portal-prototype/index.html` | 69365 | `a7dce1548afe` |
| `portal-prototype/screens/01-home.png` | 365058 | `b13a11b2eaa8` |
| `portal-prototype/screens/02-venture.png` | 334901 | `5546e9f7d628` |
| `portal-prototype/screens/02b-venture-acme.png` | 279476 | `785ca74c1ff1` |
| `portal-prototype/screens/03-initiative.png` | 288790 | `727fa1c85bb7` |
| `portal-prototype/screens/03b-initiative-acme-masked.png` | 300062 | `f6d89f3fbbf8` |
| `portal-prototype/screens/04-map.png` | 317727 | `3c251d235744` |
| `portal-prototype/screens/05-ask.png` | 289337 | `e6fb55b100df` |
| `portal-prototype/screens/06-restricted-detail.png` | 210850 | `6be08178f4d3` |
| `portal-prototype/screens/07-light-home.png` | 435557 | `01c71311bfc5` |
| `portal-prototype/screens/08-light-initiative.png` | 322043 | `acf04a9b0fe0` |
| `portal-prototype/screens/09-light-map.png` | 411833 | `4445ab687e4c` |
| `portal-prototype/screens/10-dark-map-hover.png` | 324681 | `ebde2942b2bb` |
| `portal-prototype/screens/11-light-hovercard.png` | 355693 | `724fb85aed4b` |
| `portal-prototype/screens/12-dark-tile-hover.png` | 434065 | `4bf91cfa6677` |
| `portal-prototype/screens/13-light-restricted-hovercard.png` | 354226 | `b240bf66f665` |
| `portal-prototype/screens/14-light-ask.png` | 415101 | `caa1cc77a2bc` |
| `portal-prototype/screens/wow-demo.gif` | 3898273 | `54bc11b7a92b` |
| `portal-prototype/screens/wow-demo.mp4` | 789779 | `a20f10229881` |
| `portal-prototype/tokens.json` | 28041 | `d4fecab7b328` |
| `portal-prototype/tools/capture/demo.mjs` | 2365 | `583d8d6ee565` |
| `portal-prototype/tools/capture/func.mjs` | 3316 | `a34f1ec7c419` |
| `portal-prototype/tools/capture/perf.mjs` | 2548 | `65d0a1c2779e` |
| `portal-prototype/tools/capture/rest.mjs` | 1655 | `fa4f3fd987ab` |
| `portal-prototype/tools/capture/shots.mjs` | 2711 | `49a0d6e64a77` |
| `portal-prototype/tools/contrast.py` | 5315 | `2a438ebe934d` |

## Fonts, theme, contrast

- Theme: present. Light and dark tokens live in `portal-prototype/tokens.json` (`themes.dark`, `themes.light`) and in the CSS variables in `portal-prototype/index.html`. The prototype uses localStorage key `chassis-theme` and a no-flash head script, which Step 7 must keep.
- Contrast check: present. `portal-prototype/tools/contrast.py` recomputes text/status contrast and can refresh `tokens.json` with `--write`.
- Font files: **not in the approved package.** `portal-prototype/index.html` loads Chakra Petch (500/600/700), IBM Plex Sans (400/500/600), and JetBrains Mono (400/500) from the Google Fonts CDN, with system-font fallback offline (see README). Step 7 requires self-hosted fonts and no Google CDN. Codex should self-host those three families. Fonts from unrelated projects on the box were not included.

## Notes for Codex

- Visual source only: match colors, typography, glow, tile tilt, hover cards, and status pulse. Do not treat the vanilla five-screen prototype as the canvas codebase.
- Continue C1 on branch `step7-c1-write`, then C2 and F1–F6 against that branch. Do not merge writes to main until independent SecOps review of C1/C2.
- Sample / fictional data only. No real Andy data.
- Working demo target (CoS update): Monday, 2026-11-23, morning, America/Phoenix. This replaces Friday, Nov 20.
