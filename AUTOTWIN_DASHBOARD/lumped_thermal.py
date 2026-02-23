"""
lumped_thermal.py — AUTOTWIN | Lumped Thermal Model
=====================================================
Physics-based single-node lumped thermal model for Li-ion battery cells.

Model Equation (discrete-time, zero-order hold):
    T[k+1] = T[k] + (dt / C_th) * (I[k]^2 * R  -  hA * (T[k] - T_amb))

Where:
    T[k]   — cell temperature at step k  (°C)
    I[k]   — measured current at step k  (A, sign-agnostic via I²)
    R      — effective internal resistance (Ω), taken from ECM (R0)
    C_th   — lumped thermal capacitance   (J/K)  ← estimated
    hA     — heat-transfer coefficient × area (W/K) ← estimated
    T_amb  — ambient temperature (°C), inferred from data or user-supplied

Parameter Identification:
    Two-stage: Differential Evolution (global) → L-BFGS-B (local refinement)
    Objective: minimise RMSE(T_predicted, T_measured) on calibration data.

Usage
-----
from lumped_thermal import LumpedThermalModel

model = LumpedThermalModel()
calib = model.calibrate(df_charge, R_ohm=0.08)
valid = model.validate(df_valid, calib["C_th"], calib["hA"], R_ohm=0.08)
"""

import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution, minimize
from scipy.integrate import cumulative_trapezoid

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS / DEFAULT BOUNDS
# ─────────────────────────────────────────────────────────────────────────────
_C_TH_BOUNDS  = (10.0,   500.0)    # J/K  — thermal capacitance (kept for reference)
_HA_BOUNDS    = (0.001,  2.0)      # W/K  — effective heat-transfer coeff
_DEFAULT_R    = 0.08                  # Ω    — fallback internal resistance

# NASA 18650 cell physical constants
# Mass ~46g, specific heat ~1350 J/kg·K → C_th = 0.046 × 1350 = 62.1 J/K
# This is a physical constant — does NOT change with aging
_C_TH_FIXED   = 62.1               # J/K  — fixed thermal capacitance for NASA 18650

_REQUIRED_THERMAL_COLS = {"Time", "Current_measured", "Temperature_measured"}

# ─────────────────────────────────────────────────────────────────────────────
# MAIN CLASS
# ─────────────────────────────────────────────────────────────────────────────

