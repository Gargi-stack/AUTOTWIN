"""
patch_thermal_readability.py
============================
Makes the thermal simulation results more readable.
Run from your project folder: python patch_thermal_readability.py
"""
import shutil

APP = "app.py"
shutil.copy2(APP, APP + ".readable_bak")

with open(APP, "r", encoding="utf-8") as f:
    src = f.read()

ok = 0

# ── Fix 1: Section header — add description ───────────────────────────────────
OLD1 = """            st.markdown(\"\"\"
            <div class="glass-panel" style="border-color:rgba(255,136,0,0.4);">
              <h4 style="color:#cc6600;font-size:1.15rem;margin:0 0 4px;">IDENTIFIED THERMAL PARAMETERS</h4>
            </div>\"\"\", unsafe_allow_html=True)"""

NEW1 = """            st.markdown(\"\"\"
            <div class="glass-panel" style="border-color:rgba(255,136,0,0.4);">
              <h4 style="color:#cc6600;font-size:1.15rem;margin:0 0 4px;">🌡️ IDENTIFIED THERMAL PARAMETERS</h4>
              <p style="font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:#5a7090;margin:4px 0 0;">
                Parameters identified by fitting the thermal model equation to your battery data
              </p>
            </div>\"\"\", unsafe_allow_html=True)"""

if OLD1 in src:
    src = src.replace(OLD1, NEW1, 1)
    print("[OK] Fix 1: Section header updated")
    ok += 1
else:
    print("[!] Fix 1: not found")

# ── Fix 2: Parameter cards — full names ──────────────────────────────────────
OLD2 = """            tp1, tp2, tp3, tp4 = st.columns(4)
            for col, label, val, unit, color, desc in [
                (tp1, "C_th", f"{C_th_show:.1f}", "J/K",  "#ff8800", "Thermal capacitance"),
                (tp2, "hA",   f"{hA_show:.4f}",   "W/K",  "#cc44ff", "Heat-transfer coeff"),
                (tp3, "R",    f"{calib_res['R_ohm']*1000:.2f}", "mOhm", "#00c8ff", "Internal resistance"),
                (tp4, "T_amb",f"{calib_res['T_amb']:.1f}", "degC", "#00ff88", "Ambient temperature"),
            ]:
                with col:
                    st.markdown(f\"\"\"
                    <div class="ecm-result-card">
                      <div style="font-family:'Orbitron',monospace;color:{color};font-size:0.6rem;
                                  font-weight:700;letter-spacing:0.15em;margin-bottom:10px;">{label}</div>
                      <div style="font-family:'Orbitron',monospace;color:white;font-size:2.2rem;
                                  font-weight:900;text-shadow:0 0 20px {color}88;line-height:1;">{val}</div>
                      <div style="font-family:'Share Tech Mono',monospace;color:rgba(180,230,255,0.7);
                                  font-size:0.82rem;margin-top:4px;">{unit}</div>
                      <div style="font-family:'Share Tech Mono',monospace;color:rgba(180,230,255,0.5);
                                  font-size:0.66rem;margin-top:8px;">{desc}</div>
                    </div>\"\"\", unsafe_allow_html=True)"""

