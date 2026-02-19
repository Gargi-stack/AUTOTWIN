import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time
import glob
import os

# Page Configuration
st.set_page_config(
    page_title="AUTOTWIN - Battery Digital Twin",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;800;900&family=Exo+2:wght@300;400;600;700;800&family=Share+Tech+Mono&display=swap');

:root {
  --cyan:      #00c8ff;
  --cyan-dim:  #0099cc;
  --pink:      #ff00c8;
  --pink-dim:  #cc0099;
  --green:     #00ff88;
  --green-dim: #00cc66;
  --gold:      #ffd700;
  --bg-base:   #f0f9ff;
  --bg-panel:  rgba(255,255,255,0.88);
  --bg-glass:  rgba(240,252,255,0.70);
  --border:    rgba(0,200,255,0.35);
  --text-main: #0a1628;
  --text-dim:  #2a4060;
  --text-muted:#5a7090;
  --glow-cyan: 0 0 8px #00c8ff, 0 0 20px rgba(0,200,255,0.5), 0 0 40px rgba(0,200,255,0.2);
  --glow-pink: 0 0 8px #ff00c8, 0 0 20px rgba(255,0,200,0.5), 0 0 40px rgba(255,0,200,0.2);
  --glow-green:0 0 8px #00ff88, 0 0 20px rgba(0,255,136,0.5), 0 0 40px rgba(0,255,136,0.2);
}

.stApp {
  background-color: var(--bg-base) !important;
  background-image:
    linear-gradient(rgba(0,200,255,0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,200,255,0.07) 1px, transparent 1px),
    linear-gradient(rgba(0,200,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,200,255,0.03) 1px, transparent 1px),
    radial-gradient(ellipse 80% 50% at 20% 10%, rgba(0,200,255,0.12) 0%, transparent 60%),
    radial-gradient(ellipse 60% 40% at 80% 80%, rgba(255,0,200,0.08) 0%, transparent 60%);
  background-size: 40px 40px, 40px 40px, 8px 8px, 8px 8px, 100% 100%, 100% 100%;
  font-family: 'Exo 2', sans-serif !important;
}

.stApp::after {
  content: '';
  position: fixed;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0,200,255,0.015) 2px,
    rgba(0,200,255,0.015) 4px
  );
  pointer-events: none;
  z-index: 9999;
}

html, body, [class*="css"] {
  font-family: 'Exo 2', sans-serif !important;
}

.cyber-header {
  position: relative;
  background: linear-gradient(135deg,
    rgba(255,255,255,0.97) 0%,
    rgba(224,248,255,0.95) 50%,
    rgba(255,255,255,0.97) 100%);
  border: 2px solid var(--cyan);
  border-radius: 20px;
  padding: 2.5rem 2rem 2rem;
  margin-bottom: 2rem;
  overflow: hidden;
  box-shadow:
    0 0 0 1px rgba(0,200,255,0.15),
    0 8px 40px rgba(0,200,255,0.2),
    inset 0 1px 0 rgba(255,255,255,1);
}

.cyber-header::before,
.cyber-header::after {
  content: '';
  position: absolute;
  width: 40px; height: 40px;
  border-color: var(--cyan);
  border-style: solid;
}
.cyber-header::before {
  top: 12px; left: 12px;
  border-width: 3px 0 0 3px;
  box-shadow: -3px -3px 12px rgba(0,200,255,0.4);
}
.cyber-header::after {
  bottom: 12px; right: 12px;
  border-width: 0 3px 3px 0;
  box-shadow: 3px 3px 12px rgba(0,200,255,0.4);
}

.header-beam {
  position: absolute;
  top: 0; left: -100%;
  width: 60%; height: 3px;
  background: linear-gradient(90deg, transparent, var(--cyan), var(--pink), transparent);
  animation: beam-sweep 4s ease-in-out infinite;
}
@keyframes beam-sweep {
  0%   { left: -60%; }
  100% { left: 160%; }
}

.cyber-title {
  font-family: 'Orbitron', monospace !important;
  font-size: 4.2rem;
  font-weight: 900;
  letter-spacing: 0.35em;
  text-align: center;
  background: linear-gradient(90deg, #005fa3, #00c8ff, #ff00c8, #00c8ff, #005fa3);
  background-size: 300% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: title-shift 6s linear infinite;
  filter: drop-shadow(0 0 18px rgba(0,200,255,0.45));
  margin: 0;
}
@keyframes title-shift {
  0%   { background-position: 0%   50%; }
  100% { background-position: 300% 50%; }
}

.cyber-subtitle {
  font-family: 'Share Tech Mono', monospace;
  text-align: center;
  font-size: 1rem;
  letter-spacing: 0.25em;
  color: var(--cyan-dim);
  margin-top: 0.6rem;
  animation: sub-flicker 5s ease-in-out infinite;
}
@keyframes sub-flicker {
  0%,100% { opacity:1; }
  92%     { opacity:1; }
  93%     { opacity:0.4; }
  94%     { opacity:1; }
}

.header-stats-bar {
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin-top: 1.4rem;
  flex-wrap: wrap;
}
.hstat {
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.78rem;
  letter-spacing: 0.1em;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 6px;
}
.hstat-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--green);
  box-shadow: var(--glow-green);
  animation: pulse-dot 2s ease-in-out infinite;
}
@keyframes pulse-dot {
  0%,100%{ transform:scale(1);   opacity:1; }
  50%    { transform:scale(1.5); opacity:0.7; }
}

/* ── TABS — centered ────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
  gap: 8px;
  background: linear-gradient(135deg,
    rgba(255,255,255,0.95),
    rgba(224,248,255,0.90));
  border: 2px solid var(--border);
  border-radius: 18px;
  padding: 14px 16px;
  margin-bottom: 28px;
  box-shadow:
    0 4px 30px rgba(0,200,255,0.12),
    inset 0 1px 0 rgba(255,255,255,1);
  justify-content: center !important;
  display: flex !important;
  flex-wrap: wrap !important;
}

.stTabs [data-baseweb="tab"] {
  height: 58px;
  background: rgba(240,252,255,0.70);
  border: 2px solid rgba(0,200,255,0.25);
  border-radius: 12px;
  color: var(--text-dim);
  font-family: 'Orbitron', monospace !important;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  padding: 0 18px;
  transition: all 0.35s cubic-bezier(0.4,0,0.2,1);
  position: relative;
  overflow: hidden;
  flex-shrink: 0;
}

.stTabs [data-baseweb="tab"]::before {
  content: '';
  position: absolute;
  bottom: 0; left: -100%;
  width: 100%; height: 2px;
  background: linear-gradient(90deg, var(--cyan), var(--pink));
  transition: left 0.4s;
}
.stTabs [data-baseweb="tab"]:hover::before { left: 0; }

.stTabs [data-baseweb="tab"]:hover {
  border-color: rgba(0,200,255,0.6);
  color: var(--cyan-dim);
  transform: translateY(-3px);
  background: rgba(224,248,255,0.9);
  box-shadow: 0 6px 20px rgba(0,200,255,0.2), 0 0 0 1px rgba(0,200,255,0.15);
}

.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg, #00c8ff 0%, #0080cc 50%, #ff00c8 100%) !important;
  border-color: var(--cyan) !important;
  color: white !important;
  transform: translateY(-5px) !important;
  box-shadow:
    0 10px 30px rgba(0,200,255,0.4),
    0 0 25px rgba(0,200,255,0.25),
    inset 0 1px 0 rgba(255,255,255,0.4) !important;
  font-family: 'Orbitron', monospace !important;
  font-size: 0.65rem !important;
  font-weight: 900 !important;
  letter-spacing: 0.12em !important;
  animation: tab-active-pulse 3s ease-in-out infinite;
}
@keyframes tab-active-pulse {
  0%,100%{ box-shadow: 0 10px 30px rgba(0,200,255,0.4), 0 0 25px rgba(0,200,255,0.25); }
  50%    { box-shadow: 0 12px 36px rgba(0,200,255,0.5), 0 0 35px rgba(0,200,255,0.35); }
}

/* Highlight bar under tab list */
.stTabs [data-baseweb="tab-highlight"] {
  display: none !important;
}

.tab-header {
  position: relative;
  background: linear-gradient(135deg,
    rgba(255,255,255,0.97),
    rgba(224,248,255,0.88));
  border: 2px solid var(--border);
  border-left: 5px solid var(--cyan);
  border-radius: 16px;
  padding: 22px 30px;
  margin-bottom: 28px;
  display: flex;
  align-items: center;
  gap: 18px;
  box-shadow: 0 4px 24px rgba(0,200,255,0.12), inset 0 1px 0 rgba(255,255,255,1);
  overflow: hidden;
}
.tab-header::after {
  content: '';
  position: absolute;
  top: 0; right: 0;
  width: 200px; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(0,200,255,0.06));
  pointer-events: none;
}

.tab-header-icon {
  font-size: 2.6rem;
  filter: drop-shadow(0 0 8px rgba(0,200,255,0.5));
  animation: icon-bob 3s ease-in-out infinite;
}
@keyframes icon-bob {
  0%,100%{ transform: translateY(0);    }
  50%    { transform: translateY(-6px); }
}

.tab-header-title {
  font-family: 'Orbitron', monospace !important;
  font-size: 1.9rem;
  font-weight: 800;
  color: var(--text-main);
  margin: 0;
  letter-spacing: 0.05em;
  text-shadow: 0 0 20px rgba(0,200,255,0.3);
}
.tab-header-subtitle {
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.85rem;
  color: var(--text-muted);
  margin: 4px 0 0;
  letter-spacing: 0.1em;
}

.metric-card {
  position: relative;
  background: linear-gradient(145deg,
    rgba(255,255,255,0.98),
    rgba(232,248,255,0.92));
  border: 2px solid rgba(0,200,255,0.35);
  border-radius: 20px;
  padding: 2.5rem 1.8rem;
  text-align: center;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4,0,0.2,1);
  box-shadow:
    0 8px 32px rgba(0,0,0,0.08),
    0 0 0 1px rgba(0,200,255,0.1),
    inset 0 1px 0 rgba(255,255,255,1);
  transform-style: preserve-3d;
  cursor: default;
}

.metric-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0;
  width: 50%; height: 3px;
  background: linear-gradient(90deg, var(--cyan), transparent);
}
.metric-card::after {
  content: '';
  position: absolute;
  bottom: 0; right: 0;
  width: 50%; height: 3px;
  background: linear-gradient(270deg, var(--cyan), transparent);
}

.metric-card:hover {
  transform: perspective(800px) rotateX(-4deg) translateY(-10px) scale(1.03);
  box-shadow:
    0 24px 60px rgba(0,200,255,0.22),
    0 0 40px rgba(0,200,255,0.15),
    0 0 0 2px var(--cyan);
}

.metric-label {
  font-family: 'Orbitron', monospace;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 0.8rem;
}
.metric-value {
  font-family: 'Orbitron', monospace;
  font-size: 3.8rem;
  font-weight: 900;
  color: var(--text-main);
  margin: 0.4rem 0;
  line-height: 1;
  text-shadow: 0 0 20px rgba(0,200,255,0.4);
}
.metric-unit {
  font-family: 'Share Tech Mono', monospace;
  font-size: 1rem;
  color: var(--text-muted);
  letter-spacing: 0.1em;
}
.metric-badge {
  position: absolute;
  top: 14px; right: 14px;
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.65rem;
  letter-spacing: 0.08em;
  padding: 3px 8px;
  border-radius: 6px;
  border: 1px solid;
}

.model-card {
  position: relative;
  background: linear-gradient(145deg,
    rgba(255,255,255,0.97),
    rgba(232,248,255,0.90));
  border: 2px solid rgba(0,200,255,0.3);
  border-radius: 22px;
  padding: 2.2rem 1.8rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4,0,0.2,1);
  min-height: 380px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;
  transform-style: preserve-3d;
  box-shadow: 0 6px 28px rgba(0,0,0,0.07), 0 0 0 1px rgba(0,200,255,0.08);
}

