import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from pathlib import Path

# ---------------------------------------------------------------
# AquaSense — Pahang NRW repair-priority decision support tool
# ---------------------------------------------------------------
st.set_page_config(
    page_title="AquaSense — Pahang NRW",
    page_icon="💧",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent

# Theme-agnostic chart palette — each of these clears 4.5:1 contrast
# against both white and near-black backgrounds.
C_ACTUAL = "#158AA8"                 # historical series
C_FLAT   = "#8A9AA5"                 # unchanged forecast
C_FIXED  = "#B87614"                 # after repairs (3.72 white / 5.08 dark)
C_TARGET = "#D64545"                 # national target
C_BAND   = "rgba(27,143,179,.18)"    # prediction interval
C_GRID   = "rgba(128,140,148,.28)"   # gridlines

st.markdown("""
<style>
  /* ------------------------------------------------------------------
     Colour strategy — INHERITANCE, not detection.
     ------------------------------------------------------------------
     Two earlier approaches failed:
       - prefers-color-scheme desynchronises from Streamlit's own
         in-app light/dark toggle, which does not change it.
       - var(--text-color) is not exposed in every Streamlit version,
         so it silently fell back and locked to one colour.

     Streamlit already colours its own containers correctly for whatever
     theme is active. So custom elements simply DO NOT set a text colour
     and inherit it. Secondary text uses opacity, which is always a faded
     version of the correct colour. Borders use a neutral grey visible on
     both. Only the accent is an explicit value, chosen to clear contrast
     on both backgrounds (4.01 on white, 4.71 on dark).
     ------------------------------------------------------------------ */
  /* ------------------------------------------------------------------
     Type system — exactly two families throughout.
       DISPLAY  : headings, metric numbers, eyebrows, control names
       TEXT     : body copy, questions, readouts, tables, chart labels
     Both are common system stacks, so nothing depends on a web font
     loading before the app renders.
     ------------------------------------------------------------------ */
  :root {
      --aq-accent:#158AA8;
      --aq-line: rgba(130,142,150,.38);
      --aq-panel: rgba(130,142,150,.09);
      --aq-display: "Trebuchet MS", "Segoe UI", "Helvetica Neue", sans-serif;
      --aq-text: "Segoe UI", -apple-system, "Helvetica Neue", Arial, sans-serif;
  }

  html, body, .stApp, [class*="css"] { font-family: var(--aq-text); }

  h1, h2, h3, h4 {
      font-family: var(--aq-display);
      color: var(--aq-accent) !important;
      letter-spacing:-0.02em;
  }

  /* ---------- headline metric strip ---------- */
  .metric-strip {
      display:flex; gap:0;
      border-top:2px solid var(--aq-accent);
      border-bottom:1px solid var(--aq-line);
      margin:0 0 1.8rem 0;
  }
  .metric-cell { flex:1; padding:.9rem 1.2rem .9rem 0; }
  .metric-val {
      font-family: var(--aq-display);
      font-size:1.85rem; font-weight:700; color:var(--aq-accent);
      line-height:1.1; font-variant-numeric:tabular-nums;
  }
  .metric-lab {
      font-family: var(--aq-text);
      font-size:.72rem; text-transform:uppercase; letter-spacing:.09em;
      color:inherit; opacity:.72; margin-top:.25rem;
  }

  .eyebrow {
      font-family: var(--aq-display);
      font-size:.72rem; text-transform:uppercase; letter-spacing:.14em;
      color:var(--aq-accent); font-weight:700;
  }
  .note {
      font-family: var(--aq-text);
      font-size:.86rem; color:inherit; line-height:1.55;
  }

  /* Subtitle: fills the available width, then wraps cleanly.
     `nowrap` was truncating with an ellipsis and losing the sentence end,
     so it wraps instead, with balanced line lengths and no orphan word. */
  .subtitle-oneline {
      font-size:.86rem;
      margin-top:-.6rem;
      max-width: 100%;
      text-wrap: balance;
      overflow-wrap: break-word;
  }

  /* ---------- sidebar panel ---------- */
  .aq-panel {
      background: var(--aq-panel);
      border: 1px solid var(--aq-line);
      border-radius: 10px;
      padding: .85rem .9rem .1rem .9rem;
      margin-bottom: 1.1rem;
  }
  .aq-panel .eyebrow { display:block; margin-bottom:.4rem; }

  /* ---------- sidebar control blocks ---------- */
  .ctrl-name {
      font-family: var(--aq-display);
      font-size:.88rem; font-weight:700; color:var(--aq-accent);
      margin-bottom:.1rem;
  }
  .ctrl-q {
      font-family: var(--aq-text);
      font-size:.79rem; font-style:italic;
      color:inherit; opacity:.75;
      line-height:1.4; margin-bottom:.35rem;
  }
  .ctrl-read {
      font-family: var(--aq-text);
      font-size:.76rem; color:inherit; opacity:.88;
      line-height:1.45;
      margin-top:-.5rem; margin-bottom:1.5rem;
  }

  [data-testid="stSidebar"] { border-right:1px solid var(--aq-line); }

  /* Scope the font to TEXT elements only. A blanket `*` here also hits
     Streamlit's Material Symbols icons, whose glyphs are ligatures —
     overriding their font makes the collapse arrow render as the literal
     string "keyboard_double_arrow_left". */
  [data-testid="stSidebar"] p,
  [data-testid="stSidebar"] label,
  [data-testid="stSidebar"] span:not([class*="material"]):not([class*="Icon"]),
  [data-testid="stSidebar"] div.stMarkdown,
  [data-testid="stSidebar"] .ctrl-q,
  [data-testid="stSidebar"] .ctrl-read { font-family: var(--aq-text); }

  [data-testid="stSidebar"] .ctrl-name,
  [data-testid="stSidebar"] .eyebrow { font-family: var(--aq-display); }

  /* Never let the type system touch icon glyphs, anywhere in the app. */
  [data-testid="stIconMaterial"],
  span[class*="material-symbols"],
  span[class*="MaterialIcon"],
  [data-testid="stSidebarCollapseButton"] *,
  [data-testid="stExpanderToggleIcon"] {
      font-family: "Material Symbols Rounded", "Material Symbols Outlined",
                   "Material Icons" !important;
  }

  [data-testid="stDataFrame"] {
      border:1px solid var(--aq-line); border-radius:8px;
      font-family: var(--aq-text);
  }
  hr.aq {
      border:0; border-top:1px solid var(--aq-line);
      margin:2.4rem 0 1.6rem 0;
  }

  /* ---------- Plotly text inherits the page colour ---------- */
  .js-plotly-plot .xtick text,
  .js-plotly-plot .ytick text,
  .js-plotly-plot .legendtext,
  .js-plotly-plot .g-xtitle text,
  .js-plotly-plot .g-ytitle text {
      fill: currentColor !important;
  }
  .js-plotly-plot, .js-plotly-plot .plot-container { color: inherit; }
  .js-plotly-plot text { font-family: var(--aq-text) !important; }
</style>""", unsafe_allow_html=True)


# ---------------------------------------------------------------
# Data
# ---------------------------------------------------------------
@st.cache_data
def load():
    q = pd.read_csv(BASE_DIR / "lips_queue.csv")
    try:
        f = pd.read_csv(BASE_DIR / "nrw_forecast.csv")
    except FileNotFoundError:
        f = None
    return q, f

queue_base, fc = load()

ANNUAL_PRODUCTION_M3 = 658_300_000   # state total, from PAIP_final.csv


# ---------------------------------------------------------------
# Header
# ---------------------------------------------------------------
st.markdown('<div class="eyebrow">Pahang · 74 treatment plants · 2023–2025</div>',
            unsafe_allow_html=True)
st.title("AquaSense")
st.markdown(
    '<p class="note subtitle-oneline">'
    'A decision support tool for ranking which water treatment plants to '
    'repair first, based on the water they could actually recover.'
    '</p>', unsafe_allow_html=True)


# ---------------------------------------------------------------
# Controls — question sits above each slider
# ---------------------------------------------------------------
def control_header(name, question):
    st.markdown(f'<div class="ctrl-name">{name}</div>'
                f'<div class="ctrl-q">{question}</div>',
                unsafe_allow_html=True)

def control_readout(html):
    """Readout may contain simple inline HTML (<b>, <br>)."""
    st.markdown(f'<div class="ctrl-read">{html}</div>', unsafe_allow_html=True)


with st.sidebar:
    st.markdown(
        '<div class="aq-panel">'
        '<span class="eyebrow">Set your priorities</span>'
        '<p class="note" style="opacity:.82;font-size:.79rem">'
        'These four settings define a repair plan. The first two decide '
        '<b>which</b> plants are queued. The last two decide <b>how much</b> '
        'water that plan recovers.</p>'
        '</div>', unsafe_allow_html=True)

    # ---- 1. volume vs ease -------------------------------------
    control_header("Water or speed",
                   "Do you want the most water or the quickest fix?")
    W = st.slider(
        "Water or speed", 0.0, 1.0, 0.70, 0.05,
        label_visibility="collapsed",
        help="At 1.0 the queue is ranked purely by how much water each plant "
             "could recover, so the largest plants dominate. At 0.0 it ranks "
             "purely by ease of repair, favouring small plants with "
             "concentrated, findable bursts. The default of 0.70 keeps the "
             "queue volume-led while still letting repair difficulty move "
             "plants up or down.")
    control_readout(
        f"<b>{W:.0%}</b> weight on recoverable volume<br> "
        f"<b>{1-W:.0%}</b> on ease of repair<br>"
        + ("Volume-led — favours the largest leaks" if W >= 0.65 else
           "Balanced — volume and difficulty carry similar weight"
           if W >= 0.45 else
           "Ease-led — favours small, quick repairs"))

    # ---- 2. community need -------------------------------------
    control_header("Community need",
                   "Should districts that struggle most with a water cut go first?")
    ALPHA = st.slider(
        "Community need", 0.0, 1.0, 0.00, 0.05,
        label_visibility="collapsed",
        help="Applies the District Vulnerability Index, built from 2024 DOSM "
             "relative poverty and median household income. At 0 the queue is "
             "purely engineering — a cubic metre counts the same wherever it "
             "is lost. Raising it moves plants in higher-need districts up. "
             "Note this reduces total water recovered: it is a deliberate "
             "trade-off, not a free improvement.")
    control_readout(
        "No social weighting — ranked on water and repair effort alone"
        if ALPHA == 0 else
        f"Plants in higher-need districts move up<br>"
        f"Highest need: Bera, Jerantut<br>"
        f"Lowest need: Cameron Highlands ")

    # ---- 3. crew capacity --------------------------------------
    st.markdown('<div class="eyebrow">Dispatch plan</div>',
                unsafe_allow_html=True)
    st.write("")

    control_header("Crew capacity",
                   "How many plants can you send crews to repair?")
    N = st.slider(
        "Crew capacity", 1, 30, 10, label_visibility="collapsed",
        help="How many plants the plan covers, taken from the top of the "
             "queue. This does not change the ranking — only how far down "
             "it you commit resources.")
    control_readout(
    f"Top <b>{N}</b> of 74 plants<br>"
    f"<span style='opacity:.8'>Assumed repaired over 24 months</span>")

    # ---- 4. recovery rate --------------------------------------
    control_header("Repair effectiveness",
                   "How much of a plant's leakage does a repair actually stop?")
    RECOVERY = st.slider(
        "Repair effectiveness", 0.1, 1.0, 0.40, 0.05,
        label_visibility="collapsed",
        help="No repair eliminates all leakage at a plant — some always "
             "remains in unfound or inaccessible sections. This assumption "
             "affects only the 2030 projection, not the ranking. It is "
             "exposed rather than fixed because no repair-outcome data "
             "exists to estimate it from.")
    control_readout(
        f"Assumes <b>{RECOVERY:.0%}</b> of physical loss is recovered<br>"
        + ("Conservative" if RECOVERY <= 0.35 else
           "Moderate" if RECOVERY <= 0.6 else
           "Optimistic — few repair programmes achieve this"))


# ---------------------------------------------------------------
# Scoring — recomputed live from saved percentile ranks
# ---------------------------------------------------------------
q = queue_base.copy()
q["LIPS"] = 100 * (W * q.R_volume + (1 - W) * q.R_ease)
q["PRI"]  = q.LIPS * (1 + ALPHA * q.DVI)

q["rank_engineering"] = q.LIPS.rank(ascending=False).astype(int)
q["rank_final"]       = q.PRI.rank(ascending=False).astype(int)
q["moved"]            = q.rank_engineering - q.rank_final

q = q.sort_values("PRI", ascending=False).reset_index(drop=True)
selected = q.head(N)

recovered_m3 = selected.annual_recoverable.sum() * RECOVERY
recovered_pp = recovered_m3 / ANNUAL_PRODUCTION_M3 * 100
share_of_all = (selected.annual_recoverable.sum()
                / q.annual_recoverable.sum() * 100)

st.markdown(f"""
<div class="metric-strip">
  <div class="metric-cell"><div class="metric-val">{recovered_m3/1e6:.1f}M m³</div>
    <div class="metric-lab">Recovered per year</div></div>
  <div class="metric-cell"><div class="metric-val">{recovered_pp:.1f} pp</div>
    <div class="metric-lab">Cut in state NRW</div></div>
  <div class="metric-cell"><div class="metric-val">{share_of_all:.0f}%</div>
    <div class="metric-lab">Of all recoverable water</div></div>
  <div class="metric-cell"><div class="metric-val">{selected.District.nunique()}</div>
    <div class="metric-lab">Districts covered</div></div>
</div>""", unsafe_allow_html=True)


# ===============================================================
# 1 — Repair queue
# ===============================================================
st.subheader("Repair queue")

show = selected[["Plant_Name", "District", "annual_recoverable",
                 "nrw_pct", "PRI", "moved"]].copy()
show.insert(0, "#", range(1, len(show) + 1))
show["annual_recoverable"] = show.annual_recoverable / 1e6
show["moved"] = show.moved.apply(
    lambda m: "—" if m == 0 else (f"▲{m}" if m > 0 else f"▼{abs(m)}"))
show.columns = ["#", "Plant", "District", "Recoverable Mm³",
                "Loss %", "Score", "Moved"]

# Explicit display formats — rounding the values is not enough, since
# Streamlit trims trailing zeros (2.50 would render as 2.5).
st.dataframe(
    show, hide_index=True, use_container_width=True,
    height=min(36 * len(show) + 40, 700),
    column_config={
        "#": st.column_config.NumberColumn(width="small"),
        "Recoverable Mm³": st.column_config.NumberColumn(
            format="%.2f", help="Physical leakage recoverable per year"),
        "Loss %": st.column_config.NumberColumn(
            format="%.1f", help="Non-revenue water as a share of production"),
        "Score": st.column_config.NumberColumn(
            format="%.1f", help="Priority score — higher is more urgent"),
        "Moved": st.column_config.TextColumn(
            width="small",
            help="Rank change once community need is applied"),
    })

st.markdown(
    '<p class="note" style="opacity:.78;margin-top:-.2rem">'
    'Ranked by recoverable water and ease of repair, then adjusted for '
    'community need. Loss % is shown for reference only — it does not '
    'affect the ranking.</p>', unsafe_allow_html=True)

st.download_button("Download this queue",
                   selected.to_csv(index=False),
                   "repair_queue.csv", "text/csv")


# ===============================================================
# 2 — Forecast
# ===============================================================
st.markdown('<hr class="aq">', unsafe_allow_html=True)
st.subheader("Effect on the 2030 target")

if fc is None:
    st.warning("nrw_forecast.csv not found — place it alongside app.py.")
else:
    act = fc[fc.type == "actual"]
    fut = fc[fc.type == "forecast"].reset_index(drop=True)

    # Recovery phases in linearly over 24 months, then holds.
    ramp = np.minimum(np.arange(1, len(fut) + 1) / 24, 1.0)
    improved = fut.nrw_pct.values - recovered_pp * ramp

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(fut.date) + list(fut.date[::-1]),
        y=list(fut.hi80) + list(fut.lo80[::-1]),
        fill="toself", fillcolor=C_BAND,
        line=dict(width=0), hoverinfo="skip",
        name="80% prediction interval"))
    fig.add_trace(go.Scatter(
        x=act.date, y=act.nrw_pct, mode="lines",
        line=dict(color=C_ACTUAL, width=2.5), name="Actual"))
    fig.add_trace(go.Scatter(
        x=fut.date, y=fut.nrw_pct, mode="lines",
        line=dict(color=C_FLAT, width=2, dash="dash"),
        name="No change"))
    fig.add_trace(go.Scatter(
        x=fut.date, y=improved, mode="lines",
        line=dict(color=C_FIXED, width=3),
        name=f"After {N} repairs"))
    fig.add_hline(y=25, line=dict(color=C_TARGET, width=1.5, dash="dot"),
                  annotation_text="National target 25%",
                  annotation_position="bottom right",
                  annotation_font=dict(color=C_TARGET, size=12))

    axis = dict(gridcolor=C_GRID, zerolinecolor=C_GRID, linecolor=C_GRID)

    fig.update_layout(
        height=420, margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(title="NRW (%)", **axis),
        xaxis=dict(nticks=8, **axis),
        legend=dict(orientation="h", y=-.16, x=0, font=dict(size=12)),
        font=dict(size=12))
    st.plotly_chart(fig, use_container_width=True)

    end_no  = fut.nrw_pct.iloc[-1]
    end_yes = improved[-1]
    gap = end_yes - 25

    if gap <= 0:
        st.success(f"**Target met.** Repairing {N} plants brings Pahang to "
                   f"{end_yes:.1f}% by 2030, from {end_no:.1f}% unchanged.")
    else:
        st.info(f"**{gap:.1f} points short.** Repairing {N} plants brings "
                f"Pahang to {end_yes:.1f}% by 2030, from {end_no:.1f}% "
                f"unchanged. Add more plants or raise the recovery rate "
                f"to close the gap.")


