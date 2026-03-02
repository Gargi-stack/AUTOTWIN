"""
patch_remove_graphs.py
======================
Removes 4 unwanted graphs from the AutoTwin dashboard:
1. ECM Error Distribution histogram (Analytics tab)
2. Prediction Error graph (Simulation tab)
3. SOC graph (Simulation tab) — the whole ec1/ec2 columns block
4. Thermal Error Distribution histogram (Analytics tab)

Run from your project folder: python patch_remove_graphs.py
"""
import shutil

APP = "app.py"
shutil.copy2(APP, APP + ".graphs_bak")

with open(APP, "r", encoding="utf-8") as f:
    src = f.read()

ok = 0

# ── Fix 1: Remove ECM Error Distribution histogram (Analytics tab) ────────────
OLD1 = """        # Error histogram
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown(\"\"\"
        <div class="glass-panel">
          <h4 style="font-size:1.3rem;margin:0 0 4px;">📊 ERROR DISTRIBUTION — ECM RESIDUALS</h4>
          <p style="font-family:'Share Tech Mono',monospace;font-size:0.95rem;color:#5a7090;margin:0;letter-spacing:0.1em;">
            Histogram of voltage prediction errors (mV)
          </p>
        </div>\"\"\", unsafe_allow_html=True)
        err_mV = (res["V_measured"] - res["V_simulated"]) * 1000
        fig_hist = go.Figure(go.Histogram(x=err_mV, nbinsx=30,
            marker_color="#00c8ff", marker_line_color="rgba(0,200,255,0.5)", marker_line_width=1.5,
            opacity=0.85))
        fig_hist.add_vline(x=0, line=dict(color="#ff3366", width=2, dash="dash"))
        layout_h = cyber_plotly_layout(320)
        layout_h["xaxis"]["title"] = dict(text="ERROR (mV)", font=dict(family="Orbitron,monospace", size=13, color="#0066aa"))
        layout_h["yaxis"]["title"] = dict(text="COUNT", font=dict(family="Orbitron,monospace", size=13, color="#0066aa"))
        layout_h["showlegend"] = False
        fig_hist.update_layout(**layout_h)
        st.plotly_chart(fig_hist, use_container_width=True)"""

NEW1 = ""  # Just remove it entirely

if OLD1 in src:
    src = src.replace(OLD1, NEW1, 1)
    print("[OK] Fix 1: ECM Error Distribution histogram removed")
    ok += 1
else:
    print("[!] Fix 1: ECM Error Distribution not found — check anchor text")