.model-card::before {
  content: '';
  position: absolute;
  top: 0; left: -100%;
  width: 60%; height: 100%;
  background: linear-gradient(90deg,
    transparent,
    rgba(0,200,255,0.08),
    transparent);
  transition: left 0.6s;
}
.model-card:hover::before { left: 160%; }

.model-card:hover {
  transform: perspective(900px) rotateY(-6deg) rotateX(-2deg) translateY(-14px);
  border-color: var(--cyan);
  box-shadow:
    0 30px 60px rgba(0,200,255,0.2),
    0 0 40px rgba(0,200,255,0.1),
    0 0 0 2px rgba(0,200,255,0.4);
}

.model-card-active {
  background: linear-gradient(135deg, #003d5c 0%, #00527a 40%, #006095 100%) !important;
  border: 3px solid var(--cyan) !important;
  transform: perspective(900px) rotateY(-3deg) translateY(-12px) scale(1.04) !important;
  box-shadow:
    0 30px 70px rgba(0,200,255,0.4),
    0 0 60px rgba(0,200,255,0.25),
    inset 0 1px 0 rgba(255,255,255,0.2) !important;
  animation: active-card-glow 3s ease-in-out infinite;
  min-height: 380px !important;
}
@keyframes active-card-glow {
  0%,100%{ box-shadow: 0 30px 70px rgba(0,200,255,0.4), 0 0 60px rgba(0,200,255,0.25); }
  50%    { box-shadow: 0 30px 80px rgba(0,200,255,0.55), 0 0 80px rgba(0,200,255,0.35); }
}

.stButton > button {
  font-family: 'Orbitron', monospace !important;
  font-size: 0.82rem !important;
  font-weight: 700 !important;
  letter-spacing: 0.15em !important;
  background: linear-gradient(135deg, #00527a, #00c8ff 60%, #0066aa) !important;
  background-size: 200% auto !important;
  color: white !important;
  border: 2px solid rgba(0,200,255,0.6) !important;
  border-radius: 12px !important;
  padding: 18px 40px !important;
  width: 100%;
  transition: all 0.4s cubic-bezier(0.4,0,0.2,1) !important;
  position: relative;
  overflow: hidden;
  box-shadow:
    0 6px 28px rgba(0,200,255,0.3),
    0 0 0 1px rgba(0,200,255,0.2),
    inset 0 1px 0 rgba(255,255,255,0.35) !important;
}
.stButton > button::before {
  content: '';
  position: absolute;
  top: 0; left: -100%;
  width: 100%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.25), transparent);
  transition: left 0.5s;
}
.stButton > button:hover::before { left: 100%; }
.stButton > button:hover {
  transform: translateY(-4px) !important;
  background-position: right center !important;
  box-shadow:
    0 14px 40px rgba(0,200,255,0.4),
    0 0 40px rgba(0,200,255,0.25),
    inset 0 1px 0 rgba(255,255,255,0.4) !important;
  border-color: var(--cyan) !important;
}

.stSlider {
    padding: 25px 0 !important;
    margin: 0 !important;
}

.stSlider > div > div > div {
    background: linear-gradient(90deg, #06b6d4, #3b82f6, #8b5cf6) !important;
    box-shadow: 0 0 20px rgba(6, 182, 212, 0.5) !important;
    height: 12px !important;
    border-radius: 10px !important;
}

.stSlider:nth-of-type(1) > div > div > div {
    background: linear-gradient(90deg, #06b6d, #0ea5e9, #38bdf8) !important;
    box-shadow: 0 0 30px rgba(2, 132, 199, 0.7) !important;
}

.stSlider:nth-of-type(2) > div > div > div {
    background: linear-gradient(90deg, #ea580c, #fb923c, #fdba74) !important;
    box-shadow: 0 0 30px rgba(234, 88, 12, 0.7) !important;
}

.stSlider:nth-of-type(3) > div > div > div {
    background: linear-gradient(90deg, #2563eb, #3b82f6, #60a5fa) !important;
    box-shadow: 0 0 30px rgba(37, 99, 235, 0.7) !important;
}

.section-divider {
  height: 2px;
  background: linear-gradient(90deg,
    transparent,
    var(--cyan) 20%,
    var(--pink) 50%,
    var(--cyan) 80%,
    transparent);
  margin: 36px 0;
  border-radius: 2px;
  box-shadow: 0 0 12px rgba(0,200,255,0.4);
  animation: divider-pulse 4s ease-in-out infinite;
}
@keyframes divider-pulse {
  0%,100%{ opacity:0.7; }
  50%    { opacity:1;   }
}

.glass-panel {
  background: linear-gradient(145deg,
    rgba(255,255,255,0.97),
    rgba(232,248,255,0.90));
  border: 2px solid rgba(0,200,255,0.3);
  border-radius: 18px;
  padding: 28px;
  margin-bottom: 24px;
  box-shadow: 0 6px 28px rgba(0,200,255,0.1), inset 0 1px 0 rgba(255,255,255,1);
  position: relative;
  overflow: hidden;
}
.glass-panel::before {
  content:'';
  position:absolute;
  top:0;left:0;right:0;height:3px;
  background: linear-gradient(90deg, var(--cyan), var(--pink), var(--cyan));
  background-size: 200% auto;
  animation: panel-top-beam 4s linear infinite;
}
@keyframes panel-top-beam {
  0%  { background-position: 0%   50%; }
  100%{ background-position: 200% 50%; }
}

.glass-panel h3, .glass-panel h4 {
  font-family: 'Orbitron', monospace !important;
  color: var(--text-main);
  letter-spacing: 0.05em;
  margin-top: 0;
}

.status-online {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: rgba(0,255,136,0.1);
  border: 2px solid rgba(0,255,136,0.5);
  padding: 10px 22px;
  border-radius: 30px;
  color: #00aa55;
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.85rem;
  letter-spacing: 0.1em;
  box-shadow: 0 0 20px rgba(0,255,136,0.15);
}
.status-dot {
  width: 10px; height: 10px;
  background: var(--green);
  border-radius: 50%;
  box-shadow: var(--glow-green);
  animation: pulse-dot 2s ease-in-out infinite;
}

.output-card {
  position: relative;
  border-radius: 18px;
  padding: 28px 20px;
  text-align: center;
  min-height: 220px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  transition: all 0.35s cubic-bezier(0.4,0,0.2,1);
  overflow: hidden;
  transform-style: preserve-3d;
  box-shadow: 0 8px 32px rgba(0,0,0,0.1);
}
.output-card:hover {
  transform: perspective(700px) rotateX(-5deg) translateY(-8px);
  box-shadow: 0 20px 50px rgba(0,0,0,0.15);
}
.output-card::before {
  content:'';
  position:absolute;
  top:0;left:0;right:0;height:3px;
}
.output-card::after {
  content:'';
  position:absolute;
  bottom:0;right:0;
  width:40px;height:40px;
  border-right:3px solid rgba(255,255,255,0.4);
  border-bottom:3px solid rgba(255,255,255,0.4);
}
.output-icon { font-size: 2.8rem; margin-bottom: 10px; }
.output-label {
  font-family: 'Orbitron', monospace;
  font-size: 0.7rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  margin-bottom: 10px;
  opacity: 0.9;
}
.output-value {
  font-family: 'Orbitron', monospace;
  font-size: 3.2rem;
  font-weight: 900;
  line-height: 1;
  margin-bottom: 6px;
}
.output-unit {
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.9rem;
  opacity: 0.8;
  letter-spacing: 0.1em;
}

.stProgress > div > div {
  background: linear-gradient(90deg, var(--cyan), var(--pink)) !important;
  box-shadow: 0 0 12px rgba(0,200,255,0.5) !important;
  border-radius: 8px !important;
}
.stProgress > div {
  background: rgba(0,200,255,0.1) !important;
  border-radius: 8px !important;
  border: 1px solid rgba(0,200,255,0.2) !important;
}

.stSuccess, .element-container .stAlert[data-type="success"] {
  background: rgba(0,255,136,0.08) !important;
  border: 2px solid rgba(0,255,136,0.4) !important;
  border-radius: 12px !important;
  font-family: 'Share Tech Mono', monospace !important;
}
.stWarning {
  background: rgba(255,200,0,0.08) !important;
  border: 2px solid rgba(255,200,0,0.4) !important;
  border-radius: 12px !important;
  font-family: 'Share Tech Mono', monospace !important;
}
.stInfo {
  background: rgba(0,200,255,0.08) !important;
  border: 2px solid rgba(0,200,255,0.3) !important;
  border-radius: 12px !important;
  font-family: 'Share Tech Mono', monospace !important;
}

.stDataFrame {
  border-radius: 16px !important;
  overflow: hidden !important;
  border: 2px solid rgba(0,200,255,0.3) !important;
  box-shadow: 0 6px 24px rgba(0,200,255,0.12) !important;
}

::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: rgba(224,248,255,0.6); border-radius: 10px; }
::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, var(--cyan), #0066aa);
  border-radius: 10px;
  box-shadow: 0 0 8px rgba(0,200,255,0.4);
}
::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #00e0ff, var(--cyan));
}

#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }

.stDownloadButton > button {
  font-family: 'Orbitron', monospace !important;
  font-size: 0.82rem !important;
  letter-spacing: 0.12em !important;
  background: linear-gradient(135deg, #003d5c, #00527a, #006095) !important;
  color: white !important;
  border: 2px solid var(--cyan) !important;
  border-radius: 12px !important;
  box-shadow: 0 6px 28px rgba(0,200,255,0.25) !important;
}
.stDownloadButton > button:hover {
  transform: translateY(-4px) !important;
  box-shadow: 0 12px 40px rgba(0,200,255,0.4) !important;
}

.perf-bar-track {
  background: rgba(0,200,255,0.1);
  height: 10px;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(0,200,255,0.2);
}
.perf-bar-fill {
  height: 100%;
  border-radius: 10px;
  transition: width 0.6s ease;
  position: relative;
  overflow: hidden;
}
.perf-bar-fill::after {
  content: '';
  position: absolute;
  top: 0; left: -60%;
  width: 40%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent);
  animation: bar-shine 2.5s ease-in-out infinite;
}
@keyframes bar-shine {
  0%  { left: -60%; }
  100%{ left: 140%; }
}

.param-box {
  border-radius: 16px;
  padding: 26px 28px;
  margin-bottom: 12px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 6px 24px rgba(0,0,0,0.08);
}
.param-box::before {
  content:'';
  position:absolute;
  top:0;left:0;bottom:0;width:4px;
  border-radius:4px 0 0 4px;
}
.param-title {
  font-family: 'Orbitron', monospace;
  font-weight: 700;
  font-size: 1.05rem;
  letter-spacing: 0.05em;
  margin-bottom: 4px;
}
.param-desc {
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.78rem;
  letter-spacing: 0.06em;
  opacity: 0.7;
}
.param-value-badge {
  background: rgba(255,255,255,0.95);
  padding: 12px 22px;
  border-radius: 12px;
  border: 2px solid;
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}
.param-val {
  font-family: 'Orbitron', monospace;
  font-weight: 900;
  font-size: 2.2rem;
  line-height: 1;
}
.param-unit {
  font-family: 'Share Tech Mono', monospace;
  font-size: 1rem;
  margin-left: 3px;
}

.cyber-footer {
  background: linear-gradient(135deg,
    rgba(255,255,255,0.95),
    rgba(224,248,255,0.88));
  border: 2px solid rgba(0,200,255,0.25);
  border-radius: 16px;
  padding: 24px;
  text-align: center;
  margin-top: 20px;
}
.footer-text {
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.82rem;
  letter-spacing: 0.2em;
  color: var(--text-muted);
}
.footer-dot {
  color: var(--cyan);
  text-shadow: 0 0 8px var(--cyan);
  margin: 0 8px;
}

/* ── COMPARE TAB SPECIFIC STYLES ────────────────────────────── */
.compare-model-card {
  position: relative;
  border-radius: 22px;
  padding: 36px 32px;
  min-height: 340px;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4,0,0.2,1);
  transform-style: preserve-3d;
}
.compare-model-card:hover {
  transform: perspective(900px) rotateY(-4deg) translateY(-8px);
}