NEW2 = """            tp1, tp2, tp3, tp4 = st.columns(4)
            for col, label, sublabel, val, unit, color, desc in [
                (tp1, "Thermal Capacitance", "C_th",  f"{C_th_show:.1f}", "J / K",      "#ff8800", "Energy absorbed per °C rise"),
                (tp2, "Heat Transfer Coeff", "hA",    f"{hA_show:.4f}",   "W / K",      "#cc44ff", "Rate of heat loss to surroundings"),
                (tp3, "Internal Resistance", "R",     f"{calib_res['R_ohm']*1000:.2f}", "milli-Ohm", "#00c8ff", "Electrical resistance of the cell"),
                (tp4, "Ambient Temperature", "T_amb", f"{calib_res['T_amb']:.1f}", "°C","#00ff88", "Surrounding air temperature"),
            ]:
                with col:
                    st.markdown(f\"\"\"
                    <div class="ecm-result-card">
                      <div style="font-family:'Share Tech Mono',monospace;color:rgba(180,230,255,0.9);
                                  font-size:0.65rem;margin-bottom:2px;">{label}</div>
                      <div style="font-family:'Orbitron',monospace;color:{color};font-size:0.58rem;
                                  font-weight:700;letter-spacing:0.12em;margin-bottom:10px;">({sublabel})</div>
                      <div style="font-family:'Orbitron',monospace;color:white;font-size:2.0rem;
                                  font-weight:900;text-shadow:0 0 20px {color}88;line-height:1;">{val}</div>
                      <div style="font-family:'Share Tech Mono',monospace;color:rgba(180,230,255,0.7);
                                  font-size:0.82rem;margin-top:4px;">{unit}</div>
                      <div style="font-family:'Share Tech Mono',monospace;color:rgba(180,230,255,0.45);
                                  font-size:0.62rem;margin-top:8px;">{desc}</div>
                    </div>\"\"\", unsafe_allow_html=True)"""

if OLD2 in src:
    src = src.replace(OLD2, NEW2, 1)
    print("[OK] Fix 2: Parameter cards updated with full names")
    ok += 1
else:
    print("[!] Fix 2: not found")

# ── Fix 3: Calibration metric cards ──────────────────────────────────────────
OLD3 = """                cm1, cm2, cm3 = st.columns(3)
                for col, lbl, v, u, clr in [
                    (cm1, "RMSE", f"{m_c['RMSE_C']:.4f}", "C",  "#ff8800"),
                    (cm2, "MAE",  f"{m_c['MAE_C']:.4f}",  "C",  "#ffaa44"),
                    (cm3, "R2",   f"{m_c['R2']:.4f}",     "",   "#00ff88"),
                ]:
                    with col:
                        st.markdown(f\"\"\"
                        <div style="background:rgba(255,255,255,0.97);border:2px solid {clr}44;
                                    border-radius:14px;padding:16px;text-align:center;margin-bottom:12px;">
                          <div style="font-family:'Orbitron',monospace;color:#5a7090;font-size:0.62rem;
                                      letter-spacing:0.18em;margin-bottom:6px;">{lbl}</div>
                          <div style="font-family:'Orbitron',monospace;color:{clr};font-size:1.6rem;
                                      font-weight:900;">{v}</div>
                          <div style="font-family:'Share Tech Mono',monospace;color:#8a9ab0;
                                      font-size:0.78rem;">{u}</div>
                        </div>\"\"\", unsafe_allow_html=True)"""

NEW3 = """                cm1, cm2, cm3 = st.columns(3)
                for col, lbl, sublbl, v, u, clr in [
                    (cm1, "Root Mean Square Error", "RMSE", f"{m_c['RMSE_C']:.4f}", "°C — lower is better", "#ff8800"),
                    (cm2, "Mean Absolute Error",    "MAE",  f"{m_c['MAE_C']:.4f}",  "°C — lower is better", "#ffaa44"),
                    (cm3, "R-Squared",              "R²",   f"{m_c['R2']:.4f}",     "1.0 = perfect fit",    "#00ff88"),
                ]:
                    with col:
                        st.markdown(f\"\"\"
                        <div style="background:rgba(255,255,255,0.97);border:2px solid {clr}44;
                                    border-radius:14px;padding:16px;text-align:center;margin-bottom:12px;">
                          <div style="font-family:'Share Tech Mono',monospace;color:#5a7090;font-size:0.62rem;
                                      margin-bottom:2px;">{lbl}</div>
                          <div style="font-family:'Orbitron',monospace;color:#aabbcc;font-size:0.56rem;
                                      letter-spacing:0.12em;margin-bottom:6px;">({sublbl})</div>
                          <div style="font-family:'Orbitron',monospace;color:{clr};font-size:1.6rem;
                                      font-weight:900;">{v}</div>
                          <div style="font-family:'Share Tech Mono',monospace;color:#8a9ab0;
                                      font-size:0.72rem;margin-top:4px;">{u}</div>
                        </div>\"\"\", unsafe_allow_html=True)"""

