"""
fix_compare_tab.py — removes thermal calib/valid plots from Compare tab
and makes the Physical Model card show ECM or Thermal values dynamically.
Run from your project folder: python fix_compare_tab.py
"""
import shutil, re

shutil.copy2("app.py", "app.py.cmp_bak")

with open("app.py", "r", encoding="utf-8") as f:
    src = f.read()

# ══════════════════════════════════════════════════════════════════════════════
# PATCH: Replace the entire thermal compare block + battery overview guard
# with a clean version that just feeds physical model values into the
# existing Physical Model card
# ══════════════════════════════════════════════════════════════════════════════

OLD = '''    # ── Thermal Compare Block ─────────────────────────────────────────────────
    _cmp_th_res  = st.session_state.get("thermal_results")
    _cmp_th_vres = st.session_state.get("thermal_valid_results")

    if _active == "Thermal":'''

# Find where this block ends — at "if _active != 'Thermal':"
# We'll replace from OLD to the start of "if _active != 'Thermal':"
start_idx = src.find(OLD)
if start_idx == -1:
    print("[!] Could not find thermal compare block start")
    exit(1)

end_marker = '    if _active != "Thermal":\n        # ── Battery Overview'
end_idx = src.find(end_marker, start_idx)
if end_idx == -1:
    # try alternative
    end_marker = "    if _active != \"Thermal\":"
    end_idx = src.find(end_marker, start_idx)

if end_idx == -1:
    print("[!] Could not find end of thermal block — searching...")
    # Find it by looking for Battery Overview after the thermal block
    end_marker2 = '    # ── Battery Overview'
    end_idx = src.find(end_marker2, start_idx)
    if end_idx != -1:
        print(f"[?] Found '# Battery Overview' as end marker")

if end_idx == -1:
    print("[!] Could not locate end of block. Showing context around start:")
    ctx = src[start_idx:start_idx+200]
    print(ctx)
    exit(1)

# What we remove: from OLD start to end_idx
# What we insert: just the dynamic physical model value resolver
NEW_BLOCK = '''    # ── Resolve physical model values for compare tab ───────────────────────
    _cmp_th_res = st.session_state.get("thermal_results")
    _ecm_res    = st.session_state.ecm_results

    # Determine which physical model ran and extract display values
    if _active == "Thermal" and _cmp_th_res:
        _phys_label   = "LUMPED THERMAL MODEL"
        _phys_icon    = "🌡️"
        _phys_rul     = "—"
        _phys_acc     = f"{_cmp_th_res['metrics']['R2']*100:.1f}%"
        _phys_acc_pct = round(_cmp_th_res["metrics"]["R2"] * 100, 1)
        _phys_eol     = "—"
        _phys_params  = [
            ("C_th (J/K)", f"{_cmp_th_res.get('C_th_final', _cmp_th_res['C_th']):.2f}"),
            ("hA (W/K)",   f"{_cmp_th_res.get('hA_final',   _cmp_th_res['hA']):.5f}"),
            ("T_amb (C)",  f"{_cmp_th_res['T_amb']:.2f}"),
            ("RMSE_T (C)", f"{_cmp_th_res['metrics']['RMSE_C']:.4f}"),
        ]
        _phys_desc = "Lumped thermal capacitance model · C_th & hA identified from charge data"
    elif _ecm_res:
        _phys_label   = "EQUIVALENT CIRCUIT MODEL"
        _phys_icon    = "⚡"
        _phys_rul     = "13"
        _phys_acc     = f"{round(_ecm_res['metrics']['R2']*100,1)}%"
        _phys_acc_pct = round(_ecm_res["metrics"]["R2"] * 100, 1)
        _phys_eol     = "80%"
        _phys_params  = [
            ("R0 (mOhm)", f"{_ecm_res['params']['R0_ohm']*1000:.2f}"),
            ("R1 (mOhm)", f"{_ecm_res['params']['R1_ohm']*1000:.2f}"),
            ("C1 (F)",    f"{_ecm_res['params']['C1_F']:.1f}"),
            ("tau (s)",   f"{_ecm_res['params']['tau_s']:.2f}"),
        ]
        _phys_desc = "Thevenin 1RC · R0, R1, C1 identified from discharge data"
    else:
        _phys_label   = "PHYSICAL MODEL"
        _phys_icon    = "⚙"
        _phys_rul     = "—"
        _phys_acc     = "—"
        _phys_acc_pct = 0
        _phys_eol     = "—"
        _phys_params  = []
        _phys_desc    = "Run ECM or Thermal model in the Simulation tab first"

    # ── Battery Overview ─────────────────────────────────────────────────────
'''

