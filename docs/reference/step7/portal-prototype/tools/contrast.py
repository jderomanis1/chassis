#!/usr/bin/env python3
"""Compute WCAG 2.x contrast for both Chassis themes, assert AA, and write themes into ../tokens.json.
Usage: python3 tools/contrast.py [--write]"""
import json, sys, os

THEMES = {
  "dark": {
    "bg-0": "#05080E", "bg-1": "#0A111B", "panel": "#0E1724", "raise": "#132033", "drawer": "#0C1522",
    "glass": ("#0E1724", 0.86), "ask": ("#0A111B", 0.92),
    "text": "#E7EEF6", "text-2": "#A3B4C7", "text-3": "#7D92A9",
    "cyan": "#43E3FF", "amber": "#FFB547", "red": "#FF6B70", "green": "#4BE3A0", "slate": "#93A4BC",
    "on-accent": "#05080E", "tint": 0.14, "stripe": 0.06,
  },
  "light": {
    "bg-0": "#EAEFF5", "bg-1": "#F3F6F9", "panel": "#FBFCFD", "raise": "#E2E8F0", "drawer": "#F6F8FB",
    "glass": ("#FDFEFF", 0.84), "ask": ("#FBFCFE", 0.94),
    "text": "#0A1A2F", "text-2": "#33455D", "text-3": "#4F6077",
    "cyan": "#086C93", "amber": "#8A5200", "red": "#BB2532", "green": "#0A7044", "slate": "#55667F",
    "on-accent": "#FFFFFF", "tint": 0.11, "stripe": 0.08,
  },
}

def hx(h): h = h.lstrip('#'); return [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
def to_hex(c): return '#' + ''.join('%02X' % round(x * 255) for x in c)
def mix(fg, bg, a): f, b = hx(fg), hx(bg); return to_hex([f[i]*a + b[i]*(1-a) for i in range(3)])
def lum(h):
    c = [x/12.92 if x <= 0.03928 else ((x+0.055)/1.055)**2.4 for x in hx(h)]
    return 0.2126*c[0] + 0.7152*c[1] + 0.0722*c[2]
def cr(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True); return round((la+0.05)/(lb+0.05), 2)

STATUS = ["cyan", "amber", "red", "green", "slate"]
def pairs(t):
    glass = mix(t["glass"][0], t["bg-0"], t["glass"][1])   # real card background (glass over page)
    ask = mix(t["ask"][0], t["bg-0"], t["ask"][1])
    bgs = {"bg-0": t["bg-0"], "panel": glass, "raise": t["raise"], "drawer": t["drawer"]}
    out = []
    for fg in ["text", "text-2", "text-3"] + STATUS:
        for bn, bv in bgs.items():
            out.append((f"{fg} on {bn}", t[fg], bv, 4.5, "text"))
    out.append(("text-3 (placeholder) on ask bar", t["text-3"], ask, 4.5, "text"))
    for s in STATUS:
        out.append((f"pill {s} text on own tint", t[s], mix(t[s], glass, t["tint"]), 4.5, "text"))
        out.append((f"bar {s} vs track (raise)", t[s], t["raise"], 3.0, "ui"))
        out.append((f"bar {s} vs card", t[s], glass, 3.0, "ui"))
    for s in STATUS:
        out.append((f"pill {s} text on own tint over drawer/hover card", t[s], mix(t[s], t["drawer"], t["tint"]), 4.5, "text"))
    out.append(("sample/prototype tag amber on 8% amber tint", t["amber"], mix(t["amber"], glass, 0.08), 4.5, "text"))
    out.append(("depends-on chip cyan on 8% cyan tint", t["cyan"], mix(t["cyan"], glass, 0.08), 4.5, "text"))
    out.append(("depends-on chip red on 8% red tint", t["red"], mix(t["red"], glass, 0.08), 4.5, "text"))
    out.append(("text on map node (panel)", t["text"], t["panel"], 4.5, "text"))
    out.append(("on-accent text on cyan button", t["on-accent"], t["cyan"], 4.5, "text"))
    out.append(("focus ring cyan vs page", t["cyan"], t["bg-0"], 3.0, "ui"))
    out.append(("focus ring cyan vs card", t["cyan"], glass, 3.0, "ui"))
    out.append(("restricted lock/text amber on stripe", t["amber"], mix(t["amber"], glass, t["stripe"]), 4.5, "text"))
    out.append(("restricted text on stripe", t["text"], mix(t["amber"], glass, t["stripe"]), 4.5, "text"))
    out.append(("blocked edge red vs page", t["red"], t["bg-0"], 3.0, "ui"))
    out.append(("edge cyan vs page", t["cyan"], t["bg-0"], 3.0, "ui"))
    return glass, ask, out

def main():
    ok = True; result = {}
    for name, t in THEMES.items():
        glass, ask, ps = pairs(t)
        rows = []
        for label, fg, bg, need, kind in ps:
            r = cr(fg, bg); passed = r >= need; ok &= passed
            rows.append({"pair": label, "fg": fg, "bg": bg, "contrastRatio": r, "min": need, "pass": passed})
        low = min(rows, key=lambda x: x["contrastRatio"] / x["min"])
        lowest = min(rows, key=lambda x: x["contrastRatio"])
        print(f"[{name}] pairs={len(rows)} fails={sum(not r['pass'] for r in rows)} lowest={lowest['contrastRatio']} ({lowest['pair']}) tightest-vs-min={low['contrastRatio']}/{low['min']} ({low['pair']})")
        for r in rows:
            if not r["pass"]: print("   FAIL", r)
        colors = {k: v for k, v in t.items() if isinstance(v, str)}
        colors["glass-effective"] = glass; colors["ask-effective"] = ask
        result[name] = {"color": colors, "glass": {"base": t["glass"][0], "alpha": t["glass"][1]},
                        "pillTintAlpha": t["tint"], "contrast": rows,
                        "lowest": {"pair": lowest["pair"], "contrastRatio": lowest["contrastRatio"]}}
    if "--write" in sys.argv:
        p = os.path.join(os.path.dirname(__file__), "..", "tokens.json")
        tok = json.load(open(p)); tok.pop("color", None); tok.pop("status-pill-contrast", None); tok.pop("button", None)
        tok["themes"] = result
        tok["$description"] = "Chassis portal design tokens. themes.dark and themes.light map onto the same CSS custom property names in index.html. Contrast computed by tools/contrast.py (WCAG 2.x)."
        json.dump(tok, open(p, "w"), indent=2); print("wrote tokens.json")
    print("ALL AA PASS" if ok else "AA FAILURES"); sys.exit(0 if ok else 1)
main()
