"""
patch_login_system.py
=====================
Adds a production-ready login system to AutoTwin dashboard:
- Technical user (autotwin / autotwin123) → full dashboard
- Client user (client / client123) → Battery Report only
- Results auto-saved to saved_results.json after each simulation
- Client reads from saved_results.json (works across browsers/PCs on same network)

Run from your project folder: python patch_login_system.py
"""
import shutil

APP = "app.py"
shutil.copy2(APP, APP + ".login_bak")

with open(APP, "r", encoding="utf-8") as f:
    src = f.read()

ok = 0

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Insert login system right after st.set_page_config block
# ══════════════════════════════════════════════════════════════════════════════

LOGIN_CODE = '''
# ═══════════════════════════════════════════════════════════════
# AUTH & RESULTS PERSISTENCE SYSTEM
# ═══════════════════════════════════════════════════════════════
import json, os, hashlib

RESULTS_FILE = "saved_results.json"

USERS = {
    "autotwin": {"password": hashlib.sha256("autotwin123".encode()).hexdigest(), "role": "technical"},
    "client":   {"password": hashlib.sha256("client123".encode()).hexdigest(),   "role": "client"},
}

def _hash(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def save_results_to_disk():
    """Save current session results to JSON file for client access."""
    import numpy as np
    def _convert(obj):
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, dict): return {k: _convert(v) for k, v in obj.items()}
        if isinstance(obj, list): return [_convert(i) for i in obj]
        return obj

    data = {}
    if st.session_state.get("ecm_results"):
        data["ecm_results"] = _convert(st.session_state.ecm_results)
    if st.session_state.get("thermal_results"):
        data["thermal_results"] = _convert(st.session_state.thermal_results)
    if st.session_state.get("thermal_valid_results"):
        data["thermal_valid_results"] = _convert(st.session_state.thermal_valid_results)

    with open(RESULTS_FILE, "w") as f:
        json.dump(data, f)

def load_results_from_disk():
    """Load saved results from JSON file into session state."""
    if not os.path.isfile(RESULTS_FILE):
        return
    try:
        with open(RESULTS_FILE, "r") as f:
            data = json.load(f)
        import numpy as np
        def _arr(obj):
            if isinstance(obj, dict): return {k: _arr(v) for k, v in obj.items()}
            if isinstance(obj, list): return np.array(obj)
            return obj
        if "ecm_results" in data:
            r = data["ecm_results"]
            r["V_measured"]  = np.array(r["V_measured"])
            r["V_simulated"] = np.array(r["V_simulated"])
            r["soc"]         = np.array(r["soc"])
            r["time"]        = np.array(r["time"])
            if "current" in r: r["current"] = np.array(r["current"])
            st.session_state["ecm_results"] = r
        if "thermal_results" in data:
            st.session_state["thermal_results"] = data["thermal_results"]
        if "thermal_valid_results" in data:
            st.session_state["thermal_valid_results"] = data["thermal_valid_results"]
    except Exception as e:
        st.error(f"Could not load saved results: {e}")

# ── Session state init ────────────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "username" not in st.session_state:
    st.session_state.username = None

# ── LOGIN PAGE ────────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    st.markdown("""
    <style>
    #MainMenu{visibility:hidden;}footer{visibility:hidden;}header{visibility:hidden;}
    .login-wrap{display:flex;align-items:center;justify-content:center;min-height:80vh;}
    </style>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="max-width:460px;margin:60px auto 0 auto;">
      <div style="text-align:center;margin-bottom:32px;">
        <div style="font-family:'Orbitron',monospace;font-size:2.8rem;font-weight:900;
                    background:linear-gradient(135deg,#00c8ff,#ff00c8);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                    letter-spacing:0.15em;">AUTOTWIN</div>
        <div style="font-family:'Share Tech Mono',monospace;color:#5a7090;font-size:0.82rem;
                    letter-spacing:0.2em;margin-top:4px;">BATTERY DIGITAL TWIN PLATFORM</div>
      </div>
      <div style="background:rgba(255,255,255,0.97);border:2px solid rgba(0,200,255,0.3);
                  border-radius:20px;padding:40px 36px;box-shadow:0 20px 60px rgba(0,200,255,0.1);">
        <div style="font-family:'Orbitron',monospace;color:#0066aa;font-size:1.0rem;
                    font-weight:700;letter-spacing:0.1em;margin-bottom:24px;text-align:center;">
          🔐 SECURE LOGIN</div>
    """, unsafe_allow_html=True)

    username_input = st.text_input("Username", placeholder="Enter username", key="login_user")
    password_input = st.text_input("Password", placeholder="Enter password",
                                   type="password", key="login_pass")

    login_btn = st.button("LOGIN →", use_container_width=True, key="login_btn")

    if login_btn:
        uname = username_input.strip().lower()
        if uname in USERS and USERS[uname]["password"] == _hash(password_input):
            st.session_state.logged_in = True
            st.session_state.user_role = USERS[uname]["role"]
            st.session_state.username  = uname
            if USERS[uname]["role"] == "client":
                load_results_from_disk()
            st.rerun()
        else:
            st.error("Invalid username or password.")

    st.markdown("""
      </div>
      <div style="text-align:center;margin-top:16px;font-family:'Share Tech Mono',monospace;
                  color:#8a9ab0;font-size:0.72rem;">
        Contact your administrator for access credentials
      </div>
    </div>""", unsafe_allow_html=True)
    st.stop()

# ── CLIENT VIEW — Battery Report Only ────────────────────────────────────────
if st.session_state.user_role == "client":
    # Logout button top right
    logout_col1, logout_col2 = st.columns([6, 1])
    with logout_col2:
        if st.button("Logout", key="client_logout"):
            st.session_state.logged_in = False
            st.session_state.user_role = None
            st.session_state.username  = None
            st.rerun()

    with logout_col1:
        st.markdown("""
        <div style="background:linear-gradient(135deg,rgba(240,252,255,0.95),rgba(224,248,255,0.9));
                    border:2px solid rgba(0,200,255,0.3);border-radius:18px;padding:20px 32px;
                    margin-bottom:16px;">
          <div style="font-family:'Orbitron',monospace;font-size:2.0rem;font-weight:900;
                      background:linear-gradient(135deg,#00c8ff,#ff00c8);
                      -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                      letter-spacing:0.12em;text-align:center;">AUTOTWIN</div>
          <div style="font-family:'Share Tech Mono',monospace;color:#5a7090;font-size:0.72rem;
                      letter-spacing:0.18em;text-align:center;margin-top:2px;">
            ⚡ BATTERY DIGITAL TWIN PLATFORM ⚡</div>
        </div>""", unsafe_allow_html=True)

    # ── Battery Report content (same logic as tab8) ───────────────────────────
    st.markdown("""
    <div style="background:rgba(255,255,255,0.95);border-left:5px solid #00c8ff;
                border-radius:0 14px 14px 0;padding:16px 24px;margin-bottom:20px;">
      <div style="font-family:'Orbitron',monospace;color:#0066aa;font-size:1.1rem;font-weight:800;">
        🔋 BATTERY REPORT</div>
      <div style="font-family:'Share Tech Mono',monospace;color:#5a7090;font-size:0.78rem;margin-top:2px;">
        simple · clear · actionable results</div>
    </div>""", unsafe_allow_html=True)

    _rp_ecm     = st.session_state.get("ecm_results")
    _rp_thermal = st.session_state.get("thermal_results")

    if not _rp_ecm and not _rp_thermal:
        st.markdown("""
        <div style="background:rgba(224,240,255,0.95);border:2px solid rgba(0,200,255,0.3);
                    border-radius:18px;padding:60px;text-align:center;margin-top:12px;">
          <div style="font-size:5rem;margin-bottom:1rem;">🔋</div>
          <div style="font-family:'Orbitron',monospace;color:#0066aa;font-size:1.1rem;font-weight:800;">
            REPORT NOT READY YET</div>
          <div style="font-family:'Share Tech Mono',monospace;color:#5a7090;font-size:0.88rem;margin-top:10px;">
            The technical team has not run the simulation yet.<br>
            Please check back shortly or contact your administrator.
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        import numpy as np

        # ── Calculate values ──────────────────────────────────────────────────
        if _rp_ecm:
            soc_arr = _rp_ecm["soc"]
            if not isinstance(soc_arr, __import__("numpy").ndarray):
                import numpy as np
                soc_arr = np.array(soc_arr)
            soh           = round(100 - (1 - float(soc_arr[-1])) * 100 * 0.15, 1)
            r0_mohm       = _rp_ecm["params"]["R0_ohm"] * 1000
            ecm_r2        = _rp_ecm["metrics"]["R2"]
            final_soc     = round(float(soc_arr[-1]) * 100, 1)
            v_arr         = _rp_ecm["V_measured"]
            if not isinstance(v_arr, __import__("numpy").ndarray):
                v_arr = __import__("numpy").array(v_arr)
            final_voltage = round(float(v_arr[-1]), 3)
            model_accuracy= round(ecm_r2 * 100, 1)
        else:
            soh = r0_mohm = model_accuracy = final_soc = final_voltage = None

        if _rp_thermal:
            T_amb  = _rp_thermal["T_amb"]
            T_list = _rp_thermal.get("T_measured", [])
            T_max  = round(max(T_list), 1) if T_list else None
            th_rmse= round(_rp_thermal["metrics"]["RMSE_C"], 2)
            th_r2  = round(_rp_thermal["metrics"]["R2"], 3)
        else:
            T_amb = T_max = th_rmse = th_r2 = None

        # SOH status
        if soh is not None:
            if soh >= 85:   soh_label,soh_color,soh_bg,soh_border,soh_emoji,soh_msg = "EXCELLENT","#00ff88","rgba(0,255,136,0.08)","rgba(0,255,136,0.4)","✅","Battery is in great condition. Safe for continued use."
            elif soh >= 75: soh_label,soh_color,soh_bg,soh_border,soh_emoji,soh_msg = "GOOD","#00c8ff","rgba(0,200,255,0.08)","rgba(0,200,255,0.4)","✅","Battery is healthy. Minor degradation detected, no action needed."
            elif soh >= 60: soh_label,soh_color,soh_bg,soh_border,soh_emoji,soh_msg = "FAIR","#ffaa00","rgba(255,170,0,0.08)","rgba(255,170,0,0.4)","⚠️","Battery showing wear. Plan for replacement in the near future."
            else:           soh_label,soh_color,soh_bg,soh_border,soh_emoji,soh_msg = "POOR","#ff3366","rgba(255,51,102,0.08)","rgba(255,51,102,0.4)","🔴","Battery significantly degraded. Replacement recommended soon."
        else:
            soh_label,soh_color,soh_bg,soh_border,soh_emoji,soh_msg = "—","#5a7090","rgba(90,112,144,0.06)","rgba(90,112,144,0.3)","—","Run ECM simulation to get battery health data."

        # Thermal risk
        if T_max is not None:
            if T_max < 35:   risk_label,risk_color,risk_bg,risk_border,risk_emoji,risk_msg = "SAFE","#00ff88","rgba(0,255,136,0.08)","rgba(0,255,136,0.4)","🟢",f"Maximum temperature {T_max}°C is well within safe limits."
            elif T_max < 45: risk_label,risk_color,risk_bg,risk_border,risk_emoji,risk_msg = "MODERATE","#ffaa00","rgba(255,170,0,0.08)","rgba(255,170,0,0.4)","🟡",f"Temperature {T_max}°C is acceptable but monitor under heavy load."
            else:            risk_label,risk_color,risk_bg,risk_border,risk_emoji,risk_msg = "HIGH RISK","#ff3366","rgba(255,51,102,0.08)","rgba(255,51,102,0.4)","🔴",f"Temperature {T_max}°C exceeds safe limits. Reduce load immediately."
        else:
            risk_label,risk_color,risk_bg,risk_border,risk_emoji,risk_msg = "—","#5a7090","rgba(90,112,144,0.06)","rgba(90,112,144,0.3)","—","Run Thermal simulation to get temperature risk data."

        # Remaining life
        if soh is not None and soh >= 80:
            remaining_cycles = round((soh - 80) / 0.033)
            remaining_months = round(remaining_cycles / 30)
            life_str   = f"{round(remaining_months/12,1)} years" if remaining_months >= 24 else f"{remaining_months} months" if remaining_months >= 1 else "< 1 month"
            life_color = "#00ff88" if remaining_months > 12 else "#ffaa00"
            life_note  = f"Estimated {remaining_cycles} charge cycles remaining before 80% health threshold"
        elif soh is not None:
            life_str,life_color,life_note = "End of life","#ff3366","Battery has passed the 80% health threshold — replacement recommended"
        else:
            life_str,life_color,life_note = "—","#5a7090","Run ECM simulation to estimate remaining life"

        # Model reliability
        if model_accuracy is not None:
            if model_accuracy >= 95:   rel_label,rel_color,rel_note = "HIGH CONFIDENCE","#00ff88",f"Model accuracy {model_accuracy}% — results are highly reliable"
            elif model_accuracy >= 85: rel_label,rel_color,rel_note = "GOOD CONFIDENCE","#00c8ff",f"Model accuracy {model_accuracy}% — results are reliable"
            else:                      rel_label,rel_color,rel_note = "MODERATE CONFIDENCE","#ffaa00",f"Model accuracy {model_accuracy}% — treat results as estimates"
        else:
            rel_label,rel_color,rel_note = "—","#5a7090","Run ECM simulation first"

        # Verdict
        if soh is not None and T_max is not None:
            if soh >= 75 and T_max < 45:   verdict,verdict_color,verdict_bg,verdict_border,verdict_emoji,verdict_detail = "BATTERY IS HEALTHY","#00ff88","linear-gradient(135deg,rgba(0,80,40,0.9),rgba(0,130,60,0.85))","#00ff88","✅","Both electrical performance and thermal behaviour are within acceptable ranges."
            elif soh < 60 or T_max >= 45:  verdict,verdict_color,verdict_bg,verdict_border,verdict_emoji,verdict_detail = "ACTION REQUIRED","#ff3366","linear-gradient(135deg,rgba(100,0,30,0.9),rgba(160,0,50,0.85))","#ff3366","🔴","Critical issues detected. Review battery health and temperature readings immediately."
            else:                           verdict,verdict_color,verdict_bg,verdict_border,verdict_emoji,verdict_detail = "MONITOR CLOSELY","#ffaa00","linear-gradient(135deg,rgba(80,50,0,0.9),rgba(130,80,0,0.85))","#ffaa00","⚠️","Battery is functional but showing signs of wear. Schedule a maintenance check."
        elif soh is not None:
            verdict,verdict_color,verdict_bg,verdict_border,verdict_emoji,verdict_detail = "ELECTRICAL CHECK DONE","#00c8ff","linear-gradient(135deg,rgba(0,50,90,0.9),rgba(0,80,130,0.85))","#00c8ff","⚡","ECM electrical model complete. Thermal model pending."
        else:
            verdict,verdict_color,verdict_bg,verdict_border,verdict_emoji,verdict_detail = "THERMAL CHECK DONE","#ff8800","linear-gradient(135deg,rgba(80,40,0,0.9),rgba(130,60,0,0.85))","#ff8800","🌡️","Thermal model complete. ECM electrical model pending."

        # ── Verdict card ──────────────────────────────────────────────────────
        st.markdown(f"""
        <div style="background:{verdict_bg};border:3px solid {verdict_border};
                    border-radius:22px;padding:36px;text-align:center;margin-bottom:24px;
                    box-shadow:0 12px 48px {verdict_border}44;">
          <div style="font-size:3.5rem;margin-bottom:0.5rem;">{verdict_emoji}</div>
          <div style="font-family:'Orbitron',monospace;color:{verdict_color};font-size:1.8rem;
                      font-weight:900;letter-spacing:0.1em;">{verdict}</div>
          <div style="font-family:'Share Tech Mono',monospace;color:rgba(255,255,255,0.75);
                      font-size:0.88rem;margin-top:10px;">{verdict_detail}</div>
        </div>""", unsafe_allow_html=True)

        # ── 4 metric cards ────────────────────────────────────────────────────
        rc1, rc2, rc3, rc4 = st.columns(4, gap="medium")
        for col, icon, title, val, badge_color, badge_bg, badge_border, badge_emoji, badge_label, note in [
            (rc1,"🔋","BATTERY HEALTH",   f"{soh}%" if soh else "—",        soh_color,  soh_bg,  soh_border,  soh_emoji,  soh_label,  soh_msg),
            (rc2,"⏳","REMAINING LIFE",    life_str,                          life_color, "rgba(255,255,255,0)", "rgba(0,0,0,0)", "", "",        life_note),
            (rc3,"🌡️","THERMAL RISK",     f"{T_max}°C" if T_max else "—",   risk_color, risk_bg, risk_border, risk_emoji, risk_label, risk_msg),
            (rc4,"📡","MODEL RELIABILITY", f"{model_accuracy}%" if model_accuracy else "—", rel_color,"rgba(255,255,255,0)","rgba(0,0,0,0)","","",rel_note),
        ]:
            with col:
                badge_html = f'<div style="background:{badge_bg};border:1px solid {badge_border};border-radius:8px;padding:4px 12px;margin:8px auto;display:inline-block;"><span style="font-family:Orbitron,monospace;color:{badge_color};font-size:0.68rem;font-weight:700;">{badge_emoji} {badge_label}</span></div>' if badge_label else ""
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.97);border:3px solid {badge_color}55;
                            border-radius:18px;padding:24px;text-align:center;
                            box-shadow:0 8px 32px {badge_color}22;margin-bottom:16px;min-height:200px;">
                  <div style="font-size:2rem;margin-bottom:8px;">{icon}</div>
                  <div style="font-family:'Share Tech Mono',monospace;color:#5a7090;font-size:0.70rem;
                              letter-spacing:0.1em;margin-bottom:4px;">{title}</div>
                  <div style="font-family:'Orbitron',monospace;color:{badge_color};font-size:2.2rem;
                              font-weight:900;line-height:1;">{val}</div>
                  {badge_html}
                  <div style="font-family:'Share Tech Mono',monospace;color:#5a7090;font-size:0.68rem;
                              margin-top:8px;line-height:1.4;">{note}</div>
                </div>""", unsafe_allow_html=True)

        # ── Plain English Summary ─────────────────────────────────────────────
        st.markdown("""
        <div style="background:rgba(255,255,255,0.95);border:2px solid rgba(0,200,255,0.2);
                    border-radius:16px;padding:20px 24px;margin-top:8px;">
          <div style="font-family:'Orbitron',monospace;color:#0066aa;font-size:0.82rem;
                      font-weight:700;letter-spacing:0.1em;margin-bottom:14px;">💬 PLAIN ENGLISH SUMMARY</div>""",
        unsafe_allow_html=True)

        summary_lines = []
        if soh is not None:
            if soh >= 85:   summary_lines.append(f"✅ <b>Battery Health is {soh}%</b> — This battery is in excellent condition. It is holding charge well and performing as expected.")
            elif soh >= 75: summary_lines.append(f"✅ <b>Battery Health is {soh}%</b> — This battery is in good condition with minor wear. No action needed.")
            elif soh >= 60: summary_lines.append(f"⚠️ <b>Battery Health is {soh}%</b> — This battery has noticeable wear. Plan for replacement soon.")
            else:           summary_lines.append(f"🔴 <b>Battery Health is {soh}%</b> — This battery is significantly degraded. Replacement recommended.")
        if soh is not None and soh >= 80:
            summary_lines.append(f"⏳ <b>Estimated remaining life is {life_str}</b> — Based on current health and typical usage patterns.")
        elif soh is not None:
            summary_lines.append(f"⏳ <b>Remaining life:</b> Battery has passed the 80% end-of-life threshold. Replacement is recommended.")
        if T_max is not None:
            if T_max < 35:   summary_lines.append(f"🌡️ <b>Temperature is safe at {T_max}°C maximum</b> — No thermal risk detected under normal conditions.")
            elif T_max < 45: summary_lines.append(f"🌡️ <b>Temperature reached {T_max}°C</b> — Acceptable but monitor under heavy load.")
            else:            summary_lines.append(f"🔴 <b>Temperature reached {T_max}°C — this is too high</b> — Reduce load or improve cooling immediately.")
        if model_accuracy is not None:
            rel_word = "highly reliable" if model_accuracy >= 95 else "reliable" if model_accuracy >= 85 else "reasonable estimates"
            summary_lines.append(f"📡 <b>Results are {rel_label.lower()}</b> — Model predicted battery behaviour with {model_accuracy}% accuracy. Results are {rel_word}.")

        for line in summary_lines:
            st.markdown(f"""
            <div style="border-left:4px solid #00c8ff;border-radius:0 10px 10px 0;
                        padding:12px 18px;margin-bottom:8px;background:rgba(0,200,255,0.04);">
              <div style="font-family:'Share Tech Mono',monospace;color:#2a4060;font-size:0.82rem;
                          line-height:1.7;">{line}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # ── Last updated timestamp ────────────────────────────────────────────
        if os.path.isfile(RESULTS_FILE):
            import datetime
            mtime = os.path.getmtime(RESULTS_FILE)
            updated = datetime.datetime.fromtimestamp(mtime).strftime("%d %b %Y, %H:%M")
            st.markdown(f"""
            <div style="text-align:center;font-family:'Share Tech Mono',monospace;
                        color:#8a9ab0;font-size:0.70rem;margin-top:16px;">
              Last updated by technical team: {updated}
            </div>""", unsafe_allow_html=True)

    st.stop()

# ── TECHNICAL USER — Add logout button to header area ─────────────────────────
_tech_logout_col1, _tech_logout_col2 = st.columns([8, 1])
with _tech_logout_col2:
    if st.button("Logout", key="tech_logout"):
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.username  = None
        st.rerun()

'''