# ===============================================================
# 3 — How it works
# ===============================================================
st.markdown('<hr class="aq">', unsafe_allow_html=True)

with st.expander("How the score works"):
    st.markdown("""
**Recoverable Water**

This only includes actual physical leaks. Issues like inaccurate meters or
billing mistakes are excluded because fixing them requires a metering
programme, not a repair crew.

**Ease of Repair**

This is an overall score based on pipe length, plant age, and how clustered
the leaks are. Plants with frequent, concentrated bursts have leaks that are
easier to locate, while slow leaks spread across long rural networks are much
harder to find. No actual repair cost data is available so this structural
score is used instead.

**Why Percentile Ranks Are Used**

Raw numbers are not combined directly. Recoverable water varies about 163× across the 
74 plants, while repair difficulty varies only about 5×. Combining raw values lets scale 
differences decide the ranking rather than the weighting you choose. Converting both 
into percentile ranks puts them on the same footing so the slider can actually shift the 
balance between them.

**District Hardship**

This is based on 2024 government data for median household income and relative
poverty. Income doesn't affect *where* leaks happen — that depends on pipe
geography — but it highlights which communities may suffer most during a water
supply disruption.

**The 2030 Projection**

This assumes repairs are completed gradually over 24 months rather than all at
once. The forecast uses a damped Holt model fitted on 36 months of data. Treat
it as a general trend rather than an exact point estimate since predictions
get less precise the further ahead they run.
""")
