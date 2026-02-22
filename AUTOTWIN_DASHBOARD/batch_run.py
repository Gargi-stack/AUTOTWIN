"""
batch_run.py  ─  AUTOTWIN Batch ECM Processor
══════════════════════════════════════════════
Runs the Thevenin 1-RC ECM on every NASA discharge CSV in a folder.
Saves one results CSV and one plot per file, plus a combined summary.

Usage examples
──────────────
  # Process all CSVs in a folder (fresh cells, Q_nom = 2.0 Ah)
  python batch_run.py --folder data/B0043/

  # Use a custom nominal capacity (aged cells)
  python batch_run.py --folder data/ --qnom 1.7

  # Match only certain files by pattern
  python batch_run.py --folder data/ --pattern "*B0043*"

  # Save everything to a specific output directory
  python batch_run.py --folder data/ --outdir results/B0043/

  # See all options
  python batch_run.py --help
"""

import argparse
import fnmatch
import os
import sys
import time

import numpy as np
import pandas as pd

# ── Import ECM from same directory as this script ────────────────────────────
_this_dir = os.path.dirname(os.path.abspath(__file__))
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)
try:
    from thevenin_ecm import TheveninECM, NASA_Q_NOMINAL as NASA_Q_NOM_AH
except ImportError:
    print("[ERROR] Cannot import thevenin_ecm.py — make sure it is in the same folder.")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def print_sep(char="═", width=62):
    print(char * width)


def collect_files(folder: str, pattern: str) -> list[str]:
    """Return sorted list of CSV paths inside folder matching pattern."""
    all_csv = [
        os.path.join(folder, fn)
        for fn in sorted(os.listdir(folder))
        if fn.lower().endswith(".csv") and fnmatch.fnmatch(fn, pattern)
    ]
    return all_csv


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="AUTOTWIN — Thevenin ECM Batch Processor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    ap.add_argument("--folder",  required=True,
                    help="Folder containing NASA discharge CSVs")
    ap.add_argument("--qnom",    type=float, default=NASA_Q_NOM_AH,
                    help=f"Nominal capacity [Ah] (default: {NASA_Q_NOM_AH}). "
                         "Use lower values for aged cells.")
    ap.add_argument("--outdir",  default=None,
                    help="Output directory (default: <folder>/ecm_results/)")
    ap.add_argument("--pattern", default="*.csv",
                    help="Filename glob pattern to select files (default: *.csv)")
    ap.add_argument("--plot",    action="store_true", default=True,
                    help="Generate a 4-panel plot per file (default: on)")
    ap.add_argument("--no-plot", dest="plot", action="store_false",
                    help="Skip plot generation")
    ap.add_argument("--verbose", action="store_true",
                    help="Show optimiser progress for each file")
    args = ap.parse_args()

    # ── Validate inputs ────────────────────────────────────────────────────────
    if not os.path.isdir(args.folder):
        print(f"[ERROR] Folder not found: {args.folder}")
        sys.exit(1)

    csv_files = collect_files(args.folder, args.pattern)
    if not csv_files:
        print(f"[ERROR] No CSV files matching '{args.pattern}' in {args.folder}")
        sys.exit(1)

    outdir = args.outdir or os.path.join(args.folder, "ecm_results")
    os.makedirs(outdir, exist_ok=True)

    # ── Header ─────────────────────────────────────────────────────────────────
    print_sep()
    print(f"  AUTOTWIN — Thevenin 1-RC ECM  ·  Batch Mode")
    print(f"  Folder   : {os.path.abspath(args.folder)}")
    print(f"  Files    : {len(csv_files)} CSV(s) matched")
    print(f"  Q_nom    : {args.qnom} Ah")
    print(f"  Output   : {os.path.abspath(outdir)}")
    print_sep()

    # ── Batch loop ─────────────────────────────────────────────────────────────
    summary_rows = []
    failed       = []

    for idx, fpath in enumerate(csv_files):
        fname = os.path.basename(fpath)
        base  = os.path.splitext(fname)[0]
        print(f"\n[{idx+1}/{len(csv_files)}] Processing: {fname}")

        t0 = time.time()
        try:
            df  = TheveninECM.load_csv(fpath)
            ecm = TheveninECM()
            res = ecm.run(df, Q_nominal_Ah=args.qnom, verbose=args.verbose)
            elapsed = time.time() - t0

            # Print quick summary
            p = res["params"]; m = res["metrics"]; s = res["soc"]
            print(f"    R0={p['R0_ohm']*1000:.2f} mΩ  "
                  f"R1={p['R1_ohm']*1000:.2f} mΩ  "
                  f"C1={p['C1_F']:.1f} F  τ={p['tau_s']:.2f} s")
            print(f"    RMSE={m['RMSE_V']*1000:.2f} mV  "
                  f"MAE={m['MAE_V']*1000:.2f} mV  "
                  f"R²={m['R2']:.5f}  "
                  f"MaxErr={m['MaxErr_V']*1000:.2f} mV")
            print(f"    SOC {s[0]*100:.1f}% → {s[-1]*100:.1f}%  "
                  f"DoD={( s[0]-s[-1])*100:.1f}%  "
                  f"({res['time'][-1]/60:.1f} min)  "
                  f"[{elapsed:.1f} s]")

            # Save per-file CSV
            out_csv = os.path.join(outdir, f"{base}_ecm.csv")
            pd.DataFrame({
                "Time_s":    res["time"],
                "V_meas_V":  res["V_measured"],
                "V_sim_V":   res["V_simulated"],
                "V_err_mV":  (res["V_measured"] - res["V_simulated"]) * 1000,
                "SOC":       s,
                "Current_A": res["current"],
                "Temp_C":    res["temperature"],
            }).to_csv(out_csv, index=False)
            print(f"    Saved → {os.path.basename(out_csv)}")

            # Optional plot
            if args.plot:
                _save_plot(res, base, outdir)

            summary_rows.append({
                "File":          fname,
                "R0_mOhm":       round(p["R0_ohm"]*1000, 3),
                "R1_mOhm":       round(p["R1_ohm"]*1000, 3),
                "C1_F":          round(p["C1_F"],         2),
                "tau_s":         round(p["tau_s"],         3),
                "RMSE_mV":       round(m["RMSE_V"]*1000, 3),
                "MAE_mV":        round(m["MAE_V"]*1000, 3),
                "R2":            m["R2"],
                "MaxErr_mV":     round(m["MaxErr_V"]*1000, 3),
                "MAPE_pct":      m["MAPE_pct"],
                "SOC_start_pct": round(s[0]*100,  2),
                "SOC_end_pct":   round(s[-1]*100, 2),
                "DoD_pct":       round((s[0]-s[-1])*100, 2),
                "Duration_min":  round(res["time"][-1]/60, 2),
                "n_samples":     len(res["time"]),
                "elapsed_s":     round(elapsed, 1),
                "Q_nom_Ah":      args.qnom,
            })

        except Exception as e:
            elapsed = time.time() - t0
            print(f"    [FAILED] {e}  ({elapsed:.1f} s)")
            failed.append((fname, str(e)))

    # ── Summary ────────────────────────────────────────────────────────────────
    print()
    print_sep()
    print(f"  Batch complete: {len(summary_rows)} succeeded, {len(failed)} failed")
    print_sep()

    if failed:
        print("\nFailed files:")
        for fn, err in failed:
            print(f"  ✗ {fn}: {err}")

    if summary_rows:
        summary_df = pd.DataFrame(summary_rows)
        summary_path = os.path.join(outdir, "batch_ecm_summary.csv")
        summary_df.to_csv(summary_path, index=False)
        print(f"\n[✓] Summary table → {summary_path}")

        # Print averages
        print("\n── Averages across all successful files ──────────────────")
        for col in ["R0_mOhm","R1_mOhm","C1_F","tau_s","RMSE_mV","R2","DoD_pct"]:
            print(f"  {col:15s} : {summary_df[col].mean():.4f}  "
                  f"(std={summary_df[col].std():.4f})")

        # Combined data CSV
        _save_combined(outdir)
        print(f"\n[✓] Combined data  → {os.path.join(outdir,'batch_ecm_combined.csv')}")

    print()
    print_sep()
    print("  Done.")
    print_sep()
    print()