# ── Fix 2+3: Remove Prediction Error + SOC columns block (Simulation tab) ─────
OLD2 = """            # ── Error + SOC side by side ────────────────────────────────────────
            ec1, ec2 = st.columns(2)
            with ec1:
                st.markdown(\"\"\"
                <div class="glass-panel" style="border-color:rgba(255,0,200,0.3);">
                  <h4 style="color:#cc0099;font-size:1.25rem;margin:0 0 4px;">⚠ PREDICTION ERROR</h4>
                  <p style="font-family:'Share Tech Mono',monospace;font-size:0.95rem;color:#5a7090;margin:0;letter-spacing:0.1em;">
                    Measured − Simulated (mV)
                  </p>
                </div>\"\"\", unsafe_allow_html=True)
                err_mV = (res["V_measured"] - res["V_simulated"]) * 1000
                fig_err = go.Figure()
                fig_err.add_trace(go.Scatter(x=res["time"], y=err_mV,
                    name="Error (mV)", line=dict(color="#ff00c8", width=1.8),
                    fill="tozeroy", fillcolor="rgba(255,0,200,0.08)", mode="lines"))
                fig_err.add_hline(y=0, line=dict(color="black", width=1, dash="dash"))
                layout_err = cyber_plotly_layout(320)
                layout_err["xaxis"]["title"] = dict(text="TIME (s)", font=dict(family="Orbitron,monospace", size=12))
                layout_err["yaxis"]["title"] = dict(text="ERROR (mV)", font=dict(family="Orbitron,monospace", size=12))
                layout_err["showlegend"] = False
                fig_err.update_layout(**layout_err)
                st.plotly_chart(fig_err, use_container_width=True)

            with ec2:
                st.markdown(\"\"\"
                <div class="glass-panel" style="border-color:rgba(0,255,136,0.3);">
                  <h4 style="color:#00aa55;font-size:1.25rem;margin:0 0 4px;">🔋 STATE OF CHARGE (SOC)</h4>
                  <p style="font-family:'Share Tech Mono',monospace;font-size:0.95rem;color:#5a7090;margin:0;letter-spacing:0.1em;">
                    Coulomb counting from discharge data
                  </p>
                </div>\"\"\", unsafe_allow_html=True)
                fig_soc = go.Figure()
                fig_soc.add_trace(go.Scatter(x=res["time"], y=soc*100,
                    name="SOC (%)", line=dict(color="#00ff88", width=2.5),
                    fill="tozeroy", fillcolor="rgba(0,255,136,0.08)", mode="lines"))
                layout_soc = cyber_plotly_layout(320)
                layout_soc["xaxis"]["title"] = dict(text="TIME (s)", font=dict(family="Orbitron,monospace", size=12))
                layout_soc["yaxis"]["title"] = dict(text="SOC (%)", font=dict(family="Orbitron,monospace", size=12))
                layout_soc["yaxis"]["range"]  = [-5, 105]
                layout_soc["showlegend"] = False
                fig_soc.update_layout(**layout_soc)
                st.plotly_chart(fig_soc, use_container_width=True)"""

NEW2 = ""  # Remove both graphs entirely

if OLD2 in src:
    src = src.replace(OLD2, NEW2, 1)
    print("[OK] Fix 2+3: Prediction Error and SOC graphs removed")
    ok += 1
else:
    print("[!] Fix 2+3: Prediction Error/SOC block not found — check anchor text")

# ── Fix 4: Remove Thermal Error Distribution histogram (Analytics tab) ─────────
OLD4 = """            # Error histogram
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            st.markdown(\"\"\"
            <div class="glass-panel">
              <h4 style="font-size:1.3rem;margin:0 0 4px;">&#x1F4CA; THERMAL ERROR DISTRIBUTION</h4>
              <p style="font-family:'Share Tech Mono',monospace;font-size:0.95rem;color:#5a7090;margin:0;letter-spacing:0.1em;">
                Histogram of temperature prediction errors (Celsius)
              </p>
            </div>\"\"\", unsafe_allow_html=True)
            err_th = np.array(_th_res["T_measured"]) - np.array(_th_res["T_predicted"])
            fig_th_hist = go.Figure(go.Histogram(
                x=err_th, nbinsx=30,
                marker_color="#ff8800",
                marker_line_color="rgba(255,136,0,0.5)", marker_line_width=1.5, opacity=0.85))
            fig_th_hist.add_vline(x=0, line=dict(color="#ff3366", width=2, dash="dash"))
            lay_hist = cyber_plotly_layout(320)
            lay_hist["xaxis"]["title"] = dict(text="ERROR (C)", font=dict(family="Orbitron,monospace", size=13, color="#0066aa"))
            lay_hist["yaxis"]["title"] = dict(text="COUNT", font=dict(family="Orbitron,monospace", size=13, color="#0066aa"))
            lay_hist["showlegend"] = False
            fig_th_hist.update_layout(**lay_hist)
            st.plotly_chart(fig_th_hist, use_container_width=True)"""

NEW4 = ""  # Remove entirely

if OLD4 in src:
    src = src.replace(OLD4, NEW4, 1)
    print("[OK] Fix 4: Thermal Error Distribution histogram removed")
    ok += 1
else:
    print("[!] Fix 4: Thermal Error Distribution not found — check anchor text")

with open(APP, "w", encoding="utf-8") as f:
    f.write(src)

print(f"\n[{'DONE' if ok == 3 else 'PARTIAL'}] {ok}/3 fixes applied")
print("Run: streamlit run app.py")