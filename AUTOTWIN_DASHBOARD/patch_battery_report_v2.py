"""
patch_battery_report_v2.py
==========================
Inserts the Battery Report tab (tab8) content just before the footer.
Run from your project folder: python patch_battery_report_v2.py
"""
import shutil

APP = "app.py"
shutil.copy2(APP, APP + ".report2_bak")

with open(APP, "r", encoding="utf-8") as f:
    src = f.read()

ANCHOR = """# ═══════════════════════════════════════════════════════════════

# FOOTER
# ═══════════════════════════════════════════════════════════════"""

TAB8_CONTENT = """# ═══════════════════════════════════════════════════════════════
# TAB 8 — BATTERY REPORT
# ═══════════════════════════════════════════════════════════════
with tab8:
    st.markdown(\"\"\"
    <div class="tab-header">
      <div class="tab-header-icon">🔋</div>
      <div>
        <p class="tab-header-title">BATTERY REPORT</p>
        <p class="tab-header-subtitle">simple · clear · actionable results</p>
      </div>
    </div>\"\"\", unsafe_allow_html=True)

    _rp_ecm     = st.session_state.get("ecm_results")
    _rp_thermal = st.session_state.get("thermal_results")

    if not _rp_ecm and not _rp_thermal:
        st.markdown(\"\"\"
        <div style="background:rgba(224,240,255,0.95);border:2px solid rgba(0,200,255,0.3);
                    border-radius:18px;padding:60px;text-align:center;margin-top:12px;">
          <div style="font-size:5rem;margin-bottom:1rem;">🔋</div>
          <div style="font-family:'Orbitron',monospace;color:#0066aa;font-size:1.1rem;font-weight:800;">
            NO RESULTS YET</div>
          <div style="font-family:'Share Tech Mono',monospace;color:#5a7090;font-size:0.88rem;margin-top:10px;">
            Go to <b>Models</b> tab → select ECM or Thermal → go to <b>Simulation</b> tab → run the model.<br>
            Your battery report will appear here automatically.
          </div>
        </div>\"\"\", unsafe_allow_html=True)

    else:
        # ── Calculate all report values ───────────────────────────────────────
        if _rp_ecm:
            soh           = round(100 - (1 - _rp_ecm["soc"][-1]) * 100 * 0.15, 1)
            r0_mohm       = _rp_ecm["params"]["R0_ohm"] * 1000
            ecm_r2        = _rp_ecm["metrics"]["R2"]
            final_soc     = round(_rp_ecm["soc"][-1] * 100, 1)
            final_voltage = round(_rp_ecm["V_measured"][-1], 3)
            ecm_rmse_mv   = round(_rp_ecm["metrics"]["RMSE_V"] * 1000, 2)
            model_accuracy= round(ecm_r2 * 100, 1)
        else:
            soh = r0_mohm = model_accuracy = final_soc = final_voltage = ecm_rmse_mv = None

        if _rp_thermal:
            T_amb  = _rp_thermal["T_amb"]
            T_list = _rp_thermal.get("T_measured", [])
            T_max  = round(max(T_list), 1) if T_list else None
            th_rmse= round(_rp_thermal["metrics"]["RMSE_C"], 2)
            th_r2  = round(_rp_thermal["metrics"]["R2"], 3)
        else:
            T_amb = T_max = th_rmse = th_r2 = None

        # ── SOH Status ────────────────────────────────────────────────────────
        if soh is not None:
            if soh >= 85:
                soh_label,soh_color,soh_bg,soh_border,soh_emoji = "EXCELLENT","#00ff88","rgba(0,255,136,0.08)","rgba(0,255,136,0.4)","✅"
                soh_msg = "Battery is in great condition. Safe for continued use."
            elif soh >= 75:
                soh_label,soh_color,soh_bg,soh_border,soh_emoji = "GOOD","#00c8ff","rgba(0,200,255,0.08)","rgba(0,200,255,0.4)","✅"
                soh_msg = "Battery is healthy. Minor degradation detected, no action needed."
            elif soh >= 60:
                soh_label,soh_color,soh_bg,soh_border,soh_emoji = "FAIR","#ffaa00","rgba(255,170,0,0.08)","rgba(255,170,0,0.4)","⚠️"
                soh_msg = "Battery showing wear. Plan for replacement in the near future."
            else:
                soh_label,soh_color,soh_bg,soh_border,soh_emoji = "POOR","#ff3366","rgba(255,51,102,0.08)","rgba(255,51,102,0.4)","🔴"
                soh_msg = "Battery significantly degraded. Replacement recommended soon."
        else:
            soh_label,soh_color,soh_bg,soh_border,soh_emoji = "—","#5a7090","rgba(90,112,144,0.06)","rgba(90,112,144,0.3)","—"
            soh_msg = "Run ECM simulation to get battery health data."

        # ── Thermal Risk ──────────────────────────────────────────────────────
        if T_max is not None:
            if T_max < 35:
                risk_label,risk_color,risk_bg,risk_border,risk_emoji = "SAFE","#00ff88","rgba(0,255,136,0.08)","rgba(0,255,136,0.4)","🟢"
                risk_msg = f"Maximum temperature {T_max}°C is well within safe limits. No thermal risk."
            elif T_max < 45:
                risk_label,risk_color,risk_bg,risk_border,risk_emoji = "MODERATE","#ffaa00","rgba(255,170,0,0.08)","rgba(255,170,0,0.4)","🟡"
                risk_msg = f"Maximum temperature {T_max}°C is acceptable but monitor under heavy load."
            else:
                risk_label,risk_color,risk_bg,risk_border,risk_emoji = "HIGH RISK","#ff3366","rgba(255,51,102,0.08)","rgba(255,51,102,0.4)","🔴"
                risk_msg = f"Maximum temperature {T_max}°C exceeds safe limits. Reduce load immediately."
        else:
            risk_label,risk_color,risk_bg,risk_border,risk_emoji = "—","#5a7090","rgba(90,112,144,0.06)","rgba(90,112,144,0.3)","—"
            risk_msg = "Run Thermal simulation to get temperature risk data."

        # ── Remaining Life ────────────────────────────────────────────────────
        if soh is not None:
            if soh >= 80:
                remaining_cycles = round((soh - 80) / 0.033)
                remaining_months = round(remaining_cycles / 30)
                if remaining_months >= 24:
                    life_str = f"{round(remaining_months/12, 1)} years"
                elif remaining_months >= 1:
                    life_str = f"{remaining_months} months"
                else:
                    life_str = "< 1 month"
                life_color = "#00ff88" if remaining_months > 12 else "#ffaa00"
                life_note  = f"Estimated {remaining_cycles} charge cycles remaining before reaching 80% health threshold"
            else:
                life_str   = "End of life"
                life_color = "#ff3366"
                life_note  = "Battery has passed the 80% health threshold — replacement recommended"
        else:
            life_str   = "—"
            life_color = "#5a7090"
            life_note  = "Run ECM simulation to estimate remaining life"

        # ── Model Reliability ─────────────────────────────────────────────────
        if model_accuracy is not None:
            if model_accuracy >= 95:
                rel_label = "HIGH CONFIDENCE"
                rel_color = "#00ff88"
                rel_note  = f"Model accuracy {model_accuracy}% — results are highly reliable"
            elif model_accuracy >= 85:
                rel_label = "GOOD CONFIDENCE"
                rel_color = "#00c8ff"
                rel_note  = f"Model accuracy {model_accuracy}% — results are reliable"
            else:
                rel_label = "MODERATE CONFIDENCE"
                rel_color = "#ffaa00"
                rel_note  = f"Model accuracy {model_accuracy}% — treat results as estimates"
        else:
            rel_label = "—"
            rel_color = "#5a7090"
            rel_note  = "Run ECM simulation first"

        # ── Overall Verdict ───────────────────────────────────────────────────
        if soh is not None and T_max is not None:
            if soh >= 75 and T_max < 45:
                verdict,verdict_color,verdict_bg,verdict_border,verdict_emoji = "BATTERY IS HEALTHY","#00ff88","linear-gradient(135deg,rgba(0,80,40,0.9),rgba(0,130,60,0.85))","#00ff88","✅"
                verdict_detail = "Both electrical performance and thermal behaviour are within acceptable ranges."
            elif soh < 60 or T_max >= 45:
                verdict,verdict_color,verdict_bg,verdict_border,verdict_emoji = "ACTION REQUIRED","#ff3366","linear-gradient(135deg,rgba(100,0,30,0.9),rgba(160,0,50,0.85))","#ff3366","🔴"
                verdict_detail = "Critical issues detected. Review battery health and temperature readings immediately."
            else:
                verdict,verdict_color,verdict_bg,verdict_border,verdict_emoji = "MONITOR CLOSELY","#ffaa00","linear-gradient(135deg,rgba(80,50,0,0.9),rgba(130,80,0,0.85))","#ffaa00","⚠️"
                verdict_detail = "Battery is functional but showing signs of wear. Schedule a maintenance check."
        elif soh is not None:
            verdict,verdict_color,verdict_bg,verdict_border,verdict_emoji = "ELECTRICAL CHECK DONE","#00c8ff","linear-gradient(135deg,rgba(0,50,90,0.9),rgba(0,80,130,0.85))","#00c8ff","⚡"
            verdict_detail = "ECM electrical model complete. Run Thermal model for full battery report."
        else:
            verdict,verdict_color,verdict_bg,verdict_border,verdict_emoji = "THERMAL CHECK DONE","#ff8800","linear-gradient(135deg,rgba(80,40,0,0.9),rgba(130,60,0,0.85))","#ff8800","🌡️"
            verdict_detail = "Thermal model complete. Run ECM electrical model for full battery report."

        # ── Big Verdict Card ──────────────────────────────────────────────────
        st.markdown(f\"\"\"
        <div style="background:{verdict_bg};border:3px solid {verdict_border};
                    border-radius:22px;padding:36px;text-align:center;margin-bottom:24px;
                    box-shadow:0 12px 48px {verdict_border}44;">
          <div style="font-size:3.5rem;margin-bottom:0.5rem;">{verdict_emoji}</div>
          <div style="font-family:'Orbitron',monospace;color:{verdict_color};font-size:1.8rem;
                      font-weight:900;letter-spacing:0.1em;text-shadow:0 0 32px {verdict_color}88;">
            {verdict}</div>
          <div style="font-family:'Share Tech Mono',monospace;color:rgba(255,255,255,0.75);
                      font-size:0.88rem;margin-top:10px;">{verdict_detail}</div>
        </div>\"\"\", unsafe_allow_html=True)

        # ── 4 Key Metric Cards ────────────────────────────────────────────────
        rc1, rc2, rc3, rc4 = st.columns(4, gap="medium")

        with rc1:
            st.markdown(f\"\"\"
            <div style="background:rgba(255,255,255,0.97);border:3px solid {soh_color}55;
                        border-radius:18px;padding:24px;text-align:center;
                        box-shadow:0 8px 32px {soh_color}22;margin-bottom:16px;min-height:220px;">
              <div style="font-size:2.2rem;margin-bottom:8px;">🔋</div>
              <div style="font-family:'Share Tech Mono',monospace;color:#5a7090;font-size:0.72rem;
                          letter-spacing:0.1em;margin-bottom:4px;">BATTERY HEALTH</div>
              <div style="font-family:'Orbitron',monospace;color:{soh_color};font-size:2.4rem;
                          font-weight:900;line-height:1;">{f"{soh}%" if soh is not None else "—"}</div>
              <div style="background:{soh_bg};border:1px solid {soh_border};border-radius:8px;
                          padding:4px 12px;margin:10px auto;display:inline-block;">
                <span style="font-family:'Orbitron',monospace;color:{soh_color};font-size:0.68rem;
                             font-weight:700;">{soh_emoji} {soh_label}</span></div>
              <div style="font-family:'Share Tech Mono',monospace;color:#5a7090;font-size:0.70rem;
                          margin-top:8px;line-height:1.4;">{soh_msg}</div>
            </div>\"\"\", unsafe_allow_html=True)

        with rc2:
            st.markdown(f\"\"\"
            <div style="background:rgba(255,255,255,0.97);border:3px solid {life_color}55;
                        border-radius:18px;padding:24px;text-align:center;
                        box-shadow:0 8px 32px {life_color}22;margin-bottom:16px;min-height:220px;">
              <div style="font-size:2.2rem;margin-bottom:8px;">⏳</div>
              <div style="font-family:'Share Tech Mono',monospace;color:#5a7090;font-size:0.72rem;
                          letter-spacing:0.1em;margin-bottom:4px;">ESTIMATED REMAINING LIFE</div>
              <div style="font-family:'Orbitron',monospace;color:{life_color};font-size:1.7rem;
                          font-weight:900;line-height:1.2;margin:8px 0;">{life_str}</div>
              <div style="font-family:'Share Tech Mono',monospace;color:#5a7090;font-size:0.68rem;
                          margin-top:10px;line-height:1.4;">{life_note}</div>
            </div>\"\"\", unsafe_allow_html=True)

        with rc3:
            st.markdown(f\"\"\"
            <div style="background:rgba(255,255,255,0.97);border:3px solid {risk_color}55;
                        border-radius:18px;padding:24px;text-align:center;
                        box-shadow:0 8px 32px {risk_color}22;margin-bottom:16px;min-height:220px;">
              <div style="font-size:2.2rem;margin-bottom:8px;">🌡️</div>
              <div style="font-family:'Share Tech Mono',monospace;color:#5a7090;font-size:0.72rem;
                          letter-spacing:0.1em;margin-bottom:4px;">THERMAL RISK</div>
              <div style="font-family:'Orbitron',monospace;color:{risk_color};font-size:2.0rem;
                          font-weight:900;line-height:1;">{f"{T_max}°C" if T_max is not None else "—"}</div>
              <div style="background:{risk_bg};border:1px solid {risk_border};border-radius:8px;
                          padding:4px 12px;margin:10px auto;display:inline-block;">
                <span style="font-family:'Orbitron',monospace;color:{risk_color};font-size:0.68rem;
                             font-weight:700;">{risk_emoji} {risk_label}</span></div>
              <div style="font-family:'Share Tech Mono',monospace;color:#5a7090;font-size:0.70rem;
                          margin-top:8px;line-height:1.4;">{risk_msg}</div>
            </div>\"\"\", unsafe_allow_html=True)

        with rc4:
            st.markdown(f\"\"\"
            <div style="background:rgba(255,255,255,0.97);border:3px solid {rel_color}55;
                        border-radius:18px;padding:24px;text-align:center;
                        box-shadow:0 8px 32px {rel_color}22;margin-bottom:16px;min-height:220px;">
              <div style="font-size:2.2rem;margin-bottom:8px;">📡</div>
              <div style="font-family:'Share Tech Mono',monospace;color:#5a7090;font-size:0.72rem;
                          letter-spacing:0.1em;margin-bottom:4px;">MODEL RELIABILITY</div>
              <div style="font-family:'Orbitron',monospace;color:{rel_color};font-size:2.0rem;
                          font-weight:900;line-height:1;">{f"{model_accuracy}%" if model_accuracy is not None else "—"}</div>
              <div style="font-family:'Share Tech Mono',monospace;color:#5a7090;font-size:0.70rem;
                          margin-top:10px;line-height:1.4;">{rel_label}<br><br>{rel_note}</div>
            </div>\"\"\", unsafe_allow_html=True)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # ── Detailed Measurements ─────────────────────────────────────────────
        st.markdown(\"\"\"
        <div class="glass-panel">
          <h4 style="font-size:1.1rem;margin:0;">📋 DETAILED MEASUREMENTS</h4>
          <p style="font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:#5a7090;margin:4px 0 0;">
            Key values from the simulation — what each number means in simple terms
          </p>
        </div>\"\"\", unsafe_allow_html=True)
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        detail_rows = []
        if _rp_ecm:
            detail_rows += [
                ("⚡", "Final Voltage",        f"{final_voltage} V",       "Voltage at end of test. A healthy 18650 should be above 2.5V.",                             "#00c8ff"),
                ("🔋", "Final Charge Level",   f"{final_soc}%",            "How much charge was left at the end of the discharge test.",                                "#ff8800"),
                ("🔩", "Internal Resistance",  f"{round(r0_mohm,2)} mΩ",   "Resistance inside the battery. Higher = more heat + less efficiency. New cell ~80mΩ.",     "#cc44ff"),
                ("📊", "ECM Model Accuracy",   f"{model_accuracy}%",       "How accurately the model predicted battery voltage. Above 95% is excellent.",               "#00ff88"),
            ]
        if _rp_thermal:
            detail_rows += [
                ("🌡️", "Max Temperature",      f"{T_max}°C",               "Highest temperature during the test. Safe limit for 18650 is below 45°C.",                 "#ff8800"),
                ("🌬️", "Ambient Temperature",  f"{T_amb}°C",               "Room temperature during the test. Batteries perform better at moderate temperatures.",      "#00c8ff"),
                ("📐", "Thermal Model Error",   f"{th_rmse}°C avg",         "Average difference between predicted and actual temperature. Below 1°C is very good.",      "#cc44ff"),
                ("🎯", "Thermal Model Fit",     f"{round(th_r2*100,1)}%",   "How well the thermal model explains temperature behaviour. Above 80% is good.",             "#00ff88"),
            ]

        for i in range(0, len(detail_rows), 2):
            row_cols = st.columns(2, gap="medium")
            for j, col in enumerate(row_cols):
                if i + j < len(detail_rows):
                    icon, name, val, explanation, clr = detail_rows[i+j]
                    with col:
                        st.markdown(f\"\"\"
                        <div style="background:rgba(255,255,255,0.97);border:2px solid {clr}33;
                                    border-radius:14px;padding:18px 20px;margin-bottom:12px;
                                    display:flex;gap:16px;align-items:flex-start;">
                          <div style="font-size:1.8rem;flex-shrink:0;">{icon}</div>
                          <div style="flex:1;">
                            <div style="font-family:'Orbitron',monospace;color:#0066aa;font-size:0.70rem;
                                        font-weight:700;letter-spacing:0.1em;margin-bottom:4px;">{name}</div>
                            <div style="font-family:'Orbitron',monospace;color:{clr};font-size:1.4rem;
                                        font-weight:900;margin-bottom:6px;">{val}</div>
                            <div style="font-family:'Share Tech Mono',monospace;color:#5a7090;
                                        font-size:0.72rem;line-height:1.5;">{explanation}</div>
                          </div>
                        </div>\"\"\", unsafe_allow_html=True)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # ── Plain English Summary ─────────────────────────────────────────────
        st.markdown(\"\"\"
        <div class="glass-panel">
          <h4 style="font-size:1.1rem;margin:0;">💬 PLAIN ENGLISH SUMMARY</h4>
          <p style="font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:#5a7090;margin:4px 0 0;">
            What all these results mean — explained simply
          </p>
        </div>\"\"\", unsafe_allow_html=True)

        summary_lines = []
        if soh is not None:
            if soh >= 85:
                summary_lines.append(f"✅ <b>Battery Health is {soh}%</b> — This battery is in excellent condition. It is holding charge well and performing as expected.")
            elif soh >= 75:
                summary_lines.append(f"✅ <b>Battery Health is {soh}%</b> — This battery is in good condition with minor wear. It can continue to be used normally without any concerns.")
            elif soh >= 60:
                summary_lines.append(f"⚠️ <b>Battery Health is {soh}%</b> — This battery has noticeable wear. It will not last as long on a full charge as it once did. Plan for replacement soon.")
            else:
                summary_lines.append(f"🔴 <b>Battery Health is {soh}%</b> — This battery is significantly degraded and should be replaced soon to avoid unexpected failures.")

        if soh is not None and soh >= 80:
            summary_lines.append(f"⏳ <b>Estimated remaining life is {life_str}</b> — Based on current health and typical usage, the battery should remain usable for approximately this long before needing replacement.")
        elif soh is not None:
            summary_lines.append(f"⏳ <b>Remaining life:</b> The battery has already passed the standard 80% health threshold used in industry as the end-of-life indicator. Replacement is recommended.")

        if T_max is not None:
            if T_max < 35:
                summary_lines.append(f"🌡️ <b>Temperature is safe at {T_max}°C maximum</b> — The battery stayed cool throughout the test. There is no thermal risk under normal operating conditions.")
            elif T_max < 45:
                summary_lines.append(f"🌡️ <b>Temperature reached {T_max}°C</b> — Within acceptable limits but worth monitoring. Avoid using at very high current loads for extended periods.")
            else:
                summary_lines.append(f"🔴 <b>Temperature reached {T_max}°C — this is too high</b> — The battery overheated. This can permanently damage the battery and poses a safety risk. Reduce the load or improve cooling.")

        if model_accuracy is not None:
            reliability_word = "highly reliable" if model_accuracy >= 95 else "reliable" if model_accuracy >= 85 else "reasonable estimates"
            summary_lines.append(f"📡 <b>These results are {rel_label.lower()}</b> — Our model predicted battery behaviour with {model_accuracy}% accuracy, meaning the health and life estimates above are {reliability_word}.")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        for line in summary_lines:
            st.markdown(f\"\"\"
            <div style="background:rgba(255,255,255,0.95);border-left:4px solid #00c8ff;
                        border-radius:0 12px 12px 0;padding:16px 20px;margin-bottom:10px;">
              <div style="font-family:'Share Tech Mono',monospace;color:#2a4060;font-size:0.85rem;
                          line-height:1.7;">{line}</div>
            </div>\"\"\", unsafe_allow_html=True)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown(\"\"\"
        <div style="background:rgba(0,200,255,0.05);border:2px solid rgba(0,200,255,0.25);
                    border-radius:16px;padding:20px 24px;">
          <div style="font-family:'Orbitron',monospace;color:#0066aa;font-size:0.78rem;
                      font-weight:700;letter-spacing:0.1em;margin-bottom:12px;">💡 WHAT TO DO NEXT</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
            <div style="font-family:'Share Tech Mono',monospace;color:#2a4060;font-size:0.78rem;">
              🔬 For deeper technical analysis → go to <b>Analytics</b> tab</div>
            <div style="font-family:'Share Tech Mono',monospace;color:#2a4060;font-size:0.78rem;">
              ⚙️ To see identified model parameters → go to <b>Parameters</b> tab</div>
            <div style="font-family:'Share Tech Mono',monospace;color:#2a4060;font-size:0.78rem;">
              🔄 To test a different battery file → go to <b>Simulation</b> tab</div>
            <div style="font-family:'Share Tech Mono',monospace;color:#2a4060;font-size:0.78rem;">
              📊 To compare ECM and Thermal results → go to <b>Compare</b> tab</div>
          </div>
        </div>\"\"\", unsafe_allow_html=True)

"""

if ANCHOR in src:
    src = src.replace(ANCHOR, TAB8_CONTENT + "\n" + ANCHOR, 1)
    print("[OK] Battery Report tab inserted before footer")
else:
    print("[!] Anchor not found — check the footer comment in app.py")

with open(APP, "w", encoding="utf-8") as f:
    f.write(src)

print("\nDone. Run: streamlit run app.py")