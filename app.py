
import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from PIL import Image
import re
from typing import List, Dict, Any
import datetime as dt

def ocr_text(img): if not text.strip():
    st.warning("OCR isn’t available in this build. You can paste the slate text below or edit the table.")
    text = st.text_area("Paste slate text (optional)", value="", height=200)
    # Try RapidOCR first (no system packages needed)
    try:
        from rapidocr_onnxruntime import RapidOCR
        import numpy as np
        ocr = RapidOCR()
        np_img = np.array(img.convert("RGB"))
        result, _ = ocr(np_img)
        if result:
            return "\n".join([x[1] for x in result])
    except Exception:
        pass
    # If OCR unavailable, just return empty string (we'll let the user edit/paste)
    return ""

def parse_slate(text: str) -> pd.DataFrame:
    # Extract rows: look for patterns of "Team ... ML price" for each matchup
    # We'll capture blocks separated by times; then read pairs
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    # Collect potential team + ML pairs
    pairs = []
    for ln in lines:
        # Example fragments like "Cincinnati Reds -145 ML" or "Pittsburgh Pirates +105"
        m = re.search(r"([A-Z][A-Za-z\. ]+?)\s+([+-]?\d{3})\b", ln)
        if m:
            team = m.group(1).strip()
            price = int(m.group(2))
            pairs.append((team, price))
    # Convert consecutive pairs into games
    games = []
    i = 0
    while i + 1 < len(pairs):
        t1, p1 = pairs[i]
        t2, p2 = pairs[i+1]
        games.append({"away_team": t1, "away_price": p1, "home_team": t2, "home_price": p2})
        i += 2
    df = pd.DataFrame(games)
    return df

def get_providers():
    from src.providers.mlb_statsapi import MLBStatsAPIClient
    from src.providers.odds_provider import OddsProvider
    return {
        "mlb": MLBStatsAPIClient(),
        # odds not needed (we're using the screenshot); left here if needed
    }

def run_model(df: pd.DataFrame, date_str: str) -> pd.DataFrame:
    # Use our pipeline but override odds with screenshot prices
    from src.feature_builders import build_features_stub
    from src.model import LogisticModelV1, fair_moneyline_from_prob
    from src.odds import devig_proportional, best_line
    from src.kelly import kelly_stake, expected_ev
    from src.pipeline import fetch_games_from_providers

    providers = get_providers()
    schedule_games = fetch_games_from_providers(date_str, providers)
    # map abbrev names guessed from screenshot to schedule abbreviations is tricky,
    # so we match by substring heuristic; allow manual corrections in UI later.
    model = LogisticModelV1()
    out_rows = []
    for _, row in df.iterrows():
        away = row["away_team"]
        home = row["home_team"]
        home_price = int(row["home_price"])
        away_price = int(row["away_price"])

        # Build dummy features for now; real system would query SP/bullpen/etc.
        feats = build_features_stub({
            "game_id": f"{date_str}_{home}_{away}",
            "home_field": 0.03
        })
        p_home = model.predict_proba(feats)
        # De-vig market prob using screenshot prices
        try:
            p_mkt_home, p_mkt_away = devig_proportional(home_price, away_price)
        except Exception:
            p_mkt_home, p_mkt_away = (np.nan, np.nan)
        # Kelly & EV
        bankroll = 100000.0
        stake = kelly_stake(bankroll, home_price, p_home, kelly_fraction=0.5, max_pct=0.02)
        ev = expected_ev(home_price, p_home, stake)
        out_rows.append({
            "away": away, "home": home,
            "home_price": home_price, "away_price": away_price,
            "p_home_model": round(p_home, 4),
            "p_home_market": round(p_mkt_home,4) if p_mkt_home==p_mkt_home else None,
            "edge_pct": round((p_home - p_mkt_home)*100, 2) if p_mkt_home==p_mkt_home else None,
            "stake": round(stake, 2),
            "exp_ev_$": round(ev, 2),
        })
    return pd.DataFrame(out_rows)

st.set_page_config(page_title="MLB Edge (Screenshot → Picks)", layout="wide")
st.title("MLB Edge (Upload Screenshot → Picks)")

with st.sidebar:
    date_input = st.date_input("Slate Date", value=dt.date.today())
    date_str = date_input.strftime("%Y-%m-%d")
    st.markdown("Upload an odds-board **screenshot** (moneylines required).")

uploaded = st.file_uploader("Upload slate screenshot (PNG/JPG)", type=["png","jpg","jpeg"], accept_multiple_files=True)

if uploaded:
    pages = []
    for file in uploaded:
        img = Image.open(file)
        st.image(img, caption=file.name, use_column_width=True)
        text = ocr_text(img)
        st.expander(f"OCR Text: {file.name}").write(text)
        df = parse_slate(text)
        if not df.empty:
            st.success(f"Parsed {len(df)} games from {file.name}. You can edit below before running.")
            df = st.data_editor(df, num_rows="dynamic")
            pages.append(df)
        else:
            st.warning(f"No games parsed from {file.name}. Edit manually below.")
            empty = pd.DataFrame([{"away_team":"", "away_price":+110, "home_team":"", "home_price":-120}])
            pages.append(st.data_editor(empty, num_rows="dynamic"))
    if pages:
        combined = pd.concat(pages, ignore_index=True)
        st.subheader("Combined Slate (Editable)")
        combined = st.data_editor(combined, num_rows="dynamic")
        if st.button("Run Analysis"):
            with st.spinner("Pulling live data & computing edges..."):
                try:
                    results = run_model(combined, date_str)
                    st.success("Done.")
                    st.dataframe(results.sort_values("edge_pct", ascending=False))
                    st.download_button("Download CSV", results.to_csv(index=False).encode("utf-8"), file_name=f"edges_{date_str}.csv", mime="text/csv")
                except Exception as e:
                    st.error(f"Error during analysis: {e}")
else:
    st.info("Upload at least one screenshot to begin.")
