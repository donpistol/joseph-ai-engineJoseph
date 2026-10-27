# Joseph AI Engine V2 — Matchup Intelligence

Mobile-friendly Streamlit app with three tabs: **Player Props**, **Matchups**, and **Prop Board**.

## Launch

```bash
pip install -r requirements.txt
streamlit run app.py
```

Use the local URL in a browser. For phone access from anywhere, deploy the project to a Streamlit-compatible host such as Streamlit Community Cloud. No hosting account or live API is included.

## Matchup inputs

- **NBA:** offense and defense are points scored/allowed per 100 possessions; pace is possessions per 48 minutes. Defense higher = weaker. Matchup projected scoring uses averaged offensive/defensive efficiencies multiplied by average pace.
- **NFL:** offense and defense are points scored/allowed per game. Offensive plays per game is shown as context but is not used in scoring calculations.
- **Home advantage:** signed points added to home expected score. **Lineup/injury adjustment:** signed points added to the respective team's expected score.
- **Margin/total SD:** user-selected standard deviations, not learned estimates. Win, spread-cover and totals probabilities use a normal approximation. Whole-number pushes are not separately accounted for.
- **Markets:** enter home moneyline, home spread, and game total with their American odds; the app compares implied break-even probability with the model estimate.

## Limitations

This is an **illustrative calculator**, not a trained, validated predictive AI. It does not retrieve real odds, injuries, player stats or schedules. Inputs are manual; probability quality depends on them. Matchup-adjustment sliders for player props are manual hypotheses, not derived automatically from the team matchup. No Hard Rock proprietary systems, account access or wager placement are included. No hit-rate or profitable-betting claims are supported without historical out-of-sample validation.