src = src[:start_idx] + NEW_BLOCK + src[end_idx:]
print("[OK] Thermal calib/valid plot block removed and replaced with dynamic resolver")

# ══════════════════════════════════════════════════════════════════════════════
# Now update the Physical Model card to use dynamic values
# ══════════════════════════════════════════════════════════════════════════════

# The physical model card currently hardcodes ECM values.
# Find and replace it with a dynamic version.

OLD_CARD = '''    with phys_col:
        st.markdown(f"""
        <div style="position:relative;
          background:linear-gradient(145deg,rgba(70,0,20,0.97),rgba(120,10,40,0.95));
          border:2px solid #ff3366;border-radius:22px;padding:36px 32px;
          min-height:360px;overflow:hidden;box-shadow:0 12px 40px rgba(255,51,102,0.3);">
          <div style="position:absolute;top:0;left:0;right:0;height:3px;
            background:linear-gradient(90deg,#ff3366,#cc0033,#ff3366);box-shadow:0 0 12px rgba(255,51,102,0.6);"></div>
          <div style="display:flex;align-items:center;gap:14px;margin-bottom:26px;">
            <span style="font-size:3.2rem;filter:drop-shadow(0 0 14px #00c8ff);">⚙</span>
            <div>
              <div style="font-family:'Orbitron',monospace;color:#00c8ff;font-size:1.2rem;font-weight:900;letter-spacing:0.08em;">PHYSICAL MODEL</div>
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(180,230,255,0.7);font-size:0.75rem;letter-spacing:0.1em;margin-top:3px;">Equivalent Circuit Model (ECM)</div>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:24px;">
            <div style="background:rgba(0,200,255,0.1);border:1px solid rgba(0,200,255,0.3);border-radius:14px;padding:18px 12px;text-align:center;">
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(180,230,255,0.7);font-size:0.65rem;letter-spacing:0.12em;margin-bottom:8px;">PREDICTED RUL</div>
              <div style="font-family:'Orbitron',monospace;color:#00c8ff;font-size:2.8rem;font-weight:900;text-shadow:0 0 20px rgba(0,200,255,0.7);">13</div>
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(180,230,255,0.6);font-size:0.7rem;margin-top:4px;">CYCLES</div>
            </div>
            <div style="background:rgba(0,200,255,0.1);border:1px solid rgba(0,200,255,0.3);border-radius:14px;padding:18px 12px;text-align:center;">
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(180,230,255,0.7);font-size:0.65rem;letter-spacing:0.12em;margin-bottom:8px;">ACCURACY</div>
              <div style="font-family:'Orbitron',monospace;color:#00c8ff;font-size:2.8rem;font-weight:900;text-shadow:0 0 20px rgba(0,200,255,0.7);">{ecm_acc_disp}</div>
            </div>
          </div>
          <div style="background:rgba(255,165,0,0.15);border:2px solid rgba(255,165,0,0.5);border-radius:14px;padding:14px 16px;margin-bottom:14px;display:flex;align-items:center;gap:12px;">
            <span style="font-size:1.5rem;">⚠️</span>
            <div>
              <div style="font-family:'Orbitron',monospace;color:#ffaa00;font-size:0.75rem;font-weight:700;letter-spacing:0.1em;">EOL DETECTION</div>
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(255,200,100,0.9);font-size:1.1rem;font-weight:700;margin-top:2px;">80%</div>
            </div>
            <div style="margin-left:auto;">
              <div class="perf-bar-track" style="width:120px;">
                <div class="perf-bar-fill" style="width:80%;background:linear-gradient(90deg,#ffaa00,#ffdd44);"></div>
              </div>
            </div>
          </div>
          <div style="background:rgba(0,200,255,0.06);border:1px solid rgba(0,200,255,0.2);border-radius:12px;padding:14px 16px;">
            <div style="font-family:'Share Tech Mono',monospace;color:rgba(180,230,255,0.85);font-size:0.75rem;letter-spacing:0.06em;line-height:1.8;">
              ◈ Physics-based degradation equations<br>
              ◈ Computationally lightweight<br>
              ◈ Interpretable parameter outputs
            </div>
          </div>
        </div>""", unsafe_allow_html=True)'''

