
import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from PIL import Image
import re
from typing import List, Dict, Any
import datetime as dt

# ---------------- OCR (graceful) ----------------
def ocr_text(img: Image.Image) -> str:
    """
    Try RapidOCR first (no system deps). If not available, return empty string.
    The app will then allow manual paste/edit so it never crashes.
    """
    try:
        from rapidocr_onnxruntime import RapidOCR
        ocr = RapidOCR()
        np_img = np.array(img.convert("RGB"))
        result, _ = ocr(np_img)
        if result:
            return "\n".join([x[1] for x in result])
    except Exception:
        pass
    return ""

# --------------- Parsing -----------------
TEAM_LINE_RE = re.compile(r"([A-Z][A-Za-z\. ]+?)\s+([+-]?\d{3})\b")

def parse_slate(text: str) -> pd.DataFrame:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    pairs = []
    for ln in lines:
        m = TEAM_LINE_RE.search(ln)
        if m:
            team = m.group(1).strip()
            try:
                price = int(m.group(2))
            except Exception:
                continue
            pairs.append((team, price))
    games = []
    i = 0
    while i + 1 < len(pairs):
        t1, p1 = pairs[i]
        t2, p2 = pairs[i+1]
        games.append({"away_team": t1, "away_price": p1, "home_team": t2, "home_price": p2})
        i += 2
    return pd.DataFrame(games)

# --------------- Providers (schedule only for now) ---------------
def get_providers():
    from src.providers.mlb_statsapi import MLBStatsAPIClient
    return {"mlb": MLBStatsAPIClient()}

# --------------- Modeling ---------------
def run_model(df: pd.DataFrame, date_str: str) -> pd.DataFrame:
    from src.feature_builders import build_features_stub
    from src.model import LogisticModelV1
    from src.odds import devig_proportional
    from src.kelly import kelly_stake, expected_ev
    from src.pipeline import fetch_games_from_providers

    providers = get_providers()
    _ = fetch_games_from_providers(date_str, providers)  # not strictly needed here yet

    model = LogisticModelV1()
    out = []
    for _, row in df.iterrows():
        home = str(row.get("home_team","")).strip()
        away = str(row.get("away_team","")).strip()
        try:
            home_price = int(row.get("home_price"))
            away_price = int(row.get("away_price"))
        except Exception:
            continue

        feats = build_features_stub({"game_id": f"{date_str}_{home}_{away}", "home_field": 0.03})
        p_home = model.predict_proba(feats)
        try:
            p_mkt_home, _ = devig_proportional(home_price, away_price)
        except Exception:
            p_mkt_home = np.nan

        bankroll = 100000.0
        stake = kelly_stake(bankroll, home_price, p_home, kelly_fraction=0.5, max_pct=0.02)
        ev = expected_ev(home_price, p_home, stake)

        out.append({
            "date": date_str,
            "away": away, "home": home,
            "away_price": away_price, "home_price": home_price,
            "p_home_model": round(p_home,4),
            "p_home_market": None if pd.isna(p_mkt_home) else round(p_mkt_home,4),
            "edge_pct": None if pd.isna(p_mkt_home) else round((p_home - p_mkt_home)*100,2),
            "stake": round(stake,2),
            "expected_ev_$": round(ev,2)
        })
    return pd.DataFrame(out)

# --------------- UI ----------------
st.set_page_config(page_title="MLB Edge (Screenshot → Picks)", layout="wide")
st.title("MLB Edge — Upload Screenshot → Picks")

with st.sidebar:
    date_input = st.date_input("Slate Date", value=dt.date.today())
    date_str = date_input.strftime("%Y-%m-%d")
    st.caption("Tip: Clear, full-width odds screenshots OCR best.")

uploaded = st.file_uploader("Upload slate screenshot(s) (PNG/JPG)", type=["png","jpg","jpeg"], accept_multiple_files=True)

pages = []
if uploaded:
    for f in uploaded:
        img = Image.open(f)
        st.image(img, caption=f.name, use_column_width=True)
        text = ocr_text(img)

        if not text.strip():
            st.warning("OCR engine not available in this build. Paste the slate text or edit the table.")
            text = st.text_area(f"Paste text for {f.name}", value="", height=200)

        df = parse_slate(text) if text else pd.DataFrame(columns=["away_team","away_price","home_team","home_price"])
        st.write(f"Parsed games: {len(df)}")
        df = st.data_editor(df, num_rows="dynamic")
        pages.append(df)

if pages:
    combined = pd.concat(pages, ignore_index=True)
    st.subheader("Combined / Editable Slate")
    combined = st.data_editor(combined, num_rows="dynamic", key="combined_editor")

    if st.button("Run Analysis"):
        with st.spinner("Computing edges..."):
            try:
                results = run_model(combined, date_str)
                st.success("Done.")
                st.dataframe(results.sort_values("edge_pct", ascending=False))
                st.download_button("Download CSV", results.to_csv(index=False).encode("utf-8"),
                                   file_name=f"edges_{date_str}.csv", mime="text/csv")
            except Exception as e:
                st.error(f"Error: {e}")
else:
    st.info("Upload at least one screenshot to begin.")
