"""
fix_thermal_bounds.py
=====================
Fixes the optimizer bounds in lumped_thermal.py to physically realistic
ranges for NASA 18650 lithium-ion cells, then re-runs batch calibration.

Run from your project folder: python fix_thermal_bounds.py
"""
import shutil, os, re

# ── Fix lumped_thermal.py bounds ─────────────────────────────────────────────
LT = "lumped_thermal.py"
if not os.path.isfile(LT):
    print(f"[ERROR] {LT} not found"); exit(1)

shutil.copy2(LT, LT + ".bounds_bak")

with open(LT, "r", encoding="utf-8") as f:
    src = f.read()

ok = 0

# Fix 1: bounds in calibrate() — the main bounds tuple
# Look for patterns like bounds = [(low, high), (low, high)]
# C_th bound: was likely (1, 1e6) or similar → set to (10, 500)
# hA bound:   was likely (1e-6, 50) or similar → set to (0.005, 2.0)

replacements = [
    # Pattern: wide C_th upper bound
    ("(1,    1e6)",     "(10,   500)"),
    ("(1, 1e6)",        "(10, 500)"),
    ("(1e-3, 1e6)",     "(10, 500)"),
    ("(0.001, 1e6)",    "(10, 500)"),
    ("(1e-3,1e6)",      "(10,500)"),
    # Pattern: wide hA upper bound
    ("(1e-6, 50)",      "(0.005, 2.0)"),
    ("(1e-6,50)",       "(0.005,2.0)"),
    ("(0.0, 50)",       "(0.005, 2.0)"),
    ("(0, 50)",         "(0.005, 2.0)"),
    ("(1e-4, 50)",      "(0.005, 2.0)"),
    ("(1e-4,50)",       "(0.005,2.0)"),
    ("(0.001, 50)",     "(0.005, 2.0)"),
    ("(0.001,50)",      "(0.005,2.0)"),
]

for old, new in replacements:
    if old in src:
        src = src.replace(old, new)
        print(f"[OK] Replaced bound {old} → {new}")
        ok += 1

# If no exact match found, use regex to find and fix the bounds array
if ok == 0:
    # Find bounds = [...] lines near the calibrate function
    # Pattern: two tuples in a list that look like parameter bounds
    pattern = r'bounds\s*=\s*\[\s*\(([^)]+)\)\s*,\s*\(([^)]+)\)\s*\]'
    matches = list(re.finditer(pattern, src))
    for m in matches:
        b1, b2 = m.group(1), m.group(2)
        print(f"[?] Found bounds: [({b1}), ({b2})]")
        # Replace with tight physical bounds
        new_bounds = "bounds = [(10, 500), (0.005, 2.0)]"
        src = src[:m.start()] + new_bounds + src[m.end():]
        print(f"[OK] Replaced with physical bounds: {new_bounds}")
        ok += 1
        break

# Also fix differential_evolution popsize/maxiter if they're huge
# (speeds up and avoids runaway exploration)
src = re.sub(r'popsize\s*=\s*\d+', 'popsize=12', src)
src = re.sub(r'maxiter\s*=\s*\d+', 'maxiter=300', src)
src = re.sub(r'tol\s*=\s*[\d.e-]+', 'tol=1e-4', src)

with open(LT, "w", encoding="utf-8") as f:
    f.write(src)

if ok == 0:
    print(f"\n[!] Could not auto-fix bounds. Open lumped_thermal.py and manually find")
    print(f"    the 'bounds' variable near the calibrate() function.")
    print(f"    Change C_th bound upper limit to 500")
    print(f"    Change hA bound upper limit to 2.0")
    print(f"    Then re-run:  python batch_thermal_run.py --calib Battery47/charge --valid Battery47/discharge")
else:
    print(f"\n[OK] lumped_thermal.py bounds fixed ({ok} replacements)")
    print(f"\nNow re-run the batch:")
    print(f"  python batch_thermal_run.py --calib Battery47/charge --valid Battery47/discharge")
    print(f"\nExpected results after fix:")
    print(f"  C_th  : 40 – 200 J/K  (physically realistic for 18650)")
    print(f"  hA    : 0.01 – 0.3 W/K")
    print(f"  Calib RMSE : < 0.5 C")
    print(f"  Valid RMSE : < 1.0 C  (discharge validation)")
    print(f"  Valid R2   : > 0.5")