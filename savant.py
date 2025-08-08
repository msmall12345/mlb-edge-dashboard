from __future__ import annotations
import io, csv, requests, datetime as dt
from typing import List, Dict, Any, Optional

SAVANT_CSV = "https://baseballsavant.mlb.com/statcast_search/csv"

def statcast_pitcher_game_logs(pitcher_id: int, start: str, end: str) -> List[Dict[str, Any]]:
    "
    Download Statcast CSV for a pitcher across a date range.
    start/end format: YYYY-MM-DD
    Returns list of dict rows.
    "
    params = {
        'player_type': 'pitcher',
        'player_id': pitcher_id,
        'hfPT': '',
        'hfAB': '',
        'hfBBT': '',
        'hfPR': '',
        'hfZ': '',
        'stadium': '',
        'hfBBL': '',
        'hfNewZones': '',
        'hfGT': '',
        'hfC': '',
        'hfSea': '',
        'hfSit': '',
        'hfOuts': '',
        'opponent': '',
        'batter_stands': '',
        'thrower_hand': '',
        'hfSA': '',
        'game_date_gt': start,
        'game_date_lt': end,
        'hfInfield': '',
        'team': '',
        'position': '',
        'hfOutfield': '',
        'hfRO': '',
        'home_road': '',
        'hfFlag': '',
        'hfPull': '',
        'metric_1': '',
        'hfInn': '',
        'min_pitches': '0',
        'min_results': '0',
        'group_by': 'count',
        'sort_col': 'game_date',
        'player_event_sort': 'api_p_release_speed',
        'sort_order': 'desc',
        'min_abs': '0',
        'type': 'details',
    }
    r = requests.get(SAVANT_CSV, params=params, timeout=30)
    r.raise_for_status()
    text = r.text
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)
