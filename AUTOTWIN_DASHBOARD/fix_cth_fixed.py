"""
fix_cth_fixed.py
================
Modifies lumped_thermal.py to fix C_th to the known physical value
for NASA 18650 cells (62 J/K) and only optimize hA.

This solves the identifiability problem where charge data has too little
thermal excitation to reliably estimate C_th.

Run from your project folder: python fix_cth_fixed.py
"""
import shutil

LT = "lumped_thermal.py"
shutil.copy2(LT, LT + ".cth_bak")

with open(LT, "r", encoding="utf-8") as f:
    src = f.read()

ok = 0

# ── Fix 1: Update constants ───────────────────────────────────────────────────
OLD1 = """_C_TH_BOUNDS  = (10.0,   500.0)    # J/K  — thermal capacitance
_HA_BOUNDS    = (0.001,  2.0)      # W/K  — effective heat-transfer coeff
_DEFAULT_R    = 0.08                  # Ω    — fallback internal resistance"""

NEW1 = """_C_TH_BOUNDS  = (10.0,   500.0)    # J/K  — thermal capacitance (kept for reference)
_HA_BOUNDS    = (0.001,  2.0)      # W/K  — effective heat-transfer coeff
_DEFAULT_R    = 0.08                  # Ω    — fallback internal resistance

# NASA 18650 cell physical constants
# Mass ~46g, specific heat ~1350 J/kg·K → C_th = 0.046 × 1350 = 62.1 J/K
# This is a physical constant — does NOT change with aging
_C_TH_FIXED   = 62.1               # J/K  — fixed thermal capacitance for NASA 18650"""

if OLD1 in src:
    src = src.replace(OLD1, NEW1, 1)
    print("[OK] Fix 1: Added _C_TH_FIXED = 62.1 J/K constant")
    ok += 1
else:
    print("[!] Fix 1: anchor not found")

# ── Fix 2: Update calibrate() signature and body ─────────────────────────────
OLD2 = """    def calibrate(self, df: pd.DataFrame, R_ohm: float = _DEFAULT_R,
                  verbose: bool = False) -> dict:
        \"\"\"
        Estimate C_th and hA by minimising RMSE on df.

        Parameters
        ----------
        df      : pd.DataFrame  — must contain Time, Current_measured,
                                  Temperature_measured
        R_ohm   : float         — internal resistance from ECM (Ω)
        verbose : bool

        Returns
        -------
        dict with C_th, hA, T_amb, metrics, time, T_measured, T_predicted
        \"\"\"
        df = self._preprocess(df)
        T_amb = self._estimate_tamb(df)

        time    = df["Time"].values.astype(float)
        current = df["Current_measured"].values.astype(float)
        T_meas  = df["Temperature_measured"].values.astype(float)

        bounds = [_C_TH_BOUNDS, _HA_BOUNDS]

        def cost(x):
            T_pred = self._simulate_core(time, current, T_meas[0], x[0], x[1],
                                         R_ohm, T_amb)
            return _rmse(T_meas, T_pred)

        if verbose:
            print("[Thermal] Stage 1 — Differential Evolution ...")

        de = differential_evolution(
            cost, bounds,
            seed=42, maxiter=300, tol=1e-4,
            popsize=12, mutation=(0.5, 1.5), recombination=0.8,
            workers=1, polish=False,
        )

        if verbose:
            print(f"[Thermal] Stage 1 RMSE = {de.fun:.5f} °C")
            print("[Thermal] Stage 2 — L-BFGS-B refinement ...")

        local = minimize(
            cost, de.x, method="L-BFGS-B", bounds=bounds,
            options={"maxiter": 5000, "ftol": 1e-15, "gtol": 1e-12},
        )

        if verbose:
            print(f"[Thermal] Stage 2 RMSE = {local.fun:.5f} °C")

        self.C_th = float(local.x[0])
        self.hA   = float(local.x[1])
        self._fitted = True

        T_pred = self._simulate_core(time, current, T_meas[0],
                                     self.C_th, self.hA, R_ohm, T_amb)

        return {
            "C_th":       round(self.C_th, 4),
            "hA":         round(self.hA,   6),
            "T_amb":      round(T_amb,     3),
            "R_ohm":      round(R_ohm,     6),
            "metrics":    _compute_metrics(T_meas, T_pred),
            "time":       time,
            "T_measured": T_meas,
            "T_predicted":T_pred,
        }"""

