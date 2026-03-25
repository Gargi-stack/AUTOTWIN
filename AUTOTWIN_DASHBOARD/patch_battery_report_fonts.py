"""
patch_battery_report_fonts.py
==============================
Increases all font sizes in the Battery Report tab (both technical
and client side) so all text is clearly readable.

Run from your project folder: python patch_battery_report_fonts.py
"""
import re, shutil

APP = "app.py"
shutil.copy2(APP, APP + ".brf_bak")

with open(APP, "r", encoding="utf-8") as f:
    src = f.read()

ok = 0

# Each entry: (old_font_size, new_font_size, description)
# We target only the sizes that appear inside battery report sections
# by doing a global replacement of specific size strings in context

SIZE_CHANGES = [
    # Section headers / panel titles
    ("font-size:1.1rem;margin:0;\">📋 DETAILED MEASUREMENTS",
     "font-size:1.3rem;margin:0;\">📋 DETAILED MEASUREMENTS",
     "Detailed measurements header"),

    ("font-size:1.1rem;margin:0;\">💬 PLAIN ENGLISH SUMMARY",
     "font-size:1.3rem;margin:0;\">💬 PLAIN ENGLISH SUMMARY",
     "Plain English summary header"),

    # Verdict card
    ("font-size:1.8rem;\n                      font-weight:900;letter-spacing:0.1em;text-shadow:0 0 32px",
     "font-size:2.2rem;\n                      font-weight:900;letter-spacing:0.1em;text-shadow:0 0 32px",
     "Verdict card title font"),

    ("font-size:0.88rem;margin-top:10px;\">{verdict_detail}",
     "font-size:1.0rem;margin-top:10px;\">{verdict_detail}",
     "Verdict card detail text"),

    # Metric card labels (BATTERY HEALTH, REMAINING LIFE etc)
    ("font-size:0.72rem;\n                          letter-spacing:0.1em;margin-bottom:4px;\">BATTERY HEALTH",
     "font-size:0.88rem;\n                          letter-spacing:0.1em;margin-bottom:6px;\">BATTERY HEALTH",
     "Battery health label"),

    ("font-size:0.72rem;\n                          letter-spacing:0.1em;margin-bottom:4px;\">ESTIMATED REMAINING LIFE",
     "font-size:0.88rem;\n                          letter-spacing:0.1em;margin-bottom:6px;\">ESTIMATED REMAINING LIFE",
     "Remaining life label"),

    ("font-size:0.72rem;\n                          letter-spacing:0.1em;margin-bottom:4px;\">THERMAL RISK",
     "font-size:0.88rem;\n                          letter-spacing:0.1em;margin-bottom:6px;\">THERMAL RISK",
     "Thermal risk label"),

    ("font-size:0.72rem;\n                          letter-spacing:0.1em;margin-bottom:4px;\">MODEL RELIABILITY",
     "font-size:0.88rem;\n                          letter-spacing:0.1em;margin-bottom:6px;\">MODEL RELIABILITY",
     "Model reliability label"),

    # Metric card big values
    ("font-size:2.4rem;\n                          font-weight:900;line-height:1;\">{f\"{soh}%\"",
     "font-size:2.8rem;\n                          font-weight:900;line-height:1;\">{f\"{soh}%\"",
     "SOH big value"),

    ("font-size:1.7rem;\n                          font-weight:900;line-height:1.2;margin:8px 0;\">{life_str}",
     "font-size:2.2rem;\n                          font-weight:900;line-height:1.2;margin:8px 0;\">{life_str}",
     "Remaining life big value"),

    ("font-size:2.0rem;\n                          font-weight:900;line-height:1;\">{f\"{T_max}°C\"",
     "font-size:2.4rem;\n                          font-weight:900;line-height:1;\">{f\"{T_max}°C\"",
     "Thermal risk big value"),

    ("font-size:2.0rem;\n                          font-weight:900;line-height:1;\">{f\"{model_accuracy}%\"",
     "font-size:2.4rem;\n                          font-weight:900;line-height:1;\">{f\"{model_accuracy}%\"",
     "Model reliability big value"),

    # Metric card badge labels
    ("font-size:0.68rem;\n                             font-weight:700;\">{soh_emoji} {soh_label}",
     "font-size:0.82rem;\n                             font-weight:700;\">{soh_emoji} {soh_label}",
     "SOH badge label"),

    ("font-size:0.68rem;\n                             font-weight:700;\">{risk_emoji} {risk_label}",
     "font-size:0.82rem;\n                             font-weight:700;\">{risk_emoji} {risk_label}",
     "Risk badge label"),

    # Metric card note text
    ("font-size:0.70rem;\n                          margin-top:8px;line-height:1.4;\">{soh_msg}",
     "font-size:0.82rem;\n                          margin-top:8px;line-height:1.4;\">{soh_msg}",
     "SOH note text"),

    ("font-size:0.68rem;\n                          margin-top:10px;line-height:1.4;\">{life_note}",
     "font-size:0.82rem;\n                          margin-top:10px;line-height:1.4;\">{life_note}",
     "Life note text"),

    ("font-size:0.70rem;\n                          margin-top:8px;line-height:1.4;\">{risk_msg}",
     "font-size:0.82rem;\n                          margin-top:8px;line-height:1.4;\">{risk_msg}",
     "Risk note text"),

    ("font-size:0.70rem;\n                          margin-top:10px;line-height:1.4;\">{rel_label}",
     "font-size:0.82rem;\n                          margin-top:10px;line-height:1.4;\">{rel_label}",
     "Reliability note text"),

    # Detailed measurements — name label
    ("font-size:0.70rem;\n                                        font-weight:700;letter-spacing:0.1em;margin-bottom:4px;\">{name}",
     "font-size:0.84rem;\n                                        font-weight:700;letter-spacing:0.1em;margin-bottom:4px;\">{name}",
     "Detail card name"),

    # Detailed measurements — value
    ("font-size:1.4rem;\n                                        font-weight:900;margin-bottom:6px;\">{val}",
     "font-size:1.7rem;\n                                        font-weight:900;margin-bottom:6px;\">{val}",
     "Detail card value"),

    # Detailed measurements — explanation
    ("font-size:0.72rem;line-height:1.5;\">{explanation}",
     "font-size:0.84rem;line-height:1.6;\">{explanation}",
     "Detail card explanation"),

    # Plain English summary lines
    ("font-size:0.85rem;\n                          line-height:1.7;\">{line}",
     "font-size:0.96rem;\n                          line-height:1.8;\">{line}",
     "Summary line text (tab8)"),

    # What to do next section title
    ("font-size:0.78rem;\n                      font-weight:700;letter-spacing:0.1em;margin-bottom:12px;\">💡 WHAT TO DO NEXT",
     "font-size:0.92rem;\n                      font-weight:700;letter-spacing:0.1em;margin-bottom:12px;\">💡 WHAT TO DO NEXT",
     "What to do next title"),

    # What to do next items
    ("font-size:0.78rem;\">🔬 For deeper technical analysis",
     "font-size:0.90rem;\">🔬 For deeper technical analysis",
     "What to do next item 1"),
    ("font-size:0.78rem;\">⚙️ To see identified model parameters",
     "font-size:0.90rem;\">⚙️ To see identified model parameters",
     "What to do next item 2"),
    ("font-size:0.78rem;\">🔄 To test a different battery file",
     "font-size:0.90rem;\">🔄 To test a different battery file",
     "What to do next item 3"),
    ("font-size:0.78rem;\">📊 To compare ECM and Thermal results",
     "font-size:0.90rem;\">📊 To compare ECM and Thermal results",
     "What to do next item 4"),

    # Glass panel subtitle for battery report tab header
    ("font-size:0.72rem;color:#5a7090;margin:4px 0 0;\">\n            Key values from the simulation",
     "font-size:0.84rem;color:#5a7090;margin:4px 0 0;\">\n            Key values from the simulation",
     "Detailed measurements subtitle"),

    ("font-size:0.72rem;color:#5a7090;margin:4px 0 0;\">\n            What all these results mean",
     "font-size:0.84rem;color:#5a7090;margin:4px 0 0;\">\n            What all these results mean",
     "Plain english subtitle"),

    # CLIENT SIDE — same changes for client view
    # Client summary lines
    ("font-size:0.82rem;\n                          line-height:1.7;\">{line}",
     "font-size:0.96rem;\n                          line-height:1.8;\">{line}",
     "Client summary line text"),

    # Client plain english header
    ("font-size:0.82rem;\n                      font-weight:700;letter-spacing:0.1em;margin-bottom:14px;\">💬 PLAIN ENGLISH SUMMARY",
     "font-size:0.96rem;\n                      font-weight:700;letter-spacing:0.1em;margin-bottom:14px;\">💬 PLAIN ENGLISH SUMMARY",
     "Client plain english header"),

    # Client metric card labels
    ("font-size:0.70rem;letter-spacing:0.1em;margin-bottom:4px;\">{title}",
     "font-size:0.86rem;letter-spacing:0.1em;margin-bottom:6px;\">{title}",
     "Client metric card label"),

    # Client metric card big values
    ("font-size:2.2rem;\n                              font-weight:900;line-height:1;\">{val}",
     "font-size:2.8rem;\n                              font-weight:900;line-height:1;\">{val}",
     "Client metric card value"),

    # Client metric card notes
    ("font-size:0.68rem;\n                              margin-top:8px;line-height:1.4;\">{note}",
     "font-size:0.84rem;\n                              margin-top:8px;line-height:1.4;\">{note}",
     "Client metric card note"),

    # Client verdict card title
    ("font-size:1.8rem;\n                      font-weight:900;letter-spacing:0.1em;\">{verdict}",
     "font-size:2.2rem;\n                      font-weight:900;letter-spacing:0.1em;\">{verdict}",
     "Client verdict title"),

    # Client verdict detail
    ("font-size:0.88rem;margin-top:10px;\">{verdict_detail}</div>",
     "font-size:1.0rem;margin-top:10px;\">{verdict_detail}</div>",
     "Client verdict detail"),
]

for old, new, label in SIZE_CHANGES:
    if old in src:
        src = src.replace(old, new)
        print(f"[OK] {label}")
        ok += 1
    else:
        print(f"[skip] {label} — not found")

with open(APP, "w", encoding="utf-8") as f:
    f.write(src)

print(f"\n[DONE] {ok}/{len(SIZE_CHANGES)} font changes applied")
print("Run: streamlit run app.py")