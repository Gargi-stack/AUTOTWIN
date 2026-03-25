"""
patch_remove_input_params.py
============================
Removes the INPUT PARAMETERS sliders section from the Parameters tab.
Keeps OUTPUT METRICS completely untouched.
Run from your project folder: python patch_remove_input_params.py
"""
import shutil

APP = "app.py"
shutil.copy2(APP, APP + ".inp_bak")

with open(APP, "r", encoding="utf-8") as f:
    src = f.read()

OLD = """# ═══════════════════════════════════════════════════════════════
# TAB 5 — PARAMETERS
# ═══════════════════════════════════════════════════════════════
with tab5:
    st.markdown(\"\"\"
    <div class="tab-header">
      <div class="tab-header-icon">⚙</div>
      <div>
        <p class="tab-header-title">SYSTEM PARAMETERS</p>
        <p class="tab-header-subtitle"> configure input parameters via interactive controls</p>
      </div>
    </div>\"\"\", unsafe_allow_html=True)

    # ── Model-aware notice ──────────────────────────────────────────────────
    _active = st.session_state.selected_model

    col1, col2 = st.columns([1,1])
    with col1:
        st.markdown(\"\"\"<div class="glass-panel"><h4 style="font-size:1.35rem;margin:0;">🎛 INPUT PARAMETERS</h4></div>\"\"\", unsafe_allow_html=True)
        for label, key, unit, color, desc, mn, mx, step in [
            ("⚡ STATE OF CHARGE (SOC)", "soc", "%", "#00c8ff", "current battery charge level", 0, 100, 1),
            ("🌡 TEMPERATURE", "temperature", "°C", "#ff8800", "operating temperature", 0, 60, 1),
            ("⚡ CURRENT LOAD", "current", "A", "#3366ff", "applied current", 0.0, 10.0, 0.1),
        ]:
            st.markdown(f\"\"\"
            <div class="param-box" style="background:linear-gradient(135deg,rgba(224,248,255,0.7),rgba(204,242,255,0.5));border:2px solid {color}44;">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                  <div class="param-title" style="color:#005f8a;">{label}</div>
                  <div class="param-desc" style="color:#5a7090;">{desc}</div>
                </div>
                <div class="param-value-badge" style="border-color:{color}55;box-shadow:0 0 16px {color}22;">
                  <span class="param-val" style="color:#00527a;">{st.session_state[key]}</span>
                  <span class="param-unit" style="color:#0088aa;">{unit}</span>
                </div>
              </div>
            </div>\"\"\", unsafe_allow_html=True)
            if step == 1 and isinstance(st.session_state[key], int):
                st.session_state[key] = st.slider(label, min_value=mn, max_value=mx, value=st.session_state[key], label_visibility="collapsed")
            else:
                st.session_state[key] = st.slider(label, min_value=float(mn), max_value=float(mx), value=float(st.session_state[key]), step=float(step), label_visibility="collapsed")
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    with col2:
        st.markdown(\"\"\"<div class="glass-panel"><h4 style="font-size:1.35rem;margin:0;">📊 OUTPUT METRICS</h4></div>\"\"\", unsafe_allow_html=True)"""

NEW = """# ═══════════════════════════════════════════════════════════════
# TAB 5 — PARAMETERS
# ═══════════════════════════════════════════════════════════════
with tab5:
    st.markdown(\"\"\"
    <div class="tab-header">
      <div class="tab-header-icon">⚙</div>
      <div>
        <p class="tab-header-title">MODEL PARAMETERS</p>
        <p class="tab-header-subtitle">identified parameters &amp; output metrics from simulation</p>
      </div>
    </div>\"\"\", unsafe_allow_html=True)

    # ── Model-aware notice ──────────────────────────────────────────────────
    _active = st.session_state.selected_model

    if True:
        st.markdown(\"\"\"<div class="glass-panel"><h4 style="font-size:1.35rem;margin:0;">📊 OUTPUT METRICS</h4></div>\"\"\", unsafe_allow_html=True)"""

if OLD in src:
    src = src.replace(OLD, NEW, 1)
    print("[OK] Input Parameters section removed, tab cleaned up")
else:
    print("[!] Anchor not found — check the code")

with open(APP, "w", encoding="utf-8") as f:
    f.write(src)

print("\nDone. Run: streamlit run app.py")