def _save_plot(res: dict, base: str, outdir: str) -> None:
    """Save a 4-panel plot for one file's ECM results."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(4, 1, figsize=(13, 11), sharex=True)
        t = res["time"]; soc = res["soc"]
        p = res["params"]; m = res["metrics"]

        fig.suptitle(
            f"AUTOTWIN — Thevenin 1-RC ECM │ {base}\n"
            f"R₀={p['R0_ohm']*1000:.2f} mΩ  R₁={p['R1_ohm']*1000:.2f} mΩ  "
            f"C₁={p['C1_F']:.1f} F  τ={p['tau_s']:.2f} s  │  "
            f"RMSE={m['RMSE_V']*1000:.2f} mV  R²={m['R2']:.5f}",
            fontsize=10, fontweight="bold"
        )

        axes[0].plot(t, res["V_measured"], "k-",  lw=1.5, label="Measured")
        axes[0].plot(t, res["V_simulated"],  "r--", lw=2.0, label="ECM simulated")
        axes[0].set_ylabel("Voltage (V)"); axes[0].legend(); axes[0].grid(alpha=0.3)

        axes[1].plot(t, (res["V_measured"] - res["V_simulated"]) * 1000, "b-", lw=1.2)
        axes[1].axhline(0, color="k", lw=0.8, ls="--")
        axes[1].fill_between(t, (res["V_measured"] - res["V_simulated"]) * 1000, alpha=0.22, color="blue")
        axes[1].set_ylabel("Error (mV)"); axes[1].grid(alpha=0.3)

        axes[2].plot(t, soc * 100, "g-", lw=2.0)
        axes[2].set_ylabel("SOC (%)"); axes[2].set_ylim(-2, 105); axes[2].grid(alpha=0.3)

        temp = res["temperature"]
        if not np.all(np.isnan(temp)):
            axes[3].plot(t, temp, "m-", lw=1.5); axes[3].set_ylabel("Temp (°C)")
        else:
            axes[3].plot(t, np.abs(res["current"]), "m-", lw=1.5)
            axes[3].set_ylabel("|Current| (A)")
        axes[3].set_xlabel("Time (s)"); axes[3].grid(alpha=0.3)

        plt.tight_layout()
        pout = os.path.join(outdir, f"{base}_ecm_plot.png")
        plt.savefig(pout, dpi=150, bbox_inches="tight"); plt.close()
        print(f"    Plot   → {os.path.basename(pout)}")
    except ImportError:
        pass  # matplotlib not installed — skip plot silently


def _save_combined(outdir: str) -> None:
    """Merge all per-file CSVs into one combined CSV with a 'File' column."""
    all_parts = []
    for fn in sorted(os.listdir(outdir)):
        if fn.endswith("_ecm.csv"):
            df = pd.read_csv(os.path.join(outdir, fn))
            df.insert(0, "File", fn.replace("_ecm.csv", ""))
            all_parts.append(df)
    if all_parts:
        pd.concat(all_parts, ignore_index=True).to_csv(
            os.path.join(outdir, "batch_ecm_combined.csv"), index=False
        )


if __name__ == "__main__":
    main()