if OLD3 in src:
    src = src.replace(OLD3, NEW3, 1)
    print("[OK] Fix 3: Calibration metric cards updated")
    ok += 1
else:
    print("[!] Fix 3: not found")

# ── Fix 4: Validation metric cards ───────────────────────────────────────────
OLD4 = """                    vm1, vm2, vm3 = st.columns(3)
                    for col, lbl, v, u, clr in [
                        (vm1, "RMSE", f"{m_v['RMSE_C']:.4f}", "C",  "#cc44ff"),
                        (vm2, "MAE",  f"{m_v['MAE_C']:.4f}",  "C",  "#dd66ff"),
                        (vm3, "R2",   f"{m_v['R2']:.4f}",     "",   "#00ff88"),
                    ]:
                        with col:
                            st.markdown(f\"\"\"
                            <div style="background:rgba(255,255,255,0.97);border:2px solid {clr}44;
                                        border-radius:14px;padding:16px;text-align:center;margin-bottom:12px;">
                              <div style="font-family:'Orbitron',monospace;color:#5a7090;font-size:0.62rem;
                                          letter-spacing:0.18em;margin-bottom:6px;">{lbl}</div>
                              <div style="font-family:'Orbitron',monospace;color:{clr};font-size:1.6rem;
                                          font-weight:900;">{v}</div>
                              <div style="font-family:'Share Tech Mono',monospace;color:#8a9ab0;
                                          font-size:0.78rem;">{u}</div>
                            </div>\"\"\", unsafe_allow_html=True)"""

NEW4 = """                    vm1, vm2, vm3 = st.columns(3)
                    for col, lbl, sublbl, v, u, clr in [
                        (vm1, "Root Mean Square Error", "RMSE", f"{m_v['RMSE_C']:.4f}", "°C — lower is better", "#cc44ff"),
                        (vm2, "Mean Absolute Error",    "MAE",  f"{m_v['MAE_C']:.4f}",  "°C — lower is better", "#dd66ff"),
                        (vm3, "R-Squared",              "R²",   f"{m_v['R2']:.4f}",     "1.0 = perfect fit",    "#00ff88"),
                    ]:
                        with col:
                            st.markdown(f\"\"\"
                            <div style="background:rgba(255,255,255,0.97);border:2px solid {clr}44;
                                        border-radius:14px;padding:16px;text-align:center;margin-bottom:12px;">
                              <div style="font-family:'Share Tech Mono',monospace;color:#5a7090;font-size:0.62rem;
                                          margin-bottom:2px;">{lbl}</div>
                              <div style="font-family:'Orbitron',monospace;color:#aabbcc;font-size:0.56rem;
                                          letter-spacing:0.12em;margin-bottom:6px;">({sublbl})</div>
                              <div style="font-family:'Orbitron',monospace;color:{clr};font-size:1.6rem;
                                          font-weight:900;">{v}</div>
                              <div style="font-family:'Share Tech Mono',monospace;color:#8a9ab0;
                                          font-size:0.72rem;margin-top:4px;">{u}</div>
                            </div>\"\"\", unsafe_allow_html=True)"""

if OLD4 in src:
    src = src.replace(OLD4, NEW4, 1)
    print("[OK] Fix 4: Validation metric cards updated")
    ok += 1
else:
    print("[!] Fix 4: not found")

# ── Fix 5: Summary section header ────────────────────────────────────────────
OLD5 = """                st.markdown(\"\"\"
                <div class="glass-panel">
                  <h4 style="font-size:1.15rem;margin:0 0 4px;">CALIBRATION vs VALIDATION SUMMARY</h4>
                </div>\"\"\", unsafe_allow_html=True)"""

NEW5 = """                st.markdown(\"\"\"
                <div class="glass-panel">
                  <h4 style="font-size:1.15rem;margin:0 0 4px;">📊 CALIBRATION vs VALIDATION SUMMARY</h4>
                  <p style="font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:#5a7090;margin:4px 0 0;">
                    Calibration = model accuracy on training data &nbsp;|&nbsp; Validation = accuracy on unseen data
                  </p>
                </div>\"\"\", unsafe_allow_html=True)"""