NEW_CARD = '''    with phys_col:
        _param_rows = "".join([
            f'<div style="display:flex;justify-content:space-between;padding:6px 0;'
            f'border-bottom:1px solid rgba(0,200,255,0.15);">'
            f'<span style="font-family:Share Tech Mono,monospace;color:rgba(180,230,255,0.7);font-size:0.75rem;">{k}</span>'
            f'<span style="font-family:Orbitron,monospace;color:#00c8ff;font-weight:700;font-size:0.82rem;">{v}</span>'
            f'</div>'
            for k, v in _phys_params
        ]) if _phys_params else "<div style='color:rgba(180,230,255,0.5);font-family:Share Tech Mono,monospace;font-size:0.78rem;'>Run a model first to see parameters</div>"

        st.markdown(f"""
        <div style="position:relative;
          background:linear-gradient(145deg,rgba(70,0,20,0.97),rgba(120,10,40,0.95));
          border:2px solid #ff3366;border-radius:22px;padding:36px 32px;
          min-height:360px;overflow:hidden;box-shadow:0 12px 40px rgba(255,51,102,0.3);">
          <div style="position:absolute;top:0;left:0;right:0;height:3px;
            background:linear-gradient(90deg,#ff3366,#cc0033,#ff3366);box-shadow:0 0 12px rgba(255,51,102,0.6);"></div>
          <div style="display:flex;align-items:center;gap:14px;margin-bottom:26px;">
            <span style="font-size:3.2rem;filter:drop-shadow(0 0 14px #00c8ff);">{_phys_icon}</span>
            <div>
              <div style="font-family:'Orbitron',monospace;color:#00c8ff;font-size:1.1rem;font-weight:900;letter-spacing:0.06em;">{_phys_label}</div>
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(180,230,255,0.7);font-size:0.72rem;letter-spacing:0.08em;margin-top:3px;">{_phys_desc}</div>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:24px;">
            <div style="background:rgba(0,200,255,0.1);border:1px solid rgba(0,200,255,0.3);border-radius:14px;padding:18px 12px;text-align:center;">
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(180,230,255,0.7);font-size:0.65rem;letter-spacing:0.12em;margin-bottom:8px;">PREDICTED RUL</div>
              <div style="font-family:'Orbitron',monospace;color:#00c8ff;font-size:2.8rem;font-weight:900;text-shadow:0 0 20px rgba(0,200,255,0.7);">{_phys_rul}</div>
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(180,230,255,0.6);font-size:0.7rem;margin-top:4px;">CYCLES</div>
            </div>
            <div style="background:rgba(0,200,255,0.1);border:1px solid rgba(0,200,255,0.3);border-radius:14px;padding:18px 12px;text-align:center;">
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(180,230,255,0.7);font-size:0.65rem;letter-spacing:0.12em;margin-bottom:8px;">ACCURACY (R²)</div>
              <div style="font-family:'Orbitron',monospace;color:#00c8ff;font-size:2.8rem;font-weight:900;text-shadow:0 0 20px rgba(0,200,255,0.7);">{_phys_acc}</div>
            </div>
          </div>
          <div style="background:rgba(0,200,255,0.06);border:1px solid rgba(0,200,255,0.2);border-radius:12px;padding:14px 16px;">
            <div style="font-family:'Orbitron',monospace;color:#00c8ff;font-size:0.65rem;font-weight:700;letter-spacing:0.12em;margin-bottom:8px;">IDENTIFIED PARAMETERS</div>
            {_param_rows}
          </div>
        </div>""", unsafe_allow_html=True)'''

