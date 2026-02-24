"""
AUTOTWIN Font Scaler
====================
Run this script in the same folder as your app.py:
    python scale_fonts.py

It will create app_scaled.py with ALL font sizes increased ~25-38%.
Review it, then rename to app.py when happy.
"""

import re
import shutil
import os

INPUT_FILE  = "app.py"
OUTPUT_FILE = "app_scaled.py"

# ── Font-size scaling map (rem values) ──────────────────────────────────────
# Each entry: original_value → new_value
# Small labels get a bigger boost; large display numbers get a smaller boost.
REM_MAP = {
    # Tiny labels (were barely readable)
    "0.62": "0.88",
    "0.65": "0.92",
    "0.68": "0.92",
    "0.70": "0.95",
    "0.72": "0.95",
    "0.75": "1.0",
    "0.78": "1.0",
    "0.80": "1.05",
    "0.82": "1.05",
    "0.84": "1.08",
    "0.85": "1.08",
    "0.88": "1.12",
    "0.90": "1.14",
    "0.92": "1.16",
    "0.95": "1.18",
    # Body / panel text
    "1.0":  "1.2",
    "1.05": "1.25",
    "1.1":  "1.3",
    "1.15": "1.35",
    "1.2":  "1.42",
    "1.25": "1.48",
    "1.3":  "1.55",
    "1.35": "1.6",
    "1.4":  "1.65",
    "1.5":  "1.75",
    "1.55": "1.82",
    "1.6":  "1.88",
    "1.65": "1.94",
    "1.8":  "2.1",
    "1.9":  "2.2",
    # Medium display numbers
    "2.0":  "2.3",
    "2.1":  "2.42",
    "2.2":  "2.52",
    "2.4":  "2.72",
    "2.6":  "2.9",
    "2.8":  "3.1",
    # Large display numbers
    "3.0":  "3.3",
    "3.2":  "3.5",
    "3.5":  "3.85",
    "3.8":  "4.15",
    # Hero/title sizes — slight bump only
    "4.2":  "4.55",
    "4.5":  "4.82",
}

# Also scale px font sizes (used in plotly dicts etc.)
PX_MAP = {
    "10": "12",
    "11": "13",
    "12": "14",
    "13": "15",
    "14": "16",
}


def scale_rem(match):
    """Replace font-size: Xrem with scaled value."""
    prefix = match.group(1)   # "font-size:" + optional space
    value  = match.group(2)   # numeric string e.g. "0.82"
    suffix = match.group(3)   # "rem"
    # Normalise: strip trailing zeros after decimal for lookup
    key = value.rstrip('0').rstrip('.') if '.' in value else value
    # Lookup; if not in map, scale by 1.25 and round to 2dp
    if key in REM_MAP:
        new_val = REM_MAP[key]
    else:
        new_val = f"{round(float(value) * 1.25, 2)}"
    return f"{prefix}{new_val}{suffix}"


def scale_px_in_dicts(content):
    """Scale font sizes given as integers inside Python dicts (e.g. size=12)."""
    def replacer(m):
        prefix = m.group(1)   # 'size='
        val    = m.group(2)   # digit string
        suffix = m.group(3)   # trailing char
        new_val = PX_MAP.get(val, val)
        return f"{prefix}{new_val}{suffix}"
    # Only match "size=<number>" patterns (Plotly font dicts)
    return re.sub(r'(size=)(\d{2})([\s,\)])', replacer, content)


def process(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"ERROR: {input_path} not found in current directory.")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # ── 1. Scale rem font sizes ──────────────────────────────────────────────
    # Matches: font-size: 0.82rem  OR  font-size:0.82rem
    content = re.sub(
        r'(font-size:\s*)(\d+\.?\d*)(rem)',
        scale_rem,
        content
    )

    # ── 2. Scale px font sizes inside Plotly/style dicts ────────────────────
    content = scale_px_in_dicts(content)

    # ── 3. Scale !important rem overrides (stButton, stDownloadButton etc.) ─
    # Already covered by step 1 since same pattern.

    # Count changes
    changed = sum(1 for a, b in zip(original, content) if a != b)
    print(f"✅ Done. Characters changed: {changed}")
    print(f"   Input : {input_path}")
    print(f"   Output: {output_path}")
    print()
    print("Next steps:")
    print("  1. Review app_scaled.py to confirm it looks right")
    print("  2. Back up your original: cp app.py app_backup.py")
    print("  3. Replace: mv app_scaled.py app.py")
    print("  4. Restart Streamlit: streamlit run app.py")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    process(INPUT_FILE, OUTPUT_FILE)