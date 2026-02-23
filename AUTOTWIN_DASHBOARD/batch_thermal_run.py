"""
batch_thermal_run.py
====================
Pre-processes charge + discharge CSV files for the Lumped Thermal Model.
Supports combining multiple calibration folders so the model learns
the full thermal picture of the battery (both charge and discharge).

Usage:
    # Combined charge + discharge calibration (recommended)
    python batch_thermal_run.py --calib "Battery47/discharge" "Battery47/charge" --valid_split 0.2

    # Single folder with automatic train/valid split
    python batch_thermal_run.py --calib "Battery47/discharge" --valid_split 0.2

    # Manual separate folders
    python batch_thermal_run.py --calib "Battery47/discharge" --valid "Battery47/charge"

    # Custom R value from ECM
    python batch_thermal_run.py --calib "Battery47/discharge" "Battery47/charge" --valid_split 0.2 --R_ohm 0.095

Outputs saved to <first_calib_folder>/thermal_results/
    thermal_params.csv          — final median C_th, hA, T_amb
    batch_thermal_summary.csv   — per-file calibration metrics
    batch_valid_summary.csv     — per-file validation metrics
"""

import os, sys, glob, argparse, random
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lumped_thermal import LumpedThermalModel

# ── CLI args ─────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--calib",  required=True, nargs="+",
                    help="One or more folders with calibration CSVs")
parser.add_argument("--valid",  default=None,  nargs="+",
                    help="One or more folders with validation CSVs (optional)")
parser.add_argument("--valid_split", type=float, default=0.0,
                    help="Fraction of calib files to hold out for validation (e.g. 0.2 = 20%%)")
parser.add_argument("--R_ohm", type=float, default=0.080,
                    help="Internal resistance in Ohm (default 0.080 = 80 mOhm)")
parser.add_argument("--out",   default=None,
                    help="Output folder (default: <first_calib_folder>/thermal_results)")
parser.add_argument("--seed",  type=int, default=42,
                    help="Random seed for train/valid split (default 42)")
args = parser.parse_args()

CALIB_FOLDERS = args.calib
VALID_FOLDERS  = args.valid
VALID_SPLIT    = args.valid_split
R_OHM          = args.R_ohm
OUT_FOLDER     = args.out or os.path.join(CALIB_FOLDERS[0], "thermal_results")

os.makedirs(OUT_FOLDER, exist_ok=True)

print(f"\n{'='*60}")
print(f"  AUTOTWIN — Batch Thermal Model Runner")
print(f"{'='*60}")
print(f"  Calibration folders : {', '.join(CALIB_FOLDERS)}")
print(f"  Validation          : {', '.join(VALID_FOLDERS) if VALID_FOLDERS else f'auto-split {VALID_SPLIT*100:.0f}%' if VALID_SPLIT > 0 else 'None'}")
print(f"  R_ohm               : {R_OHM*1000:.1f} mOhm")
print(f"  Output folder       : {OUT_FOLDER}")
print(f"{'='*60}\n")

# ── Collect all calibration files ─────────────────────────────────────────────
all_calib_files = []
for folder in CALIB_FOLDERS:
    files = sorted(glob.glob(os.path.join(folder, "*.csv")))
    if files:
        print(f"[INFO] Found {len(files)} files in {folder}")
        all_calib_files.extend(files)
    else:
        print(f"[!] No CSV files found in {folder}")

if not all_calib_files:
    print("[ERROR] No calibration files found"); sys.exit(1)

print(f"[INFO] Total calibration files: {len(all_calib_files)}\n")

# ── Auto train/valid split if requested ──────────────────────────────────────
auto_valid_files = []
if VALID_SPLIT > 0 and not VALID_FOLDERS:
    random.seed(args.seed)
    shuffled = all_calib_files.copy()
    random.shuffle(shuffled)
    n_valid = max(1, int(len(shuffled) * VALID_SPLIT))
    auto_valid_files = shuffled[:n_valid]
    all_calib_files  = shuffled[n_valid:]
    print(f"[INFO] Auto-split: {len(all_calib_files)} calibration, {len(auto_valid_files)} validation\n")

# ── Run calibration ───────────────────────────────────────────────────────────
model = LumpedThermalModel()
calib_results = []
cth_vals, ha_vals = [], []

