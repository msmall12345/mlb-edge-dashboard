-- Core relational schema for MLB edge pipeline

CREATE TABLE IF NOT EXISTS games (
  game_id TEXT PRIMARY KEY,
  date DATE NOT NULL,
  start_time TIMESTAMP,
  home TEXT NOT NULL,
  away TEXT NOT NULL,
  park_id TEXT,
  roof TEXT,
  timezone TEXT
);

CREATE TABLE IF NOT EXISTS pitchers (
  game_id TEXT NOT NULL,
  team TEXT NOT NULL,
  sp_id TEXT NOT NULL,
  rest_days INT,
  pitch_count_limit INT,
  handedness TEXT,
  k_minus_bb REAL,
  xera REAL,
  xfip REAL,
  gb_rate REAL,
  hard_hit_rate REAL,
  velo_trend REAL,
  tto_penalty REAL,
  il_flag BOOLEAN,
  platoon_split REAL,
  PRIMARY KEY (game_id, team),
  FOREIGN KEY (game_id) REFERENCES games(game_id)
);

CREATE TABLE IF NOT EXISTS bullpens (
  team_date TEXT PRIMARY KEY,
  team TEXT NOT NULL,
  date DATE NOT NULL,
  xfip REAL,
  last3_ip REAL,
  top2_available BOOLEAN,
  lh_pct REAL,
  rh_pct REAL
);

CREATE TABLE IF NOT EXISTS batters (
  team_date_player TEXT PRIMARY KEY,
  team TEXT NOT NULL,
  date DATE NOT NULL,
  player_id TEXT NOT NULL,
  proj_pa REAL,
  woba REAL,
  wrc_plus_vs_l REAL,
  wrc_plus_vs_r REAL,
  avg_ev REAL,
  injury_status TEXT
);

CREATE TABLE IF NOT EXISTS defense (
  team_date TEXT PRIMARY KEY,
  team TEXT NOT NULL,
  date DATE NOT NULL,
  oaa REAL,
  drs REAL,
  catcher_framing REAL
);

CREATE TABLE IF NOT EXISTS weather (
  game_id TEXT PRIMARY KEY,
  temp_f REAL,
  wind_mph REAL,
  wind_dir TEXT,
  humidity REAL
);

CREATE TABLE IF NOT EXISTS odds (
  odds_id TEXT PRIMARY KEY,
  game_id TEXT NOT NULL,
  book TEXT NOT NULL,
  market TEXT NOT NULL, -- moneyline_home, moneyline_away, total_over_8.5, etc.
  line REAL,
  price INT, -- American odds
  ts TIMESTAMP NOT NULL,
  FOREIGN KEY (game_id) REFERENCES games(game_id)
);

CREATE TABLE IF NOT EXISTS model_outputs (
  game_id TEXT PRIMARY KEY,
  p_home_win REAL,
  mu_home_runs REAL,
  mu_away_runs REAL,
  fair_ml_home INT,
  fair_total REAL,
  ts TIMESTAMP NOT NULL,
  FOREIGN KEY (game_id) REFERENCES games(game_id)
);

CREATE TABLE IF NOT EXISTS bets (
  bet_id TEXT PRIMARY KEY,
  game_id TEXT NOT NULL,
  market TEXT NOT NULL,
  line REAL,
  price INT,
  stake REAL,
  kelly_frac REAL,
  expected_ev REAL,
  placed_ts TIMESTAMP NOT NULL,
  FOREIGN KEY (game_id) REFERENCES games(game_id)
);

CREATE TABLE IF NOT EXISTS results (
  game_id TEXT PRIMARY KEY,
  home_runs INT,
  away_runs INT,
  settled_ts TIMESTAMP
);