class LumpedThermalModel:
    """
    Single-node lumped thermal model for Li-ion cells.

    Workflow
    --------
    1.  calibrate(df_charge, R)    → estimates C_th, hA from charge data
    2.  validate(df_val,  C_th, hA, R) → RMSE on a held-out file
    3.  simulate(df, C_th, hA, R)  → returns T_predicted array
    """

    def __init__(self):
        self.C_th   = None
        self.hA     = None
        self._fitted = False

    # ── Public API ─────────────────────────────────────────────────────────

    def calibrate(self, df: pd.DataFrame, R_ohm: float = _DEFAULT_R,
                  verbose: bool = False,
                  C_th_fixed: float = _C_TH_FIXED) -> dict:
        """
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
        """
        df = self._preprocess(df)
        T_amb = self._estimate_tamb(df)

        time    = df["Time"].values.astype(float)
        current = df["Current_measured"].values.astype(float)
        T_meas  = df["Temperature_measured"].values.astype(float)

        # Only optimise hA — C_th is fixed to physical value
        bounds_ha = [_C_TH_BOUNDS, _HA_BOUNDS]

        def cost(x):
            T_pred = self._simulate_core(time, current, T_meas[0],
                                         x[0], x[1], R_ohm, T_amb)
            return _rmse(T_meas, T_pred)

        if verbose:
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
        }

    def validate(self, df: pd.DataFrame,
                 C_th: float, hA: float,
                 R_ohm: float = _DEFAULT_R,
                 T_amb: float = None) -> dict:
        """
        Run the thermal model on a NEW file using already-calibrated params.
        No re-fitting; pure forward simulation.
        """
        df = self._preprocess(df)
        if T_amb is None:
            T_amb = self._estimate_tamb(df)

        time    = df["Time"].values.astype(float)
        current = df["Current_measured"].values.astype(float)
        T_meas  = df["Temperature_measured"].values.astype(float)

        T_pred = self._simulate_core(time, current, T_meas[0],
                                     C_th, hA, R_ohm, T_amb)

        return {
            "C_th":        round(C_th,  4),
            "hA":          round(hA,    6),
            "T_amb":       round(T_amb, 3),
            "R_ohm":       round(R_ohm, 6),
            "metrics":     _compute_metrics(T_meas, T_pred),
            "time":        time,
            "T_measured":  T_meas,
            "T_predicted": T_pred,
        }

    def simulate(self, df: pd.DataFrame,
                 C_th: float, hA: float,
                 R_ohm: float = _DEFAULT_R,
                 T_amb: float = None) -> np.ndarray:
        """Return T_predicted array for a dataframe (no metrics)."""
        df = self._preprocess(df)
        if T_amb is None:
            T_amb = self._estimate_tamb(df)
        time    = df["Time"].values.astype(float)
        current = df["Current_measured"].values.astype(float)
        T0      = df["Temperature_measured"].values[0] if \
                  "Temperature_measured" in df.columns else T_amb
        return self._simulate_core(time, current, float(T0),
                                   C_th, hA, R_ohm, T_amb)

    # ── Static helpers ──────────────────────────────────────────────────────

    @staticmethod
    def check_columns(df: pd.DataFrame) -> bool:
        """Return True if df has all required thermal columns."""
        return _REQUIRED_THERMAL_COLS.issubset(set(df.columns))

    @staticmethod
    def load_csv(filepath: str) -> pd.DataFrame:
        df = pd.read_csv(filepath)
        df.columns = df.columns.str.strip()
        return df

    @staticmethod
    def load_uploaded(file_obj) -> pd.DataFrame:
        import io
        raw = file_obj.read() if hasattr(file_obj, "read") else file_obj
        df = pd.read_csv(io.BytesIO(raw))
        df.columns = df.columns.str.strip()
        return df

    # ── Internals ───────────────────────────────────────────────────────────

    @staticmethod
    def _preprocess(df: pd.DataFrame) -> pd.DataFrame:
        missing = _REQUIRED_THERMAL_COLS - set(df.columns)
        if missing:
            raise ValueError(
                f"CSV missing required thermal columns: {missing}\n"
                f"Need: Time, Current_measured, Temperature_measured"
            )
        df = df.copy()
        df = df.sort_values("Time").reset_index(drop=True)
        # Drop rows with NaN in required columns
        df = df.dropna(subset=list(_REQUIRED_THERMAL_COLS)).reset_index(drop=True)
        if len(df) < 10:
            raise ValueError("Too few usable rows after preprocessing (< 10).")
        return df

    @staticmethod
    def _estimate_tamb(df: pd.DataFrame) -> float:
        """
        Estimate ambient temperature.
        Strategy: use the minimum temperature in the file (battery at rest
        before excitation) — robust for both charge and discharge profiles.
        """
        temps = df["Temperature_measured"].values.astype(float)
        # Use 5th-percentile to be robust against noise
        return float(np.percentile(temps, 5))

    @staticmethod
    def _simulate_core(time:    np.ndarray,
                       current: np.ndarray,
                       T0:      float,
                       C_th:    float,
                       hA:      float,
                       R:       float,
                       T_amb:   float) -> np.ndarray:
        """
        Discrete-time forward simulation of the lumped thermal model.

        T[k+1] = T[k] + (dt/C_th) * (I[k]^2 * R  -  hA*(T[k]-T_amb))

        Numerical guard: dt clipped to [1e-6, 600] s.
        """
        n = len(time)
        T = np.empty(n, dtype=np.float64)
        T[0] = T0

        for k in range(1, n):
            dt  = float(np.clip(time[k] - time[k - 1], 1e-6, 600.0))
            # Clip temperature to physically plausible range to prevent overflow
            T_prev = float(np.clip(T[k - 1], -50.0, 200.0))
            Q_gen  = float(current[k - 1]) ** 2 * R    # heat generated (W)
            Q_diss = hA * (T_prev - T_amb)              # heat dissipated (W)
            dT = (dt / max(C_th, 1e-6)) * (Q_gen - Q_diss)
            # Guard against runaway
            dT = float(np.clip(dT, -50.0, 50.0))
            T[k] = T_prev + dT

        return T