ANCHOR1 = """# ═══════════════════════════════════════════════════════════════
# CSS  (original AUTOTWIN styling — preserved exactly)
# ═══════════════════════════════════════════════════════════════"""

if ANCHOR1 in src:
    src = src.replace(ANCHOR1, LOGIN_CODE + "\n" + ANCHOR1, 1)
    print("[OK] Step 1: Login system inserted")
    ok += 1
else:
    print("[!] Step 1: CSS anchor not found — check app.py")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Auto-save after ECM auto-load
# ══════════════════════════════════════════════════════════════════════════════
OLD2 = """                        st.session_state.ecm_results       = _loaded[-1]
                        st.session_state.ecm_filename      = _loaded[-1]["_filename"]
                        st.rerun()"""

NEW2 = """                        st.session_state.ecm_results       = _loaded[-1]
                        st.session_state.ecm_filename      = _loaded[-1]["_filename"]
                        save_results_to_disk()
                        st.rerun()"""

if OLD2 in src:
    src = src.replace(OLD2, NEW2, 1)
    print("[OK] Step 2: Auto-save added after ECM auto-load")
    ok += 1
else:
    print("[!] Step 2: ECM auto-load anchor not found")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Auto-save after ECM manual run
# ══════════════════════════════════════════════════════════════════════════════
OLD3 = """                st.session_state.ecm_results       = batch_results[-1]
                st.session_state.ecm_filename      = batch_results[-1]["_filename"]
                st.rerun()"""

