"""
thevenin_ecm.py  —  AUTOTWIN | Thevenin 1RC Equivalent Circuit Model
======================================================================
Backend physics engine for NASA battery discharge data.

Model Topology (1RC Thevenin):
 ┌──── R0 ────┬──── R1 ────┐
 │            │            │
OCV(SOC)     C1          V_terminal
 │            │            │
 └────────────┴────────────┘

Equations
---------
  V_t[k]    = OCV(SOC[k]) + I[k]*R0 + V_RC[k]
  V_RC[k+1] = V_RC[k]*exp(-dt/tau) + I[k]*R1*(1 - exp(-dt/tau))
  SOC[k]    = SOC[0] - integral(|I|dt) / Q_nominal

Parameter Identification: Two-stage — global (Differential Evolution)
followed by local (L-BFGS-B) optimisation.

Usage
-----
    from thevenin_ecm import TheveninECM
    ecm = TheveninECM()
    results = ecm.run(df, Q_nominal_Ah=2.0)
"""

import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution, minimize
from scipy.integrate import cumulative_trapezoid


# ─────────────────────────────────────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

NASA_Q_NOMINAL = 2.0   # Rated capacity for fresh NASA 18650 cells (Ah)

# OCV-SOC look-up table (18650 NMC, calibrated to NASA B00xx family)
_SOC_LUT = np.linspace(0.0, 1.0, 21)
_OCV_LUT = np.array([
    2.70, 2.90, 3.10, 3.22, 3.32, 3.40, 3.46, 3.51, 3.56, 3.60, 3.65,
    3.69, 3.73, 3.77, 3.82, 3.87, 3.93, 3.99, 4.05, 4.13, 4.20
])
_OCV_POLY_DEGREE = 8


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN CLASS
# ─────────────────────────────────────────────────────────────────────────────