if OLD_CARD in src:
    src = src.replace(OLD_CARD, NEW_CARD, 1)
    print("[OK] Physical Model card updated to show ECM or Thermal values dynamically")
else:
    print("[!] Physical Model card anchor not found — it may already be updated or wording differs")

# ══════════════════════════════════════════════════════════════════════════════
# Update the Performance Summary bar to use _phys_acc_pct dynamically
# ══════════════════════════════════════════════════════════════════════════════
OLD_BAR = '''              <span style="font-family:Orbitron,monospace;color:#00c8ff;font-weight:900;font-size:1.1rem;">{ecm_acc_disp}</span>
              </div>
              <div class="perf-bar-track"><div class="perf-bar-fill" style="width:{ecm_pct}%;background:linear-gradient(90deg,#00c8ff,#0088ff);"></div></div>'''

NEW_BAR = '''              <span style="font-family:Orbitron,monospace;color:#00c8ff;font-weight:900;font-size:1.1rem;">{_phys_acc}</span>
              </div>
              <div class="perf-bar-track"><div class="perf-bar-fill" style="width:{_phys_acc_pct}%;background:linear-gradient(90deg,#00c8ff,#0088ff);"></div></div>'''

if OLD_BAR in src:
    src = src.replace(OLD_BAR, NEW_BAR, 1)
    print("[OK] Performance summary bar updated to use dynamic accuracy")
else:
    print("[!] Performance bar anchor not found")

# Also update the conclusion text that references ecm_acc_disp
OLD_CONC = "AI model provides slightly higher accuracy (91% vs {ecm_acc_disp})"
NEW_CONC = "AI model provides slightly higher accuracy (91% vs {_phys_acc})"
if OLD_CONC in src:
    src = src.replace(OLD_CONC, NEW_CONC, 1)
    print("[OK] Conclusion text updated")
else:
    print("[!] Conclusion text anchor not found")

# ══════════════════════════════════════════════════════════════════════════════
# Remove the "if _active != Thermal" wrapper since compare tab now always
# shows physical vs AI — just with dynamic values
# ══════════════════════════════════════════════════════════════════════════════
OLD_GUARD = '    if _active != "Thermal":\n        # ── Battery Overview'
NEW_GUARD = '    # ── Battery Overview'
if OLD_GUARD in src:
    # Need to de-indent everything inside this guard block
    # Find the block and remove the extra 4 spaces
    lines = src.splitlines(keepends=True)
    in_guard = False
    guard_start = None
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if '    if _active != "Thermal":' in line and '# ── Battery Overview' in (lines[i+1] if i+1 < len(lines) else ""):
            # Skip this guard line, de-indent following lines
            in_guard = True
            guard_start = i
            i += 1
            continue
        if in_guard:
            # De-indent by 4 spaces
            if line.startswith("        "):
                result.append(line[4:])
            elif line.strip() == "":
                result.append(line)
            else:
                in_guard = False
                result.append(line)
        else:
            result.append(line)
        i += 1
    src = "".join(result)
    print("[OK] Battery overview guard removed — compare tab always shows physical vs AI")
else:
    print("[!] Guard wrapper not found — may already be removed")

with open("app.py", "w", encoding="utf-8") as f:
    f.write(src)

print("\n[DONE] Run:  streamlit run app.py")
print("\nCompare tab now:")
print("  - Physical Model card shows ECM values when ECM selected")
print("  - Physical Model card shows Thermal values when Thermal selected")
print("  - AI Model card stays fixed (LSTM)")
print("  - Degradation chart stays as-is")
print("  - No extra thermal calib/valid plots")