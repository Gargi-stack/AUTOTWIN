"""
patch_thermal_fonts.py
======================
Increases font sizes in the thermal simulation results
so values, labels and units are clearly visible.
Run from your project folder: python patch_thermal_fonts.py
"""
import shutil

APP = "app.py"
shutil.copy2(APP, APP + ".fonts_bak")

with open(APP, "r", encoding="utf-8") as f:
    src = f.read()

ok = 0
changes = [

    # ── Parameter cards: full name label (top of card) ────────────────────────
    (
        'font-family:\'Share Tech Mono\',monospace;color:rgba(180,230,255,0.9);\n                                  font-size:0.65rem;margin-bottom:2px;">{label}',
        'font-family:\'Share Tech Mono\',monospace;color:rgba(180,230,255,0.9);\n                                  font-size:0.82rem;margin-bottom:4px;">{label}',
        "Param card: name label font"
    ),

    # ── Parameter cards: symbol label (C_th, hA, etc) ─────────────────────────
    (
        'font-family:\'Orbitron\',monospace;color:{color};font-size:0.58rem;\n                                  font-weight:700;letter-spacing:0.12em;margin-bottom:10px;">({sublabel})',
        'font-family:\'Orbitron\',monospace;color:{color};font-size:0.72rem;\n                                  font-weight:700;letter-spacing:0.12em;margin-bottom:10px;">({sublabel})',
        "Param card: symbol label font"
    ),

    # ── Parameter cards: big value number ─────────────────────────────────────
    (
        'font-family:\'Orbitron\',monospace;color:white;font-size:2.0rem;\n                                  font-weight:900;text-shadow:0 0 20px {color}88;line-height:1;">{val}',
        'font-family:\'Orbitron\',monospace;color:white;font-size:2.6rem;\n                                  font-weight:900;text-shadow:0 0 20px {color}88;line-height:1;">{val}',
        "Param card: big value font"
    ),

    # ── Parameter cards: unit ─────────────────────────────────────────────────
    (
        'font-family:\'Share Tech Mono\',monospace;color:rgba(180,230,255,0.7);\n                                  font-size:0.82rem;margin-top:4px;">{unit}',
        'font-family:\'Share Tech Mono\',monospace;color:rgba(180,230,255,0.7);\n                                  font-size:0.92rem;margin-top:4px;">{unit}',
        "Param card: unit font"
    ),

    # ── Parameter cards: description (bottom of card) ─────────────────────────
    (
        'font-family:\'Share Tech Mono\',monospace;color:rgba(180,230,255,0.45);\n                                  font-size:0.62rem;margin-top:8px;">{desc}',
        'font-family:\'Share Tech Mono\',monospace;color:rgba(180,230,255,0.6);\n                                  font-size:0.72rem;margin-top:8px;">{desc}',
        "Param card: description font"
    ),

    # ── Metric cards (calib + valid): full name label ─────────────────────────
    (
        'font-family:\'Share Tech Mono\',monospace;color:#5a7090;font-size:0.62rem;\n                                      margin-bottom:2px;">{lbl}',
        'font-family:\'Share Tech Mono\',monospace;color:#5a7090;font-size:0.75rem;\n                                      margin-bottom:4px;">{lbl}',
        "Metric card (calib): name label font"
    ),
    (
        'font-family:\'Share Tech Mono\',monospace;color:#5a7090;font-size:0.62rem;\n                                          margin-bottom:2px;">{lbl}',
        'font-family:\'Share Tech Mono\',monospace;color:#5a7090;font-size:0.75rem;\n                                          margin-bottom:4px;">{lbl}',
        "Metric card (valid): name label font"
    ),

    # ── Metric cards (calib + valid): symbol label ────────────────────────────
    (
        'font-family:\'Orbitron\',monospace;color:#aabbcc;font-size:0.56rem;\n                                      letter-spacing:0.12em;margin-bottom:6px;">({sublbl})',
        'font-family:\'Orbitron\',monospace;color:#aabbcc;font-size:0.68rem;\n                                      letter-spacing:0.12em;margin-bottom:6px;">({sublbl})',
        "Metric card (calib): symbol font"
    ),
    (
        'font-family:\'Orbitron\',monospace;color:#aabbcc;font-size:0.56rem;\n                                          letter-spacing:0.12em;margin-bottom:6px;">({sublbl})',
        'font-family:\'Orbitron\',monospace;color:#aabbcc;font-size:0.68rem;\n                                          letter-spacing:0.12em;margin-bottom:6px;">({sublbl})',
        "Metric card (valid): symbol font"
    ),

    # ── Metric cards (calib + valid): big value ───────────────────────────────
    (
        'font-family:\'Orbitron\',monospace;color:{clr};font-size:1.6rem;\n                                      font-weight:900;">{v}',
        'font-family:\'Orbitron\',monospace;color:{clr};font-size:2.0rem;\n                                      font-weight:900;">{v}',
        "Metric card (calib): value font"
    ),
    (
        'font-family:\'Orbitron\',monospace;color:{clr};font-size:1.6rem;\n                                          font-weight:900;">{v}',
        'font-family:\'Orbitron\',monospace;color:{clr};font-size:2.0rem;\n                                          font-weight:900;">{v}',
        "Metric card (valid): value font"
    ),

    # ── Metric cards (calib + valid): unit hint ───────────────────────────────
    (
        'font-family:\'Share Tech Mono\',monospace;color:#8a9ab0;\n                                      font-size:0.72rem;margin-top:4px;">{u}',
        'font-family:\'Share Tech Mono\',monospace;color:#8a9ab0;\n                                      font-size:0.80rem;margin-top:4px;">{u}',
        "Metric card (calib): unit font"
    ),
    (
        'font-family:\'Share Tech Mono\',monospace;color:#8a9ab0;\n                                          font-size:0.72rem;margin-top:4px;">{u}',
        'font-family:\'Share Tech Mono\',monospace;color:#8a9ab0;\n                                          font-size:0.80rem;margin-top:4px;">{u}',
        "Metric card (valid): unit font"
    ),

    # ── Summary cards: full name label ────────────────────────────────────────
    (
        'font-family:\'Share Tech Mono\',monospace;color:#5a7090;font-size:0.68rem;\n                                      margin-bottom:2px;">{lbl}',
        'font-family:\'Share Tech Mono\',monospace;color:#5a7090;font-size:0.80rem;\n                                      margin-bottom:4px;">{lbl}',
        "Summary card: name label font"
    ),

    # ── Summary cards: hint text ──────────────────────────────────────────────
    (
        'font-family:\'Share Tech Mono\',monospace;color:#aabbcc;font-size:0.60rem;\n                                      margin-bottom:8px;">{sublbl}',
        'font-family:\'Share Tech Mono\',monospace;color:#aabbcc;font-size:0.70rem;\n                                      margin-bottom:8px;">{sublbl}',
        "Summary card: hint font"
    ),

    # ── Summary cards: big value ──────────────────────────────────────────────
    (
        'font-family:\'Orbitron\',monospace;color:{clr};font-size:1.8rem;\n                                      font-weight:900;">{v}',
        'font-family:\'Orbitron\',monospace;color:{clr};font-size:2.2rem;\n                                      font-weight:900;">{v}',
        "Summary card: value font"
    ),

    # ── Summary cards: unit ───────────────────────────────────────────────────
    (
        'font-family:\'Share Tech Mono\',monospace;color:#8a9ab0;\n                                      font-size:0.78rem;margin-top:4px;">{u}',
        'font-family:\'Share Tech Mono\',monospace;color:#8a9ab0;\n                                      font-size:0.86rem;margin-top:4px;">{u}',
        "Summary card: unit font"
    ),
]

for old, new, label in changes:
    if old in src:
        src = src.replace(old, new, 1)
        print(f"[OK] {label}")
        ok += 1
    else:
        print(f"[skip] {label} — not found (may already be updated)")

with open(APP, "w", encoding="utf-8") as f:
    f.write(src)

print(f"\n[DONE] {ok}/{len(changes)} font changes applied")
print("Run: streamlit run app.py")