class TheveninECM:
    """
    1RC Thevenin Equivalent Circuit Model for Li-ion batteries.

    Self-calibrates the OCV-SOC polynomial to each battery file and uses
    a two-stage global + local optimiser to identify R0, R1, C1.
    """

    _BOUNDS = [
        (0.001, 0.50),      # R0 (Ohm)
        (0.001, 0.50),      # R1 (Ohm)
        (50.0,  20000.0),   # C1 (F)
    ]

    def __init__(self):
        self.R0  = None
        self.R1  = None
        self.C1  = None
        self.tau = None
        self._ocv_poly = np.polyfit(_SOC_LUT, _OCV_LUT, _OCV_POLY_DEGREE)
        self._fitted = False

    # ── Public API ────────────────────────────────────────────────────────────

    def run(self, df, Q_nominal_Ah=NASA_Q_NOMINAL, verbose=False):
        """
        Full pipeline: preprocess -> SOC -> calibrate OCV ->
        identify params -> simulate -> metrics.

        Parameters
        ----------
        df : pd.DataFrame   NASA discharge CSV as a DataFrame
        Q_nominal_Ah : float   Cell rated capacity in Ah
        verbose : bool          Print optimiser progress

        Returns
        -------
        dict with keys:
            params, metrics, time, V_measured, V_simulated, soc, current,
            temperature (if column exists in df)
        """
        df = self._preprocess(df)
        if df is None or len(df) < 10:
            raise ValueError("Too few discharge samples after preprocessing.")

        soc = self._coulomb_count(df, Q_nominal_Ah)
        self._calibrate_ocv(df, soc)
        self._identify_parameters(df, soc, verbose)

        V_sim = self._simulate(
            df["Time"].values,
            df["Current_measured"].values,
            soc, self.R0, self.R1, self.C1
        )

        metrics = self._compute_metrics(df["Voltage_measured"].values, V_sim)

        result = {
            "params": {
                "R0_ohm": round(self.R0, 6),
                "R1_ohm": round(self.R1, 6),
                "C1_F":   round(self.C1, 4),
                "tau_s":  round(self.tau, 4),
            },
            "metrics":     metrics,
            "time":        df["Time"].values,
            "V_measured":  df["Voltage_measured"].values,
            "V_simulated": V_sim,
            "soc":         soc,
            "current":     df["Current_measured"].values,
            "Q_nominal_Ah": Q_nominal_Ah,
        }

        if "Temperature_measured" in df.columns:
            result["temperature"] = df["Temperature_measured"].values

        return result

    @staticmethod
    def load_csv(filepath):
        """Load a NASA battery discharge CSV from a file path."""
        df = pd.read_csv(filepath)
        df.columns = df.columns.str.strip()
        return df

    @staticmethod
    def load_uploaded(file_obj):
        """
        Load a CSV from a Streamlit UploadedFile or file-like object.
        """
        import io
        raw = file_obj.read() if hasattr(file_obj, "read") else file_obj
        df = pd.read_csv(io.BytesIO(raw))
        df.columns = df.columns.str.strip()
        return df

    def ocv(self, soc):
        """Return OCV (V) for given SOC array using the calibrated polynomial."""
        return np.polyval(self._ocv_poly, np.clip(soc, 0.0, 1.0))

    # ── Internals ─────────────────────────────────────────────────────────────

    def _preprocess(self, df):
        required = {"Voltage_measured", "Current_measured", "Time"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"CSV missing required columns: {missing}")

        df = df.copy()
        df = df.sort_values("Time").reset_index(drop=True)

        # Keep only the discharge phase (current clearly negative)
        df = df[df["Current_measured"] < -0.1].reset_index(drop=True)
        if len(df) < 10:
            return None

        df["dt"] = df["Time"].diff().fillna(0).clip(lower=0)
        return df

    def _coulomb_count(self, df, Q_nominal_Ah):
        """Coulomb counting: SOC in [0,1], starts at 1.0."""
        Q_As = Q_nominal_Ah * 3600.0
        charge_out = cumulative_trapezoid(
            np.abs(df["Current_measured"].values),
            df["Time"].values,
            initial=0
        )
        return np.clip(1.0 - charge_out / Q_As, 0.0, 1.0)

    def _calibrate_ocv(self, df, soc):
        """
        Adapt OCV-SOC polynomial to THIS battery using a coarse IR-corrected
        voltage estimate: OCV_approx = V_measured - I*R0_coarse
        """
        I = df["Current_measured"].values
        V = df["Voltage_measured"].values

        dV = np.abs(np.diff(V[:6]))
        dI = np.abs(np.diff(I[:6]))
        mask = dI > 0.05
        R0_coarse = float(np.clip(
            np.median(dV[mask] / dI[mask]) if mask.any() else 0.10,
            0.01, 0.30
        ))

        V_ocv_approx = V - I * R0_coarse
        with np.errstate(all="ignore"):
            self._ocv_poly = np.polyfit(soc, V_ocv_approx, _OCV_POLY_DEGREE)

    def _simulate(self, time, current, soc, R0, R1, C1):
        """
        Discrete-time 1RC Thevenin simulation using zero-order hold (ZOH).
        alpha = exp(-dt / tau)
        V_RC[k+1] = alpha*V_RC[k] + R1*(1-alpha)*I[k]
        V_t[k]    = OCV(SOC[k]) + R0*I[k] + V_RC[k]
        """
        n   = len(time)
        tau = R1 * C1
        V_RC = np.zeros(n)
        V_t  = np.zeros(n)

        V_t[0] = self.ocv(soc[0:1])[0] + current[0] * R0

        for k in range(1, n):
            dt    = max(float(time[k] - time[k-1]), 1e-6)
            alpha = np.exp(-dt / tau) if tau > 1e-9 else 0.0
            V_RC[k] = V_RC[k-1] * alpha + current[k-1] * R1 * (1.0 - alpha)
            V_t[k]  = self.ocv(soc[k:k+1])[0] + current[k] * R0 + V_RC[k]

        return V_t

    def _identify_parameters(self, df, soc, verbose):
        """
        Two-stage optimisation to minimise RMSE(V_measured, V_simulated).
        Stage 1 — Differential Evolution (global, seed=42 for reproducibility)
        Stage 2 — L-BFGS-B (local refinement from Stage 1 best)
        """
        time    = df["Time"].values
        current = df["Current_measured"].values
        V_meas  = df["Voltage_measured"].values

        def cost(x):
            V_sim = self._simulate(time, current, soc, *x)
            return np.sqrt(np.mean((V_sim - V_meas) ** 2))

        if verbose:
            print("[ECM] Stage 1 — Differential Evolution …")
        de = differential_evolution(
            cost, self._BOUNDS,
            seed=42, maxiter=500, tol=1e-7,
            popsize=15, mutation=(0.5, 1.5), recombination=0.75,
            workers=1, polish=False
        )
        if verbose:
            print(f"[ECM] Stage 1 RMSE = {de.fun*1000:.3f} mV")
            print("[ECM] Stage 2 — L-BFGS-B refinement …")

        local = minimize(
            cost, de.x, method="L-BFGS-B", bounds=self._BOUNDS,
            options={"maxiter": 3000, "ftol": 1e-13, "gtol": 1e-11}
        )
        if verbose:
            print(f"[ECM] Stage 2 RMSE = {local.fun*1000:.3f} mV")

        self.R0  = float(local.x[0])
        self.R1  = float(local.x[1])
        self.C1  = float(local.x[2])
        self.tau = self.R1 * self.C1
        self._fitted = True

    @staticmethod
    def _compute_metrics(V_meas, V_sim):
        err    = V_meas - V_sim
        rmse   = float(np.sqrt(np.mean(err ** 2)))
        mae    = float(np.mean(np.abs(err)))
        ss_res = float(np.sum(err ** 2))
        ss_tot = float(np.sum((V_meas - V_meas.mean()) ** 2))
        r2     = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
        maxe   = float(np.max(np.abs(err)))
        mape   = float(np.mean(np.abs(err / np.where(V_meas != 0, V_meas, 1e-9))) * 100)
        return {
            "RMSE_V":   round(rmse, 6),
            "MAE_V":    round(mae,  6),
            "R2":       round(r2,   6),
            "MaxErr_V": round(maxe, 6),
            "MAPE_pct": round(mape, 4),
        }