if OLD5 in src:
    src = src.replace(OLD5, NEW5, 1)
    print("[OK] Fix 5: Summary header updated")
    ok += 1
else:
    print("[!] Fix 5: not found")

# ── Fix 6: Summary metric cards ──────────────────────────────────────────────
OLD6 = """                sv1, sv2, sv3, sv4 = st.columns(4)
                for col, lbl, v, u, clr in [
                    (sv1, "CALIB RMSE", f"{calib_res['metrics']['RMSE_C']:.4f}", "C",  "#ff8800"),
                    (sv2, "VALID RMSE", f"{valid_res['metrics']['RMSE_C']:.4f}",  "C",  "#cc44ff"),
                    (sv3, "CALIB R2",   f"{calib_res['metrics']['R2']:.4f}",      "",   "#00c8ff"),
                    (sv4, "VALID R2",   f"{valid_res['metrics']['R2']:.4f}",      "",   "#00ff88"),
                ]:
                    with col:
                        st.markdown(f\"\"\"
                        <div style="background:rgba(255,255,255,0.97);border:2px solid {clr}44;
                                    border-radius:14px;padding:18px;text-align:center;margin-bottom:16px;">
                          <div style="font-family:'Orbitron',monospace;color:#5a7090;font-size:0.65rem;
                                      letter-spacing:0.18em;margin-bottom:8px;">{lbl}</div>
                          <div style="font-family:'Orbitron',monospace;color:{clr};font-size:1.8rem;
                                      font-weight:900;">{v}</div>
                          <div style="font-family:'Share Tech Mono',monospace;color:#8a9ab0;
                                      font-size:0.8rem;">{u}</div>
                        </div>\"\"\", unsafe_allow_html=True)"""

NEW6 = """                sv1, sv2, sv3, sv4 = st.columns(4)
                for col, lbl, sublbl, v, u, clr in [
                    (sv1, "Calibration RMSE", "(lower is better)", f"{calib_res['metrics']['RMSE_C']:.4f}", "°C", "#ff8800"),
                    (sv2, "Validation RMSE",  "(lower is better)", f"{valid_res['metrics']['RMSE_C']:.4f}",  "°C", "#cc44ff"),
                    (sv3, "Calibration R²",   "(1.0 = perfect)",   f"{calib_res['metrics']['R2']:.4f}",     "",   "#00c8ff"),
                    (sv4, "Validation R²",    "(1.0 = perfect)",   f"{valid_res['metrics']['R2']:.4f}",     "",   "#00ff88"),
                ]:
                    with col:
                        st.markdown(f\"\"\"
                        <div style="background:rgba(255,255,255,0.97);border:2px solid {clr}44;
                                    border-radius:14px;padding:18px;text-align:center;margin-bottom:16px;">
                          <div style="font-family:'Share Tech Mono',monospace;color:#5a7090;font-size:0.68rem;
                                      margin-bottom:2px;">{lbl}</div>
                          <div style="font-family:'Share Tech Mono',monospace;color:#aabbcc;font-size:0.60rem;
                                      margin-bottom:8px;">{sublbl}</div>
                          <div style="font-family:'Orbitron',monospace;color:{clr};font-size:1.8rem;
                                      font-weight:900;">{v}</div>
                          <div style="font-family:'Share Tech Mono',monospace;color:#8a9ab0;
                                      font-size:0.78rem;margin-top:4px;">{u}</div>
                        </div>\"\"\", unsafe_allow_html=True)"""

if OLD6 in src:
    src = src.replace(OLD6, NEW6, 1)
    print("[OK] Fix 6: Summary cards updated")
    ok += 1
else:
    print("[!] Fix 6: not found")

with open(APP, "w", encoding="utf-8") as f:
    f.write(src)

print(f"\n[{'DONE' if ok >= 5 else 'PARTIAL'}] {ok}/6 fixes applied")
if ok >= 5:
    print("Run: streamlit run app.py")
else:
    print("Some anchors not found — the code may have already been modified")