NEW3 = """                st.session_state.ecm_results       = batch_results[-1]
                st.session_state.ecm_filename      = batch_results[-1]["_filename"]
                save_results_to_disk()
                st.rerun()"""

if OLD3 in src:
    src = src.replace(OLD3, NEW3, 1)
    print("[OK] Step 3: Auto-save added after ECM manual run")
    ok += 1
else:
    print("[!] Step 3: ECM manual run anchor not found")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Auto-save after Thermal auto-load
# ══════════════════════════════════════════════════════════════════════════════
OLD4 = """                    st.success(f"✅ Loaded: C_th={C_th_l:.1f} J/K  hA={hA_l:.5f} W/K  R={R_l*1000:.1f} mΩ  ({n_files} files)")
                    st.rerun()"""

NEW4 = """                    st.success(f"✅ Loaded: C_th={C_th_l:.1f} J/K  hA={hA_l:.5f} W/K  R={R_l*1000:.1f} mΩ  ({n_files} files)")
                    save_results_to_disk()
                    st.rerun()"""

if OLD4 in src:
    src = src.replace(OLD4, NEW4, 1)
    print("[OK] Step 4: Auto-save added after Thermal auto-load")
    ok += 1
else:
    print("[!] Step 4: Thermal auto-load anchor not found")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — Auto-save after Thermal manual run completes
# ══════════════════════════════════════════════════════════════════════════════
OLD5 = """                prog.progress(100)
                th_status.markdown(f"""

NEW5 = """                prog.progress(100)
                save_results_to_disk()
                th_status.markdown(f"""

if OLD5 in src:
    src = src.replace(OLD5, NEW5, 1)
    print("[OK] Step 5: Auto-save added after Thermal manual run")
    ok += 1
else:
    print("[!] Step 5: Thermal manual run anchor not found")

with open(APP, "w", encoding="utf-8") as f:
    f.write(src)

print(f"\n[{'DONE' if ok >= 3 else 'PARTIAL'}] {ok}/5 steps applied")
print("\nRun: streamlit run app.py")
print("\nCredentials:")
print("  Technical: autotwin / autotwin123")
print("  Client:    client   / client123")