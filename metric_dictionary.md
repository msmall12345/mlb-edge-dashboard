# MLB Metric Dictionary (Signal Stack v1)

Each metric lists a definition, directionality (↑ good for home, ↓ bad for home), and notes.

## Starting Pitcher (SP)
- **K-BB%**: Strikeout% minus Walk%. ↑ Higher favors that pitcher/team.
- **xERA/xFIP**: Expected ERA / Expected FIP. ↓ Lower is better.
- **Stuff+ (proxy allowed)**: Composite of pitch quality. ↑
- **GB%**: Groundball rate. Contextual (↑ in HR-heavy parks).
- **HardHit% (HH%)**: Share of batted balls ≥95 mph. ↓
- **Velo trend (3/5 starts)**: Rolling avg fastball velocity vs season avg. ↑
- **TTO penalty**: Performance drop each time through order. ↓ (more negative worse).
- **Rest days**: Days since last start. Too low → ↓ (fatigue). Too high → check sharpness.
- **IL history**: Recent injuries. ↓
- **Platoon splits**: SP vs L/R batters. Contextual with opponent lineup.

## Bullpen
- **xFIP (pen)**: Lower better ↓
- **Last 3 days IP / leverage**: Fatigue proxy; high recent usage ↓
- **Top 2 relievers available**: Boolean/percent available ↑
- **Handedness mix (LH%/RH%)**: Matchup leverage vs opponent splits ↑

## Offense
- **Team wRC+ vs SP handedness**: Park-adjusted run creation. ↑
- **Projected lineup sum of wOBA / wRC+**: ↑
- **Quality of contact (EV, HH%)**: ↑ EV (with plate discipline) → ↑
- **Plate discipline (O-Swing%, Z-Contact%)**: Lower O-Swing% and higher Z-Contact% ↑
- **BsR (baserunning)**: ↑
- **Key injuries**: Starters out ↓

## Defense
- **OAA/DRS**: Outs Above Average / Defensive Runs Saved. ↑
- **Catcher framing**: Extra strikes created. ↑

## Park & Weather
- **Park factor (overall, HR)**: >100 boosts offense. For totals ↑; for ML, context.
- **Temperature**: Warmer → ↑ run environment.
- **Wind speed/direction**: Out to CF ↑; in from CF ↓
- **Humidity**: Higher often ↑ carry.
- **Roof status**: Closed reduces variance ↓

## Travel & Rest
- **Consecutive games / days since last game**: Fatigue proxy ↓
- **Time-zone hops**: East-to-west same-day ↓

## Market Priors
- **Team rating/Elo prior**: Low-weight baseline; decays weekly.