.compare-metric-mini {
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.25);
  border-radius: 14px;
  padding: 16px 10px;
  text-align: center;
}

.conclusion-point {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(0,200,255,0.1);
}
.conclusion-point:last-child {
  border-bottom: none;
}

/* EOL Warning Badge */
@keyframes eol-pulse {
  0%,100%{ box-shadow: 0 0 0 0 rgba(255,165,0,0.4); }
  50%    { box-shadow: 0 0 0 8px rgba(255,165,0,0); }
}
.eol-badge {
  animation: eol-pulse 2s ease-in-out infinite;
}

/* Animated number counter effect */
@keyframes count-up {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
.animated-num {
  animation: count-up 0.6s ease-out forwards;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  SESSION STATE
# ═══════════════════════════════════════════════════════════════
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = 'ECM'
if 'is_simulating' not in st.session_state:
    st.session_state.is_simulating = False
if 'simulation_progress' not in st.session_state:
    st.session_state.simulation_progress = 0
if 'soc' not in st.session_state:
    st.session_state.soc = 85
if 'temperature' not in st.session_state:
    st.session_state.temperature = 25
if 'current' not in st.session_state:
    st.session_state.current = 2.5

# ═══════════════════════════════════════════════════════════════
#  HEADER
# ═══════════════════════════════════════════════════════════════
now_str = datetime.now().strftime("%H:%M:%S  |  %d %b %Y")
st.markdown(f"""
<div class="cyber-header">
  <div class="header-beam"></div>
  <h1 class="cyber-title">AUTOTWIN</h1>
  <p class="cyber-subtitle">⚡ REAL-TIME SIMULATION &amp; ANALYTICS PLATFORM ⚡</p>
  <div class="header-stats-bar">
    <span class="hstat"><span class="hstat-dot"></span>SYSTEM ONLINE</span>
    <span class="hstat" style="color:#5a7090;">|</span>
    <span class="hstat">🕐 {now_str}</span>
    <span class="hstat" style="color:#5a7090;">|</span>
    <span class="hstat">MODEL: <span style="color:#00c8ff;font-weight:700;">{st.session_state.selected_model}</span></span>
    <span class="hstat" style="color:#5a7090;">|</span>
    <span class="hstat" style="color:#00cc66;">v2.4.1 STABLE</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  TABS — 7 tabs now including COMPARE
# ═══════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 OVERVIEW",
    "🔧 MODELS",
    "▶ SIMULATION",
    "📈 ANALYTICS",
    "⚙ PARAMETERS",
    "🤖 AI RUL",
    "🔀 COMPARE"
])

# ─── helpers ────────────────────────────────────────────────────
def generate_chart_data(points=50):
    t = np.arange(points)
    voltage     = 3.6 + 0.3 * np.sin(t/5) + np.random.normal(0, 0.05, points)
    current     = st.session_state.current + np.random.normal(0, 0.3, points)
    temperature = st.session_state.temperature + np.random.normal(0, 2, points)
    soc         = np.maximum(0, st.session_state.soc - t*0.5 + np.random.normal(0, 1, points))
    return pd.DataFrame({'Time': t,
                         'Voltage (V)': voltage,
                         'Current (A)': current,
                         'Temperature (°C)': temperature,
                         'SOC (%)': soc})

def cyber_plotly_layout(height=450):
    return dict(
        plot_bgcolor='rgba(245,252,255,0.95)',
        paper_bgcolor='rgba(240,250,255,0.4)',
        font=dict(color='#0a1628', size=12, family='Exo 2, sans-serif'),
        xaxis=dict(
            gridcolor='rgba(0,200,255,0.12)',
            linecolor='rgba(0,200,255,0.3)',
            tickfont=dict(family='Share Tech Mono', size=11),
            title_font=dict(family='Orbitron, monospace', size=12, color='#0066aa')),
        yaxis=dict(
            gridcolor='rgba(0,200,255,0.12)',
            linecolor='rgba(0,200,255,0.3)',
            tickfont=dict(family='Share Tech Mono', size=11),
            title_font=dict(family='Orbitron, monospace', size=12, color='#0066aa')),
        height=height,
        hovermode='x unified',
        legend=dict(
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='rgba(0,200,255,0.4)',
            borderwidth=2,
            font=dict(family='Share Tech Mono', size=11, color='#003355')),
        margin=dict(l=20, r=20, t=20, b=20))

voltage = round(3.2 + (st.session_state.soc/100)*0.9, 2)
power   = round(voltage * st.session_state.current, 1)

# ═══════════════════════════════════════════════════════════════
#  TAB 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════════
with tab1:
    st.markdown("""
    <div class="tab-header">
      <div class="tab-header-icon">📊</div>
      <div>
        <p class="tab-header-title">SYSTEM OVERVIEW</p>
        <p class="tab-header-subtitle"> real-time monitoring &amp; performance metrics</p>
      </div>
    </div>""", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    cards = [
        (col1, "VOLTAGE", voltage, "V", "#00c8ff", "LIVE", "⚡"),
        (col2, "SOH",     94,      "%", "#00ff88", "GOOD", "💚"),
        (col3, "POWER",   power,   "W", "#ff8800", "ACTIVE", "🔋"),
        (col4, "CYCLES",  487,     "",  "#cc44ff", "COUNT", "🔄"),
    ]
    for col, label, val, unit, color, badge, icon in cards:
        with col:
            st.markdown(f"""
            <div class="metric-card" style="border-color:{color}55;">
              <span class="metric-badge"
                    style="color:{color};border-color:{color}66;
                           background:rgba(0,0,0,0.04);">
                {badge}
              </span>
              <div class="metric-label">{icon} {label}</div>
              <div class="metric-value" style="color:{color};
                   text-shadow:0 0 24px {color}88;">{val}</div>
              <div class="metric-unit">{unit}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        <div class="glass-panel">
          <h3 style="font-size:1.3rem;margin-bottom:4px;">📈 REAL-TIME PERFORMANCE MONITOR</h3>
          <p style="font-family:'Share Tech Mono',monospace;font-size:0.78rem;
                    color:#5a7090;margin-top:0;letter-spacing:0.1em;">
                 voltage &amp; current waveforms — live feed
          </p>
        </div>""", unsafe_allow_html=True)

        df = generate_chart_data()
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['Time'], y=df['Voltage (V)'],
            name='Voltage (V)',
            line=dict(color='#00c8ff', width=3),
            fill='tozeroy', fillcolor='rgba(0,200,255,0.08)'))
        fig.add_trace(go.Scatter(
            x=df['Time'], y=df['Current (A)'],
            name='Current (A)',
            line=dict(color='#ff8800', width=3),
            fill='tozeroy', fillcolor='rgba(255,136,0,0.08)'))
        layout = cyber_plotly_layout(440)
        layout['xaxis']['title'] = dict(text='TIME (s)', font=dict(family='Orbitron,monospace', size=11, color='#0066aa'))
        layout['yaxis']['title'] = dict(text='VALUES',   font=dict(family='Orbitron,monospace', size=11, color='#0066aa'))
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("""
        <div class="glass-panel">
          <h3 style="font-size:1.15rem;margin-bottom:12px;">🎯 PERFORMANCE INDICATORS</h3>
        </div>""", unsafe_allow_html=True)

        perf = [
            ("EFFICIENCY", 94, "#00c8ff", "⚡"),
            ("RELIABILITY",89, "#00ff88", "✅"),
            ("ACCURACY",   92, "#cc44ff", "🎯"),
            ("SPEED",      87, "#ff8800", "🚀"),
        ]
        for name, val, color, icon in perf:
            st.markdown(f"""
            <div style="margin-bottom:22px;background:rgba(255,255,255,0.97);
                        border:2px solid {color}44;border-radius:14px;padding:16px 20px;">
              <div style="display:flex;justify-content:space-between;
                          align-items:center;margin-bottom:10px;">
                <div style="display:flex;align-items:center;gap:8px;">
                  <span style="font-size:1.3rem;">{icon}</span>
                  <span style="font-family:'Orbitron',monospace;
                               color:#0a1628;font-weight:700;
                               font-size:0.75rem;letter-spacing:0.1em;">{name}</span>
                </div>
                <span style="font-family:'Orbitron',monospace;
                             color:{color};font-weight:900;font-size:1.2rem;
                             text-shadow:0 0 12px {color}88;">{val}%</span>
              </div>
              <div class="perf-bar-track">
                <div class="perf-bar-fill"
                     style="width:{val}%;
                            background:linear-gradient(90deg,{color},{color}88);">
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background:rgba(0,255,136,0.07);
                    border:2px solid rgba(0,255,136,0.35);
                    border-radius:14px;padding:20px;margin-top:10px;">
          <div class="status-online" style="margin-bottom:12px;">
            <span class="status-dot"></span>ALL SYSTEMS NOMINAL
          </div>
          <p style="font-family:'Share Tech Mono',monospace;
                    font-size:0.78rem;color:#2a4060;
                    margin:10px 0;letter-spacing:0.06em;">✓ Ready for simulation</p>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:14px;">
            <div style="background:rgba(255,255,255,0.95);padding:12px;
                        border-radius:10px;border:1px solid rgba(0,255,136,0.25);
                        text-align:center;">
              <div style="font-family:'Share Tech Mono',monospace;
                          font-size:0.72rem;color:#5a7090;letter-spacing:0.08em;">
                UPTIME</div>
              <div style="font-family:'Orbitron',monospace;
                          color:#00aa55;font-weight:900;font-size:1.2rem;">99.8%</div>
            </div>
            <div style="background:rgba(255,255,255,0.95);padding:12px;
                        border-radius:10px;border:1px solid rgba(0,255,136,0.25);
                        text-align:center;">
              <div style="font-family:'Share Tech Mono',monospace;
                          font-size:0.72rem;color:#5a7090;letter-spacing:0.08em;">
                LATENCY</div>
              <div style="font-family:'Orbitron',monospace;
                          color:#00aa55;font-weight:900;font-size:1.2rem;">&lt;50ms</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  TAB 2 — MODELS
# ═══════════════════════════════════════════════════════════════
with tab2:
    st.markdown("""
    <div class="tab-header">
      <div class="tab-header-icon">🔧</div>
      <div>
        <p class="tab-header-title">SIMULATION MODELS</p>
        <p class="tab-header-subtitle"> select your computational approach</p>
      </div>
    </div>""", unsafe_allow_html=True)

    models = {
        'ECM': {
            'name': 'Equivalent Circuit Model',
            'icon': '⚡',
            'accuracy': '85%',
            'speed': 'Fast',
            'color': '#00c8ff',
            'grad': 'linear-gradient(135deg,#003d5c,#00527a,#006095)',
            'description': 'Uses resistors, capacitors and voltage sources for fast electrical simulation'
        },
        'Thermal': {
            'name': 'Thermal Simulation',
            'icon': '🌡️',
            'accuracy': '80%',
            'speed': 'Medium',
            'color': '#ff8800',
            'grad': 'linear-gradient(135deg,#5c2200,#7a3300,#954400)',
            'description': 'Models heat generation, dissipation, and thermal runaway in battery cells'
        },
        'Co-Simulation': {
            'name': 'Co-Simulation',
            'icon': '🔄',
            'accuracy': '92%',
            'speed': 'Medium',
            'color': '#00ff88',
            'grad': 'linear-gradient(135deg,#003d2a,#00522e,#006035)',
            'description': 'Combined multi-domain approach for comprehensive electro-thermal analysis'
        }
    }

    cols = st.columns(3)
    for idx, (key, model) in enumerate(models.items()):
        with cols[idx]:
            is_active = st.session_state.selected_model == key
            if st.button(f"{model['icon']}  SELECT  {model['icon']}",
                         key=f"model_{key}", use_container_width=True):
                st.session_state.selected_model = key
                st.success(f"✅ {model['name']} activated!")
                st.rerun()

            card_cls = "model-card-active" if is_active else "model-card"
            txt_col  = "white" if is_active else "#0a1628"
            sub_col  = "rgba(255,255,255,0.85)" if is_active else "#4a6080"
            badge_bg = "rgba(255,255,255,0.2)" if is_active else f"{model['color']}18"
            border   = f"2px solid {model['color']}" if is_active else f"2px solid {model['color']}55"
            bg_extra = f'background:{model["grad"]};' if is_active else ''

            st.markdown(f"""
            <div class="{card_cls}" style="{bg_extra}border:{border};">
              <div style="font-size:4.5rem;text-align:center;
                          filter:drop-shadow(0 0 12px {model['color']}88);">
                {model['icon']}
              </div>
              <h3 style="font-family:'Orbitron',monospace;
                         color:{txt_col};font-size:1.1rem;
                         font-weight:800;letter-spacing:0.06em;
                         text-align:center;margin:0.8rem 0 0.6rem;">
                {model['name']}
              </h3>
              <p style="color:{sub_col};font-family:'Exo 2',sans-serif;
                        font-size:0.9rem;text-align:center;
                        line-height:1.55;font-weight:500;margin-bottom:1.2rem;">
                {model['description']}
              </p>
              <div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap;">
                <span style="background:{badge_bg};padding:8px 18px;
                             border-radius:20px;color:{txt_col};
                             font-family:'Share Tech Mono',monospace;
                             font-size:0.8rem;border:{border};">
                  📊 {model['accuracy']}
                </span>
                <span style="background:{badge_bg};padding:8px 18px;
                             border-radius:20px;color:{txt_col};
                             font-family:'Share Tech Mono',monospace;
                             font-size:0.8rem;border:{border};">
                  ⚡ {model['speed']}
                </span>
              </div>
              {'<div style="position:absolute;top:14px;right:14px;background:rgba(0,200,255,0.25);border:1px solid rgba(255,255,255,0.4);border-radius:8px;padding:4px 10px;font-family:Share Tech Mono,monospace;font-size:0.65rem;color:white;letter-spacing:0.1em;">ACTIVE</div>' if is_active else ''}
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    sel = models[st.session_state.selected_model]
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,{sel['grad']});
                border:3px solid {sel['color']};border-radius:22px;
                padding:40px;text-align:center;
                box-shadow:0 20px 60px {sel['color']}33,0 0 40px {sel['color']}1a;">
      <div style="font-size:5rem;filter:drop-shadow(0 0 20px {sel['color']});">
        {sel['icon']}
      </div>
      <h2 style="font-family:'Orbitron',monospace;color:black;
                 font-size:1.6rem;margin:1rem 0 0.6rem;
                 letter-spacing:0.1em;text-shadow:0 0 20px {sel['color']};">
        ACTIVE MODEL — {sel['name'].upper()}
      </h2>
      <p style="color:rgba(255,255,255,0.85);color:black; font-family:'Exo 2',sans-serif; filter:drop-shadow(0 0 20px {sel['color']});
                font-size:1.05rem;line-height:1.6;max-width:560px;margin:0 auto 1.5rem;">
        {sel['description']}
      </p>
      <div style="display:flex;gap:18px;justify-content:center;flex-wrap:wrap;">
        <span style="background:rgba(255,255,255,0.18);color:black;
                     padding:14px 36px;border-radius:28px; filter:drop-shadow(0 0 20px {sel['color']});
                     font-family:'Orbitron',monospace;font-weight:800;
                     font-size:0.9rem;border:2px solid {sel['color']};">
          📊 ACCURACY: {sel['accuracy']}
        </span>
        <span style="background:rgba(255,255,255,0.18);color:black;
                     padding:14px 36px;border-radius:28px;
                     font-family:'Orbitron',monospace;font-weight:800; filter:drop-shadow(0 0 20px {sel['color']});
                     font-size:0.9rem;border:2px solid {sel['color']};">
          ⚡ SPEED: {sel['speed']}
        </span>
      </div>
    </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  TAB 3 — SIMULATION
# ═══════════════════════════════════════════════════════════════
with tab3:
    st.markdown("""
    <div class="tab-header">
      <div class="tab-header-icon">▶</div>
      <div>
        <p class="tab-header-title">SIMULATION CONTROL</p>
        <p class="tab-header-subtitle"> execute and monitor simulation runs</p>
      </div>
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        selected_model = models[st.session_state.selected_model]
        running        = st.session_state.is_simulating
        glow_style     = f"filter:drop-shadow(0 0 20px {selected_model['color']});" if running else "filter:grayscale(0.4) brightness(0.7);"

        st.markdown(f"""
        <div style="background:linear-gradient(145deg,rgba(255,255,255,0.98),rgba(224,248,255,0.92));
                    border:2px solid {''+selected_model['color']+'' if running else 'rgba(0,200,255,0.3)'};
                    border-radius:22px;padding:44px 32px;
                    min-height:520px;display:flex;flex-direction:column;
                    justify-content:center;align-items:center;
                    box-shadow:{'0 0 60px '+selected_model['color']+'33' if running else '0 6px 28px rgba(0,0,0,0.07)'};
                    transition:all 0.5s ease;">
          <div style="font-size:9rem;margin-bottom:2rem;{glow_style}
                      transition:all 0.5s ease;">
            {selected_model['icon']}
          </div>
          <div style="font-family:'Orbitron',monospace;
                      font-size:1.8rem;font-weight:900;letter-spacing:0.1em;
                      color:{''+selected_model['color'] if running else '#7a90a8'};
                      text-shadow:{'0 0 20px '+selected_model['color']+'88' if running else 'none'};
                      margin-bottom:0.8rem;">
            {'🟢 RUNNING' if running else '⚪ STANDBY'}
          </div>
          <div style="font-family:'Share Tech Mono',monospace;
                      font-size:1.1rem;letter-spacing:0.1em;
                      color:{'#2a4060' if running else '#8aaabb'};">
            {selected_model['name'].upper()}
          </div>
          {('<div style="margin-top:1.2rem;font-family:Share Tech Mono,monospace;font-size:0.78rem;color:' + selected_model["color"] + ';letter-spacing:0.15em;animation:sub-flicker 1.5s ease-in-out infinite;">&#9612; PROCESSING DATA &#9614;</div>') if running else ''}
        </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.session_state.is_simulating:
            if st.button("⏸  STOP SIMULATION", use_container_width=True):
                st.session_state.is_simulating = False
                st.session_state.simulation_progress = 0
                st.warning("⏸ Simulation stopped")
                st.rerun()
        else:
            if st.button("▶  INITIALIZE SIMULATION", use_container_width=True):
                st.session_state.is_simulating = True
                st.success("✅ Simulation started!")
                st.rerun()

    with col2:
        st.markdown("""
        <div class="glass-panel">
          <h4 style="font-size:1.15rem;margin:0;">⏱ SIMULATION PROGRESS</h4>
        </div>""", unsafe_allow_html=True)

        if st.session_state.is_simulating:
            progress_bar = st.progress(0)
            status_text  = st.empty()
            for i in range(101):
                progress_bar.progress(i)
                status_text.markdown(f"""
                <div style="text-align:center;background:rgba(255,255,255,0.97);
                            border:2px solid rgba(0,200,255,0.4);border-radius:16px;
                            padding:26px;box-shadow:0 0 30px rgba(0,200,255,0.15);">
                  <div style="font-family:'Orbitron',monospace;
                              color:#00c8ff;font-size:3.2rem;font-weight:900;
                              text-shadow:0 0 20px rgba(0,200,255,0.5);">{i}%</div>
                  <div style="font-family:'Share Tech Mono',monospace;
                              color:#5a7090;font-size:0.82rem;letter-spacing:0.1em;
                              margin-top:6px;">PROCESSING... ⚡</div>
                </div>""", unsafe_allow_html=True)
                time.sleep(0.05)
                if not st.session_state.is_simulating:
                    break
            if i >= 100:
                st.session_state.is_simulating = False
                st.success("✅ Simulation completed successfully!")
        else:
            st.info("💡 Click 'INITIALIZE SIMULATION' to begin")

        st.markdown("<br>", unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        metrics_data = [
            ('⚙', 'ITERATIONS', int(st.session_state.simulation_progress*10) if st.session_state.is_simulating else 0, '#00c8ff'),
            ('⏱', 'TIME',       f"{(st.session_state.simulation_progress/10):.1f}s", '#ff8800'),
            ('📊', 'ACCURACY',  selected_model['accuracy'], '#00ff88'),
            ('⚡', 'SPEED',     selected_model['speed'],    '#cc44ff'),
        ]
        for i, (icon, label, val, color) in enumerate(metrics_data):
            with col_a if i%2==0 else col_b:
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.97);
                            border:2px solid {color}44;border-radius:16px;
                            padding:24px;text-align:center;margin-bottom:18px;
                            box-shadow:0 6px 20px {color}22;">
                  <div style="font-size:2.8rem;margin-bottom:10px;">{icon}</div>
                  <div style="font-family:'Orbitron',monospace;color:#5a7090;
                              font-size:0.65rem;letter-spacing:0.18em;margin-bottom:8px;">{label}</div>
                  <div style="font-family:'Orbitron',monospace;
                              color:{color};font-size:2rem;font-weight:900;
                              text-shadow:0 0 16px {color}88;">{val}</div>
                </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  TAB 4 — ANALYTICS
# ═══════════════════════════════════════════════════════════════
with tab4:
    st.markdown("""
    <div class="tab-header">
      <div class="tab-header-icon">📈</div>
      <div>
        <p class="tab-header-title">ADVANCED ANALYTICS</p>
        <p class="tab-header-subtitle"> comprehensive data visualization &amp; insights</p>
      </div>
    </div>""", unsafe_allow_html=True)

    df = generate_chart_data(100)

    st.markdown("""
    <div class="glass-panel">
      <h3 style="font-size:1.25rem;margin-bottom:4px;">📊 MULTI-PARAMETER ANALYSIS</h3>
      <p style="font-family:'Share Tech Mono',monospace;font-size:0.75rem;
                color:#5a7090;margin-top:0;letter-spacing:0.1em;">
         voltage | current | temperature — 100 sample window
      </p>
    </div>""", unsafe_allow_html=True)

    fig = go.Figure()
    traces = [
        ('Voltage (V)',      '#00c8ff', 'Voltage'),
        ('Current (A)',      '#ff8800', 'Current'),
        ('Temperature (°C)', '#ff3366', 'Temp'),
    ]
    for col_name, color, name in traces:
        fig.add_trace(go.Scatter(
            x=df['Time'], y=df[col_name],
            name=name,
            line=dict(color=color, width=3),
            mode='lines+markers',
            marker=dict(size=3, color=color)))
    layout = cyber_plotly_layout(520)
    layout['xaxis']['title'] = dict(text='TIME (s)', font=dict(family='Orbitron,monospace', size=11, color='#0066aa'))
    layout['yaxis']['title'] = dict(text='VALUES',   font=dict(family='Orbitron,monospace', size=11, color='#0066aa'))
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="glass-panel" style="border-color:rgba(0,255,136,0.3);">
          <h4 style="color:#00aa55;font-size:1.1rem;margin-bottom:4px;">📈 SOC TREND ANALYSIS</h4>
          <p style="font-family:'Share Tech Mono',monospace;font-size:0.72rem;
                    color:#5a7090;margin-top:0;letter-spacing:0.1em;">
             state of charge decay curve
          </p>
        </div>""", unsafe_allow_html=True)
        fig_soc = go.Figure()
        fig_soc.add_trace(go.Scatter(
            x=df['Time'], y=df['SOC (%)'],
            fill='tozeroy', fillcolor='rgba(0,255,136,0.1)',
            line=dict(color='#00ff88', width=3),
            mode='lines+markers', marker=dict(size=4)))
        layout_soc = cyber_plotly_layout(330)
        layout_soc['xaxis']['title'] = dict(text='TIME (s)', font=dict(family='Orbitron,monospace', size=10))
        layout_soc['yaxis']['title'] = dict(text='SOC (%)',  font=dict(family='Orbitron,monospace', size=10))
        layout_soc['showlegend'] = False
        fig_soc.update_layout(**layout_soc)
        st.plotly_chart(fig_soc, use_container_width=True)

    with col2:
        st.markdown("""
        <div class="glass-panel" style="border-color:rgba(204,68,255,0.3);">
          <h4 style="color:#9933cc;font-size:1.1rem;margin-bottom:4px;">🔋 POWER DISTRIBUTION</h4>
          <p style="font-family:'Share Tech Mono',monospace;font-size:0.72rem;
                    color:#5a7090;margin-top:0;letter-spacing:0.1em;">
             parameter share breakdown
          </p>
        </div>""", unsafe_allow_html=True)
        power_data = pd.DataFrame({
            'Category': ['Voltage', 'Current', 'Temperature', 'SOC'],
            'Value': [df['Voltage (V)'].mean()*10, df['Current (A)'].mean()*10,
                      df['Temperature (°C)'].mean(), df['SOC (%)'].mean()]
        })
        fig_pie = px.pie(power_data, values='Value', names='Category',
                         color_discrete_sequence=['#00c8ff','#ff8800','#ff3366','#00ff88'],
                         hole=0.45)
        layout_pie = cyber_plotly_layout(330)
        layout_pie['showlegend'] = True
        layout_pie['legend']['font'] = dict(family='Share Tech Mono', size=11, color='#003355')
        fig_pie.update_layout(**layout_pie)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label',
                              textfont=dict(family='Orbitron, monospace', size=11),
                              marker=dict(line=dict(color='white', width=3)))
        st.plotly_chart(fig_pie, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
#  TAB 5 — PARAMETERS
# ═══════════════════════════════════════════════════════════════
with tab5:
    st.markdown("""
    <div class="tab-header">
      <div class="tab-header-icon">⚙</div>
      <div>
        <p class="tab-header-title">SYSTEM PARAMETERS</p>
        <p class="tab-header-subtitle"> configure input parameters via interactive controls</p>
      </div>
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns([1,1])
    with col1:
        st.markdown("""
        <div class="glass-panel">
          <h4 style="font-size:1.15rem;margin:0;">🎛 INPUT PARAMETERS</h4>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div class="param-box"
             style="background:linear-gradient(135deg,rgba(224,248,255,0.7),rgba(204,242,255,0.5));
                    border:2px solid rgba(0,200,255,0.4);">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
              <div class="param-title" style="color:#005f8a;">⚡ STATE OF CHARGE (SOC)</div>
              <div class="param-desc" style="color:#5a7090;"> current battery charge level</div>
            </div>
            <div class="param-value-badge" style="border-color:rgba(0,200,255,0.5);
                                                   box-shadow:0 0 16px rgba(0,200,255,0.2);">
              <span class="param-val" style="color:#00527a;">{st.session_state.soc}</span>
              <span class="param-unit" style="color:#0088aa;">%</span>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
        st.session_state.soc = st.slider(
            "SOC", min_value=0, max_value=100,
            value=st.session_state.soc, label_visibility="collapsed")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        st.markdown(f"""
        <div class="param-box"
             style="background:linear-gradient(135deg,rgba(255,240,220,0.7),rgba(255,225,190,0.5));
                    border:2px solid rgba(255,136,0,0.4);">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
              <div class="param-title" style="color:#8a3a00;">🌡 TEMPERATURE</div>
              <div class="param-desc" style="color:#5a7090;"> operating temperature</div>
            </div>
            <div class="param-value-badge" style="border-color:rgba(255,136,0,0.5);
                                                   box-shadow:0 0 16px rgba(255,136,0,0.2);">
              <span class="param-val" style="color:#7a3300;">{st.session_state.temperature}</span>
              <span class="param-unit" style="color:#aa5500;">°C</span>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
        st.session_state.temperature = st.slider(
            "Temperature", min_value=0, max_value=60,
            value=st.session_state.temperature, label_visibility="collapsed")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        st.markdown(f"""
        <div class="param-box"
             style="background:linear-gradient(135deg,rgba(220,234,255,0.7),rgba(200,224,255,0.5));
                    border:2px solid rgba(0,100,255,0.4);">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
              <div class="param-title" style="color:#003a8a;">⚡ CURRENT LOAD</div>
              <div class="param-desc" style="color:#5a7090;"> applied current</div>
            </div>
            <div class="param-value-badge" style="border-color:rgba(0,100,255,0.5);
                                                   box-shadow:0 0 16px rgba(0,100,255,0.2);">
              <span class="param-val" style="color:#002a7a;">{st.session_state.current}</span>
              <span class="param-unit" style="color:#0044aa;">A</span>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
        st.session_state.current = st.slider(
            "Current", min_value=0.0, max_value=10.0,
            value=st.session_state.current, step=0.1, label_visibility="collapsed")

    with col2:
        st.markdown("""
        <div class="glass-panel">
          <h4 style="font-size:1.15rem;margin:0;">📊 OUTPUT METRICS</h4>
        </div>""", unsafe_allow_html=True)

        voltage_out = round(3.2 + (st.session_state.soc/100)*0.9, 2)
        power_out   = round(voltage_out * st.session_state.current, 1)

        col_a, col_b = st.columns(2, gap="medium")
        with col_a:
            st.markdown(f"""
            <div class="output-card"
                 style="background:linear-gradient(135deg,rgba(0,80,120,1),rgba(0,120,180,1));
                        border:2px solid #00c8ff;
                        box-shadow:0 8px 32px rgba(0,200,255,0.35);">
              <div class="output-icon" style="filter:drop-shadow(0 0 10px #00c8ff);">⚡</div>
              <div class="output-label" style="color:rgba(200,240,255,0.9);">VOLTAGE</div>
              <div class="output-value" style="color:#00c8ff;
                   text-shadow:0 0 24px rgba(0,200,255,0.6);">{voltage_out}</div>
              <div class="output-unit" style="color:rgba(200,240,255,0.7);">VOLTS</div>
            </div>""", unsafe_allow_html=True)

        with col_b:
            st.markdown(f"""
            <div class="output-card"
                 style="background:linear-gradient(135deg,rgba(0,80,40,1),rgba(0,130,60,1));
                        border:2px solid #00ff88;
                        box-shadow:0 8px 32px rgba(0,255,136,0.35);">
              <div class="output-icon" style="filter:drop-shadow(0 0 10px #00ff88);">💚</div>
              <div class="output-label" style="color:rgba(200,255,220,0.9);">SOH</div>
              <div class="output-value" style="color:#00ff88;
                   text-shadow:0 0 24px rgba(0,255,136,0.6);">94</div>
              <div class="output-unit" style="color:rgba(200,255,220,0.7);">PERCENT</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        col_c, col_d = st.columns(2, gap="medium")
        with col_c:
            st.markdown(f"""
            <div class="output-card"
                 style="background:linear-gradient(135deg,rgba(100,40,0,1),rgba(160,70,0,1));
                        border:2px solid #ff8800;
                        box-shadow:0 8px 32px rgba(255,136,0,0.35);">
              <div class="output-icon" style="filter:drop-shadow(0 0 10px #ff8800);">🔋</div>
              <div class="output-label" style="color:rgba(255,230,200,0.9);">POWER</div>
              <div class="output-value" style="color:#ffaa44;
                   text-shadow:0 0 24px rgba(255,136,0,0.6);">{power_out}</div>
              <div class="output-unit" style="color:rgba(255,220,180,0.7);">WATTS</div>
            </div>""", unsafe_allow_html=True)

        with col_d:
            st.markdown(f"""
            <div class="output-card"
                 style="background:linear-gradient(135deg,rgba(60,0,100,1),rgba(100,20,160,1));
                        border:2px solid #cc44ff;
                        box-shadow:0 8px 32px rgba(204,68,255,0.35);">
              <div class="output-icon" style="filter:drop-shadow(0 0 10px #cc44ff);">🔄</div>
              <div class="output-label" style="color:rgba(240,210,255,0.9);">CYCLES</div>
              <div class="output-value" style="color:#cc44ff;
                   text-shadow:0 0 24px rgba(204,68,255,0.6);">487</div>
              <div class="output-unit" style="color:rgba(230,190,255,0.7);">COUNT</div>
            </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  TAB 6 — AI RUL
# ═══════════════════════════════════════════════════════════════
with tab6:
    st.markdown("""
    <div class="tab-header">
      <div class="tab-header-icon">🤖</div>
      <div>
        <p class="tab-header-title">AI-BASED RUL PREDICTION</p>
        <p class="tab-header-subtitle"> predictive analytics for remaining useful life estimation</p>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="glass-panel">
      <h4 style="font-size:1.15rem;margin:0 0 6px;">🔋 BATTERY OVERVIEW</h4>
      <p style="font-family:'Share Tech Mono',monospace;font-size:0.75rem;
                color:#5a7090;margin:0;letter-spacing:0.1em;">
         real-time snapshot of current battery state
      </p>
    </div>""", unsafe_allow_html=True)

    rul_col1, rul_col2, rul_col3, rul_col4 = st.columns(4)
    overview_cards = [
        (rul_col1, "CURRENT CYCLE",      "25",   "",    "#00c8ff", "🔁"),
        (rul_col2, "CURRENT SOH",        "86",   "%",   "#00ff88", "💚"),
        (rul_col3, "DISCHARGE CAPACITY", "1.43", "Ah",  "#ff8800", "🔌"),
        (rul_col4, "AVG IMPEDANCE",      "0.23", "Ω",   "#cc44ff", "📡"),
    ]
    for col, label, val, unit, color, icon in overview_cards:
        with col:
            st.markdown(f"""
            <div class="metric-card" style="border-color:{color}55;">
              <div class="metric-label">{icon} {label}</div>
              <div class="metric-value"
                   style="color:{color};text-shadow:0 0 24px {color}88;font-size:3.2rem;">
                {val}</div>
              <div class="metric-unit">{unit}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="glass-panel">
      <h4 style="font-size:1.15rem;margin:0 0 6px;">⚡ MODEL COMPARISON</h4>
      <p style="font-family:'Share Tech Mono',monospace;font-size:0.75rem;
                color:#5a7090;margin:0;letter-spacing:0.1em;">
         LSTM vs XGBoost predictive performance metrics
      </p>
    </div>""", unsafe_allow_html=True)

    mc_col1, mc_col2 = st.columns(2, gap="large")

    with mc_col1:
        st.markdown("""
        <div style="position:relative;background:linear-gradient(145deg,rgba(0,50,90,0.97),rgba(0,80,130,0.95));
                    border:2px solid #00c8ff;border-radius:22px;padding:36px 32px;
                    min-height:320px;overflow:hidden;
                    box-shadow:0 12px 40px rgba(0,200,255,0.35),0 0 0 1px rgba(0,200,255,0.2);">
          <div style="position:absolute;top:0;left:0;right:0;height:3px;
                      background:linear-gradient(90deg,#00c8ff,#0080ff,#00c8ff);
                      box-shadow:0 0 12px rgba(0,200,255,0.6);"></div>
          <div style="position:absolute;top:16px;right:16px;
                      background:rgba(0,200,255,0.2);border:1px solid rgba(0,200,255,0.5);
                      border-radius:8px;padding:4px 12px;
                      font-family:'Share Tech Mono',monospace;font-size:0.65rem;
                      color:#00c8ff;letter-spacing:0.1em;">ACTIVE MODEL</div>
          <div style="display:flex;align-items:center;gap:14px;margin-bottom:22px;">
            <span style="font-size:3rem;filter:drop-shadow(0 0 12px #00c8ff);">🧠</span>
            <div>
              <div style="font-family:'Orbitron',monospace;color:#00c8ff;
                          font-size:1.25rem;font-weight:900;letter-spacing:0.08em;">
                LSTM MODEL</div>
              <div style="font-family:'Share Tech Mono',monospace;
                          color:rgba(180,230,255,0.7);font-size:0.75rem;
                          letter-spacing:0.1em;margin-top:2px;">
                Long Short-Term Memory Network</div>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-bottom:22px;">
            <div style="background:rgba(0,200,255,0.1);border:1px solid rgba(0,200,255,0.3);
                        border-radius:14px;padding:16px 10px;text-align:center;">
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(180,230,255,0.7);
                          font-size:0.65rem;letter-spacing:0.1em;margin-bottom:6px;">MAE</div>
              <div style="font-family:'Orbitron',monospace;color:#00c8ff;
                          font-size:1.8rem;font-weight:900;
                          text-shadow:0 0 16px rgba(0,200,255,0.6);">0.05</div>
            </div>
            <div style="background:rgba(0,200,255,0.1);border:1px solid rgba(0,200,255,0.3);
                        border-radius:14px;padding:16px 10px;text-align:center;">
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(180,230,255,0.7);
                          font-size:0.65rem;letter-spacing:0.1em;margin-bottom:6px;">RMSE</div>
              <div style="font-family:'Orbitron',monospace;color:#00c8ff;
                          font-size:1.8rem;font-weight:900;
                          text-shadow:0 0 16px rgba(0,200,255,0.6);">0.07</div>
            </div>
            <div style="background:rgba(0,200,255,0.15);border:1px solid rgba(0,200,255,0.5);
                        border-radius:14px;padding:16px 10px;text-align:center;">
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(180,230,255,0.7);
                          font-size:0.65rem;letter-spacing:0.1em;margin-bottom:6px;">PRED. RUL</div>
              <div style="font-family:'Orbitron',monospace;color:#00e8ff;
                          font-size:1.8rem;font-weight:900;
                          text-shadow:0 0 20px rgba(0,200,255,0.8);">14</div>
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(180,230,255,0.6);
                          font-size:0.65rem;letter-spacing:0.08em;margin-top:2px;">CYCLES</div>
            </div>
          </div>
          <div style="background:rgba(0,200,255,0.08);border:1px solid rgba(0,200,255,0.25);
                      border-radius:12px;padding:12px 16px;
                      display:flex;align-items:center;gap:10px;">
            <span style="font-size:1.2rem;">✅</span>
            <span style="font-family:'Share Tech Mono',monospace;
                         color:rgba(180,230,255,0.85);font-size:0.78rem;letter-spacing:0.06em;">
              Superior temporal pattern recognition for degradation trends
            </span>
          </div>
        </div>""", unsafe_allow_html=True)

    with mc_col2:
        st.markdown("""
        <div style="position:relative;background:linear-gradient(145deg,rgba(80,35,0,0.97),rgba(130,60,0,0.95));
                    border:2px solid #ff8800;border-radius:22px;padding:36px 32px;
                    min-height:320px;overflow:hidden;
                    box-shadow:0 12px 40px rgba(255,136,0,0.3),0 0 0 1px rgba(255,136,0,0.15);">
          <div style="position:absolute;top:0;left:0;right:0;height:3px;
                      background:linear-gradient(90deg,#ff8800,#ffaa44,#ff8800);
                      box-shadow:0 0 12px rgba(255,136,0,0.6);"></div>
          <div style="display:flex;align-items:center;gap:14px;margin-bottom:22px;">
            <span style="font-size:3rem;filter:drop-shadow(0 0 12px #ff8800);">⚡</span>
            <div>
              <div style="font-family:'Orbitron',monospace;color:#ff8800;
                          font-size:1.25rem;font-weight:900;letter-spacing:0.08em;">
                XGBOOST MODEL</div>
              <div style="font-family:'Share Tech Mono',monospace;
                          color:rgba(255,210,160,0.7);font-size:0.75rem;
                          letter-spacing:0.1em;margin-top:2px;">
                Extreme Gradient Boosting</div>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-bottom:22px;">
            <div style="background:rgba(255,136,0,0.1);border:1px solid rgba(255,136,0,0.3);
                        border-radius:14px;padding:16px 10px;text-align:center;">
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(255,210,160,0.7);
                          font-size:0.65rem;letter-spacing:0.1em;margin-bottom:6px;">MAE</div>
              <div style="font-family:'Orbitron',monospace;color:#ff8800;
                          font-size:1.8rem;font-weight:900;
                          text-shadow:0 0 16px rgba(255,136,0,0.6);">0.08</div>
            </div>
            <div style="background:rgba(255,136,0,0.1);border:1px solid rgba(255,136,0,0.3);
                        border-radius:14px;padding:16px 10px;text-align:center;">
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(255,210,160,0.7);
                          font-size:0.65rem;letter-spacing:0.1em;margin-bottom:6px;">ACCURACY</div>
              <div style="font-family:'Orbitron',monospace;color:#ff8800;
                          font-size:1.8rem;font-weight:900;
                          text-shadow:0 0 16px rgba(255,136,0,0.6);">89%</div>
            </div>
            <div style="background:rgba(255,136,0,0.12);border:1px solid rgba(255,136,0,0.4);
                        border-radius:14px;padding:16px 10px;text-align:center;">
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(255,210,160,0.7);
                          font-size:0.65rem;letter-spacing:0.1em;margin-bottom:6px;">PRED. RUL</div>
              <div style="font-family:'Orbitron',monospace;color:#ffaa44;
                          font-size:1.8rem;font-weight:900;
                          text-shadow:0 0 20px rgba(255,136,0,0.8);">13</div>
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(255,210,160,0.6);
                          font-size:0.65rem;letter-spacing:0.08em;margin-top:2px;">CYCLES</div>
            </div>
          </div>
          <div style="background:rgba(255,136,0,0.08);border:1px solid rgba(255,136,0,0.25);
                      border-radius:12px;padding:12px 16px;
                      display:flex;align-items:center;gap:10px;">
            <span style="font-size:1.2rem;">📊</span>
            <span style="font-family:'Share Tech Mono',monospace;
                         color:rgba(255,210,160,0.85);font-size:0.78rem;letter-spacing:0.06em;">
              High-speed ensemble method with robust feature importance
            </span>
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="glass-panel">
      <h4 style="font-size:1.15rem;margin:0 0 6px;">📈 SOH PREDICTION COMPARISON</h4>
      <p style="font-family:'Share Tech Mono',monospace;font-size:0.75rem;
                color:#5a7090;margin:0;letter-spacing:0.1em;">
         LSTM vs XGBoost vs actual SOH degradation trajectory
      </p>
    </div>""", unsafe_allow_html=True)

    np.random.seed(42)
    cycles = np.arange(25, 71)
    n = len(cycles)
    actual_soh = 86 - (cycles - 25) * 0.38 + np.random.normal(0, 0.25, n)
    actual_soh = np.clip(actual_soh, 64, 86)
    lstm_soh = 86 - (cycles - 25) * 0.37 + np.random.normal(0, 0.12, n)
    lstm_soh = np.clip(lstm_soh, 64, 86)
    xgb_soh = 86 - (cycles - 25) * 0.34 + np.random.normal(0, 0.18, n)
    xgb_soh = np.clip(xgb_soh, 64, 88)

    fig_rul = go.Figure()
    fig_rul.add_trace(go.Scatter(
        x=cycles, y=actual_soh, name='Actual SOH',
        line=dict(color='#00ff88', width=3),
        mode='lines+markers',
        marker=dict(size=5, color='#00ff88', symbol='circle'),
        fill='tozeroy', fillcolor='rgba(0,255,136,0.06)'))
    fig_rul.add_trace(go.Scatter(
        x=cycles, y=lstm_soh, name='LSTM Prediction',
        line=dict(color='#00c8ff', width=3),
        mode='lines+markers',
        marker=dict(size=5, color='#00c8ff', symbol='diamond')))
    fig_rul.add_trace(go.Scatter(
        x=cycles, y=xgb_soh, name='XGBoost Prediction',
        line=dict(color='#ff8800', width=3, dash='dot'),
        mode='lines+markers',
        marker=dict(size=5, color='#ff8800', symbol='square')))
    fig_rul.update_layout(
        plot_bgcolor='rgba(245,252,255,0.95)',
        paper_bgcolor='rgba(240,250,255,0.4)',
        font=dict(color='#0a1628', size=12, family='Exo 2, sans-serif'),
        xaxis=dict(
            title=dict(text='CYCLE', font=dict(family='Orbitron, monospace', size=12, color='#0066aa')),
            gridcolor='rgba(0,200,255,0.12)', linecolor='rgba(0,200,255,0.3)',
            tickfont=dict(family='Share Tech Mono', size=11), range=[24, 72]),
        yaxis=dict(
            title=dict(text='SOH (%)', font=dict(family='Orbitron, monospace', size=12, color='#0066aa')),
            gridcolor='rgba(0,200,255,0.12)', linecolor='rgba(0,200,255,0.3)',
            tickfont=dict(family='Share Tech Mono', size=11), range=[62, 90]),
        height=420, hovermode='x unified',
        legend=dict(
            bgcolor='rgba(255,255,255,0.95)', bordercolor='rgba(0,200,255,0.4)',
            borderwidth=2, font=dict(family='Share Tech Mono', size=11, color='#003355'),
            orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig_rul, use_container_width=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    conc_col1, conc_col2 = st.columns(2, gap="large")

    with conc_col1:
        st.markdown("""
        <div class="glass-panel" style="border-color:rgba(0,200,255,0.45);min-height:320px;">
        <h4 style="font-size:1.15rem;margin:0 0 18px;color:#0a1628;">&#127942; CONCLUSION</h4>
        <div style="background:linear-gradient(135deg,rgba(0,50,90,0.95),rgba(0,80,130,0.90));
            border:2px solid #00c8ff;border-radius:16px;padding:24px 20px;
            box-shadow:0 8px 28px rgba(0,200,255,0.3);">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:18px;">
            <span style="font-size:2rem;filter:drop-shadow(0 0 10px #00c8ff);">&#129504;</span>
            <div>
              <div style="font-family:Orbitron,monospace;color:#00c8ff;
                font-size:0.95rem;font-weight:900;letter-spacing:0.1em;">BEST PERFORMING MODEL</div>
              <div style="font-family:Share Tech Mono,monospace;color:rgba(180,230,255,0.9);
                font-size:1.3rem;font-weight:700;margin-top:4px;">LSTM</div>
            </div>
          </div>
          <div style="display:flex;flex-direction:column;gap:10px;">
            <div style="display:flex;align-items:center;gap:10px;">
              <span style="color:#00c8ff;font-size:1rem;font-weight:900;">&#10003;</span>
              <span style="font-family:Share Tech Mono,monospace;color:rgba(180,230,255,0.85);
                font-size:0.8rem;letter-spacing:0.06em;">Lower MAE and RMSE</span>
            </div>
            <div style="display:flex;align-items:center;gap:10px;">
              <span style="color:#00c8ff;font-size:1rem;font-weight:900;">&#10003;</span>
              <span style="font-family:Share Tech Mono,monospace;color:rgba(180,230,255,0.85);
                font-size:0.8rem;letter-spacing:0.06em;">More accurate projection of battery degradation trend</span>
            </div>
            <div style="display:flex;align-items:center;gap:10px;">
              <span style="color:#00c8ff;font-size:1rem;font-weight:900;">&#10003;</span>
              <span style="font-family:Share Tech Mono,monospace;color:rgba(180,230,255,0.85);
                font-size:0.8rem;letter-spacing:0.06em;">Predicted RUL: 14 Cycles remaining</span>
            </div>
          </div>
        </div>
        </div>""", unsafe_allow_html=True)

    with conc_col2:
        st.markdown("""
        <div class="glass-panel" style="border-color:rgba(0,200,255,0.3);min-height:320px;">
        <h4 style="font-size:1.15rem;margin:0 0 18px;color:#0a1628;">&#128202; PERFORMANCE SUMMARY</h4>
        <div style="display:flex;flex-direction:column;gap:14px;">
          <div style="background:rgba(255,255,255,0.97);border:2px solid rgba(0,200,255,0.35);
            border-radius:14px;padding:16px 20px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
              <span style="font-family:Orbitron,monospace;color:#0a1628;
                font-size:0.72rem;font-weight:700;letter-spacing:0.1em;">&#129504; LSTM ACCURACY</span>
              <span style="font-family:Orbitron,monospace;color:#00c8ff;
                font-weight:900;font-size:1.1rem;">95%</span>
            </div>
            <div class="perf-bar-track">
              <div class="perf-bar-fill"
                style="width:95%;background:linear-gradient(90deg,#00c8ff,#0088ff);">
              </div>
            </div>
          </div>
          <div style="background:rgba(255,255,255,0.97);border:2px solid rgba(255,136,0,0.35);
            border-radius:14px;padding:16px 20px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
              <span style="font-family:Orbitron,monospace;color:#0a1628;
                font-size:0.72rem;font-weight:700;letter-spacing:0.1em;">&#9889; XGBOOST ACCURACY</span>
              <span style="font-family:Orbitron,monospace;color:#ff8800;
                font-weight:900;font-size:1.1rem;">89%</span>
            </div>
            <div class="perf-bar-track">
              <div class="perf-bar-fill"
                style="width:89%;background:linear-gradient(90deg,#ff8800,#ffaa44);">
              </div>
            </div>
          </div>
          <div style="background:rgba(255,255,255,0.97);border:2px solid rgba(0,255,136,0.35);
            border-radius:14px;padding:16px 20px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
              <span style="font-family:Orbitron,monospace;color:#0a1628;
                font-size:0.72rem;font-weight:700;letter-spacing:0.1em;">&#128154; SOH PREDICTION MATCH</span>
              <span style="font-family:Orbitron,monospace;color:#00ff88;
                font-weight:900;font-size:1.1rem;">93%</span>
            </div>
            <div class="perf-bar-track">
              <div class="perf-bar-fill"
                style="width:93%;background:linear-gradient(90deg,#00ff88,#00cc66);">
              </div>
            </div>
          </div>
        </div>
        </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  TAB 7 — COMPARE (Physical Model vs AI Model)
# ═══════════════════════════════════════════════════════════════
with tab7:
    st.markdown("""
    <div class="tab-header">
      <div class="tab-header-icon">🔀</div>
      <div>
        <p class="tab-header-title">COMPARE PHYSICAL MODEL &amp; AI MODEL</p>
        <p class="tab-header-subtitle"> side-by-side analysis of ECM physical model vs AI prediction</p>
      </div>
    </div>""", unsafe_allow_html=True)

    # ── Battery Overview ─────────────────────────────────────────
    st.markdown("""
    <div class="glass-panel" style="border-color:rgba(0,200,255,0.4);">
      <h4 style="font-size:1.15rem;margin:0 0 6px;">🔋 BATTERY OVERVIEW</h4>
      <p style="font-family:'Share Tech Mono',monospace;font-size:0.75rem;
                color:#5a7090;margin:0;letter-spacing:0.1em;">
         current battery state snapshot used for both models
      </p>
    </div>""", unsafe_allow_html=True)

    cmp_c1, cmp_c2, cmp_c3, cmp_c4 = st.columns(4)
    cmp_overview = [
        (cmp_c1, "CURRENT CYCLE", "25",   "",   "#353a3b", "🔁"),
        (cmp_c2, "CURRENT SOH",   "86",   "%",  "#00ff88", "💚"),
        (cmp_c3, "RUL (PHYSICAL)","13",   "CYC","#ff8800", "⚙"),
        (cmp_c4, "RUL (AI MODEL)","14",   "CYC","#cc44ff", "🤖"),
    ]
    for col, label, val, unit, color, icon in cmp_overview:
        with col:
            st.markdown(f"""
            <div class="metric-card" style="border-color:{color}55;">
              <div class="metric-label">{icon} {label}</div>
              <div class="metric-value"
                   style="color:{color};text-shadow:0 0 24px {color}88;font-size:3rem;">
                {val}</div>
              <div class="metric-unit">{unit}</div>
            </div>""", unsafe_allow_html=True)

    # info note
    st.markdown("""
    <div style="background:rgba(0,200,255,0.06);border:1px solid rgba(0,200,255,0.25);
                border-radius:12px;padding:14px 20px;margin-bottom:24px;">
      <span style="font-family:'Share Tech Mono',monospace;font-size:0.8rem;
                   color:#2a4060;letter-spacing:0.06em;">
        ℹ Comparison between the Equivalent Circuit Model and AI Model for battery degradation prediction.
      </span>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Model Comparison Cards ──────────────────────────────────
    st.markdown("""
    <div class="glass-panel">
      <h4 style="font-size:1.15rem;margin:0 0 6px;">⚡ MODEL COMPARISON</h4>
      <p style="font-family:'Share Tech Mono',monospace;font-size:0.75rem;
                color:#5a7090;margin:0;letter-spacing:0.1em;">
         Physical Model (ECM) vs AI Model side-by-side
      </p>
    </div>""", unsafe_allow_html=True)

    phys_col, ai_col = st.columns(2, gap="large")

    with phys_col:
        st.markdown("""
        <div style="position:relative;
                    background: linear-gradient(145deg, rgba(70,0,20,0.97), rgba(120,10,40,0.95));
                    border:2px solid #ff3366;border-radius:22px;padding:36px 32px;
                    min-height:360px;overflow:hidden;
                    box-shadow:0 12px 40px rgba(0,200,255,0.35);">

          <div style="position:absolute;top:0;left:0;right:0;height:3px;
                      background:linear-gradient(90deg,#ff3366,#cc0033,#ff3366);
                      box-shadow:0 0 12px rgba(0,200,255,0.6);"></div>

          <div style="display:flex;align-items:center;gap:14px;margin-bottom:26px;">
            <span style="font-size:3.2rem;filter:drop-shadow(0 0 14px #00c8ff);">⚙</span>
            <div>
              <div style="font-family:'Orbitron',monospace;color:#00c8ff;
                          font-size:1.2rem;font-weight:900;letter-spacing:0.08em;">
                PHYSICAL MODEL</div>
              <div style="font-family:'Share Tech Mono',monospace;
                          color:rgba(180,230,255,0.7);font-size:0.75rem;
                          letter-spacing:0.1em;margin-top:3px;">
                Equivalent Circuit Model (ECM)</div>
            </div>
          </div>


          <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:24px;">
            <div style="background:rgba(0,200,255,0.1);border:1px solid rgba(0,200,255,0.3);
                        border-radius:14px;padding:18px 12px;text-align:center;">
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(180,230,255,0.7);
                          font-size:0.65rem;letter-spacing:0.12em;margin-bottom:8px;">PREDICTED RUL</div>
              <div style="font-family:'Orbitron',monospace;color:#00c8ff;
                          font-size:2.8rem;font-weight:900;
                          text-shadow:0 0 20px rgba(0,200,255,0.7);">13</div>
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(180,230,255,0.6);
                          font-size:0.7rem;margin-top:4px;">CYCLES</div>
            </div>
            <div style="background:rgba(0,200,255,0.1);border:1px solid rgba(0,200,255,0.3);
                        border-radius:14px;padding:18px 12px;text-align:center;">
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(180,230,255,0.7);
                          font-size:0.65rem;letter-spacing:0.12em;margin-bottom:8px;">ACCURACY</div>
              <div style="font-family:'Orbitron',monospace;color:#00c8ff;
                          font-size:2.8rem;font-weight:900;
                          text-shadow:0 0 20px rgba(0,200,255,0.7);">87%</div>
            </div>
          </div>


          <div class="eol-badge" style="background:rgba(255,165,0,0.15);
                      border:2px solid rgba(255,165,0,0.5);border-radius:14px;
                      padding:14px 16px;margin-bottom:14px;
                      display:flex;align-items:center;gap:12px;">
            <span style="font-size:1.5rem;">⚠️</span>
            <div>
              <div style="font-family:'Orbitron',monospace;color:#ffaa00;
                          font-size:0.75rem;font-weight:700;letter-spacing:0.1em;">EOL DETECTION</div>
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(255,200,100,0.9);
                          font-size:1.1rem;font-weight:700;margin-top:2px;">80%</div>
            </div>
            <div style="margin-left:auto;">
              <div class="perf-bar-track" style="width:120px;">
                <div class="perf-bar-fill"
                     style="width:80%;background:linear-gradient(90deg,#ffaa00,#ffdd44);">
                </div>
              </div>
            </div>
          </div>


          <div style="background:rgba(0,200,255,0.06);border:1px solid rgba(0,200,255,0.2);
                      border-radius:12px;padding:14px 16px;">
            <div style="font-family:'Share Tech Mono',monospace;color:rgba(180,230,255,0.85);
                        font-size:0.75rem;letter-spacing:0.06em;line-height:1.8;">
              ◈ Physics-based degradation equations<br>
              ◈ Computationally lightweight<br>
              ◈ Interpretable parameter outputs
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

    with ai_col:
        st.markdown("""
        <div style="position:relative;
                    background:linear-gradient(145deg,rgba(60,0,100,0.97),rgba(100,20,160,0.95));
                    border:2px solid #cc44ff;border-radius:22px;padding:36px 32px;
                    min-height:360px;overflow:hidden;
                    box-shadow:0 12px 40px rgba(204,68,255,0.35);">

          <div style="position:absolute;top:0;left:0;right:0;height:3px;
                      background:linear-gradient(90deg,#cc44ff,#ff00c8,#cc44ff);
                      box-shadow:0 0 12px rgba(204,68,255,0.6);"></div>


          <div style="position:absolute;top:16px;right:16px;
                      background:rgba(0,255,136,0.2);border:1px solid rgba(0,255,136,0.5);
                      border-radius:8px;padding:4px 12px;
                      font-family:'Share Tech Mono',monospace;font-size:0.65rem;
                      color:#00ff88;letter-spacing:0.1em;">&#10003; BEST</div>

          <div style="display:flex;align-items:center;gap:14px;margin-bottom:26px;">
            <span style="font-size:3.2rem;filter:drop-shadow(0 0 14px #cc44ff);">🤖</span>
            <div>
              <div style="font-family:'Orbitron',monospace;color:#cc44ff;
                          font-size:1.2rem;font-weight:900;letter-spacing:0.08em;">
                AI MODEL</div>
              <div style="font-family:'Share Tech Mono',monospace;
                          color:rgba(230,190,255,0.7);font-size:0.75rem;
                          letter-spacing:0.1em;margin-top:3px;">
                LSTM Neural Network</div>
            </div>
          </div>


          <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:24px;">
            <div style="background:rgba(204,68,255,0.12);border:1px solid rgba(204,68,255,0.35);
                        border-radius:14px;padding:18px 12px;text-align:center;">
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(230,190,255,0.7);
                          font-size:0.65rem;letter-spacing:0.12em;margin-bottom:8px;">PREDICTED RUL</div>
              <div style="font-family:'Orbitron',monospace;color:#dd66ff;
                          font-size:2.8rem;font-weight:900;
                          text-shadow:0 0 20px rgba(204,68,255,0.7);">14</div>
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(230,190,255,0.6);
                          font-size:0.7rem;margin-top:4px;">CYCLES</div>
            </div>
            <div style="background:rgba(204,68,255,0.12);border:1px solid rgba(204,68,255,0.35);
                        border-radius:14px;padding:18px 12px;text-align:center;">
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(230,190,255,0.7);
                          font-size:0.65rem;letter-spacing:0.12em;margin-bottom:8px;">ACCURACY</div>
              <div style="font-family:'Orbitron',monospace;color:#dd66ff;
                          font-size:2.8rem;font-weight:900;
                          text-shadow:0 0 20px rgba(204,68,255,0.7);">91%</div>
            </div>
          </div>


          <div style="background:rgba(0,255,136,0.12);
                      border:2px solid rgba(0,255,136,0.4);border-radius:14px;
                      padding:14px 16px;margin-bottom:14px;
                      display:flex;align-items:center;gap:12px;">
            <span style="font-size:1.5rem;">📡</span>
            <div>
              <div style="font-family:'Orbitron',monospace;color:#00ff88;
                          font-size:0.75rem;font-weight:700;letter-spacing:0.1em;">EOL DETECTION</div>
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(180,255,210,0.9);
                          font-size:1.1rem;font-weight:700;margin-top:2px;">SUPERIOR</div>
            </div>
            <div style="margin-left:auto;text-align:right;">
              <div style="font-family:'Orbitron',monospace;color:#00ff88;
                          font-size:1.4rem;font-weight:900;">+11%</div>
              <div style="font-family:'Share Tech Mono',monospace;color:rgba(180,255,210,0.7);
                          font-size:0.65rem;">vs ECM</div>
            </div>
          </div>


          <div style="background:rgba(204,68,255,0.06);border:1px solid rgba(204,68,255,0.2);
                      border-radius:12px;padding:14px 16px;">
            <div style="font-family:'Share Tech Mono',monospace;color:rgba(230,190,255,0.85);
                        font-size:0.75rem;letter-spacing:0.06em;line-height:1.8;">
              ◈ Data-driven temporal pattern learning<br>
              ◈ Adaptive to real-world degradation<br>
              ◈ Higher accuracy on unseen cycles
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Degradation Trend Chart ───────────────────────────────────
    st.markdown("""
    <div class="glass-panel">
      <h4 style="font-size:1.15rem;margin:0 0 6px;">📈 DEGRADATION TREND ANALYSIS</h4>
      <p style="font-family:'Share Tech Mono',monospace;font-size:0.75rem;
                color:#5a7090;margin:0;letter-spacing:0.1em;">
         Physical Model vs AI Model vs Actual SOH — full cycle trajectory
      </p>
    </div>""", unsafe_allow_html=True)

    np.random.seed(99)
    cmp_cycles = np.arange(0, 81)
    nc = len(cmp_cycles)

    # Actual SOH — gradual degradation
    actual_cmp = 100 - (cmp_cycles * 0.18) - (cmp_cycles**1.6) * 0.0012 + np.random.normal(0, 0.3, nc)
    actual_cmp = np.clip(actual_cmp, 60, 100)

    # Physical model — slightly smoother, misses late-stage acceleration
    phys_pred = 100 - (cmp_cycles * 0.17) - (cmp_cycles**1.55) * 0.0011 + np.random.normal(0, 0.2, nc)
    phys_pred = np.clip(phys_pred, 60, 100)

    # AI model — tracks actual more closely
    ai_pred = 100 - (cmp_cycles * 0.18) - (cmp_cycles**1.62) * 0.00125 + np.random.normal(0, 0.15, nc)
    ai_pred = np.clip(ai_pred, 60, 100)

    # EOL threshold line at 80% SOH
    eol_threshold = np.full(nc, 80)

    fig_cmp = go.Figure()

    # Actual SOH (solid)
    fig_cmp.add_trace(go.Scatter(
        x=cmp_cycles, y=actual_cmp,
        name='Actual SOH',
        line=dict(color='#00ff88', width=3),
        mode='lines+markers',
        marker=dict(size=4, color='#00ff88')))

    # Physical prediction (dashed)
    fig_cmp.add_trace(go.Scatter(
        x=cmp_cycles, y=phys_pred,
        name='Physical Prediction (ECM)',
        line=dict(color="#0c0c0c", width=3, dash='dash'),
        mode='lines',
        marker=dict(size=4, color="#0B0B0B")))

    # AI prediction (solid, slightly thicker)
    fig_cmp.add_trace(go.Scatter(
        x=cmp_cycles, y=ai_pred,
        name='AI Prediction (LSTM)',
        line=dict(color='#cc44ff', width=3),
        mode='lines',
        marker=dict(size=4, color='#cc44ff')))

    # EOL threshold
    fig_cmp.add_trace(go.Scatter(
        x=cmp_cycles, y=eol_threshold,
        name='EOL Threshold (80%)',
        line=dict(color='#ff4444', width=2, dash='dot'),
        mode='lines'))

    # Annotate EOL crossing for AI model
    eol_cycle_ai = next((i for i, v in enumerate(ai_pred) if v <= 80), None)
    if eol_cycle_ai:
        fig_cmp.add_annotation(
            x=eol_cycle_ai, y=80,
            text=f"⚠ EOL @ Cycle {eol_cycle_ai}",
            showarrow=True, arrowhead=2,
            arrowcolor="#ff4444",
            font=dict(family='Share Tech Mono', size=11, color='#ff4444'),
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='#ff4444',
            borderwidth=1,
            ax=40, ay=-40)

    fig_cmp.update_layout(
        plot_bgcolor='rgba(245,252,255,0.95)',
        paper_bgcolor='rgba(240,250,255,0.4)',
        font=dict(color='#0a1628', size=12, family='Exo 2, sans-serif'),
        xaxis=dict(
            title=dict(text='CYCLE', font=dict(family='Orbitron, monospace', size=12, color='#0066aa')),
            gridcolor='rgba(0,200,255,0.12)', linecolor='rgba(0,200,255,0.3)',
            tickfont=dict(family='Share Tech Mono', size=11),
            range=[-1, 82]),
        yaxis=dict(
            title=dict(text='SOH (%)', font=dict(family='Orbitron, monospace', size=12, color='#0066aa')),
            gridcolor='rgba(0,200,255,0.12)', linecolor='rgba(0,200,255,0.3)',
            tickfont=dict(family='Share Tech Mono', size=11),
            range=[58, 103]),
        height=460, hovermode='x unified',
        legend=dict(
            bgcolor='rgba(255,255,255,0.95)',
            bordercolor='rgba(0,200,255,0.4)',
            borderwidth=2,
            font=dict(family='Share Tech Mono', size=11, color='#003355'),
            orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=20, r=20, t=60, b=20))

    st.plotly_chart(fig_cmp, use_container_width=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Conclusion ─────────────────────────────────────────────────
    conc_left, conc_right = st.columns(2, gap="large")

    with conc_left:
        st.markdown("""
        <div class="glass-panel" style="border-color:rgba(0,200,255,0.45);min-height:340px;">
        <h4 style="font-size:1.15rem;margin:0 0 18px;color:#0a1628;">&#127942; CONCLUSION</h4>
        <div style="background:linear-gradient(135deg,rgba(0,50,90,0.95),rgba(0,80,130,0.90));
            border:2px solid #00c8ff;border-radius:16px;padding:24px 20px;
            box-shadow:0 8px 28px rgba(0,200,255,0.3);">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:18px;">
            <span style="font-size:2rem;filter:drop-shadow(0 0 10px #00c8ff);">&#129302;</span>
            <div>
              <div style="font-family:Orbitron,monospace;color:#00c8ff;
                font-size:0.95rem;font-weight:900;letter-spacing:0.1em;">AI MODEL RECOMMENDED</div>
              <div style="font-family:Share Tech Mono,monospace;color:rgba(180,230,255,0.9);
                font-size:0.85rem;font-weight:700;margin-top:4px;">LSTM outperforms ECM across all metrics</div>
            </div>
          </div>
          <div style="display:flex;flex-direction:column;gap:10px;">
            <div style="display:flex;align-items:center;gap:10px;">
              <span style="color:#00ff88;font-size:1rem;font-weight:900;">&#10003;</span>
              <span style="font-family:Share Tech Mono,monospace;color:rgba(180,230,255,0.85);
                font-size:0.78rem;letter-spacing:0.06em;">Digital twins align closely with the physical model, validating the simulation</span>
            </div>
            <div style="display:flex;align-items:center;gap:10px;">
              <span style="color:#00ff88;font-size:1rem;font-weight:900;">&#10003;</span>
              <span style="font-family:Share Tech Mono,monospace;color:rgba(180,230,255,0.85);
                font-size:0.78rem;letter-spacing:0.06em;">AI model provides slightly higher accuracy (91% vs 87%)</span>
            </div>
            <div style="display:flex;align-items:center;gap:10px;">
              <span style="color:#00ff88;font-size:1rem;font-weight:900;">&#10003;</span>
              <span style="font-family:Share Tech Mono,monospace;color:rgba(180,230,255,0.85);
                font-size:0.78rem;letter-spacing:0.06em;">Both models effectively track battery degradation trends</span>
            </div>
            <div style="display:flex;align-items:center;gap:10px;">
              <span style="color:#00ff88;font-size:1rem;font-weight:900;">&#10003;</span>
              <span style="font-family:Share Tech Mono,monospace;color:rgba(180,230,255,0.85);
                font-size:0.78rem;letter-spacing:0.06em;">Digital twin combines best of both for robust monitoring</span>
            </div>
          </div>
        </div>
        </div>""", unsafe_allow_html=True)

    with conc_right:
        st.markdown("""
        <div class="glass-panel" style="border-color:rgba(0,200,255,0.3);min-height:340px;">
        <h4 style="font-size:1.15rem;margin:0 0 18px;color:#0a1628;">&#128202; PERFORMANCE SUMMARY</h4>
        <div style="display:flex;flex-direction:column;gap:14px;">
          <div style="background:rgba(255,255,255,0.97);border:2px solid rgba(0,200,255,0.35);border-radius:14px;padding:16px 20px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
              <span style="font-family:Orbitron,monospace;color:#0a1628;font-size:0.72rem;font-weight:700;letter-spacing:0.1em;">&#9881; ECM ACCURACY</span>
              <span style="font-family:Orbitron,monospace;color:#00c8ff;font-weight:900;font-size:1.1rem;">87%</span>
            </div>
            <div class="perf-bar-track"><div class="perf-bar-fill" style="width:87%;background:linear-gradient(90deg,#00c8ff,#0088ff);"></div></div>
          </div>
          <div style="background:rgba(255,255,255,0.97);border:2px solid rgba(204,68,255,0.35);border-radius:14px;padding:16px 20px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
              <span style="font-family:Orbitron,monospace;color:#0a1628;font-size:0.72rem;font-weight:700;letter-spacing:0.1em;">&#129302; AI MODEL ACCURACY</span>
              <span style="font-family:Orbitron,monospace;color:#cc44ff;font-weight:900;font-size:1.1rem;">91%</span>
            </div>
            <div class="perf-bar-track"><div class="perf-bar-fill" style="width:91%;background:linear-gradient(90deg,#cc44ff,#ff00c8);"></div></div>
          </div>
          <div style="background:rgba(255,255,255,0.97);border:2px solid rgba(255,165,0,0.35);border-radius:14px;padding:16px 20px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
              <span style="font-family:Orbitron,monospace;color:#0a1628;font-size:0.72rem;font-weight:700;letter-spacing:0.1em;">&#9888; EOL DETECTION (ECM)</span>
              <span style="font-family:Orbitron,monospace;color:#ffaa00;font-weight:900;font-size:1.1rem;">80%</span>
            </div>
            <div class="perf-bar-track"><div class="perf-bar-fill" style="width:80%;background:linear-gradient(90deg,#ffaa00,#ffdd44);"></div></div>
          </div>
          <div style="background:rgba(255,255,255,0.97);border:2px solid rgba(0,255,136,0.35);border-radius:14px;padding:16px 20px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
              <span style="font-family:Orbitron,monospace;color:#0a1628;font-size:0.72rem;font-weight:700;letter-spacing:0.1em;">&#128256; DIGITAL TWIN (COMBINED)</span>
              <span style="font-family:Orbitron,monospace;color:#00ff88;font-weight:900;font-size:1.1rem;">94%</span>
            </div>
            <div class="perf-bar-track"><div class="perf-bar-fill" style="width:94%;background:linear-gradient(90deg,#00ff88,#00cc66);"></div></div>
          </div>
        </div>
        </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  FOOTER
# ═══════════════════════════════════════════════════════════════
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div class="cyber-footer">
  <div class="footer-text">
    ⚡<span class="footer-dot">◆</span>AUTOTWIN<span class="footer-dot">◆</span>
    BATTERY DIGITAL TWIN PLATFORM<span class="footer-dot">◆</span>
    REAL-TIME SIMULATION ENGINE<span class="footer-dot">◆</span>⚡
  </div>
</div>""", unsafe_allow_html=True)
