from __future__ import annotations
import os, json, datetime as dt
from typing import Dict, Any, List
from .feature_builders import build_features_stub
from .model import LogisticModelV1, fair_moneyline_from_prob
from .odds import devig_proportional, best_line
from .kelly import kelly_stake, expected_ev
from .utils import american_to_decimal

def run_day(date_str: str, bankroll: float=100000.0, mock: bool=True, providers: dict|None=None) -> Dict[str, Any]:
    # 1) Ingest games (mock)
    if mock:
        games = mock_games(date_str)
    else:
        games = fetch_games_from_providers(date_str, providers)

    # 2) Build features & predict
    model = LogisticModelV1()
    outputs = []
    for g in games:
        feats = build_features_stub(g)
        p_home = model.predict_proba(feats)
        fair_ml_home = fair_moneyline_from_prob(p_home)
        outputs.append({
            "game_id": g["game_id"],
            "home": g["home"],
            "away": g["away"],
            "p_home": p_home,
            "fair_ml_home": fair_ml_home,
        })

    # 3) Pull odds & devig (mock lines per game with two books)
    recommendations = []
    for out in outputs:
        lines = mock_lines(out["game_id"]) if mock else fetch_lines(out["game_id"])
        # assume home/away pair available from the same book for devig
        home_price = lines["pinnacle"]["home"]
        away_price = lines["pinnacle"]["away"]
        p_mkt_home, p_mkt_away = devig_proportional(home_price, away_price)
        edge = out["p_home"] - p_mkt_home

        # choose best playable price for home side (example strategy)
        home_lines = {book:quote["home"] for book,quote in lines.items()}
        book, price = best_line(home_lines)
        stake = kelly_stake(bankroll, price, out["p_home"], kelly_fraction=0.5, max_pct=0.02)
        ev = expected_ev(price, out["p_home"], stake)
        rec = {
            **out,
            "book": book,
            "price": price,
            "edge": edge,
            "stake": round(stake, 2),
            "expected_ev": round(ev, 2),
            "decimal": round(american_to_decimal(price), 3),
        }
        recommendations.append(rec)

    # 4) Persist output
    os.makedirs("/mnt/data/mlb_edge_pipeline/data/outputs", exist_ok=True)
    outpath = f"/mnt/data/mlb_edge_pipeline/data/outputs/recommendations_{date_str}.json"
    with open(outpath, "w") as f:
        json.dump(recommendations, f, indent=2)
    return {
        "date": date_str,
        "count": len(recommendations),
        "file": outpath,
        "recs": recommendations
    }

def mock_games(date_str: str):
    return [
        {"game_id": f"{date_str}_NYY_BOS", "date": date_str, "home": "NYY", "away": "BOS", "home_field": 0.03},
        {"game_id": f"{date_str}_LAD_SF", "date": date_str, "home": "LAD", "away": "SF", "home_field": 0.03},
    ]

def mock_lines(game_id: str):
    # simplistic prices, vary by game
    if "NYY" in game_id:
        return {
            "pinnacle": {"home": -128, "away": +118},
            "circa": {"home": -125, "away": +115},
        }
    else:
        return {
            "pinnacle": {"home": -142, "away": +132},
            "circa": {"home": -138, "away": +128},
        }

def fetch_games_from_db(date_str: str):
    raise NotImplementedError("Hook up to your DB.")

def fetch_lines(game_id: str):
    raise NotImplementedError("Hook up to your odds provider.")


def fetch_games_from_providers(date_str: str, providers: dict|None) -> list[dict]:
    if not providers or 'mlb' not in providers:
        raise RuntimeError("Pass providers={'mlb': MLBStatsAPIClient(), 'odds': OddsProvider(...)}")
    import datetime as dt
    mlb = providers['mlb']
    date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
    sched = mlb.schedule(date)
    games = []
    for g in sched:
        # statsapi returns 'game_id' as game_id or game_id may be 'game_id'/'game_pk'
        game_id = g.get('game_id') or g.get('game_pk') or g.get('gamePk') or str(g.get('game_id', ''))
        games.append({
            'game_id': str(game_id),
            'date': date_str,
            'home': g.get('home_name_abbrev') or g.get('teams', {}).get('home', {}).get('team', {}).get('abbreviation'),
            'away': g.get('away_name_abbrev') or g.get('teams', {}).get('away', {}).get('team', {}).get('abbreviation'),
            'home_field': 0.03,
        })
    return games