print(f"{'─'*60}")
print(f"  CALIBRATION")
print(f"{'─'*60}")

for i, fp in enumerate(all_calib_files):
    fname = os.path.basename(fp)
    folder_tag = os.path.basename(os.path.dirname(fp))
    print(f"  [{i+1:3d}/{len(all_calib_files)}] {folder_tag}/{fname} ...", end="", flush=True)
    try:
        df = LumpedThermalModel.load_csv(fp)
        if not LumpedThermalModel.check_columns(df):
            print(f" SKIP (missing columns)")
            continue
        res = model.calibrate(df, R_ohm=R_OHM, verbose=False)
        res["_filename"] = fname
        res["_folder"]   = folder_tag
        calib_results.append(res)
        cth_vals.append(res["C_th"])
        ha_vals.append(res["hA"])

        out_csv = os.path.join(OUT_FOLDER, f"{folder_tag}_{fname.replace('.csv','')}_thermal.csv")
        pd.DataFrame({
            "Time_s":   res["time"],
            "T_meas_C": res["T_measured"],
            "T_pred_C": res["T_predicted"],
            "Error_C":  np.array(res["T_measured"]) - np.array(res["T_predicted"]),
        }).to_csv(out_csv, index=False)

        m = res["metrics"]
        print(f" RMSE={m['RMSE_C']:.3f}C  R2={m['R2']:.4f}  C_th={res['C_th']:.1f}  hA={res['hA']:.5f}")
    except Exception as e:
        print(f" ERROR: {e}")

if not calib_results:
    print("[ERROR] No files calibrated successfully."); sys.exit(1)

# ── Compute median parameters ─────────────────────────────────────────────────
C_TH_UPPER = 490.0
valid_cth = [c for c in cth_vals if c < C_TH_UPPER]
valid_ha  = [h for h, c in zip(ha_vals, cth_vals) if c < C_TH_UPPER]
if len(valid_cth) == 0:
    valid_cth = cth_vals
    valid_ha  = ha_vals
C_th_final = float(np.median(valid_cth))
hA_final   = float(np.median(valid_ha))
print(f"[INFO] Used {len(valid_cth)}/{len(cth_vals)} files for median (excluded boundary hits)")
best_calib = min(calib_results, key=lambda r: r["metrics"]["RMSE_C"])

print(f"\n{'─'*60}")
print(f"  CALIBRATION COMPLETE")
print(f"  Files processed : {len(calib_results)}/{len(all_calib_files)}")
print(f"  Median C_th     : {C_th_final:.4f} J/K")
print(f"  Median hA       : {hA_final:.6f} W/K")
print(f"  Best RMSE       : {best_calib['metrics']['RMSE_C']:.4f} C ({best_calib['_folder']}/{best_calib['_filename']})")
print(f"{'─'*60}\n")

# ── Save calibration summary ──────────────────────────────────────────────────
summary_rows = []
for r in calib_results:
    m = r["metrics"]
    summary_rows.append({
        "Folder":    r["_folder"],
        "File":      r["_filename"],
        "C_th_J_K":  round(r["C_th"], 4),
        "hA_W_K":    round(r["hA"], 6),
        "T_amb_C":   round(r["T_amb"], 3),
        "R_ohm":     round(r["R_ohm"], 6),
        "RMSE_C":    round(m["RMSE_C"], 4),
        "MAE_C":     round(m["MAE_C"], 4),
        "R2":        round(m["R2"], 4),
        "MaxErr_C":  round(m["MaxErr_C"], 4),
        "MAPE_pct":  round(m["MAPE_pct"], 4),
    })
pd.DataFrame(summary_rows).to_csv(
    os.path.join(OUT_FOLDER, "batch_thermal_summary.csv"), index=False)
print(f"[OK] Calibration summary saved")

# ── Save final parameters ─────────────────────────────────────────────────────
pd.DataFrame([{
    "C_th_J_K":      round(C_th_final, 4),
    "hA_W_K":        round(hA_final, 6),
    "T_amb_C":       round(best_calib["T_amb"], 3),
    "R_ohm":         round(R_OHM, 6),
    "best_file":     f"{best_calib['_folder']}/{best_calib['_filename']}",
    "best_RMSE_C":   round(best_calib["metrics"]["RMSE_C"], 4),
    "best_R2":       round(best_calib["metrics"]["R2"], 4),
    "n_calib_files": len(calib_results),
    "calib_folders": ", ".join(CALIB_FOLDERS),
}]).to_csv(os.path.join(OUT_FOLDER, "thermal_params.csv"), index=False)
print(f"[OK] Final parameters saved")