# ─────────────────────────────────────────────────────────────────────────────
#  CLI ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse, os, sys

    parser = argparse.ArgumentParser(description="AUTOTWIN — Thevenin 1RC ECM")
    parser.add_argument("--file",   required=True, help="Path to discharge CSV")
    parser.add_argument("--qnom",   type=float, default=NASA_Q_NOMINAL)
    parser.add_argument("--outdir", default=".", help="Output directory")
    args = parser.parse_args()

    if not os.path.isfile(args.file):
        print(f"[ERROR] File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.outdir, exist_ok=True)
    print(f"\n{'='*55}\n  AUTOTWIN — Thevenin 1RC ECM\n  File: {args.file}\n{'='*55}")

    ecm = TheveninECM()
    raw = TheveninECM.load_csv(args.file)
    res = ecm.run(raw, Q_nominal_Ah=args.qnom, verbose=True)

    print("\n── Parameters ──────────────────────────────────")
    for k, v in res["params"].items():
        print(f"  {k:10s} : {v}")
    print("\n── Metrics ─────────────────────────────────────")
    for k, v in res["metrics"].items():
        print(f"  {k:12s} : {v}")
    soc = res["soc"]
    print(f"\n── SOC ─────────────────────────────────────────")
    print(f"  Initial : {soc[0]*100:.1f}%")
    print(f"  Final   : {soc[-1]*100:.1f}%")
    print(f"  DoD     : {(soc[0]-soc[-1])*100:.1f}%")

    base    = os.path.splitext(os.path.basename(args.file))[0]
    out_csv = os.path.join(args.outdir, f"{base}_ecm_output.csv")
    pd.DataFrame({
        "Time":        res["time"],
        "V_measured":  res["V_measured"],
        "V_simulated": res["V_simulated"],
        "V_error_mV":  (res["V_measured"] - res["V_simulated"]) * 1000,
        "SOC":         soc,
        "Current":     res["current"],
    }).to_csv(out_csv, index=False)
    print(f"\n[OK] Results -> {out_csv}\n")