# ─────────────────────────────────────────────────────────────────────────────
# UTILITY FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def _rmse(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.sqrt(np.mean((a - b) ** 2)))


def _compute_metrics(T_meas: np.ndarray, T_pred: np.ndarray) -> dict:
    err  = T_meas - T_pred
    rmse = float(np.sqrt(np.mean(err ** 2)))
    mae  = float(np.mean(np.abs(err)))
    ss_res = float(np.sum(err ** 2))
    ss_tot = float(np.sum((T_meas - T_meas.mean()) ** 2))
    r2   = 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else float("nan")
    maxe = float(np.max(np.abs(err)))
    mape = float(np.mean(np.abs(err / np.where(
           np.abs(T_meas) > 0.1, T_meas, 0.1))) * 100)
    return {
        "RMSE_C":    round(rmse, 6),
        "MAE_C":     round(mae,  6),
        "R2":        round(r2,   6),
        "MaxErr_C":  round(maxe, 6),
        "MAPE_pct":  round(mape, 4),
    }


# ─────────────────────────────────────────────────────────────────────────────
# BATCH HELPER  (mirrors batch_run.py style)
# ─────────────────────────────────────────────────────────────────────────────

def run_batch_calibration(csv_paths: list[str],
                          R_ohm: float = _DEFAULT_R,
                          verbose: bool = False) -> tuple[float, float, list]:
    """
    Calibrate C_th and hA using MULTIPLE charge files.
    Returns the median-of-medians C_th and hA for robustness,
    plus a list of per-file result dicts.
    """
    model = LumpedThermalModel()
    results = []
    cth_list, ha_list = [], []

    for path in csv_paths:
        try:
            df  = LumpedThermalModel.load_csv(path)
            res = model.calibrate(df, R_ohm=R_ohm, verbose=verbose, C_th_fixed=_C_TH_FIXED)
            res["_filename"] = path
            results.append(res)
            cth_list.append(res["C_th"])
            ha_list.append(res["hA"])
        except Exception as exc:
            if verbose:
                print(f"[Thermal] Skipping {path}: {exc}")

    if not cth_list:
        raise RuntimeError("No valid charge files for calibration.")

    C_th_final = float(np.median(cth_list))
    hA_final   = float(np.median(ha_list))

    return C_th_final, hA_final, results


# ─────────────────────────────────────────────────────────────────────────────
# CLI ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse, os, sys

    parser = argparse.ArgumentParser(description="AUTOTWIN — Lumped Thermal Model")
    parser.add_argument("--calib",  required=True, nargs="+",
                        help="Calibration charge CSV file(s)")
    parser.add_argument("--valid",  nargs="+", default=[],
                        help="Validation CSV file(s)")
    parser.add_argument("--R",      type=float, default=_DEFAULT_R,
                        help=f"Internal resistance Ω (default {_DEFAULT_R})")
    args = parser.parse_args()

    model = LumpedThermalModel()

    print("\n" + "=" * 55)
    print(" AUTOTWIN — Lumped Thermal Model | Calibration")
    print("=" * 55)

    for fp in args.calib:
        if not os.path.isfile(fp):
            print(f"[ERROR] File not found: {fp}", file=sys.stderr)
            continue
        df  = LumpedThermalModel.load_csv(fp)
        res = model.calibrate(df, R_ohm=args.R, verbose=True)
        print(f"\n── {os.path.basename(fp)}")
        print(f"   C_th = {res['C_th']:.2f} J/K  |  hA = {res['hA']:.4f} W/K")
        for k, v in res["metrics"].items():
            print(f"   {k:12s}: {v}")

    if args.valid and model._fitted:
        print("\n" + "=" * 55)
        print(" Validation")
        print("=" * 55)
        for fp in args.valid:
            if not os.path.isfile(fp):
                continue
            df  = LumpedThermalModel.load_csv(fp)
            res = model.validate(df, model.C_th, model.hA, R_ohm=args.R)
            print(f"\n── {os.path.basename(fp)}")
            for k, v in res["metrics"].items():
                print(f"   {k:12s}: {v}")