# ── Validation ────────────────────────────────────────────────────────────────
valid_files = []

if auto_valid_files:
    valid_files = auto_valid_files
    print(f"\n[INFO] Using auto-split validation: {len(valid_files)} files")
elif VALID_FOLDERS:
    for folder in VALID_FOLDERS:
        files = sorted(glob.glob(os.path.join(folder, "*.csv")))
        valid_files.extend(files)
    print(f"\n[INFO] Found {len(valid_files)} validation files")

if valid_files:
    print(f"{'─'*60}")
    print(f"  VALIDATION")
    print(f"{'─'*60}")
    valid_results = []

    for i, fp in enumerate(valid_files):
        fname = os.path.basename(fp)
        folder_tag = os.path.basename(os.path.dirname(fp))
        print(f"  [{i+1:3d}/{len(valid_files)}] {folder_tag}/{fname} ...", end="", flush=True)
        try:
            df = LumpedThermalModel.load_csv(fp)
            if not LumpedThermalModel.check_columns(df):
                print(f" SKIP (missing columns)")
                continue
            res = model.validate(df, C_th=C_th_final, hA=hA_final, R_ohm=R_OHM)
            res["_filename"] = fname
            res["_folder"]   = folder_tag
            valid_results.append(res)

            out_csv = os.path.join(OUT_FOLDER, f"{folder_tag}_{fname.replace('.csv','')}_valid.csv")
            pd.DataFrame({
                "Time_s":   res["time"],
                "T_meas_C": res["T_measured"],
                "T_pred_C": res["T_predicted"],
                "Error_C":  np.array(res["T_measured"]) - np.array(res["T_predicted"]),
            }).to_csv(out_csv, index=False)

            m = res["metrics"]
            print(f" RMSE={m['RMSE_C']:.3f}C  R2={m['R2']:.4f}")
        except Exception as e:
            print(f" ERROR: {e}")

    if valid_results:
        avg_rmse = np.mean([r["metrics"]["RMSE_C"] for r in valid_results])
        avg_r2   = np.mean([r["metrics"]["R2"]     for r in valid_results])
        best_v   = min(valid_results, key=lambda r: r["metrics"]["RMSE_C"])

        print(f"\n{'─'*60}")
        print(f"  VALIDATION COMPLETE")
        print(f"  Files processed : {len(valid_results)}/{len(valid_files)}")
        print(f"  Avg RMSE        : {avg_rmse:.4f} C")
        print(f"  Avg R2          : {avg_r2:.4f}")
        print(f"  Best RMSE       : {best_v['metrics']['RMSE_C']:.4f} C ({best_v['_folder']}/{best_v['_filename']})")
        print(f"{'─'*60}\n")

        valid_rows = []
        for r in valid_results:
            m = r["metrics"]
            valid_rows.append({
                "Folder":   r["_folder"],
                "File":     r["_filename"],
                "RMSE_C":   round(m["RMSE_C"], 4),
                "MAE_C":    round(m["MAE_C"], 4),
                "R2":       round(m["R2"], 4),
                "MaxErr_C": round(m["MaxErr_C"], 4),
                "MAPE_pct": round(m["MAPE_pct"], 4),
            })
        pd.DataFrame(valid_rows).to_csv(
            os.path.join(OUT_FOLDER, "batch_valid_summary.csv"), index=False)
        print(f"[OK] Validation summary saved")
else:
    print(f"\n[INFO] No validation files specified — skipping validation")
    print(f"[TIP] Re-run with --valid_split 0.2 to auto-split 20% for validation")

print(f"\n{'='*60}")
print(f"  ALL DONE — Results saved to: {OUT_FOLDER}")
print(f"  C_th (median) : {C_th_final:.2f} J/K")
print(f"  hA   (median) : {hA_final:.6f} W/K")
print(f"  Load in app   : Simulation → Thermal → Auto Load")
print(f"  Folder path   : {OUT_FOLDER}")
print(f"{'='*60}\n")