NEW2 = """    def calibrate(self, df: pd.DataFrame, R_ohm: float = _DEFAULT_R,
                  verbose: bool = False,
                  C_th_fixed: float = _C_TH_FIXED) -> dict:
        \"\"\"
        Estimate hA by minimising RMSE on df, with C_th fixed to physical value.

        C_th is fixed to the known NASA 18650 value (62.1 J/K) because charge
        data has insufficient thermal excitation to reliably identify it.
        Only hA (heat transfer coefficient) is optimised — it changes with
        battery aging and mounting conditions.

        Parameters
        ----------
        df         : pd.DataFrame — must contain Time, Current_measured,
                                    Temperature_measured
        R_ohm      : float        — internal resistance from ECM (Ω)
        verbose    : bool
        C_th_fixed : float        — fixed thermal capacitance (J/K)
                                    default = 62.1 J/K for NASA 18650

        Returns
        -------
        dict with C_th, hA, T_amb, metrics, time, T_measured, T_predicted
        \"\"\"
        df = self._preprocess(df)
        T_amb = self._estimate_tamb(df)

        time    = df["Time"].values.astype(float)
        current = df["Current_measured"].values.astype(float)
        T_meas  = df["Temperature_measured"].values.astype(float)

        # Only optimise hA — C_th is fixed to physical value
        bounds_ha = [_HA_BOUNDS]

        def cost(x):
            T_pred = self._simulate_core(time, current, T_meas[0],
                                         C_th_fixed, x[0], R_ohm, T_amb)
            return _rmse(T_meas, T_pred)

        if verbose:
            print(f"[Thermal] C_th fixed = {C_th_fixed:.1f} J/K (NASA 18650 physical value)")
            print("[Thermal] Stage 1 — Differential Evolution (optimising hA) ...")

        de = differential_evolution(
            cost, bounds_ha,
            seed=42, maxiter=500, tol=1e-6,
            popsize=15, mutation=(0.5, 1.5), recombination=0.8,
            workers=1, polish=False,
        )

        if verbose:
            print(f"[Thermal] Stage 1 RMSE = {de.fun:.5f} °C")
            print("[Thermal] Stage 2 — L-BFGS-B refinement ...")

        local = minimize(
            cost, de.x, method="L-BFGS-B", bounds=bounds_ha,
            options={"maxiter": 5000, "ftol": 1e-15, "gtol": 1e-12},
        )

        if verbose:
            print(f"[Thermal] Stage 2 RMSE = {local.fun:.5f} °C")

        self.C_th = float(C_th_fixed)
        self.hA   = float(local.x[0])
        self._fitted = True

        T_pred = self._simulate_core(time, current, T_meas[0],
                                     self.C_th, self.hA, R_ohm, T_amb)

        return {
            "C_th":       round(self.C_th, 4),
            "hA":         round(self.hA,   6),
            "T_amb":      round(T_amb,     3),
            "R_ohm":      round(R_ohm,     6),
            "metrics":    _compute_metrics(T_meas, T_pred),
            "time":       time,
            "T_measured": T_meas,
            "T_predicted":T_pred,
        }"""

if OLD2 in src:
    src = src.replace(OLD2, NEW2, 1)
    print("[OK] Fix 2: calibrate() now fixes C_th and only optimises hA")
    ok += 1
else:
    print("[!] Fix 2: anchor not found")

# ── Fix 3: Update run_batch_calibration to pass C_th_fixed ───────────────────
OLD3 = """        res = model.calibrate(df, R_ohm=R_ohm, verbose=verbose)"""
NEW3 = """        res = model.calibrate(df, R_ohm=R_ohm, verbose=verbose, C_th_fixed=_C_TH_FIXED)"""

if OLD3 in src:
    src = src.replace(OLD3, NEW3, 1)
    print("[OK] Fix 3: run_batch_calibration updated")
    ok += 1
else:
    print("[!] Fix 3: anchor not found")

with open(LT, "w", encoding="utf-8") as f:
    f.write(src)

print(f"\n[{'DONE' if ok >= 2 else 'PARTIAL'}] {ok}/3 fixes applied to {LT}")
if ok >= 2:
    print("""
Now re-run the batch:
    python batch_thermal_run.py --calib "Battery47/charge" --valid "Battery47/discharge"

Expected results after fix:
    C_th       : 62.1 J/K  (fixed — physical constant)
    hA         : 0.01–0.3 W/K  (estimated — changes with aging)
    Calib RMSE : 0.4–0.7 C  (similar to before)
    Valid RMSE : < 1.0 C  (much better — discharge now works)
    Valid R2   : > 0.5  (positive, meaningful)
""")